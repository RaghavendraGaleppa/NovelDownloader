import requests
from bs4 import BeautifulSoup
import re
import cloudscraper
import os
import time
import json
import random
import argparse

# PROGRESS_FILE constant is removed, will be generated dynamically.

# --- Helper Functions ---

# Ensure other functions (scrape_chapter, get_next_chapter_url, scrape_novel_content, get_chapter_number)
# are defined above this point, or imported if they were in separate files.

def scrape_chapter(url):
    # Initialize cloudscraper
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'linux',  # Or 'windows', 'darwin' based on your OS
            'mobile': False
        }
    )
    response = None # Initialize response to None
    try:
        response = scraper.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e: # More specific exception
        error_message = f"Failed to fetch {url}"
        if response is not None: 
            error_message += f" - Status Code: {response.status_code}"
        error_message += f" - Error: {e}"
        print(error_message)
        return None # Return None to indicate failure
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred in scrape_chapter for URL {url}: {e}")
        return None


def get_next_chapter_url(html_content):
    """
    Extracts the URL for the next chapter from the given HTML content.

    Args:
        html_content (str): The HTML content of the novel chapter page.

    Returns:
        str or None: The URL of the next chapter, or None if not found.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the 'div' with class 'page1' which contains navigation links
    page_navigation_div = soup.find('div', class_='page1')

    if page_navigation_div:
        # Look for an 'a' tag within this div that has the text "下一章" (Next Chapter)
        # Note: '下一章' is the Chinese text for "Next Chapter"
        next_chapter_link = page_navigation_div.find('a', string="下一章")
        
        if next_chapter_link and 'href' in next_chapter_link.attrs:
            return next_chapter_link['href']
    
    return None # Return None if the next chapter link is not found

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

    # Get the next chapter URL
    next_chapter_url = get_next_chapter_url(html_doc)
    # Get the chapter number
    chapter_number = get_chapter_number(html_doc)

    # Parse the HTML content
    soup = BeautifulSoup(html_doc, 'html.parser')

    # Extract the title from the <title> tag in the <head> section
    page_title = soup.title.string.strip() if soup.title and soup.title.string else "No Title Found"

    # Extract the novel text paragraphs
    novel_text_container = soup.find('div', class_='txtnav')
    final_paragraphs = []

    if novel_text_container:
        # Get the chapter title from the <h1> tag inside 'txtnav' to remove potential duplication in text
        chapter_title_in_h1 = ""
        h1_tag = novel_text_container.find('h1')
        if h1_tag:
            chapter_title_in_h1 = h1_tag.get_text(strip=True)

        # Remove advertisement, info, and navigation divs before extracting text
        for div_id in ['txtright', 'baocuo', 'tuijian']:
            div_to_remove = novel_text_container.find('div', id=div_id)
            if div_to_remove:
                div_to_remove.extract()
        for div_class in ['bottom-ad', 'contentadv', 'txtinfo', 'page1']:
            for div_to_remove in novel_text_container.find_all('div', class_=div_class):
                div_to_remove.extract()
        
        # Extract the entire text content from the cleaned novel_text_container
        # We need to preserve <br> tags as they indicate line/paragraph breaks.
        # Get the inner HTML of the container after removing unwanted elements.
        raw_text_html = str(novel_text_container)

        # Clean up specific HTML entities (like &emsp;)
        raw_text_html = raw_text_html.replace('&emsp;', '')
        
        # Replace <br> tags with a unique temporary placeholder for easier processing later
        # Use regex to catch variations like <br/>, <br > etc.
        raw_text_html = re.sub(r'<br\s*?/?>', '__BR__', raw_text_html)

        # Now, parse this modified HTML snippet to get the text content.
        # BeautifulSoup's get_text() with a separator helps here.
        cleaned_text = BeautifulSoup(raw_text_html, 'html.parser').get_text(separator='').strip()
        
        # Replace sequences of two or more '__BR__' with a standardized paragraph break (\n\n)
        # This treats `<br><br>` (or more) as a new paragraph.
        cleaned_text = cleaned_text.replace('__BR____BR__', '\n\n')
        # Remove single '__BR__' which typically represent line breaks within a paragraph, not new paragraphs.
        cleaned_text = cleaned_text.replace('__BR__', '').strip()
        
        # Remove the duplicated chapter title from the beginning of the text content if it exists
        if chapter_title_in_h1 and cleaned_text.startswith(chapter_title_in_h1):
            cleaned_text = cleaned_text[len(chapter_title_in_h1):].strip()

        # Normalize any remaining sequences of multiple newlines into a single paragraph break
        cleaned_text = re.sub(r'\n{2,}', '\n\n', cleaned_text).strip()
        
        # Split the cleaned text into paragraphs based on the double newline separator
        final_paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]

    return page_title, final_paragraphs, next_chapter_url, chapter_number

def get_chapter_number(html_content: str) -> str | None:
    """
    Extracts the chapter number from the given HTML content.

    Args:
        html_content (str): The HTML content of the novel chapter page.

    Returns:
        str or None: The chapter number as a string, or None if not found.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    chapter_number = None

    # Try to find chapter number in <h1> tag within div.txtnav
    txtnav_div = soup.find('div', class_='txtnav')
    if txtnav_div:
        h1_tag = txtnav_div.find('h1')
        if h1_tag and h1_tag.string:
            # Regex to find "第<number>章"
            match = re.search(r'第(\d+)章', h1_tag.string)
            if match:
                chapter_number = match.group(1)

    # If not found in <h1>, try to find in <title> tag
    if not chapter_number and soup.title and soup.title.string:
        match = re.search(r'第(\d+)章', soup.title.string)
        if match:
            chapter_number = match.group(1)
            
    # Fallback: try to find a pattern like "Chapter <number>" or "第<number>话" etc.
    # This is a more generic attempt if the specific "第X章" is not found.
    if not chapter_number:
        # Attempt to find chapter number in h1 tag within div.txtnav if specific pattern failed
        if txtnav_div:
            h1_tag = txtnav_div.find('h1')
            if h1_tag and h1_tag.string:
                # Regex for "第" followed by digits, then "章" or "话" or space or end of string
                match = re.search(r'第\s*(\d+)\s*章|第\s*(\d+)\s*话|Chapter\s*(\d+)|第\s*(\d+)', h1_tag.string, re.IGNORECASE)
                if match:
                    # match.groups() will return a tuple like (None, '5', None, None)
                    # We need to find the first non-None group
                    chapter_number = next((g for g in match.groups() if g is not None), None)

        # If still not found, try in <title> tag with the more generic regex
        if not chapter_number and soup.title and soup.title.string:
            match = re.search(r'第\s*(\d+)\s*章|第\s*(\d+)\s*话|Chapter\s*(\d+)|第\s*(\d+)', soup.title.string, re.IGNORECASE)
            if match:
                chapter_number = next((g for g in match.groups() if g is not None), None)
                
    return chapter_number


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
        
        # Use custom output path if provided, otherwise use novel title directory
        if args.output_path:
            base_output_dir = args.output_path
            progress_file_path = os.path.join(base_output_dir, f"{safe_novel_title_dir_name}_progress.json")
        else:
            base_output_dir = safe_novel_title_dir_name
            progress_file_path = os.path.join(safe_novel_title_dir_name, f"{safe_novel_title_dir_name}_progress.json")

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

    # Set final output directory - use custom path if provided, otherwise use novel title with Raws subfolder
    if args.output_path:
        output_dir_path = os.path.join(args.output_path, "Raws")
    else:
        output_dir_path = os.path.join(safe_novel_title_dir_name, "Raws")

    if not _ensure_output_directory(output_dir_path):
        return

    chapters_saved_this_session = 0
    max_chapters = args.max_chapters

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

# Ensure other functions (scrape_chapter, get_next_chapter_url, scrape_novel_content, get_chapter_number)
# ... existing code ...
