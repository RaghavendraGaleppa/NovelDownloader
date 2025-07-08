import os
import traceback
import re
import json
import argparse
import time # For potential future use with actual translation APIs
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from rich.console import Console
from rich.text import Text
from main import db_client
from bson.objectid import ObjectId
from datetime import datetime
from pymongo.database import Database


# Create a thread-safe console instance
console = Console()

# Attempt to import the translation function and providers
try:
    from src.translation.openrouter import translate_chinese_to_english, api_providers, LOADED_API_KEYS
    TRANSLATION_AVAILABLE = True
except ImportError:
    console.print("⚠️  WARNING: openrouter.py not found or its components could not be imported.", style="yellow")
    console.print("Translation functionality will be disabled; using placeholder.", style="yellow")
    TRANSLATION_AVAILABLE = False
    api_providers = {} # Define as empty if import fails
    LOADED_API_KEYS = []

def create_translation_progress_record(db: Database, novel_id: ObjectId, raw_chapter_id: ObjectId, translated_title: str) -> ObjectId:
    """
    Creates a record in the translation_progress collection.
    """
    record = {
        "novel_id": novel_id,
        "raw_chapter_id": raw_chapter_id,
        "title": translated_title,
        "pickup_epoch": time.time(),
        "status": "in_progress"
    }
    result = db.translation_progress.insert_one(record)
    console.print(f"Created translation progress record for raw chapter {raw_chapter_id}", style="green")
    return result.inserted_id


def finalize_translation_record(db: Database, progress_id: ObjectId, status: str, saved_at: str, provider: str, n_tries: int):
    """
    Moves the translation record from translation_progress to translated_chapters
    and updates it with the final status.
    """
    progress_record = db.translation_progress.find_one({"_id": progress_id})
    if progress_record:
        del progress_record["_id"]  # Remove old ID to allow insertion
        progress_record["status"] = status
        progress_record["saved_at"] = saved_at
        progress_record["end_epoch"] = time.time()
        progress_record["provider"] = provider
        progress_record["n_tries"] = n_tries

        db.translated_chapters.insert_one(progress_record)
        db.translation_progress.delete_one({"_id": progress_id})
        console.print(f"Finalized translation for progress record {progress_id} with status {status}", style="green" if status == "completed" else "red")


def _update_novel_translated_chapters_available(db: Database, novel_id: ObjectId):
    """
    Updates the 'translated_chapters_available' field with the total count of
    completed translations for the novel.
    """
    count = db.translated_chapters.count_documents({
        "novel_id": novel_id,
        "status": "completed"
    })
    
    db.novels.update_one(
        {"_id": novel_id},
        {"$set": {"translated_chapters_available": count}}
    )
    console.print(f"Updated 'translated_chapters_available' for novel {novel_id} to {count}", style="dim")


def _process_single_chapter_from_db(
    raw_chapter: dict,
    db: Database,
    novel_folder_path: str,
):
    """
    Processes a single chapter from a raw chapter record from the database.
    """
    raw_chapter_id = raw_chapter["_id"]
    chapter_num = raw_chapter.get("chapter_number", "N/A")
    console.print(f"Processing chapter {raw_chapter_id} (Chapter Num: {chapter_num}) for translation.", style="dim")
    novel_id = raw_chapter["novel_id"]
    chapter_number = raw_chapter.get("chapter_number")
    try:
        with open(raw_chapter["saved_at"], 'r', encoding='utf-8') as f:
            chapter_content = f.read()
    except Exception as e:
        console.print(f"Error reading raw chapter file {raw_chapter['saved_at']}: {e}", style="red")
        raise
    provider = None

    # Check for existing translation record to resume/retry
    existing_translation = db.translated_chapters.find_one({"raw_chapter_id": raw_chapter_id})
    
    current_pickup_epoch = time.time()

    if existing_translation:
        record_id = existing_translation["_id"]
        n_tries = existing_translation.get("n_tries", 0) + 1
        db.translated_chapters.update_one(
            {"_id": record_id},
            {
                "$set": {
                    "status": "in_progress",
                    "pickup_epoch": current_pickup_epoch,
                    "n_tries": n_tries,
                    "chapter_number": chapter_number,
                },
                "$unset": {"end_epoch": "", "provider": "", "time_taken_epoch": ""}  # Clear old data
            }
        )
    else:
        n_tries = 1
        # Create the record in translated_chapters first to mark it as in-progress
        initial_record = {
            "novel_id": novel_id,
            "raw_chapter_id": raw_chapter_id,
            "title": None,
            "pickup_epoch": current_pickup_epoch,
            "status": "in_progress",
            "n_tries": n_tries,
            "chapter_number": chapter_number
        }
        result = db.translated_chapters.insert_one(initial_record)
        record_id = result.inserted_id

    try:
        # 1. Translate content
        translated_content, provider = translate(chapter_content)
        if translated_content.startswith("Error:"):
            raise Exception(f"Translation failed: {translated_content}")

        # 2. Extract title from content
        lines = translated_content.splitlines()
        translated_title = lines[0] if lines else raw_chapter["title"]
        if translated_title.startswith("#"):
            translated_title = translated_title.lstrip("# ").strip()

        # 3. Save translated chapter
        translation_dir = os.path.join(novel_folder_path, "Translations")
        _ensure_directory_exists(translation_dir)
        
        if chapter_number is None:
            # Fallback for old records that might not have chapter_number
            safe_filename = "".join(x for x in translated_title if x.isalnum() or x in " ._").rstrip()
            safe_filename = safe_filename[:100] # Truncate to be safe
        else:
            safe_filename = f"Chapter_{chapter_number:05d}"
        
        save_path = os.path.join(translation_dir, f"{safe_filename}.md")
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        # 4. Finalize record on success
        current_end_epoch = time.time()
        db.translated_chapters.update_one(
            {"_id": record_id},
            {"$set": {
                "status": "completed",
                "title": translated_title,
                "saved_at": save_path,
                "end_epoch": current_end_epoch,
                "provider": provider,
                "time_taken_epoch": current_end_epoch - current_pickup_epoch
            }}
        )
        # Update the main progress document
        db.translation_progress.update_one(
            {"novel_id": novel_id},
            {"$inc": {"completed_chapters": 1}, "$set": {"last_updated_epoch": time.time()}}
        )
        _update_novel_translated_chapters_available(db, novel_id)
        console.print(f"Successfully translated and saved chapter {chapter_number} ({raw_chapter_id}) in {current_end_epoch - current_pickup_epoch} seconds", style="green")

    except Exception as e:
        console.print(f"Error processing chapter {raw_chapter_id}: {e}", style="red")
        # Finalize record on failure
        current_end_epoch = time.time()
        db.translated_chapters.update_one(
            {"_id": record_id},
            {"$set": {"status": "failed", "end_epoch": current_end_epoch, "provider": provider if provider else "N/A", "time_taken_epoch": current_end_epoch - current_pickup_epoch}}
        )
        raise e  # Re-raise the exception to be caught by the main loop


def translate_novel_by_id(novel_id: str, workers: int = 1, skip_validation: bool = False, wait_for_new_chapters: bool = False):
    """
    Translates a novel using the new database-driven approach.
    """
    if not skip_validation and not perform_api_validation():
        return

    db = db_client
    novel_object_id = ObjectId(novel_id)

    novel = db.novels.find_one({"_id": novel_object_id})
    if not novel:
        console.print(f"Novel with id {novel_id} not found.", style="red")
        return

    novel_folder_path = novel.get("folder_path")
    if not novel_folder_path:
        console.print(f"Novel with id {novel_id} is missing the 'folder_path' attribute. Cannot determine where to save translations.", style="red")
        return

    novel_name = novel["novel_name"]
    console.print(f"Starting translation for novel '{novel_name}' ({novel_id}) with {workers} workers.", style="bold blue")
    

    while True:

        # 1. Get all raw chapter IDs for this novel, sorted by creation time (ascending)
        all_raw_chapter_docs = db.raw_chapters.find({"novel_id": novel_object_id}, {"_id": 1}).sort("_id", 1)
        all_raw_chapter_ids_sorted = [str(doc["_id"]) for doc in all_raw_chapter_docs]

        # 2. Get all raw_chapter_ids that have already been successfully translated
        completed_chapters_cursor = db.translated_chapters.find(
            {"novel_id": novel_object_id, "status": "completed"},
            {"raw_chapter_id": 1, "_id": 0}
        )
        completed_raw_ids = {str(c["raw_chapter_id"]) for c in completed_chapters_cursor}

        # 3. Determine which chapters to process, preserving the original sort order
        chapters_to_process_ids = [
            chap_id for chap_id in all_raw_chapter_ids_sorted if chap_id not in completed_raw_ids
        ]

        console.print(f"Found {len(all_raw_chapter_ids_sorted)} total raw chapters.", style="blue")
        console.print(f"Found {len(completed_raw_ids)} already completed chapters.", style="blue")
        console.print(f"Found {len(chapters_to_process_ids)} chapters to translate.", style="bold blue")

        if not chapters_to_process_ids:
            console.print("All chapters already translated.", style="green")
            return

        # 4. Initialize/update the main progress document
        db.translation_progress.update_one(
            {"novel_id": novel_object_id},
            {"$set": {
                "novel_id": novel_object_id,
                "total_chapters": len(all_raw_chapter_ids_sorted),
                "completed_chapters": len(completed_raw_ids),
                "last_updated_epoch": time.time()
            }},
            upsert=True
        )

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for chapter_id in chapters_to_process_ids:
                raw_chapter_doc = db.raw_chapters.find_one({"_id": ObjectId(chapter_id)})
                if raw_chapter_doc:
                    futures.append(executor.submit(_process_single_chapter_from_db, raw_chapter_doc, db, novel_folder_path))

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    console.print(f"A worker failed while processing a chapter: {e}", style="red")
                    # Print traceback
                    traceback.print_exc()

        if not wait_for_new_chapters:
            console.print(f"Translation finished for novel {novel_id}.", style="bold green")
            break
        else:
            console.print(f"Waiting for new chapters to be added to the database...", style="bold blue")
            time.sleep(10)


def validate_api_keys() -> tuple[bool, str | None]:
    """
    Validates that the secrets.json file exists and contains at least one valid key.
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not TRANSLATION_AVAILABLE:
        return False, "Translation module not available"
    
    if not os.path.exists("secrets.json"):
        return False, "secrets.json file not found. Please create it from secrets.example.json."
        
    if not LOADED_API_KEYS:
        return False, "No valid API keys found in secrets.json. Please check the file format."
        
    return True, None

def test_api_connectivity(test_all: bool = False) -> tuple[bool, str]:
    """
    Tests API connectivity by attempting a simple translation.
    
    Args:
        test_all (bool): If True, tests all keys. If False, tests only the first valid key.
        
    Returns:
        tuple: (is_connected: bool, result_message: str)
    """
    test_message = "Hello"
    keys_to_test = LOADED_API_KEYS if test_all else LOADED_API_KEYS[:1]
    
    if not keys_to_test:
        return False, "No keys available to test."

    console.print(f"🔍 Testing API connectivity for {len(keys_to_test)} key(s)...", style="blue")
    
    overall_success = True
    final_message = ""

    for i, key_info in enumerate(keys_to_test):
        provider_name = key_info.get("provider")
        key_name = key_info.get("name", f"Provider: {provider_name}")
        
        console.print(f"  - Testing Key #{i + 1}: [bold cyan]{key_name}[/bold cyan]...", end="")
        
        # This is a simplified, targeted test, not using the full fallback logic.
        try:
            # We are calling a simplified, targeted version of translate for testing
            result, _ = translate_chinese_to_english(test_message, key_override=key_info)
            
            if result.startswith("Error:"):
                console.print(" [bold red]FAILED[/bold red]")
                final_message += f"\\n  - {key_name}: {result}"
                overall_success = False
            else:
                console.print(" [bold green]SUCCESS[/bold green]")

        except Exception as e:
            console.print(" [bold red]FAILED[/bold red]")
            final_message += f"\\n  - {key_name}: Exception - {e}"
            overall_success = False

    if overall_success:
        return True, "All tested keys connected successfully."
    else:
        return False, f"One or more API keys failed the connectivity test:{final_message}"

def perform_api_validation(test_all_keys: bool = False) -> bool:
    """
    Performs complete API validation including key file check and connectivity.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    console.print(f"\\n🔧 Validating API key configuration from secrets.json...", style="bold blue")
    
    # Step 1: Validate key file and contents
    config_valid, config_error = validate_api_keys()
    if not config_valid:
        console.print(f"❌ API Configuration Error: {config_error}", style="red")
        console.print("\\n💡 To fix this:", style="yellow")
        if config_error and "not found" in config_error:
            console.print("   1. Copy 'secrets.example.json' to 'secrets.json'", style="cyan")
            console.print("   2. Add your API keys to 'secrets.json'", style="cyan")
        elif config_error and "No valid API keys" in config_error:
            console.print("   1. Ensure 'secrets.json' contains a list under the 'api_keys' key.", style="cyan")
            console.print("   2. Ensure each item has a 'provider' and 'key'.", style="cyan")
        return False
    
    console.print("✅ API key configuration is valid.", style="green")
    
    # Step 2: Test connectivity
    connectivity_valid, connectivity_message = test_api_connectivity(test_all=test_all_keys)
    if not connectivity_valid:
        console.print(f"❌ API Connectivity Error: {connectivity_message}", style="red")
        console.print("\\n💡 Possible solutions:", style="yellow")
        console.print("   1. Check your internet connection.", style="cyan")
        console.print("   2. Verify your API keys in secrets.json are correct and have sufficient credits.", style="cyan")
        console.print("   3. Check if the API services (Chutes, OpenRouter) are available.", style="cyan")
        return False
    
    console.print("✅ API validation completed successfully.", style="bold green")
    return True

def translate(text: str) -> tuple[str, str | None]:
    """
    Translates text using the fallback logic from OpenRouter API if available,
    otherwise returns original text (placeholder behavior).
    """
    if TRANSLATION_AVAILABLE:
        translated_text, provider = translate_chinese_to_english(text)
        
        # Check if the translation itself returned an error string from the API wrapper
        if translated_text.startswith(("Error:", "HTTP error", "Connection error", 
                                       "Timeout error", "An unexpected error", 
                                       "An unforeseen error", "Rate limit exceeded")):
            return translated_text, provider # Propagate the error message
        return translated_text, provider
    else:
        return text, None # Placeholder behavior

def _ensure_directory_exists(dir_path: str) -> bool:
    """Ensures the directory exists, creating it if necessary."""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            console.print(f"📁 Created directory: {dir_path}", style="green")
        except OSError as e:
            console.print(f"❌ Error creating directory {dir_path}: {e}", style="red")
            return False
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Translate raw novel chapters using the dynamic key system."
    )
    parser.add_argument("-n", "--novel-title",
                        required=True,
                        help="The title of the novel to translate (must exist in the database).")
    parser.add_argument("-w", "--workers",
                        type=int,
                        default=1,
                        help="Number of worker threads for parallel processing (default: 1).")

    parser.add_argument("--skip-validation",
                        action="store_true",
                        help="Skip API validation before starting translation (not recommended).")

    args = parser.parse_args()

    # Find novel_id from title
    novel = db_client.novels.find_one({"novel_name": args.novel_title})
    if not novel:
        console.print(f"Novel with title '{args.novel_title}' not found.", style="red")
    else:
        novel_id = str(novel["_id"])
        translate_novel_by_id(
            novel_id=novel_id,
            workers=args.workers,
            skip_validation=args.skip_validation
        ) 