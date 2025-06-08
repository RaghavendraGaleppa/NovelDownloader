import requests
from bs4 import BeautifulSoup
import re
import cloudscraper
import os
import time
import json
import random
import argparse
import urllib3
from extraction_backends import ExtractionBackend, EB69Shu, EB1QXS
from urllib.parse import urlparse

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# PROGRESS_FILE constant is removed, will be generated dynamically.

# --- Scraper Class ---

class NovelScraper:
    """
    A web scraper class specifically designed for fetching novel content from websites.
    Handles SSL issues and provides robust HTTP request functionality.
    """
    
    def __init__(self, timeout=30):
        """
        Initialize the NovelScraper with SSL verification disabled.
        
        Args:
            timeout (int): Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.scraper = self._setup_scraper()
    
    def _setup_scraper(self):
        """
        Set up cloudscraper with complete SSL verification bypass.
        
        Returns:
            cloudscraper.CloudScraper: Configured scraper instance
        """
        # Initialize cloudscraper with SSL verification completely disabled
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'linux',  # Or 'windows', 'darwin' based on your OS
                'mobile': False
            }
        )
        
        # Completely disable SSL verification and hostname checking
        scraper.verify = False
        
        # Mount a custom HTTPAdapter that disables SSL verification
        from requests.adapters import HTTPAdapter
        from urllib3.util.ssl_ import create_urllib3_context
        import ssl
        
        class NoSSLAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                ctx = create_urllib3_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                kwargs['ssl_context'] = ctx
                return super().init_poolmanager(*args, **kwargs)
        
        scraper.mount('https://', NoSSLAdapter())
        scraper.mount('http://', HTTPAdapter())
        
        return scraper
    
    def fetch_url(self, url):
        """
        Fetch content from the given URL with error handling.
        
        Args:
            url (str): The URL to fetch
            
        Returns:
            str or None: The HTML content if successful, None if failed
        """
        response = None
        try:
            response = self.scraper.get(url, verify=False, timeout=self.timeout)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            return response.text
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to fetch {url}"
            if response is not None: 
                error_message += f" - Status Code: {response.status_code}"
            error_message += f" - Error: {e}"
            print(error_message)
            return None
        except Exception as e:
            print(f"An unexpected error occurred while fetching URL {url}: {e}")
            return None

# --- Backend Detection ---

def detect_extraction_backend(url: str) -> ExtractionBackend:
    """
    Detect the appropriate extraction backend based on the URL.
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        ExtractionBackend: The appropriate backend instance
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # Check for 1qxs domains
    if '1qxs' in domain:
        return EB1QXS()
    
    # Check for 69shu domains
    if '69shu' in domain or 'shu69' in domain or '69shuba' in domain:
        return EB69Shu()
    
    # Default to 69shu backend for now
    # In the future, add more conditions for other websites
    return EB69Shu()

# --- Helper Functions (Updated to use backends) ---

def scrape_chapter(url):
    """
    Scrape a chapter from the given URL using the NovelScraper class.
    
    Args:
        url (str): The URL of the chapter to scrape
        
    Returns:
        str or None: The HTML content if successful, None if failed
    """
    scraper = NovelScraper()
    return scraper.fetch_url(url)

def get_next_chapter_url(html_content: str, url: str = None) -> str | None:
    """
    Extracts the URL for the next chapter from the given HTML content.

    Args:
        html_content (str): The HTML content of the novel chapter page.
        url (str, optional): The original URL for backend detection.

    Returns:
        str or None: The URL of the next chapter, or None if not found.
    """
    # Use default backend if no URL provided for detection
    backend = detect_extraction_backend(url) if url else EB69Shu()
    return backend.get_next_chapter_url(html_content)

def scrape_novel_content(source: str, source_type: str = 'file') -> tuple[str, list[str], str | None, str | None]:
    """
    Scrapes the title, Chinese novel text paragraphs, next chapter URL, and chapter number from an HTML source.

    Args:
        source (str): The path to an HTML file or a URL.
        source_type (str): 'file' if source is a file path, 'url' if source is a URL.
                          Defaults to 'file'.

    Returns:
        tuple: A tuple containing (title, paragraphs_list, next_chapter_url, chapter_number).
               Returns ("No Title Found", [], None, None) if scraping fails or no content is found.
    """
    html_doc = None
    if source_type == 'file':
        try:
            with open(source, 'r', encoding='utf-8') as file:
                html_doc = file.read()
        except FileNotFoundError:
            print(f"Error: File not found at {source}")
            return "Error: File Not Found", [], None, None
        except Exception as e:
            print(f"Error reading file {source}: {e}")
            return f"Error Reading File: {e}", [], None, None
    elif source_type == 'url':
        try:
            html_doc = scrape_chapter(source)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {source}: {e}")
            return f"Error Fetching URL: {e}", [], None, None
    else:
        print("Invalid source_type. Must be 'file' or 'url'.")
        return "Invalid Source Type", [], None, None

    if not html_doc:
        return "No Content Found", [], None, None

    # Detect the appropriate backend based on the source URL
    backend = detect_extraction_backend(source) if source_type == 'url' else EB69Shu()
    
    # Extract all content using the backend
    title, paragraphs, next_chapter_url, chapter_number = backend.extract_all_content(html_doc)

    return title, paragraphs, next_chapter_url, chapter_number

def get_chapter_number(html_content: str, url: str = None) -> str | None:
    """
    Extracts the chapter number from the given HTML content.

    Args:
        html_content (str): The HTML content of the novel chapter page.
        url (str, optional): The original URL for backend detection.

    Returns:
        str or None: The chapter number as a string, or None if not found.
    """
    # Use default backend if no URL provided for detection
    backend = detect_extraction_backend(url) if url else EB69Shu()
    return backend.get_chapter_number(html_content)

def _ensure_output_directory(dir_path: str) -> bool:
    """Ensures the output directory exists, creating it if necessary."""
    if not os.path.exists(dir_path):
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(dir_path), exist_ok=True) 
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")
            return False
    return True

def _attempt_cleanup_completed_progress_file(progress_file_path: str):
    """Checks if the progress file indicates completion and removes it if so."""
    if os.path.exists(progress_file_path):
        try:
            with open(progress_file_path, 'r', encoding='utf-8') as pf:
                progress_data = json.load(pf)
            if progress_data.get('next_url_to_scrape') is None:
                os.remove(progress_file_path)
                print(f"Cleaned up completed progress file: {progress_file_path}")
        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"Could not process or remove progress file {progress_file_path} during cleanup: {e}")

def _save_current_progress(
    progress_file_path: str, 
    novel_title: str, 
    original_start_url: str, 
    output_base_dir_name: str, 
    processed_url: str | None, # URL of the chapter just processed (or None if initial save)
    next_url_to_process: str | None
):
    """Saves the current scraping progress (including identity) to the progress file."""
    progress_data_to_save = {
        'novel_title': novel_title,
        'original_start_url': original_start_url,
        'output_base_dir_name': output_base_dir_name,
        'last_scraped_url': processed_url, # Can be None initially
        'next_url_to_scrape': next_url_to_process
    }
    try:
        # Ensure parent directory for progress file exists
        os.makedirs(os.path.dirname(progress_file_path), exist_ok=True)
        with open(progress_file_path, 'w', encoding='utf-8') as pf:
            json.dump(progress_data_to_save, pf, indent=4)
    except IOError as e:
        print(f"Error saving progress to {progress_file_path}: {e}")

def _create_chapter_file(output_dir_path: str, chapter_num_str: str, title: str, paragraphs: list[str]) -> bool:
    """Creates a markdown file for the given chapter content in the specified output directory."""
    filename = f"Chapter_{chapter_num_str}.md"
    filepath = os.path.join(output_dir_path, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            if paragraphs:
                f.write("\n\n".join(paragraphs))
            f.write("\n")
        return True
    except IOError as e:
        print(f"Error writing file {filepath}: {e}")
        return False

# --- Main Function ---

def main(args: argparse.Namespace):
    novel_title: str
    original_start_url: str
    current_url: str | None
    safe_novel_title_dir_name: str # This is the output_base_dir_name
    progress_file_path: str
    output_dir_path: str # For Raws subfolder

    if args.progress_file:  # Resume with explicit progress file
        progress_file_path = args.progress_file
        if not os.path.exists(progress_file_path):
            print(f"Error: Progress file not found: {progress_file_path}")
            return

        try:
            with open(progress_file_path, 'r', encoding='utf-8') as pf:
                data = json.load(pf)
            novel_title = data['novel_title']
            original_start_url = data['original_start_url']
            safe_novel_title_dir_name = data['output_base_dir_name']
            current_url = data.get('next_url_to_scrape')
            print(f"Resuming scrape for '{novel_title}' from progress file: {progress_file_path}")
            if current_url is None:
                print("Progress file indicates task was already completed.")
                _attempt_cleanup_completed_progress_file(progress_file_path)
                return
        except (KeyError, json.JSONDecodeError, IOError) as e:
            print(f"Error reading or parsing progress file {progress_file_path}: {e}")
            return
    
    elif args.new_scrape:  # New scrape (or implicit resume)
        start_url_param = args.new_scrape[0]
        novel_title_param = args.new_scrape[1]
        
        novel_title = novel_title_param
        original_start_url = start_url_param # Tentative, might be overwritten if implicitly resuming
        safe_novel_title_dir_name = novel_title.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # Use custom output path if provided, otherwise use Novels/novel_title directory structure
        if args.output_path:
            base_output_dir = args.output_path
            progress_file_path = os.path.join(base_output_dir, f"{safe_novel_title_dir_name}_progress.json")
        else:
            base_output_dir = os.path.join("Novels", safe_novel_title_dir_name)
            progress_file_path = os.path.join(base_output_dir, f"{safe_novel_title_dir_name}_progress.json")

        if os.path.exists(progress_file_path):
            print(f"Found existing progress file based on novel title: {progress_file_path}. Attempting implicit resume.")
            try:
                with open(progress_file_path, 'r', encoding='utf-8') as pf:
                    data = json.load(pf)
                # Use data from file for consistency if implicitly resuming
                novel_title = data.get('novel_title', novel_title) # Prefer file if available
                original_start_url = data.get('original_start_url', original_start_url) # Prefer file
                safe_novel_title_dir_name = data.get('output_base_dir_name', safe_novel_title_dir_name) # Prefer file
                current_url = data.get('next_url_to_scrape')
                
                if current_url is None:
                    print("Existing progress file indicates task was already completed.")
                    _attempt_cleanup_completed_progress_file(progress_file_path)
                    return
                print(f"Implicitly resuming for '{novel_title}'. Next URL: {current_url}")
            except (KeyError, json.JSONDecodeError, IOError) as e:
                print(f"Error reading existing progress file {progress_file_path}: {e}. Starting as new scrape from {original_start_url}.")
                current_url = original_start_url
                # Save initial full progress for this truly new attempt
                _save_current_progress(progress_file_path, novel_title, original_start_url, base_output_dir, None, current_url)
        else:
            print(f"Starting new scrape for '{novel_title}' from URL: {original_start_url}")
            current_url = original_start_url
            # Save initial progress state for a brand new scrape
            _save_current_progress(progress_file_path, novel_title, original_start_url, base_output_dir, None, current_url)
    else:
        # Should not happen due to mutually exclusive group in argparse
        print("Error: Invalid arguments. Please specify a progress file or new scrape details.")
        return

    # Set final output directory - use custom path if provided, otherwise use Novels/novel_title with novel-specific Raws subfolder
    if args.output_path:
        output_dir_path = os.path.join(args.output_path, f"{safe_novel_title_dir_name}-Raws")
    else:
        output_dir_path = os.path.join("Novels", safe_novel_title_dir_name, f"{safe_novel_title_dir_name}-Raws")

    if not _ensure_output_directory(output_dir_path):
        return

    chapters_saved_this_session = 0
    max_chapters = args.max_chapters

    # Detect and print which extraction backend will be used
    if current_url:
        backend = detect_extraction_backend(current_url)
        backend_name = backend.__class__.__name__
        print(f"Using extraction backend: {backend_name}")

    print(f"--- Starting scrape for '{novel_title}' --- URL: {current_url}")
    print(f"Output directory: {output_dir_path}")
    print(f"Progress file: {progress_file_path}")
    print(f"Maximum chapters to scrape in this session: {max_chapters}")

    for i in range(max_chapters):
        if not current_url:
            print("No more chapters to scrape (current URL is None).")
            _attempt_cleanup_completed_progress_file(progress_file_path)
            break

        print(f"Scraping chapter from: {current_url}")
        title, paragraphs, next_url_from_scraper, chapter_num_str = scrape_novel_content(current_url, source_type='url')

        if title is None or title.startswith("Error:") or title == "No Content Found" or title == "Invalid Source Type":
            print(f"Error scraping {current_url}: {title}. Stopping session.")
            # Progress not saved for this failed attempt, will retry current_url next time
            break

        if not chapter_num_str:
            print(f"Warning: Could not determine chapter number for URL {current_url} (Title: \"{title}\"). Skipping save.")
            _save_current_progress(progress_file_path, novel_title, original_start_url, safe_novel_title_dir_name, current_url, next_url_from_scraper)
            print(f"Progress updated to skip {current_url}.")
        else:
            if _create_chapter_file(output_dir_path, chapter_num_str, title, paragraphs):
                chapters_saved_this_session += 1
                print("-" * 70) 
                print(f"Successfully saved: {os.path.join(output_dir_path, f'Chapter_{chapter_num_str}.md')} (Session total: {chapters_saved_this_session})")
                _save_current_progress(progress_file_path, novel_title, original_start_url, safe_novel_title_dir_name, current_url, next_url_from_scraper)

                if not next_url_from_scraper:
                    print("Successfully processed the last available chapter for this novel.")
                    _attempt_cleanup_completed_progress_file(progress_file_path)
            else:
                print(f"Failed to save {os.path.join(output_dir_path, f'Chapter_{chapter_num_str}.md')}. Stopping session to allow retry.")
                break 
        
        last_processed_url = current_url # For progress saving on skip
        current_url = next_url_from_scraper 

        if current_url:
            sleep_duration = random.uniform(1, 3)
            print(f"Sleeping for {sleep_duration:.2f} seconds before next chapter...")
            time.sleep(sleep_duration)
    
    else: 
        if i == max_chapters - 1 and current_url:
            print(f"Reached maximum scrape limit of {max_chapters} chapters for '{novel_title}'.")
            print(f"More chapters might be available. Progress for resuming from {current_url} is saved in {progress_file_path}.")

    print(f"\nScraping session finished for '{novel_title}'. Total chapters saved in this session: {chapters_saved_this_session}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape novel chapters. Provide either a progress file to resume or details for a new scrape.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", "--progress-file", 
                       help="Path to an existing progress JSON file to resume scraping.")
    group.add_argument("-n", "--new-scrape", 
                       nargs=2, 
                       metavar=('START_URL', 'NOVEL_TITLE'),
                       help="Start a new scrape. Requires START_URL and NOVEL_TITLE.\nExample: -n \"https://example.com/chapter1\" \"My Novel Title\"")

    parser.add_argument("-m", "--max-chapters", 
                        type=int, 
                        default=1000, 
                        help="Maximum number of chapters to scrape in this session (default: 1000).")
    
    parser.add_argument("-o", "--output-path", 
                        type=str, 
                        help="Custom output directory path. If not specified, uses novel title as directory name.")
    
    args = parser.parse_args()
    main(args) # Pass the parsed args object to main
