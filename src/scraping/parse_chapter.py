import requests
from bs4 import BeautifulSoup
import re
import cloudscraper
import os
import sys
import time
import json
import random
import argparse
import urllib3

# Ensure the package root is in the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import src.scraping.generic_parser as generic_parser
from urllib.parse import urlparse, urljoin
from typing import Optional

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

# --- Helper Functions ---

def _ensure_output_directory(dir_path: str) -> bool:
    """Ensures the output directory exists, creating it if necessary."""
    if not os.path.exists(dir_path):
        try:
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
    processed_url: str | None,
    next_url_to_process: str | None
):
    """Saves the current scraping progress to a JSON file."""
    progress = {
        'novel_title': novel_title,
        'original_start_url': original_start_url,
        'output_base_dir_name': output_base_dir_name,
        'last_processed_url': processed_url,
        'next_url_to_scrape': next_url_to_process,
        'last_save_time': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(progress_file_path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=4)

def _create_chapter_file(output_dir_path: str, chapter_num_str: str, title: str, content: str) -> bool:
    """Creates a new chapter file, ensuring no overwrite."""
    if not chapter_num_str:
        print("Warning: Chapter number not found. Skipping file creation.")
        return False
        
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    file_name = f"chapter_{chapter_num_str.zfill(4)}_{safe_title}.html"
    file_path = os.path.join(output_dir_path, file_name)

    if os.path.exists(file_path):
        print(f"File already exists: {file_path}. Skipping.")
        return False

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n')
            file.write(f'  <meta charset="UTF-8">\n  <title>{title}</title>\n')
            file.write('</head>\n<body>\n')
            file.write(f'  <h1>{title}</h1>\n')
            file.write(content)
            file.write('\n</body>\n</html>')
        print(f"Successfully saved chapter: {file_name}")
        return True
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")
        return False

def main(args: argparse.Namespace):
    """Main function to run the novel scraper."""
    
    # Use the custom output path if provided, otherwise default to "Novels"
    novels_base_dir = args.output_path if args.output_path else "Novels"

    start_url = args.url
    output_dir_name = args.output_dir
    max_chapters = args.max_chapters
    start_chapter = args.start_chapter

    # Load all scraper configurations
    try:
        all_configs = generic_parser.load_configs_from_directory('scraper_configs/')
        if not all_configs:
            print("Error: No scraper configurations found in 'scraper_configs/'. Exiting.")
            return
    except FileNotFoundError as e:
        print(f"Error: {e}. Exiting.")
        return

    scraper = NovelScraper()
    current_url = start_url
    chapters_scraped = 0
    novel_title = "Unknown Novel" # Default title
    output_dir_path = ""
    progress_file_path = ""
    novel_base_dir_path = ""
    current_chapter_num = 0 # To track chapter numbers for skipping

    # The progress file path is now determined AFTER the novel title is known
    # so it can be placed inside the novel's main directory.

    # Try to determine novel title early for resuming, if possible
    temp_title_for_resume = "Unknown"
    if args.title:
        temp_title_for_resume = args.title
    elif args.output_dir:
        temp_title_for_resume = args.output_dir

    if temp_title_for_resume != "Unknown":
        temp_novel_base_path = os.path.join(novels_base_dir, temp_title_for_resume)
        temp_progress_file = os.path.join(temp_novel_base_path, f"{temp_title_for_resume}_progress.json")
        if not args.no_progress and os.path.exists(temp_progress_file):
            progress_file_path = temp_progress_file # Set the real progress file path
            _attempt_cleanup_completed_progress_file(progress_file_path)
            if os.path.exists(progress_file_path):
                with open(progress_file_path, 'r', encoding='utf-8') as pf:
                    progress = json.load(pf)
                    print(f"Resuming from saved progress: {progress['last_processed_url']}")
                    current_url = progress['next_url_to_scrape']
                    novel_title = progress['novel_title']
                    output_dir_name = progress['output_base_dir_name']

    if not current_url:
        print("Scraping has already been completed for this URL. Exiting.")
        return

    while current_url and (max_chapters is None or chapters_scraped < max_chapters):
        # Get the config for the current URL
        site_config = generic_parser.get_config_for_url(current_url, all_configs)
        if not site_config:
            print(f"Error: Unsupported website '{urlparse(current_url).netloc}'. No configuration found.")
            print("Please create a configuration file in 'scraper_configs/' to support this site.")
            break
            
        print(f"\nScraping chapter from: {current_url}")
        html_content = scraper.fetch_url(current_url)

        if not html_content:
            print(f"Failed to retrieve content for chapter at {current_url}. Stopping.")
            if progress_file_path and not args.no_progress:
                _save_current_progress(progress_file_path, novel_title, start_url, output_dir_name, current_url, current_url)
            break
        
        # Parse the HTML using the generic parser
        parsed_data = generic_parser.parse_html(html_content, site_config, current_url)
        
        title = parsed_data.get("chapter_title")
        content = parsed_data.get("content")
        next_chapter_url = parsed_data.get("next_chapter_url")
        chapter_number = parsed_data.get("chapter_number")

        if not title or not content:
            print(f"Could not extract title or content from {current_url}. Stopping.")
            if progress_file_path and not args.no_progress:
                _save_current_progress(progress_file_path, novel_title, start_url, output_dir_name, current_url, current_url)
            break

        if chapters_scraped == 0:
            # First chapter, set up all paths
            novel_title = args.title or title.split(' ')[0]
            
            # Define the main directory for the novel
            safe_novel_title = re.sub(r'[\\/*?:"<>|]', "", novel_title)
            novel_base_dir_path = os.path.join(novels_base_dir, safe_novel_title)
            
            # Define the directory for the raw chapter files
            output_dir_name = f"{safe_novel_title}-Raws"
            output_dir_path = os.path.join(novel_base_dir_path, output_dir_name)
            
            # Define the progress file path inside the main novel directory
            progress_file_path = os.path.join(novel_base_dir_path, f"{safe_novel_title}_progress.json")
            
            _ensure_output_directory(output_dir_path)
        
        current_chapter_num = chapter_number or (current_chapter_num + 1)

        if start_chapter and current_chapter_num < start_chapter:
            print(f"Skipping Chapter {current_chapter_num} (Starting at {start_chapter})")
            current_url = next_chapter_url
            continue

        if _create_chapter_file(output_dir_path, str(current_chapter_num), title, content):
            chapters_scraped += 1
        
        last_processed_url = current_url
        current_url = next_chapter_url
        
        if not args.no_progress and progress_file_path:
            _save_current_progress(progress_file_path, novel_title, start_url, os.path.basename(novel_base_dir_path), last_processed_url, current_url)

        if current_url:
            time.sleep(random.uniform(1, 4)) # Respectful delay
        else:
            print("\nNo next chapter URL found. Scraping finished.")
            if progress_file_path:
                _attempt_cleanup_completed_progress_file(progress_file_path)

    print(f"\nScraping complete. Total chapters scraped: {chapters_scraped}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape a novel from a website.')
    parser.add_argument('url', help='The starting URL of the novel to scrape.')
    parser.add_argument('--max-chapters', '-m', type=int, help='The maximum number of chapters to scrape.')
    parser.add_argument('--output-dir', '-o', help='Specify the output directory name. Defaults to novel title.')
    parser.add_argument('--start-chapter', '-s', type=int, help='The chapter number to start scraping from.')
    parser.add_argument('--title', '-t', help='Set a custom title for the novel folder.')
    parser.add_argument('--output-path', help='Specify a custom base output path. Overrides the default "Novels" directory.')
    parser.add_argument('--no-progress', action='store_true', help='Disable loading from or saving to progress files.')
    
    args = parser.parse_args()
    main(args)
