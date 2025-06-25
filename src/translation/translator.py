import os
import re
import json
import argparse
import time # For potential future use with actual translation APIs
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from rich.console import Console
from rich.text import Text

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
            result = translate_chinese_to_english(test_message, key_override=key_info)
            
            if result.startswith("Error:"):
                console.print(" [bold red]FAILED[/bold red]")
                final_message += f"\n  - {key_name}: {result}"
                overall_success = False
            else:
                console.print(" [bold green]SUCCESS[/bold green]")
        
        except Exception as e:
                console.print(" [bold red]FAILED[/bold red]")
                final_message += f"\n  - {key_name}: Exception - {e}"
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
    console.print(f"\n🔧 Validating API key configuration from secrets.json...", style="bold blue")
    
    # Step 1: Validate key file and contents
    config_valid, config_error = validate_api_keys()
    if not config_valid:
        console.print(f"❌ API Configuration Error: {config_error}", style="red")
        console.print("\n💡 To fix this:", style="yellow")
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
        console.print("\n💡 Possible solutions:", style="yellow")
        console.print("   1. Check your internet connection.", style="cyan")
        console.print("   2. Verify your API keys in secrets.json are correct and have sufficient credits.", style="cyan")
        console.print("   3. Check if the API services (Chutes, OpenRouter) are available.", style="cyan")
        return False
    
    console.print("✅ API validation completed successfully.", style="bold green")
    return True

def extract_chapter_number(filename: str) -> int:
    """Extracts the chapter number from a filename like 'Chapter_123.md'."""
    match = re.search(r'Chapter_(\d+)\.md', filename)
    if match:
        return int(match.group(1))
    return -1 # Indicates an issue or non-standard filename

def translate(text: str) -> str:
    """
    Translates text using the fallback logic from OpenRouter API if available,
    otherwise returns original text (placeholder behavior).
    """
    if TRANSLATION_AVAILABLE:
        translated_text = translate_chinese_to_english(text)
        
        # Check if the translation itself returned an error string from the API wrapper
        if translated_text.startswith(("Error:", "HTTP error", "Connection error", 
                                       "Timeout error", "An unexpected error", 
                                       "An unforeseen error", "Rate limit exceeded")):
            return translated_text # Propagate the error message
        return translated_text
    else:
        return text # Placeholder behavior

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

def _validate_chapter_processing(chapter_filename, retry_failed_only, progress_data, max_retries_per_chapter, raws_dir, progress_lock):
    """
    Validates if a chapter should be processed based on current state.
    
    Returns:
        tuple: (should_process: bool, error_message: str or None)
    """
    with progress_lock:
        if not retry_failed_only and chapter_filename in progress_data["translated_files"]:
            return False, "Already translated (skipped)"

        current_failure_count = progress_data['failed_translation_attempts'].get(chapter_filename, 0)
        if current_failure_count >= max_retries_per_chapter:
            return False, f"Max retries reached ({current_failure_count})"

    raw_chapter_filepath = os.path.join(raws_dir, chapter_filename)
    if not os.path.exists(raw_chapter_filepath):
        with progress_lock:
            if chapter_filename in progress_data['failed_translation_attempts']:
                del progress_data['failed_translation_attempts'][chapter_filename]
        return False, "Raw file not found"
    
    return True, None

def _read_chapter_content(chapter_filename, raws_dir):
    """
    Reads the content of a chapter file.
    
    Returns:
        tuple: (success: bool, content: str, error_message: str or None)
    """
    try:
        raw_chapter_filepath = os.path.join(raws_dir, chapter_filename)
        with open(raw_chapter_filepath, 'r', encoding='utf-8') as infile:
            raw_content = infile.read()
        return True, raw_content, None
    except FileNotFoundError:
        return False, "", "Raw file not found during processing"
    except Exception as e:
        return False, "", f"Error reading file: {e}"

def _determine_translation_context():
    """
    Determines if a real translation can be attempted.
    """
    if not TRANSLATION_AVAILABLE or not LOADED_API_KEYS:
        return False, "Translation module/keys not available, using placeholder"
    else:
        return True, None

def _perform_translation_with_timing(raw_content, chapter_filename, status_or_console):
    """
    Performs the actual translation with timing and status updates.
    """
    translation_start = time.time()
    
    if hasattr(status_or_console, 'update'):
        status_or_console.update(f"Translating {chapter_filename}...")
    
    translated_content = translate(raw_content)
    translation_time = time.time() - translation_start
    
    if translated_content.startswith(("Error:", "HTTP error")):
        return False, translated_content, translation_time, f"Translation API Error: {translated_content}"
    
    return True, translated_content, translation_time, None

def _save_translated_chapter(chapter_filename, translated_content, translated_raws_dir, status_or_console):
    """
    Formats and saves the translated chapter content.
    
    Args:
        status_or_console: Either a rich status object or console object
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        # Update status if it has an update method (status spinner), otherwise just proceed
        if hasattr(status_or_console, 'update'):
            status_or_console.update(f"Saving {chapter_filename}...")
        
        chapter_num = extract_chapter_number(chapter_filename)
        padded_chapter_num = f"{chapter_num:03d}"
        placeholder_title = chapter_filename.replace(".md", "")
        formatted_output = f"# Chapter -{padded_chapter_num}\\n## {placeholder_title}\\n\\n{translated_content}"
        
        translated_chapter_filepath = os.path.join(translated_raws_dir, chapter_filename)
        with open(translated_chapter_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(formatted_output)
        
        return True, None
    except Exception as e:
        return False, f"Error saving file: {e}"

def _update_translation_progress(chapter_filename, progress_data, progress_file_path, progress_lock, success=True):
    """
    Updates the translation progress tracking.
    
    Args:
        success: True for successful translation, False for failure
    """
    with progress_lock:
        if success:
            if chapter_filename not in progress_data["translated_files"]:
                progress_data["translated_files"].append(chapter_filename)
            if chapter_filename in progress_data['failed_translation_attempts']:
                del progress_data['failed_translation_attempts'][chapter_filename]
        else:
            current_failure_count = progress_data['failed_translation_attempts'].get(chapter_filename, 0)
            progress_data['failed_translation_attempts'][chapter_filename] = current_failure_count + 1
        
        try:
            with open(progress_file_path, 'w', encoding='utf-8') as pf:
                json.dump(progress_data, pf, indent=4)
        except IOError:
            pass

def _process_single_chapter(chapter_filename, retry_failed_only, progress_data, raws_dir, translated_raws_dir, progress_file_path, max_retries_per_chapter, progress_lock, use_status_spinner=True):
    """
    Processes a single chapter file for translation using modular helper functions.
    
    Args:
        chapter_filename: Name of the chapter file to process
        retry_failed_only: Whether this is a retry-only session
        progress_data: Progress tracking dictionary
        raws_dir: Directory containing raw chapter files
        translated_raws_dir: Directory for translated chapter files
        progress_file_path: Path to progress JSON file
        max_retries_per_chapter: Maximum retry attempts per chapter
        progress_lock: Threading lock for progress data access
        use_status_spinner: Whether to use a status spinner for console output
    
    Returns:
        tuple: (success: bool, chapter_filename: str, message: str)
    """
    # Start timing
    start_time = time.time()
    
    # Step 1: Validate if chapter should be processed
    should_process, validation_error = _validate_chapter_processing(
        chapter_filename, retry_failed_only, progress_data, max_retries_per_chapter, raws_dir, progress_lock
    )
    if not should_process:
        validation_error = validation_error or "Unknown validation error"
        return (True if "skipped" in validation_error else False, chapter_filename, validation_error, 0.0)
    
    # Step 2: Create status context for thread-safe output
    status_text = f"Starting translation of {chapter_filename}..."
    
    try:
        if use_status_spinner:
            with console.status(status_text, spinner="dots") as status:
                # Step 3: Read chapter content
                read_success, raw_content, read_error = _read_chapter_content(chapter_filename, raws_dir)
                if not read_success:
                    total_time = time.time() - start_time
                    console.print(f"❌ FAILED: {chapter_filename} - {read_error} [total_time={total_time:.1f}s]", style="red", markup=False)
                    return (False, chapter_filename, read_error, 0.0)
                
                # Step 4: Determine translation context
                has_real_translation, info_msg = _determine_translation_context()
                
                # Step 5: Perform translation with timing
                translation_success, translated_content, translation_time, translation_error = _perform_translation_with_timing(
                    raw_content, chapter_filename, status
                )
                
                if not translation_success:
                    total_time = time.time() - start_time
                    status.stop()
                    console.print(f"❌ FAILED: {chapter_filename} - Translation error [total_time={total_time:.1f}s]", style="red", markup=False)
                    _update_translation_progress(chapter_filename, progress_data, progress_file_path, progress_lock, success=False)
                    return (False, chapter_filename, translation_error, 0.0)
                
                # Step 6: Save translated content
                save_success, save_error = _save_translated_chapter(
                    chapter_filename, translated_content, translated_raws_dir, status
                )
                
                if not save_success:
                    total_time = time.time() - start_time
                    status.stop()
                    console.print(f"❌ FAILED: {chapter_filename} - {save_error} [total_time={total_time:.1f}s]", style="red", markup=False)
                    _update_translation_progress(chapter_filename, progress_data, progress_file_path, progress_lock, success=False)
                    return (False, chapter_filename, save_error, 0.0)
                
                # Step 7: Update progress tracking
                _update_translation_progress(chapter_filename, progress_data, progress_file_path, progress_lock, success=True)
                
                # Step 8: Calculate final timing and display results
                total_time = time.time() - start_time
                status.stop()
                
                if info_msg:
                    console.print(f"⚠️  PLACEHOLDER: {chapter_filename} - {info_msg} [total_time={total_time:.1f}s]", style="yellow", markup=False)
                    success_msg = f"{info_msg}, saved as placeholder in {total_time:.2f}s"
                    return (True, chapter_filename, success_msg, 0.0)  # No real translation time for placeholder
                else:
                    if use_status_spinner:
                        if translation_time > 0:
                            console.print(f"✅ SUCCESS: {chapter_filename} - Translation completed [translation_time={translation_time:.1f}s] [total_time={total_time:.1f}s]", style="green", markup=False)
                        else:
                            console.print(f"✅ SUCCESS: {chapter_filename} - Translation completed [total_time={total_time:.1f}s]", style="green", markup=False)
                    success_msg = f"Successfully translated in {translation_time:.2f}s (Total: {total_time:.2f}s)"
                    return (True, chapter_filename, success_msg, translation_time)
        else:
            # Step 3: Read chapter content
            read_success, raw_content, read_error = _read_chapter_content(chapter_filename, raws_dir)
            if not read_success:
                total_time = time.time() - start_time
                if use_status_spinner:
                    console.print(f"❌ FAILED: {chapter_filename} - {read_error} [total_time={total_time:.1f}s]", style="red", markup=False)
                return (False, chapter_filename, read_error, 0.0)
            
            # Step 4: Determine translation context
            has_real_translation, info_msg = _determine_translation_context()
            
            # Step 5: Perform translation with timing
            translation_success, translated_content, translation_time, translation_error = _perform_translation_with_timing(
                raw_content, chapter_filename, console
            )
            
            if not translation_success:
                total_time = time.time() - start_time
                if use_status_spinner:
                    console.print(f"❌ FAILED: {chapter_filename} - Translation error [total_time={total_time:.1f}s]", style="red", markup=False)
                _update_translation_progress(chapter_filename, progress_data, progress_file_path, progress_lock, success=False)
                return (False, chapter_filename, translation_error, 0.0)
            
            # Step 6: Save translated content
            save_success, save_error = _save_translated_chapter(
                chapter_filename, translated_content, translated_raws_dir, console
            )
            
            if not save_success:
                total_time = time.time() - start_time
                if use_status_spinner:
                    console.print(f"❌ FAILED: {chapter_filename} - {save_error} [total_time={total_time:.1f}s]", style="red", markup=False)
                _update_translation_progress(chapter_filename, progress_data, progress_file_path, progress_lock, success=False)
                return (False, chapter_filename, save_error, 0.0)
            
            # Step 7: Update progress tracking
            _update_translation_progress(chapter_filename, progress_data, progress_file_path, progress_lock, success=True)
            
            # Step 8: Calculate final timing and display results
            total_time = time.time() - start_time
            
            if info_msg:
                if use_status_spinner:
                    console.print(f"⚠️  PLACEHOLDER: {chapter_filename} - {info_msg} [total_time={total_time:.1f}s]", style="yellow", markup=False)
                success_msg = f"{info_msg}, saved as placeholder in {total_time:.2f}s"
                return (True, chapter_filename, success_msg, 0.0)  # No real translation time for placeholder
            else:
                if use_status_spinner:
                    if translation_time > 0:
                        console.print(f"✅ SUCCESS: {chapter_filename} - Translation completed [translation_time={translation_time:.1f}s] [total_time={total_time:.1f}s]", style="green", markup=False)
                    else:
                        console.print(f"✅ SUCCESS: {chapter_filename} - Translation completed [total_time={total_time:.1f}s]", style="green", markup=False)
                success_msg = f"Successfully translated in {translation_time:.2f}s (Total: {total_time:.2f}s)"
                return (True, chapter_filename, success_msg, translation_time)

    except Exception as e:
        total_time = time.time() - start_time
        if use_status_spinner:
            console.print(f"❌ FAILED: {chapter_filename} - Processing error: {str(e)} [total_time={total_time:.1f}s]", style="red", markup=False)
        _update_translation_progress(chapter_filename, progress_data, progress_file_path, progress_lock, success=False)
        return (False, chapter_filename, f"Processing error: {e}", 0.0)

def _process_chapters(files_to_process, retry_failed_only, progress_data, raws_dir, translated_raws_dir, progress_file_path, novel_name_from_dir, max_retries_per_chapter=3, api_call_delay=5, workers=1):
    """
    Processes a list of chapter files for translation using multiple workers.
    
    Args:
        files_to_process: List of chapter filenames to process
        retry_failed_only: Whether this is a retry-only session
        progress_data: Progress tracking dictionary
        raws_dir: Directory containing raw chapter files
        translated_raws_dir: Directory for translated chapter files
        progress_file_path: Path to progress JSON file
        novel_name_from_dir: Novel title from directory name
        max_retries_per_chapter: Maximum retry attempts per chapter
        api_call_delay: Delay between API calls in seconds
        workers: Number of worker threads
    
    Returns:
        int: Number of chapters processed in this session
    """
    chapters_processed_this_session = 0
    progress_lock = threading.Lock()
    
    # Start session timing
    session_start_time = time.time()
    successful_chapter_times = []  # Track timing for successfully translated chapters
    
    if workers == 1:
        # Single-threaded processing (original behavior)
        for chapter_filename in files_to_process:
            chapter_start_time = time.time()
            success, filename, message, translation_time = _process_single_chapter(
                chapter_filename, retry_failed_only, progress_data, raws_dir, translated_raws_dir,
                progress_file_path, max_retries_per_chapter, progress_lock, use_status_spinner=True
            )
            chapter_end_time = time.time()
            chapter_duration = chapter_end_time - chapter_start_time
            
            # Ensure message is never None for string operations
            message = message or ""
            
            if success and "skipped" not in message.lower():
                chapters_processed_this_session += 1
                # Only track timing for successful real translations (not skipped or placeholder)
                if "placeholder" not in message.lower():
                    successful_chapter_times.append(chapter_duration)
            
            # Rate limiting for API calls - only apply for successful real translations
            # Skip rate limiting for: failures, skipped chapters, or placeholder translations
            if (success and 
                TRANSLATION_AVAILABLE and 
                os.getenv("API_KEY") and 
                "skipped" not in message.lower() and
                "placeholder" not in message.lower()):
                console.print(f"    ⏳ Waiting {api_call_delay} seconds before next API call...", style="dim")
                time.sleep(api_call_delay)
    else:
        # Multi-threaded processing
        console.print(f"🚀 Starting translation with {workers} workers...", style="bold blue")
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks with timing
            future_to_chapter = {}
            chapter_start_times = {}
            
            for chapter_filename in files_to_process:
                chapter_start_time = time.time()
                future = executor.submit(_process_single_chapter, chapter_filename, retry_failed_only, progress_data, 
                                       raws_dir, translated_raws_dir, progress_file_path, max_retries_per_chapter, progress_lock, use_status_spinner=False)
                future_to_chapter[future] = chapter_filename
                chapter_start_times[future] = chapter_start_time
            
            # Process completed tasks
            for future in as_completed(future_to_chapter):
                chapter_filename = future_to_chapter[future]
                chapter_start_time = chapter_start_times[future]
                chapter_duration = time.time() - chapter_start_time
                
                try:
                    success, filename, message, translation_time = future.result()
                    
                    # Ensure message is never None for string operations
                    message = message or ""
                    
                    # Print individual chapter completion status with timing
                    if success:
                        if "skipped" in message.lower():
                            console.print(f"⏭️  SKIPPED: {chapter_filename} - {message} [total_time={chapter_duration:.1f}s]", style="dim", markup=False)
                        elif "placeholder" in message.lower():
                            console.print(f"⚠️  PLACEHOLDER: {chapter_filename} - Translation completed (placeholder) [total_time={chapter_duration:.1f}s]", style="yellow", markup=False)
                        else:
                            if translation_time > 0:
                                console.print(f"✅ SUCCESS: {chapter_filename} - Translation completed [translation_time={translation_time:.1f}s] [total_time={chapter_duration:.1f}s]", style="green", markup=False)
                            else:
                                console.print(f"✅ SUCCESS: {chapter_filename} - Translation completed [total_time={chapter_duration:.1f}s]", style="green", markup=False)
                    else:
                        console.print(f"❌ FAILED: {chapter_filename} - {message} [total_time={chapter_duration:.1f}s]", style="red", markup=False)
                    
                    if success and "skipped" not in message.lower():
                        chapters_processed_this_session += 1
                        # Only track timing for successful real translations (not skipped or placeholder)
                        if "placeholder" not in message.lower():
                            successful_chapter_times.append(chapter_duration)
                        
                    # Rate limiting for multi-threaded API calls - only apply for successful real translations
                    # Skip rate limiting for: failures, skipped chapters, or placeholder translations
                    if (success and 
                        TRANSLATION_AVAILABLE and 
                        os.getenv("API_KEY") and 
                        "skipped" not in message.lower() and
                        "placeholder" not in message.lower()):
                        time.sleep(api_call_delay / workers)  # Distribute delay across workers
                        
                except Exception as e:
                    console.print(f"❌ {chapter_filename}: Unexpected error: {e}", style="red")

    # Calculate session timing and statistics
    session_end_time = time.time()
    total_session_time = session_end_time - session_start_time
    
    console.print(f"\n🎉 Translation session finished for '{novel_name_from_dir}'.", style="bold green")
    console.print(f"📊 Chapters processed (or attempted) in this session: {chapters_processed_this_session}", style="blue")
    console.print(f"📋 Total chapters marked as successfully translated: {len(progress_data['translated_files'])}", style="blue")
    
    # Timing statistics
    console.print(f"⏱️  Session timing:", style="bold cyan")
    console.print(f"   • Total session time: {total_session_time:.1f} seconds ({total_session_time/60:.1f} minutes)", style="cyan")
    
    if successful_chapter_times:
        # For average time per chapter, use session time divided by chapters (accounts for parallel processing)
        avg_time_per_chapter = total_session_time / len(successful_chapter_times)
        console.print(f"   • Chapters successfully translated: {len(successful_chapter_times)}", style="cyan")
        console.print(f"   • Average time per chapter: {avg_time_per_chapter:.1f} seconds", style="cyan")
        console.print(f"   • Fastest chapter: {min(successful_chapter_times):.1f} seconds", style="cyan")
        console.print(f"   • Slowest chapter: {max(successful_chapter_times):.1f} seconds", style="cyan")
    else:
        console.print(f"   • No chapters were successfully translated in this session", style="dim cyan")
    
    if progress_data['failed_translation_attempts']:
        console.print("⚠️  Chapters with persistent translation failures:", style="yellow")
        for fname, count in progress_data['failed_translation_attempts'].items():
            console.print(f"  - {fname}: {count} attempts", style="dim yellow")
    
    return chapters_processed_this_session

def translate_novel_chapters(novel_base_directory: str, retry_failed_only: bool = False, skip_validation: bool = False):
    """
    Processes raw chapter files, translates them using the specified provider, and saves them.
    Maintains progress and can optionally only retry previously failed translations.
    
    Args:
        novel_base_directory: Base directory containing the novel files
        retry_failed_only: Whether to only retry previously failed translations
        skip_validation: Whether to skip API validation (default: False, validation runs by default)
    """
    novel_name_from_dir = os.path.basename(os.path.normpath(novel_base_directory))

    # Perform API validation before starting translation (unless skipped)
    if not skip_validation:
        if not perform_api_validation():
            console.print("\n❌ API validation failed. Cannot proceed with translation.", style="bold red")
            console.print("Please fix the API configuration issues above and try again.", style="yellow")
            console.print("💡 Tip: Use --skip-validation to bypass this check (not recommended).", style="cyan")
            return
    else:
        console.print("⚠️  API validation skipped as requested.", style="yellow")

    raws_dir = os.path.join(novel_base_directory, f"{novel_name_from_dir}-Raws")
    translated_raws_dir = os.path.join(novel_base_directory, f"{novel_name_from_dir}-English")
    progress_file_path = os.path.join(novel_base_directory, f"{novel_name_from_dir}_translation_progress.json")

    if not os.path.isdir(raws_dir):
        console.print(f"❌ Error: Raws directory not found at '{raws_dir}'", style="red")
        return

    if not _ensure_directory_exists(translated_raws_dir):
        return

    progress_data = {
        "novel_title": novel_name_from_dir,
        "raws_directory": os.path.abspath(raws_dir),
        "translated_raws_directory": os.path.abspath(translated_raws_dir),
        "last_used_provider": "dynamic (see secrets.json)",
        "translated_files": [],
        "failed_translation_attempts": {}
    }
    if os.path.exists(progress_file_path):
        try:
            with open(progress_file_path, 'r', encoding='utf-8') as pf:
                loaded_progress = json.load(pf)
                if loaded_progress.get("novel_title") == novel_name_from_dir:
                    progress_data.update(loaded_progress)
                    console.print(f"📂 Loaded translation progress from: {progress_file_path}", style="blue")
                else:
                    console.print(f"⚠️  Warning: Progress file found ({progress_file_path}) but novel title mismatch. Using fresh translation data for this directory.", style="yellow")
        except (json.JSONDecodeError, IOError) as e:
            console.print(f"❌ Error reading progress file {progress_file_path}: {e}. Using fresh translation data.", style="red")
    else:
        console.print(f"📄 No translation progress file found. Starting new translation process for '{novel_name_from_dir}'.", style="blue")

    files_to_process = []
    if retry_failed_only:
        console.print("🔄 Mode: Retrying Failed Translations Only", style="bold yellow")
        if not progress_data['failed_translation_attempts']:
            console.print("✅ No previously failed translations found in progress file. Nothing to retry.", style="green")
            return
        files_to_process = sorted(
            list(progress_data['failed_translation_attempts'].keys()), 
            key=extract_chapter_number
        )
        console.print(f"🔍 Found {len(files_to_process)} chapters to retry.", style="yellow")
        
        # Process the failed chapters once and exit
        chapters_processed_this_session = _process_chapters(files_to_process, retry_failed_only, progress_data, raws_dir, translated_raws_dir, progress_file_path, novel_name_from_dir, workers=args.workers)
    else:
        console.print("🆕 Mode: Standard Translation (New & Unfinished) - Dynamic Discovery", style="bold green")
        console.print("📁 Will continuously check for new chapters during translation...", style="cyan")
        
        total_chapters_processed_this_session = 0
        iteration = 1
        max_retries_per_chapter = 3  # Default value
        
        while True:
            # Get current list of all raw files
            all_raw_files = [f for f in os.listdir(raws_dir) if f.startswith("Chapter_") and f.endswith(".md")]
            all_raw_files.sort(key=extract_chapter_number)
            
            if not all_raw_files:
                if iteration == 1:
                    console.print(f"📁 No chapter files found in {raws_dir}.", style="yellow")
                break
            
            # Filter to get only unprocessed files
            unprocessed_files = []
            for filename in all_raw_files:
                if filename not in progress_data["translated_files"]:
                    # Also check if it's not currently failing too many times
                    current_failure_count = progress_data['failed_translation_attempts'].get(filename, 0)
                    if current_failure_count < max_retries_per_chapter:
                        unprocessed_files.append(filename)
            
            if not unprocessed_files:
                console.print(f"✅ No more chapters to process. All available chapters have been translated or have reached max retry limit.", style="green")
                break
            
            console.print(f"\n🔄 Iteration {iteration}: Found {len(unprocessed_files)} chapters to process", style="bold blue")
            console.print(f"📚 Total chapters in directory: {len(all_raw_files)}", style="blue")
            console.print(f"✅ Already translated: {len(progress_data['translated_files'])}", style="green")
            failed_at_limit = len([f for f in progress_data['failed_translation_attempts'] if progress_data['failed_translation_attempts'][f] >= max_retries_per_chapter])
            if failed_at_limit > 0:
                console.print(f"❌ Failed (at retry limit): {failed_at_limit}", style="red")
            
            # Process this batch of unprocessed files
            chapters_processed_this_batch = _process_chapters(
                unprocessed_files, 
                retry_failed_only, 
                progress_data, 
                raws_dir, 
                translated_raws_dir, 
                progress_file_path, 
                novel_name_from_dir, 
                workers=args.workers
            )
            
            total_chapters_processed_this_session += chapters_processed_this_batch
            
            # If no chapters were processed in this iteration, break to avoid infinite loop
            if chapters_processed_this_batch == 0:
                console.print("⏹️  No chapters were processed in this iteration. Stopping to avoid infinite loop.", style="yellow")
                break
            
            iteration += 1
            
            # Brief pause before checking for new files again (only if we processed something)
            console.print("⏳ Checking for new chapters in 3 seconds...", style="dim")
            time.sleep(3)
        
        console.print(f"\n🎯 Dynamic translation completed! Total chapters processed across all iterations: {total_chapters_processed_this_session}", style="bold green")
        return  # Return here since we already processed everything

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Translate raw novel chapters using the dynamic key system."
    )
    parser.add_argument("-n", "--novel-base-dir", 
                        dest="novel_base_directory",
                        required=True, 
                        help="The base directory of the novel (must contain a 'Raws' subdirectory).")
    parser.add_argument("-r", "--retry-failed",
                        action="store_true",
                        help="Only attempt to translate chapters that previously failed.")
    
    parser.add_argument("-w", "--workers",
                        type=int,
                        default=1,
                        help="Number of worker threads for parallel processing (default: 1).")
    
    parser.add_argument("--skip-validation",
                        action="store_true",
                        help="Skip API validation before starting translation (not recommended).")
    
    args = parser.parse_args()

    # No longer need to check for provider or individual API_KEY env var here.
    # The check is now inside the validation function.
    if not os.path.isdir(args.novel_base_directory):
        console.print(f"❌ Error: The provided path '{args.novel_base_directory}' is not a valid directory.", style="red")
    else:
        translate_novel_chapters(
            args.novel_base_directory, 
                                 retry_failed_only=args.retry_failed,
            skip_validation=args.skip_validation
        ) 