import os
import re
import json
import argparse
import time # For potential future use with actual translation APIs
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Attempt to import the translation function and providers
try:
    from openrouter import translate_chinese_to_english, api_providers # model_names no longer directly needed here
    OPENROUTER_AVAILABLE = True
except ImportError:
    print("WARNING: openrouter.py not found or its components could not be imported.")
    print("Translation functionality will be disabled; using placeholder.")
    OPENROUTER_AVAILABLE = False
    api_providers = {} # Define as empty if import fails

def extract_chapter_number(filename: str) -> int:
    """Extracts the chapter number from a filename like 'Chapter_123.md'."""
    match = re.search(r'Chapter_(\d+)\.md', filename)
    if match:
        return int(match.group(1))
    return -1 # Indicates an issue or non-standard filename

def translate(text: str, api_provider_name: str) -> str:
    """
    Translates text using the specified provider from OpenRouter API if available,
    otherwise returns original text (placeholder behavior).
    """
    if OPENROUTER_AVAILABLE:
        # The API key is now handled within translate_chinese_to_english based on the provider
        # print(f"    Attempting actual translation for text snippet: '{text[:70].replace('\\n', ' ')}...' with provider: {api_provider_name}")
        translated_text = translate_chinese_to_english(text, api_provider_name=api_provider_name)
        
        # Check if the translation itself returned an error string from the API wrapper
        if translated_text.startswith(("Error:", "HTTP error", "Connection error", 
                                       "Timeout error", "An unexpected error", 
                                       "An unforeseen error", "Rate limit exceeded")): # Added Rate limit
            # The error message is already formatted by translate_chinese_to_english
            return translated_text # Propagate the error message
        return translated_text
    else:
        # This warning is already printed at import time
        # print("    Warning: OpenRouter module not available, returning original text.")
        return text # Placeholder behavior

def _ensure_directory_exists(dir_path: str) -> bool:
    """Ensures the directory exists, creating it if necessary."""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")
            return False
    return True

def _process_single_chapter(chapter_filename, retry_failed_only, progress_data, raws_dir, translated_raws_dir, progress_file_path, api_provider_name, max_retries_per_chapter, progress_lock):
    """
    Processes a single chapter file for translation.
    
    Args:
        chapter_filename: Name of the chapter file to process
        retry_failed_only: Whether this is a retry-only session
        progress_data: Progress tracking dictionary
        raws_dir: Directory containing raw chapter files
        translated_raws_dir: Directory for translated chapter files
        progress_file_path: Path to progress JSON file
        api_provider_name: API provider name for translation
        max_retries_per_chapter: Maximum retry attempts per chapter
        progress_lock: Threading lock for progress data access
    
    Returns:
        tuple: (success: bool, chapter_filename: str, message: str)
    """
    with progress_lock:
        if not retry_failed_only and chapter_filename in progress_data["translated_files"]:
            return (True, chapter_filename, "Already translated (skipped)")

        current_failure_count = progress_data['failed_translation_attempts'].get(chapter_filename, 0)
        if current_failure_count >= max_retries_per_chapter:
            return (False, chapter_filename, f"Max retries reached ({current_failure_count})")

    raw_chapter_filepath = os.path.join(raws_dir, chapter_filename)
    if not os.path.exists(raw_chapter_filepath):
        with progress_lock:
            if chapter_filename in progress_data['failed_translation_attempts']:
                del progress_data['failed_translation_attempts'][chapter_filename]
        return (False, chapter_filename, "Raw file not found")
        
    translated_chapter_filepath = os.path.join(translated_raws_dir, chapter_filename)

    try:
        with open(raw_chapter_filepath, 'r', encoding='utf-8') as infile:
            raw_content = infile.read()
        
        # API_KEY check is implicitly handled by openrouter.py now.
        if not OPENROUTER_AVAILABLE:
            info_msg = "Translation module not available, using placeholder"
        elif not os.getenv("API_KEY"):
            info_msg = "API_KEY not set, using placeholder"
        else:
            info_msg = None

        translated_content = translate(raw_content, api_provider_name=api_provider_name)

        if translated_content.startswith(("Error:", "HTTP error", "Connection error", 
                                          "Timeout error", "An unexpected error", 
                                          "An unforeseen error", "Rate limit exceeded")):
            with progress_lock:
                progress_data['failed_translation_attempts'][chapter_filename] = current_failure_count + 1
                try:
                    with open(progress_file_path, 'w', encoding='utf-8') as pf:
                        json.dump(progress_data, pf, indent=4)
                except IOError:
                    pass
            return (False, chapter_filename, f"Translation API Error: {translated_content}")
        
        # Save translated content
        chapter_num = extract_chapter_number(chapter_filename)
        padded_chapter_num = f"{chapter_num:03d}"
        placeholder_title = chapter_filename.replace(".md", "")
        formatted_output = f"# Chapter -{padded_chapter_num}\\n## {placeholder_title}\\n\\n{translated_content}"
        
        with open(translated_chapter_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(formatted_output)
        
        # Update progress safely
        with progress_lock:
            if chapter_filename not in progress_data["translated_files"]:
                progress_data["translated_files"].append(chapter_filename)
            if chapter_filename in progress_data['failed_translation_attempts']:
                del progress_data['failed_translation_attempts'][chapter_filename]
            
            try:
                with open(progress_file_path, 'w', encoding='utf-8') as pf:
                    json.dump(progress_data, pf, indent=4)
            except IOError:
                pass
        
        success_msg = "Successfully translated"
        if info_msg:
            success_msg = f"{info_msg}, saved as placeholder"
        
        return (True, chapter_filename, success_msg)

    except FileNotFoundError:
        return (False, chapter_filename, "Raw file not found during processing")
    except Exception as e:
        with progress_lock:
            progress_data['failed_translation_attempts'][chapter_filename] = current_failure_count + 1
            try:
                with open(progress_file_path, 'w', encoding='utf-8') as pf:
                    json.dump(progress_data, pf, indent=4)
            except IOError:
                pass
        return (False, chapter_filename, f"Processing error: {e}")

def _process_chapters(files_to_process, retry_failed_only, progress_data, raws_dir, translated_raws_dir, progress_file_path, api_provider_name, novel_name_from_dir, max_retries_per_chapter=3, api_call_delay=5, workers=1):
    """
    Processes a list of chapter files for translation using multiple workers.
    
    Args:
        files_to_process: List of chapter filenames to process
        retry_failed_only: Whether this is a retry-only session
        progress_data: Progress tracking dictionary
        raws_dir: Directory containing raw chapter files
        translated_raws_dir: Directory for translated chapter files
        progress_file_path: Path to progress JSON file
        api_provider_name: API provider name for translation
        novel_name_from_dir: Novel title from directory name
        max_retries_per_chapter: Maximum retry attempts per chapter
        api_call_delay: Delay between API calls in seconds
        workers: Number of worker threads
    
    Returns:
        int: Number of chapters processed in this session
    """
    chapters_processed_this_session = 0
    progress_lock = threading.Lock()
    
    if workers == 1:
        # Single-threaded processing (original behavior)
        for chapter_filename in files_to_process:
            success, filename, message = _process_single_chapter(
                chapter_filename, retry_failed_only, progress_data, raws_dir, translated_raws_dir,
                progress_file_path, api_provider_name, max_retries_per_chapter, progress_lock
            )
            
            if success and "skipped" not in message.lower():
                chapters_processed_this_session += 1
                print(f"✓ {filename}: {message}")
            elif not success:
                print(f"✗ {filename}: {message}")
            
            # Rate limiting for API calls
            if success and OPENROUTER_AVAILABLE and os.getenv("API_KEY") and "placeholder" not in message.lower():
                print(f"    Waiting {api_call_delay} seconds before next API call...")
                time.sleep(api_call_delay)
    else:
        # Multi-threaded processing
        print(f"Starting translation with {workers} workers...")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_chapter = {
                executor.submit(_process_single_chapter, chapter_filename, retry_failed_only, progress_data, 
                               raws_dir, translated_raws_dir, progress_file_path, api_provider_name, 
                               max_retries_per_chapter, progress_lock): chapter_filename 
                for chapter_filename in files_to_process
            }
            
            # Process completed tasks
            for future in as_completed(future_to_chapter):
                chapter_filename = future_to_chapter[future]
                try:
                    success, filename, message = future.result()
                    
                    if success and "skipped" not in message.lower():
                        chapters_processed_this_session += 1
                        print(f"✓ {filename}: {message}")
                    elif not success:
                        print(f"✗ {filename}: {message}")
                        
                    # Rate limiting for multi-threaded API calls
                    if success and OPENROUTER_AVAILABLE and os.getenv("API_KEY") and "placeholder" not in message.lower():
                        time.sleep(api_call_delay / workers)  # Distribute delay across workers
                        
                except Exception as e:
                    print(f"✗ {chapter_filename}: Unexpected error: {e}")

    print(f"\nTranslation session finished for '{novel_name_from_dir}'.")
    print(f"Chapters processed (or attempted) in this session: {chapters_processed_this_session}")
    print(f"Total chapters marked as successfully translated: {len(progress_data['translated_files'])}")
    if progress_data['failed_translation_attempts']:
        print("Chapters with persistent translation failures (max retries reached or ongoing):")
        for fname, count in progress_data['failed_translation_attempts'].items():
            print(f"  - {fname}: {count} attempts")
    
    return chapters_processed_this_session

def translate_novel_chapters(novel_base_directory: str, api_provider_name: str, retry_failed_only: bool = False):
    """
    Processes raw chapter files, translates them using the specified provider, and saves them.
    Maintains progress and can optionally only retry previously failed translations.
    """
    novel_name_from_dir = os.path.basename(os.path.normpath(novel_base_directory))

    raws_dir = os.path.join(novel_base_directory, "Raws")
    translated_raws_dir = os.path.join(novel_base_directory, "TranslatedRaws")
    progress_file_path = os.path.join(novel_base_directory, f"{novel_name_from_dir}_translation_progress.json")

    if not os.path.isdir(raws_dir):
        print(f"Error: Raws directory not found at '{raws_dir}'")
        return

    if not _ensure_directory_exists(translated_raws_dir):
        return

    progress_data = {
        "novel_title": novel_name_from_dir,
        "raws_directory": os.path.abspath(raws_dir),
        "translated_raws_directory": os.path.abspath(translated_raws_dir),
        "last_used_provider": api_provider_name, # Store the provider used
        "translated_files": [],
        "failed_translation_attempts": {}
    }
    if os.path.exists(progress_file_path):
        try:
            with open(progress_file_path, 'r', encoding='utf-8') as pf:
                loaded_progress = json.load(pf)
                if loaded_progress.get("novel_title") == novel_name_from_dir:
                    progress_data.update(loaded_progress)
                    progress_data["last_used_provider"] = api_provider_name # Update with current provider
                    if 'failed_translation_attempts' not in progress_data:
                        progress_data['failed_translation_attempts'] = {}
                    print(f"Loaded translation progress from: {progress_file_path}")
                    if loaded_progress.get("last_used_provider") and loaded_progress.get("last_used_provider") != api_provider_name:
                        print(f"  Note: Previous translations used provider '{loaded_progress.get('last_used_provider')}'. Current session is using '{api_provider_name}'.")
                else:
                    print(f"Warning: Progress file found ({progress_file_path}) but novel title mismatch. Using fresh translation data for this directory.")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading progress file {progress_file_path}: {e}. Using fresh translation data.")
    else:
        print(f"No translation progress file found. Starting new translation process for '{novel_name_from_dir}'.")

    files_to_process = []
    if retry_failed_only:
        print("--- Mode: Retrying Failed Translations Only ---")
        if not progress_data['failed_translation_attempts']:
            print("No previously failed translations found in progress file. Nothing to retry.")
            return
        files_to_process = sorted(
            list(progress_data['failed_translation_attempts'].keys()), 
            key=extract_chapter_number
        )
        print(f"Found {len(files_to_process)} chapters to retry.")
    else:
        print("--- Mode: Standard Translation (New & Unfinished) ---")
        try:
            all_raw_files = [f for f in os.listdir(raws_dir) if f.startswith("Chapter_") and f.endswith(".md")]
            all_raw_files.sort(key=extract_chapter_number)
            files_to_process = all_raw_files
        except FileNotFoundError:
            print(f"Error: Raws directory not found at {raws_dir} when trying to list files.")
            return
        if not files_to_process:
            print(f"No chapter files found in {raws_dir} to translate.")
            return
        print(f"Found {len(files_to_process)} total chapter files in '{raws_dir}' for potential processing.")

    chapters_processed_this_session = _process_chapters(files_to_process, retry_failed_only, progress_data, raws_dir, translated_raws_dir, progress_file_path, api_provider_name, novel_name_from_dir, workers=args.workers)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Translate raw novel chapters using OpenRouter API or a placeholder."
    )
    parser.add_argument("-n", "--novel-base-dir", 
                        dest="novel_base_directory",
                        required=True, 
                        help="The base directory of the novel (must contain a 'Raws' subdirectory).")
    parser.add_argument("-r", "--retry-failed",
                        action="store_true",
                        help="Only attempt to translate chapters that previously failed.")
    parser.add_argument("-p", "--provider",
                        dest="api_provider_name",
                        default="chutes",
                        help="The API provider to use (e.g., 'chutes', 'openrouter'). Defaults to 'chutes'.")
    
    parser.add_argument("-w", "--workers",
                        type=int,
                        default=1,
                        help="Number of worker threads for parallel processing (default: 1).")
    
    args = parser.parse_args()

    # The API key is now sourced by openrouter.py based on the provider.
    # We just check if API_KEY is set for a general warning if real translation is expected.
    print(f"Selected API Provider: {args.api_provider_name}")
    if OPENROUTER_AVAILABLE and not os.getenv("API_KEY"):
        print("WARNING: API_KEY environment variable not set.")
        print(f"Ensure API_KEY is set to the correct key for the '{args.api_provider_name}' provider if you expect real translations.")
        print("Proceeding, but will use placeholder translation if API calls fail due to missing key.")
        # Decide if you want to exit or proceed with placeholder
        # exit(1) # Uncomment to exit if API key is strictly required

    if not os.path.isdir(args.novel_base_directory):
        print(f"Error: The provided path '{args.novel_base_directory}' is not a valid directory.")
    else:
        translate_novel_chapters(args.novel_base_directory, 
                                 api_provider_name=args.api_provider_name, 
                                 retry_failed_only=args.retry_failed) 