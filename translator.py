import os
import re
import json
import argparse
import time # For potential future use with actual translation APIs

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

    chapters_processed_this_session = 0
    api_call_delay = 5  
    max_retries_per_chapter = 3

    for chapter_filename in files_to_process:
        if not retry_failed_only and chapter_filename in progress_data["translated_files"]:
            # In standard mode, skip already translated files.
            # In retry_failed_only mode, we always attempt, even if it was somehow in translated_files list.
            continue

        current_failure_count = progress_data['failed_translation_attempts'].get(chapter_filename, 0)
        if current_failure_count >= max_retries_per_chapter:
            print(f"Skipping {chapter_filename}, as it has already failed translation {current_failure_count} times (max: {max_retries_per_chapter}).")
            continue

        raw_chapter_filepath = os.path.join(raws_dir, chapter_filename)
        # Check if raw file exists, especially important in retry_failed_only mode
        if not os.path.exists(raw_chapter_filepath):
            print(f"  Warning: Raw chapter file {raw_chapter_filepath} not found. Skipping.")
            # Optionally remove from failed_translation_attempts if source is gone
            if chapter_filename in progress_data['failed_translation_attempts']:
                del progress_data['failed_translation_attempts'][chapter_filename]
            continue 
            
        translated_chapter_filepath = os.path.join(translated_raws_dir, chapter_filename)

        print(f"Processing: {chapter_filename} (Attempt {current_failure_count + 1})...")
        
        # ... (rest of the try-except block for translation and saving remains largely the same) ...
        # Ensure the print messages and progress updates are correct for retry logic
        try:
            with open(raw_chapter_filepath, 'r', encoding='utf-8') as infile:
                raw_content = infile.read()
            
            # API_KEY check is implicitly handled by openrouter.py now.
            # We still check OPENROUTER_AVAILABLE for a general capability warning.
            if not OPENROUTER_AVAILABLE:
                 print(f"  INFO: Translation module (openrouter.py) not available. Using placeholder for {chapter_filename}.")
            elif not os.getenv("API_KEY"): # Check if API_KEY is set for an early warning
                 print(f"  INFO: API_KEY environment variable not set. Using placeholder translation for {chapter_filename}.")

            translated_content = translate(raw_content, api_provider_name=api_provider_name)

            if translated_content.startswith(("Error:", "HTTP error", "Connection error", 
                                              "Timeout error", "An unexpected error", 
                                              "An unforeseen error", "Rate limit exceeded")): # Added Rate limit
                print(f"  Translation API Error for {chapter_filename} (Provider: {api_provider_name}): {translated_content}")
                progress_data['failed_translation_attempts'][chapter_filename] = current_failure_count + 1
            elif not OPENROUTER_AVAILABLE or not os.getenv("API_KEY"): # If using placeholder due to no module or no key
                 with open(translated_chapter_filepath, 'w', encoding='utf-8') as outfile:
                    # outfile.write(translated_content) # Old way
                    # New formatting
                    chapter_num = extract_chapter_number(chapter_filename)
                    padded_chapter_num = f"{chapter_num:03d}"
                    placeholder_title = chapter_filename.replace(".md", "")
                    formatted_output = f"# Chapter -{padded_chapter_num}\\n## {placeholder_title}\\n\\n{translated_content}"
                    outfile.write(formatted_output)
                 print(f"  Placeholder translation saved to: {translated_chapter_filepath}")
                 if chapter_filename not in progress_data["translated_files"]:
                    progress_data["translated_files"].append(chapter_filename)
                 if chapter_filename in progress_data['failed_translation_attempts']:
                    del progress_data['failed_translation_attempts'][chapter_filename] # Clear failure on placeholder "success"
                 chapters_processed_this_session += 1
            else: 
                with open(translated_chapter_filepath, 'w', encoding='utf-8') as outfile:
                    # outfile.write(translated_content) # Old way
                    # New formatting
                    chapter_num = extract_chapter_number(chapter_filename)
                    padded_chapter_num = f"{chapter_num:03d}"
                    placeholder_title = chapter_filename.replace(".md", "")
                    formatted_output = f"# Chapter -{padded_chapter_num}\\n## {placeholder_title}\\n\\n{translated_content}"
                    outfile.write(formatted_output)
                
                print(f"  Successfully translated and saved to: {translated_chapter_filepath}")
                if chapter_filename not in progress_data["translated_files"]:
                     progress_data["translated_files"].append(chapter_filename)
                if chapter_filename in progress_data['failed_translation_attempts']:
                    del progress_data['failed_translation_attempts'][chapter_filename]
                chapters_processed_this_session += 1

        except FileNotFoundError: # Should be caught by earlier check, but as a safeguard
            print(f"  Error: Raw chapter file not found during attempt: {raw_chapter_filepath}. Skipping.")
        except Exception as e:
            print(f"  Error processing {chapter_filename}: {e}. Skipping.")
            progress_data['failed_translation_attempts'][chapter_filename] = current_failure_count + 1 # Record general processing error as a failure
        
        try:
            with open(progress_file_path, 'w', encoding='utf-8') as pf:
                json.dump(progress_data, pf, indent=4)
        except IOError as e:
            print(f"    Warning: Could not save progress to {progress_file_path}: {e}")

        if OPENROUTER_AVAILABLE and os.getenv("API_KEY"): # Only delay if we actually might have made an API call
            print(f"    Waiting for {api_call_delay} seconds before next API call...")
            time.sleep(api_call_delay)

    print(f"\nTranslation session finished for '{novel_name_from_dir}'.")
    print(f"Chapters processed (or attempted) in this session: {chapters_processed_this_session}")
    print(f"Total chapters marked as successfully translated: {len(progress_data['translated_files'])}")
    if progress_data['failed_translation_attempts']:
        print("Chapters with persistent translation failures (max retries reached or ongoing):")
        for fname, count in progress_data['failed_translation_attempts'].items():
            print(f"  - {fname}: {count} attempts")

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