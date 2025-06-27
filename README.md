# Novel Translation Pipeline

A complete Python-based pipeline for scraping, translating, and converting Chinese novels into EPUB format. This project automates the entire workflow from web scraping to final EPUB generation using a unified command-line interface.

## 🚀 Features

- **Unified Tool Interface**: A single, intuitive `tool.py` for all operations.
- **MongoDB Progress Tracking**: All scraping and translation progress is stored in a MongoDB database, eliminating local progress files and enabling robust, centralized state management.
- **Dynamic API Key Management**: Configure all your API keys in a single `secrets.json` file.
- **Automatic Provider Fallback**: If one API key fails (rate limit, error), the tool automatically tries the next one.
- **Multi-Website Support**: Scrape chapters from 69shu.com, 1qxs.com, and their variants.
- **Resilient Scraping & Translation**: Resume scraping or translation by simply providing the novel's title.
- **Dynamic Chapter Discovery**: The translator automatically detects and processes new `RAW` chapters as you add them ("hot-reloading").
- **Comprehensive Novel Statistics**: A dedicated `info` command to get a detailed progress report.
- **Parallel Processing**: Multi-threaded translation for maximum speed.
- **EPUB Generation**: Convert translated chapters into a professional EPUB format.

## 🌐 Supported Extraction Backends

The scraper supports multiple Chinese novel websites through specialized extraction backends:

### EB69Shu Backend
- **69shu.com** and variants (69shu, shu69, 69shuba)
- Handles standard chapter navigation and content extraction
- Supports both numbered chapters and traditional Chinese chapter formats

### EB1QXS Backend  
- **1qxs.com** (一七小说)
- Handles multi-part chapters (automatically combines parts into single chapter files)
- Specialized URL pattern recognition for chapter/part structure

**Note**: The system automatically detects which backend to use based on the URL domain.

## 📋 Prerequisites

- Python 3.8 or higher
- Pandoc (for EPUB conversion)
- A running MongoDB instance.
- API keys for one or more translation services (e.g., OpenRouter, Chutes).

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Pandoc**:
    -   **Ubuntu/Debian**: `sudo apt-get install pandoc`
    -   **macOS**: `brew install pandoc`
    -   **Windows**: Download from [pandoc.org](https://pandoc.org/installing.html)

4.  **Configure your API keys**:
    -   Copy the example secrets file:
        ```bash
        cp secrets.example.json secrets.json
        ```
    -   Open `secrets.json` and add your API keys. You can add multiple keys from different providers. The tool will try them in order.

        ```json
        {
          "api_keys": [
            {
              "name": "Chutes Primary",
              "provider": "chutes",
              "key": "YOUR_CHUTES_API_KEY_HERE"
            },
            {
              "name": "OpenRouter Free Tier",
              "provider": "openrouter",
              "key": "YOUR_OPENROUTER_API_KEY_HERE"
            }
          ]
        }
        ```
    - The `secrets.json` file is included in `.gitignore`, so your keys will not be committed.

5.  **Configure your Environment**:
    -   This project uses a `.env` file to manage database credentials.
    -   Copy the example file: `cp .env.example .env`
    -   Edit the `.env` file with your MongoDB connection details.

## 🎯 Quick Start

The unified `tool.py` provides five main commands for the complete workflow:

```bash
# Show help and examples
python tool.py

# Show help for a specific command
python tool.py scrape --help
python tool.py translate --help
python tool.py convert --help
python tool.py validate --help
python tool.py info --help
python tool.py list --help
```

## 📚 Complete Workflow Example

This example shows how to scrape the first 50 chapters of a novel, check the progress, translate them, and finally convert them into an EPUB.

```bash
# Step 1: Validate your API keys in secrets.json (optional, but recommended)
# Test only the first key for a quick check
python tool.py validate

# Or, test all keys to see which ones are working
python tool.py validate --all

# Step 2: Start scraping a new novel
python tool.py scrape --novel-title "My Awesome Novel" --start-url "https://www.69shu.com/book/123.htm" -m 50

# Step 3 (can be run in a separate terminal while scraping):
# Start translating by title. It will automatically find new chapters as they are scraped.
python tool.py translate -n "My Awesome Novel" -w 4

# Step 4: Check the progress at any time
# The info command still operates on the folder path
python tool.py info -d "./Novels/My_Awesome_Novel"

# You can also list all novels in the database at any time
python tool.py list

# Step 5: If scraping was interrupted, resume it by providing the title
python tool.py scrape --novel-title "My Awesome Novel" -m 50

# Step 6: Once everything is translated, create the EPUB
python tool.py convert -f "./Novels/My_Awesome_Novel/My_Awesome_Novel-English" \
    -o "My_Awesome_Novel.epub" \
    -t "My Awesome Novel" \
    -a "The Author"
```

## 🔧 Detailed Command Usage

### 1. Validate (`validate`)
Tests your API keys configured in `secrets.json`.

```bash
# Quick test using the first key
python tool.py validate

# Test all keys
python tool.py validate --all
```
-   **What it checks**:
    -   `secrets.json` exists and is formatted correctly.
    -   Performs a simple API call to test connectivity and authentication for one or all keys.

### 2. Scrape (`scrape`)
Scrapes novel chapters from supported websites. Progress is tracked in MongoDB.

```bash
# Start a new scrape for a novel not yet in the database
python tool.py scrape --novel-title "TITLE" --start-url "URL"

# Resume scraping for a novel already in the database
python tool.py scrape --novel-title "TITLE"
```
-   `--novel-title`: The title of the novel. This is used to uniquely identify the novel in the database for both new scrapes and resuming.
-   `--start-url`: The starting URL for the scrape. This is **required** for new novels but optional when resuming.
-   `-m, --max-chapters`: The maximum number of chapters to scrape in this session (default: 1000).
-   `-o, --output-path`: Custom base directory for output (default: `./Novels`).

### 3. Info (`info`)
Displays detailed statistics about a novel's progress by inspecting its folder.

```bash
python tool.py info -d "FOLDER_PATH"
```
-   `-d, --novel-dir`: The base directory of the novel.
-   **What it shows**:
    -   Counts of raw and translated chapter files.
    -   **Note**: With the new MongoDB tracking, this command provides a file-system-level view. For precise progress, checking the database is recommended.

### 4. List (`list`)
Lists all novels currently tracked in the database.

```bash
python tool.py list
```
- This command provides a quick, numbered list of all novels, making it easy to see what's in your collection and get the correct titles for other commands.

### 5. Translate (`translate`)
Translates raw chapters into English. Progress is tracked in MongoDB.

```bash
# Start or resume translating a novel by its title
python tool.py translate -n "NOVEL_TITLE" [-r] [-w WORKERS]
```
-   **Dynamic Discovery**: This command runs continuously, watching for new raw chapters and translating them as they appear. You can run this at the same time as the scraper.
-   `-n, --novel-title`: The title of the novel as it exists in the database.
-   `-w, --workers`: Number of parallel threads to use for translation (default: 1).
-   `-r, --retry-failed`: In this mode, only chapters that have previously failed will be retried.
-   `--skip-validation`: Skips the initial API key validation.

### 6. Convert (`convert`)
Converts a folder of translated markdown files into a single EPUB file.

```bash
python tool.py convert -f "FOLDER_PATH" -o "OUTPUT.epub"
```
-   `-f, --folder-path`: The folder containing the translated `-English` markdown files.
-   `-o, --output-name`: The desired filename for the final EPUB.
-   `-t, --title`: The title of the book for the EPUB metadata.
-   `-a, --author`: The author's name for the EPUB metadata.

## 📁 Project Structure

After running the complete workflow:

```
project-root/
├── tool.py                        # Unified command-line interface
├── src/                           # Source code modules
│   ├── scraping/
│   │   ├── parse_chapter.py       # Web scraping logic
│   │   └── extraction_backends.py # Website-specific extractors
│   ├── translation/
│   │   ├── translator.py          # Translation logic
│   │   └── openrouter.py         # API integration
│   └── conversion/
│       ├── epub_converter.py      # EPUB generation
│       └── merge_chapters.py      # Chapter merging utilities
├── Novels/                        # Output directory
│   └── Novel_Title/
│       ├── Novel_Title-Raws/      # Original Chinese chapters
│       │   ├── Chapter_001.md
│       │   ├── Chapter_002.md
│       │   └── ...
│       ├── Novel_Title-English/   # Translated English chapters
│       │   ├── Chapter_001.md
│       │   ├── Chapter_002.md
│       │   └── ...
├── secrets.json                   # Your secret API keys (gitignored)
├── secrets.example.json           # Example API key file
├── .env                           # Your environment variables (gitignored)
├── .env.example                   # Example environment file
└── scripts/                       # Utility scripts
    └── *.lua                      # Pandoc filters
```

## 🔧 Configuration

### API Keys (`secrets.json`)
All API configuration is managed in the `secrets.json` file. This allows for storing multiple keys and enables the automatic fallback feature.

1.  **Create `secrets.json`**: If it doesn't exist, copy the example file:
    ```bash
    cp secrets.example.json secrets.json
    ```
2.  **Add Your Keys**: Edit `secrets.json` to include your API keys. You can specify a custom name for each key, which will be used in the logs.

    ```json
    {
      "api_keys": [
        {
          "name": "Chutes Primary",
          "provider": "chutes",
          "key": "sk-your-chutes-key"
        },
        {
          "name": "OpenRouter Fallback",
          "provider": "openrouter",
          "key": "sk-or-your-openrouter-key"
        }
      ]
    }
    ```

### API Validation
The `validate` command is the best way to ensure your keys are configured correctly before starting a large job.

```bash
# Test the first key in the list
python tool.py validate

# Test all keys in secrets.json
python tool.py validate --all
```

### Rate Limiting & Resumption
-   **Rate Limiting**: Includes built-in delays to avoid being blocked.
-   **Resumption**: If a scrape is interrupted, you can easily resume it by running the `scrape` command again with the same `--novel-title`. The tool will automatically pick up where it left off based on the progress in MongoDB.

### Translation
-   **API Key Fallback**: If an API call fails with one key (e.g., rate limit, server error), the system automatically retries the request with the next key in `secrets.json`.
-   **Failed Chapter Tracking**: Failed attempts are tracked atomically in the `translation_progress` collection in MongoDB.
-   **Retry Failed Only**: You can run `translate -n "NOVEL_TITLE" -r` to specifically re-process only the chapters that failed previously.
-   **Dynamic Discovery**: The translator runs in a loop, so if it stops for any reason, you can simply restart it with the same `translate -n "NOVEL_TITLE"` command, and it will find any remaining untranslated chapters.

## 🚨 Error Handling & Recovery

The pipeline is designed for resilience and easy recovery from common issues.

### Scraping
-   **SSL Issues**: Automatically bypasses SSL verification for problematic sites.
-   **Rate Limiting**: Includes built-in delays to avoid being blocked.
-   **Resumption**: If a scrape is interrupted, you can easily resume it by running the `scrape` command again with the same `--novel-title`. The tool will automatically pick up where it left off based on the progress in MongoDB.

### Translation
-   **API Key Fallback**: If an API call fails with one key (e.g., rate limit, server error), the system automatically retries the request with the next key in `secrets.json`.
-   **Failed Chapter Tracking**: Failed attempts are tracked atomically in the `translation_progress` collection in MongoDB.
-   **Retry Failed Only**: You can run `translate -n "NOVEL_TITLE" -r` to specifically re-process only the chapters that failed previously.
-   **Dynamic Discovery**: The translator runs in a loop, so if it stops for any reason, you can simply restart it with the same `translate -n "NOVEL_TITLE"` command, and it will find any remaining untranslated chapters.

## 📖 Advanced Usage

### Resuming Operations
With the new MongoDB backend, resuming is the default behavior. Simply run the same command you used to start the process.

-   **Scraping**: Resume an interrupted scrape by providing the novel's title.
    ```bash
    python tool.py scrape --novel-title "My Awesome Novel"
    ```
-   **Translation**: Translation is a dynamic process. Simply run the command again, and it will pick up any untranslated chapters based on the database record. To retry only failed chapters, use the `-r` flag.
    ```bash
    # Continue translating any new/pending chapters
    python tool.py translate -n "My Awesome Novel"

    # Specifically retry chapters that failed before
    python tool.py translate -n "My Awesome Novel" -r
    ```

### Parallel Processing
Use the `-w` or `--workers` flag with the `translate` command to speed up translation.

```bash
# Use 4 worker threads for faster translation
python tool.py translate -n "My Awesome Novel" -w 4
```
**Note**: Be mindful of your API provider's rate limits. Using too many workers can lead to keys being temporarily blocked. The automatic fallback helps, but setting a reasonable number of workers is best.

## ☕ Support the Project

If this project has been helpful to you, consider supporting its development:

[![Buy me a coffee](https://img.shields.io/badge/☕-Buy%20me%20a%20coffee-orange?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://coff.ee/raghavendragaleppa)

Your support helps maintain and improve this open-source novel translation pipeline. Thank you! 🙏
