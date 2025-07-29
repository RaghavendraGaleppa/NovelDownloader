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
from src.scraping.extraction_backends import ExtractionBackend, EB69Shu, EB1QXS
from urllib.parse import urlparse
from typing import Optional
from datetime import datetime
from main import db_client
from bson.objectid import ObjectId

# Add these imports at the top
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# PROGRESS_FILE constant is removed, will be generated dynamically.

# --- Scraper Class ---

class SeleniumScraper:
    """
    Browser-based scraper using Selenium for handling complex Cloudflare challenges.
    """
    
    def __init__(self, timeout=30, headless=True):
        self.timeout = timeout
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Set up Chrome driver with options to bypass detection."""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        # Anti-detection options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable SSL verification
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def fetch_url(self, url, wait_for_element=None):
        """
        Fetch content using Selenium.
        
        Args:
            url (str): URL to fetch
            wait_for_element (str): CSS selector to wait for (optional)
            
        Returns:
            str or None: Page source if successful
        """
        try:
            print(f"Loading {url} with Selenium...")
            self.driver.get(url)
            
            # Wait for Cloudflare challenge to complete
            print("Waiting for page to load and challenges to resolve...")
            time.sleep(5)
            
            # If specific element provided, wait for it
            if wait_for_element:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
            else:
                # Wait for body element to ensure page is loaded
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            
            # Additional wait to ensure any dynamic content loads
            time.sleep(3)
            
            return self.driver.page_source
            
        except Exception as e:
            print(f"Selenium fetch failed for {url}: {e}")
            return None
    
    def close(self):
        """Clean up the driver."""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class NovelScraper:
    """
    A web scraper class specifically designed for fetching novel content from websites.
    Handles SSL issues and provides robust HTTP request functionality.
    """
    
    def __init__(self, timeout=30, use_selenium=False):
        """
        Initialize the NovelScraper with SSL verification disabled.
        
        Args:
            timeout (int): Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.use_selenium = use_selenium
        
        if use_selenium:
            self.scraper = SeleniumScraper(timeout=timeout)
        else:
            self.scraper = self._setup_scraper()
    
    def _setup_scraper(self):
        """
        Set up cloudscraper with enhanced Cloudflare bypass capabilities.
        
        Returns:
            cloudscraper.CloudScraper: Configured scraper instance
        """
        # Initialize cloudscraper with better browser simulation
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'linux',
                'mobile': False
            },
            delay=10,  # Add delay for challenge solving
            debug=False
        )
        
        # Add realistic headers
        scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Completely disable SSL verification
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

    def fetch_url(self, url, max_retries=3):
        """
        Fetch content from the given URL with enhanced error handling and retries.
        
        Args:
            url (str): The URL to fetch
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            str or None: The HTML content if successful, None if failed
        """
        if self.use_selenium:
            # Use Selenium scraper directly
            return self.scraper.fetch_url(url)
        
        # Use CloudScraper with retries
        for attempt in range(max_retries):
            try:
                print(f"Attempting to fetch {url} (attempt {attempt + 1}/{max_retries})")
                
                # Add delay between attempts
                if attempt > 0:
                    wait_time = (attempt * 5) + random.uniform(2, 5)
                    print(f"Waiting {wait_time:.2f} seconds before retry...")
                    time.sleep(wait_time)
                
                response = self.scraper.get(url, verify=False, timeout=self.timeout)
                
                # Check for Cloudflare challenge
                if response.status_code == 403 and 'Just a moment' in response.text:
                    print(f"Cloudflare challenge detected on attempt {attempt + 1}. Retrying...")
                    continue
                
                response.raise_for_status()
                return response.text
                
            except requests.exceptions.RequestException as e:
                error_message = f"Attempt {attempt + 1} failed to fetch {url}"
                if 'response' in locals():
                    error_message += f" - Status Code: {response.status_code}"
                error_message += f" - Error: {e}"
                print(error_message)
                
                if attempt == max_retries - 1:
                    print(f"All {max_retries} attempts failed for {url}")
                    return None
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1} for URL {url}: {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def close(self):
        """Clean up resources."""
        if self.use_selenium and hasattr(self.scraper, 'close'):
            self.scraper.close()

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

def scrape_chapter(url, use_selenium=False):
    """
    Scrape a chapter from the given URL.
    
    Args:
        url (str): The URL of the chapter to scrape
        use_selenium (bool): Whether to use Selenium instead of CloudScraper
        
    Returns:
        str or None: The HTML content if successful, None if failed
    """
    scraper = NovelScraper(use_selenium=use_selenium)
    try:
        return scraper.fetch_url(url)
    finally:
        if use_selenium:
            scraper.close()

def get_next_chapter_url(html_content: str, url: Optional[str] = None) -> Optional[str]:
    """
    Extracts the URL for the next chapter from the given HTML content.

    Args:
        html_content (str): The HTML content of the novel chapter page.
        url (str, optional): The original URL for backend detection and relative URL resolution.

    Returns:
        str or None: The URL of the next chapter, or None if not found.
    """
    # Use default backend if no URL provided for detection
    backend = detect_extraction_backend(url) if url else EB69Shu()
    return backend.get_next_chapter_url(html_content, url)

def scrape_novel_content(source: str, source_type: str = 'file', use_selenium: bool = False) -> tuple[str, list[str], str | None, str | None]:
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
            html_doc = scrape_chapter(source, use_selenium=use_selenium)
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
    
    # Extract all content using the backend, passing current URL for relative URL resolution
    current_url = source if source_type == 'url' else None
    title, paragraphs, next_chapter_url, chapter_number = backend.extract_all_content(html_doc, current_url)

    return title, paragraphs, next_chapter_url, chapter_number

def get_chapter_number(html_content: str, url: Optional[str] = None) -> Optional[str]:
    """
    Extracts the chapter number from the given HTML content.

    Args:
        html_content (str): The HTML content of the novel chapter page.
        url (str, optional): The original URL for backend detection and URL-based extraction fallback.

    Returns:
        str or None: The chapter number as a string, or None if not found.
    """
    # Use default backend if no URL provided for detection
    backend = detect_extraction_backend(url) if url else EB69Shu()
    return backend.get_chapter_number(html_content, url)

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

def _save_current_progress(
    novel_id: ObjectId, 
    processed_url: str | None, # URL of the chapter just processed
    next_url_to_process: str | None,
    last_chapter_parsed_num: Optional[int]
):
    """Saves the current scraping progress to MongoDB."""
    progress_collection = db_client["scraping_progress"]
    
    update_payload = {
        'last_scraped_url': processed_url,
        'next_url_to_scrape': next_url_to_process,
        'last_chapter_parsed': last_chapter_parsed_num
    }
    
    progress_collection.update_one(
        {'novel_id': novel_id},
        {'$set': update_payload}
    )

def _upsert_raw_chapter_record(
    novel_id: ObjectId,
    progress_id: ObjectId,
    chapter_number: int,
    title: str,
    saved_at: str
):
    """Creates or updates a record for the scraped chapter in 'raw_chapters' collection."""
    raw_chapters_collection = db_client["raw_chapters"]
    
    filter_query = {
        'novel_id': novel_id,
        'chapter_number': chapter_number
    }
    
    update_payload = {
        '$inc': {'n_parts': 1},
        '$set': { 'updated_at': datetime.now() },
        '$setOnInsert': {
            'novel_id': novel_id,
            'progress_id': progress_id,
            'chapter_number': chapter_number,
            'title': title,
            'saved_at': saved_at,
            'created_at': datetime.now()
        }
    }
    
    raw_chapters_collection.update_one(
        filter_query,
        update_payload,
        upsert=True
    )

def _update_novel_raw_chapters_available(
    novel_id: ObjectId
):
    """Updates the 'raw_chapters_available' field in the 'novels' collection with the total count."""
    raw_chapters_collection = db_client["raw_chapters"]
    novels_collection = db_client["novels"]
    
    count = raw_chapters_collection.count_documents({'novel_id': novel_id})
    
    novels_collection.update_one(
        {'_id': novel_id},
        {'$set': {'raw_chapters_available': count}}
    )

def _create_chapter_file(output_dir_path: str, chapter_num_str: str, title: str, paragraphs: list[str]) -> bool:
    """Creates or appends to a markdown file for the given chapter content in the specified output directory."""
    filename = f"Chapter_{chapter_num_str}.md"
    filepath = os.path.join(output_dir_path, filename)
    
    try:
        # Check if file already exists
        file_exists = os.path.exists(filepath)
        
        # Use append mode if file exists, write mode if new
        mode = 'a' if file_exists else 'w'
        
        with open(filepath, mode, encoding='utf-8') as f:
            if not file_exists:
                # New file - write header and title
                f.write(f"# {title}\n\n")
            else:
                # Existing file - add separator and content
                f.write(f"\n\n---\n\n**{title}**\n\n")
            
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
    output_dir_path: str # For Raws subfolder
    novel_id: ObjectId
    progress_id: Optional[ObjectId] = None

    novel_title = args.novel_title
    start_url_param = args.start_url
    
    safe_novel_title_dir_name = novel_title.replace(' ', '_').replace('/', '_').replace('\\', '_')
    
    # Use custom output path if provided, otherwise use Novels/novel_title directory structure
    if args.output_path:
        base_output_dir = args.output_path
    else:
        base_output_dir = os.path.join("Novels", safe_novel_title_dir_name)

    # --- MongoDB integration for progress ---
    novels_collection = db_client["novels"]
    progress_collection = db_client["scraping_progress"]

    # Check if novel exists to decide between new scrape and resume
    novel_doc = novels_collection.find_one({'novel_name': novel_title})

    if novel_doc:
        # Novel exists, potential resume
        novel_id = novel_doc['_id']
        print(f"Found existing novel '{novel_title}' with ID: {novel_id}. Checking for progress.")

        progress_doc = progress_collection.find_one({'novel_id': novel_id})
        progress_id = progress_doc['_id'] if progress_doc else None

        if progress_doc:
            # Resume scrape
            original_start_url = progress_doc['original_start_url']
            safe_novel_title_dir_name = progress_doc['output_base_dir_name']
            current_url = progress_doc.get('next_url_to_scrape')
            # Initialize last known chapter from existing record
            last_known_chapter_num = progress_doc.get('last_chapter_parsed')
            print(f"Resuming scrape for '{novel_title}'.")

            raws_folder_from_db = progress_doc.get('raws_folder')
            if raws_folder_from_db:
                output_dir_path = raws_folder_from_db
            else:
                # Fallback for old records: use folder_path from novel doc
                novel_folder_path = novel_doc.get('folder_path')
                if novel_folder_path:
                    output_dir_path = os.path.join(novel_folder_path, "Raws")
                else:
                    # Fallback if folder_path is somehow missing
                    output_dir_path = os.path.join(base_output_dir, "Raws")

            if current_url is None:
                print("Progress data indicates task was previously completed. Checking for new chapters...")
                # Check if there are new chapters available by re-scraping the last URL
                last_scraped_url = progress_doc.get('last_scraped_url')
                
                if last_scraped_url:
                    print(f"Checking last scraped URL for new chapters: {last_scraped_url}")
                    
                    try:
                        # Scrape the last URL to see if there's a new next chapter
                        html_content = scrape_chapter(last_scraped_url, use_selenium=args.use_selenium)
                        if html_content:
                            new_next_url = get_next_chapter_url(html_content, last_scraped_url)
                            if new_next_url:
                                print(f"🎉 Found new chapter! Will continue from: {new_next_url}")
                                current_url = new_next_url
                                # Update progress to reflect the new URL to scrape
                                _save_current_progress(novel_id, last_scraped_url, current_url, last_known_chapter_num)
                            else:
                                print("No new chapters found. Novel appears to be up to date.")
                                return
                        else:
                            print("Failed to re-scrape last URL. Unable to check for new chapters.")
                            return
                    except Exception as e:
                        print(f"Error while checking for new chapters: {e}")
                        return
                else:
                    print("No last scraped URL available. Cannot check for new chapters.")
                    return
        else:
            # Novel exists but no progress. Start from beginning, but need a URL.
            if not start_url_param:
                print(f"Error: Novel '{novel_title}' exists but has no progress record. Please provide a --start-url.")
                return
            
            print(f"No active progress found for '{novel_title}'. Starting new scraping session from {start_url_param}.")
            
            absolute_folder_path = os.path.abspath(base_output_dir)
            output_dir_path = os.path.join(absolute_folder_path, "Raws")
            
            original_start_url = start_url_param
            current_url = original_start_url
            last_known_chapter_num = None # New scrape starts with no chapter parsed
            progress_record = {
                'novel_id': novel_id,
                'original_start_url': original_start_url,
                'output_base_dir_name': safe_novel_title_dir_name,
                'raws_folder': output_dir_path,
                'last_scraped_url': None,
                'next_url_to_scrape': current_url,
                'last_chapter_parsed': None
            }
            inserted_progress = progress_collection.insert_one(progress_record)
            progress_id = inserted_progress.inserted_id

    else:
        # New novel, new scrape
        if not start_url_param:
            print(f"Error: Novel '{novel_title}' not found in DB. Please provide a --start-url to start scraping.")
            return

        print(f"Starting new scrape for '{novel_title}' from URL: {start_url_param}")
        original_start_url = start_url_param
        current_url = original_start_url
        last_known_chapter_num = None # New scrape starts with no chapter parsed

        absolute_folder_path = os.path.abspath(base_output_dir)
        output_dir_path = os.path.join(absolute_folder_path, "Raws")
        
        novel_document = {
            'novel_name': novel_title,
            'added_datetime': datetime.now(),
            'folder_path': absolute_folder_path
        }
        insert_result = novels_collection.insert_one(novel_document)
        novel_id = insert_result.inserted_id
        print(f"Added entry for '{novel_title}' to MongoDB with ID: {novel_id}.")

        # Insert into scraping_progress collection
        progress_record = {
            'novel_id': novel_id,
            'original_start_url': original_start_url,
            'output_base_dir_name': safe_novel_title_dir_name,
            'raws_folder': output_dir_path,
            'last_scraped_url': None,
            'next_url_to_scrape': current_url,
            'last_chapter_parsed': None
        }
        inserted_progress = progress_collection.insert_one(progress_record)
        progress_id = inserted_progress.inserted_id
        print("Created new progress tracking record.")

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
    print(f"Maximum chapters to scrape in this session: {max_chapters}")

    for i in range(max_chapters):
        if not current_url:
            print("No more chapters to scrape (current URL is None).")
            break

        print(f"Scraping chapter from: {current_url}")
        title, paragraphs, next_url_from_scraper, chapter_num_str = scrape_novel_content(
            current_url, 
            source_type='url',
            use_selenium=args.use_selenium
        )

        if title is None or title.startswith("Error:") or title == "No Content Found" or title == "Invalid Source Type":
            print(f"Error scraping {current_url}: {title}. Stopping session.")
            # Progress not saved for this failed attempt, will retry current_url next time
            break

        # Logic to update chapter number
        current_chapter_num_to_save = last_known_chapter_num
        if chapter_num_str:
            match = re.search(r'^\d+', chapter_num_str)
            if match:
                current_chapter_num_to_save = int(match.group(0))
        last_known_chapter_num = current_chapter_num_to_save

        if not chapter_num_str:
            print(f"Warning: Could not determine chapter number for URL {current_url} (Title: \"{title}\"). Skipping save.")
            _save_current_progress(novel_id, current_url, next_url_from_scraper, last_known_chapter_num)
            print(f"Progress updated to skip {current_url}.")
        else:
            # Check if file exists before creation to determine action
            filepath = os.path.join(output_dir_path, f"Chapter_{chapter_num_str}.md")
            file_existed = os.path.exists(filepath)
            
            if _create_chapter_file(output_dir_path, chapter_num_str, title, paragraphs):
                chapters_saved_this_session += 1
                
                if progress_id and last_known_chapter_num is not None:
                    _upsert_raw_chapter_record(
                        novel_id=novel_id,
                        progress_id=progress_id,
                        chapter_number=last_known_chapter_num,
                        title=title,
                        saved_at=filepath
                    )
                    _update_novel_raw_chapters_available(
                        novel_id=novel_id
                    )

                print("-" * 70) 
                
                # Show appropriate message based on whether file existed
                file_action = "Appended to existing" if file_existed else "Successfully saved new"
                print(f"{file_action}: {filepath} (Session total: {chapters_saved_this_session})")
                
                _save_current_progress(novel_id, current_url, next_url_from_scraper, last_known_chapter_num)

                if not next_url_from_scraper:
                    print("Successfully processed the last available chapter for this novel.")
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
            print(f"More chapters might be available. Progress for resuming from {current_url} is saved.")

    print(f"\nScraping session finished for '{novel_title}'. Total chapters saved in this session: {chapters_saved_this_session}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape novel chapters from a URL, with progress tracking in MongoDB.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    parser.add_argument("--novel-title",
                        required=True,
                        help="Title of the novel. Used to identify novel in the database.")
    parser.add_argument("--start-url",
                        help="The starting URL for a scrape. Required for new novels.")

    parser.add_argument("-m", "--max-chapters", 
                        type=int, 
                        default=1000, 
                        help="Maximum number of chapters to scrape in this session (default: 1000).")
    
    parser.add_argument("-o", "--output-path", 
                        type=str, 
                        help="Custom output directory path. If not specified, uses novel title as directory name.")
    
    parser.add_argument("--use-selenium", 
                    action="store_true",
                    help="Use Selenium WebDriver instead of CloudScraper for bypassing Cloudflare")
    
    args = parser.parse_args()
    main(args) # Pass the parsed args object to main
