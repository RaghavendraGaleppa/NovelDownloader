# Implementation Plan: Backend-Agnostic Scraping Framework (Revised)

This document outlines the step-by-step process for refactoring the scraper to use a modular, configuration-driven framework. This plan incorporates the idea of using a dedicated directory with one configuration file per website for better organization and testing.

## Addressing the Scope of Changes

-   **`src/scraping/extraction_backends.py`**: Will be **deleted**.
-   **`src/scraping/parse_chapter.py`**: Will be **heavily refactored** to use the new generic parser.
-   **New Folder: `scraper_configs/`**: Will be **created** to hold the individual website JSON configuration files.
-   **New File: `src/scraping/generic_parser.py`**: Will be **created** to house the new parsing engine.
-   **`tool.py`**: No changes expected.

---

## Step 1: Create the Modular Configuration Structure

1.  **Create Directory**: Create a new directory named `scraper_configs` in the root of the project. This will store all website-specific configurations.

2.  **Create `69shu.com.json`**: Inside `scraper_configs/`, create a new file named `69shu.com.json`. Populate it with the configuration for 69shu:
    ```json
    {
      "next_chapter_url": {
        "selector": "div.page1 a",
        "text_contains": "下一章",
        "attribute": "href"
      },
      "chapter_title": {
        "selector": "div.txtnav h1"
      },
      "content_container": {
        "selector": "div.txtnav",
        "cleanup_selectors": ["#txtright", ".bottom-ad", ".contentadv", ".txtinfo", ".page1"]
      },
      "chapter_number": {
        "selector": "div.txtnav h1",
        "regex": "第(\\d+)章"
      }
    }
    ```

3.  **Create `1qxs.com.json`**: Inside `scraper_configs/`, create `1qxs.com.json`. Populate it with the configuration for 1qxs:
    ```json
    {
      "next_chapter_url": {
        "selector": "#next",
        "attribute": "href"
      },
      "chapter_title": {
        "selector": ".title h1"
      },
      "content_container": {
        "selector": "div.content",
        "content_element": "p",
        "cleanup_text_contains": ["本章未完，点击"]
      },
      "chapter_number": {
        "selector": ".title h1",
        "regex": "^(\\d+)："
      }
    }
    ```

## Step 2: Create and Build the Generic Parser

This step focuses entirely on the self-contained, reusable `generic_parser.py` file.

1.  **Create File Stub**: Create the new file `src/scraping/generic_parser.py`.

2.  **Implement Configuration Loader**: In `generic_parser.py`, create the function `load_configs_from_directory(dir_path: str) -> dict`.
    *   It will take a directory path as input (e.g., `scraper_configs`).
    *   It will scan the directory for all `.json` files.
    *   It will loop through each file, read its JSON content, and build a dictionary where the key is the filename without the `.json` extension (e.g., `"69shu.com"`) and the value is the parsed JSON object from that file.
    *   It should include error handling for an invalid directory or non-JSON files.
    *   It will return the master dictionary containing all website configurations.

3.  **Implement Domain Matcher**: In `generic_parser.py`, create the function `get_config_for_url(url: str, configs: dict) -> dict | None`.
    *   This function will extract the domain (`netloc`) from the given `url`.
    *   It will first try to find a direct match for the `netloc` in the `configs` dictionary.
    *   If no direct match is found, it will remove a leading `www.` from the `netloc` and try matching again (e.g., `www.69shu.com` becomes `69shu.com`).
    *   It returns the configuration object if found, otherwise `None`.

4.  **Implement Core HTML Parser**: In `generic_parser.py`, create the main parsing function `parse_html(html_content: str, config: dict, current_url: str) -> dict`.
    *   This function will contain all the `BeautifulSoup` logic.
    *   It will systematically use the rules from the `config` object to find and clean the `chapter_title`, `chapter_number`, `next_chapter_url`, and the main `content`.
    *   It will return a dictionary with the cleanly extracted data. This is the most complex function in this file.

## Step 3: Refactor the Main Scraper (`parse_chapter.py`)

This step connects the main application logic to the new generic parser.

1.  **Isolate Old Logic (Optional but Recommended)**: Before deleting, you can rename `parse_chapter.py` to `_parse_chapter_legacy.py` and create a fresh `parse_chapter.py` to avoid confusion.

2.  **Setup New `parse_chapter.py`**:
    *   Import `generic_parser`.
    *   In the `main` function (or equivalent starting point), call `generic_parser.load_configs_from_directory('scraper_configs/')` **once** at the very beginning to get the `all_configs` dictionary.

3.  **Integrate Parser into Scraping Loop**:
    *   Inside the `while` loop that processes chapters:
        a. Get the configuration for the current URL by calling `generic_parser.get_config_for_url(current_url, all_configs)`.
        b. **Add the critical check**: If the config is `None`, print the "Unsupported Website" error message and exit gracefully.
        c. Replace all the old `backend.extract_*` calls with a single call to `generic_parser.parse_html(html, site_config, current_url)`.
        d. Adapt the rest of the loop to use the data from the dictionary returned by `parse_html`.

## Step 4: Final Cleanup and Testing

1.  **Delete `extraction_backends.py`**: With the refactoring complete, this file is now obsolete and can be safely deleted.

2.  **Comprehensive Testing**:
    *   **Test 1 (69shu)**: Run a scrape for a `69shu.com` novel. Verify the output is correct.
    *   **Test 2 (1qxs)**: Run a scrape for a `1qxs.com` novel. Verify the output is correct.
    *   **Test 3 (Unsupported Site)**: Run a scrape for a random, unsupported URL (e.g., `https://www.wikipedia.org`). Verify the tool exits with the proper error message.
    *   **Test 4 (Invalid Config)**: Temporarily introduce a syntax error into one of the JSON config files and run a scrape for that site. Verify that an informative error is shown. 