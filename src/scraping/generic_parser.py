# src/scraping/generic_parser.py 
import json
import os
from pathlib import Path
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup

def load_configs_from_directory(dir_path: str) -> dict:
    """
    Scans a directory for .json files and loads them into a dictionary.

    The dictionary key is the filename without the .json extension.

    Args:
        dir_path: The path to the directory containing the configuration files.

    Returns:
        A dictionary containing all website configurations.
    """
    config_dir = Path(dir_path)
    if not config_dir.is_dir():
        raise FileNotFoundError(f"Configuration directory not found: {dir_path}")

    configs = {}
    for file_path in config_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                config_key = file_path.stem
                configs[config_key] = config_data
        except json.JSONDecodeError:
            print(f"Warning: Skipping invalid JSON file: {file_path.name}")
        except Exception as e:
            print(f"Warning: Could not process file {file_path.name}: {e}")
    
    return configs 

def get_config_for_url(url: str, configs: dict) -> dict | None:
    """
    Finds the matching configuration for a given URL based on its domain.
    It supports direct matches, 'www.' stripping, and partial matches for site families.
    """
    if not url:
        return None
        
    try:
        netloc = urlparse(url).netloc
    except Exception:
        return None # Handle potential malformed URLs

    if not netloc:
        return None

    # 1. Try direct match (e.g., "www.example.com")
    if netloc in configs:
        return configs[netloc]

    # 2. Try stripping "www." (e.g., "example.com")
    if netloc.startswith("www."):
        domain = netloc[4:]
        if domain in configs:
            return configs[domain]
            
    # 3. Handle common domain families
    # Example: "69shuba.pro" should match a "69shu-family" config
    if "69shu" in netloc:
        if "69shu-family" in configs:
            return configs["69shu-family"]

    return None

def parse_html(html_content: str, config: dict, current_url: str) -> dict:
    """
    Parses the HTML content of a chapter page based on a site-specific config.

    Args:
        html_content: The HTML content of the chapter page.
        config: The configuration dictionary for the website.
        current_url: The URL of the page being parsed (for resolving relative links).

    Returns:
        A dictionary containing the extracted data.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    extracted_data = {
        "chapter_title": None,
        "chapter_number": None,
        "next_chapter_url": None,
        "content": ""
    }

    # --- Extract Chapter Title ---
    title_config = config.get("chapter_title", {})
    if title_config.get("selector"):
        title_element = soup.select_one(title_config["selector"])
        if title_element:
            extracted_data["chapter_title"] = title_element.get_text(strip=True)

    # --- Extract Chapter Number ---
    number_config = config.get("chapter_number", {})
    if number_config.get("selector") and number_config.get("regex"):
        number_element = soup.select_one(number_config["selector"])
        if number_element:
            match = re.search(number_config["regex"], number_element.get_text())
            if match and match.group(1):
                extracted_data["chapter_number"] = int(match.group(1))

    # --- Extract Next Chapter URL ---
    next_url_config = config.get("next_chapter_url", {})
    next_chapter_url = None
    if next_url_config.get("selector"):
        links = soup.select(next_url_config["selector"])
        
        if "text_contains" in next_url_config:
            for link in links:
                if next_url_config["text_contains"] in link.get_text():
                    next_chapter_url = link.get(next_url_config.get("attribute", "href"))
                    break
        elif links:
            next_chapter_url = links[0].get(next_url_config.get("attribute", "href"))
    
    if next_chapter_url:
        extracted_data["next_chapter_url"] = urljoin(current_url, next_chapter_url)

    # --- Extract and Clean Content ---
    content_config = config.get("content_container", {})
    content_container = soup.select_one(content_config.get("selector", ""))
    
    if content_container:
        if "cleanup_selectors" in content_config:
            for selector in content_config["cleanup_selectors"]:
                for element in content_container.select(selector):
                    element.decompose()

        if "cleanup_text_contains" in content_config:
            for text_to_find in content_config["cleanup_text_contains"]:
                for element in content_container.find_all(string=re.compile(re.escape(text_to_find))):
                    if element.parent.name != '[document]':
                         element.parent.decompose()

        if "content_element" in content_config:
            elements = content_container.select(content_config["content_element"])
            extracted_data["content"] = "\n".join(str(elem) for elem in elements)
        else:
            extracted_data["content"] = str(content_container)

    return extracted_data 