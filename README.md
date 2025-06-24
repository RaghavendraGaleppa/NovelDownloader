# Novel Translation Pipeline

A complete Python-based pipeline for scraping, translating, and converting Chinese novels into EPUB format. This project automates the entire workflow from web scraping to final EPUB generation using a unified command-line interface.

## 🚀 Features

- **Unified Tool Interface**: A single, intuitive `tool.py` for all operations.
- **Dynamic API Key Management**: Configure all your API keys in a single `secrets.json` file.
- **Automatic Provider Fallback**: If one API key fails (rate limit, error), the tool automatically tries the next one.
- **Multi-Website Support**: Scrape chapters from 69shu.com, 1qxs.com, and their variants.
- **Resilient Scraping & Translation**: Resume scraping or translation from where you left off.
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
```

## 📚 Complete Workflow Example

This example shows how to scrape the first 50 chapters of a novel, check the progress, translate them, and finally convert them into an EPUB.

```bash
# Step 1: Validate your API keys in secrets.json (optional, but recommended)
# Test only the first key for a quick check
python tool.py validate

# Or, test all keys to see which ones are working
python tool.py validate --all

# Step 2: Start scraping the first 50 chapters
python tool.py scrape -n "https://www.69shu.com/book/123.htm" "My Awesome Novel" -m 50

# Step 3 (can be run in a separate terminal while scraping):
# Start translating. It will automatically find new chapters as they are scraped.
python tool.py translate -n "./Novels/My_Awesome_Novel" -w 4

# Step 4: Check the progress at any time
python tool.py info -d "./Novels/My_Awesome_Novel"

# Step 5: If scraping was interrupted, resume it
python tool.py scrape -r "./Novels/My_Awesome_Novel" -m 50

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
python tool.py validate -a
```
-   **What it checks**:
    -   `secrets.json` exists and is formatted correctly.
    -   Performs a simple API call to test connectivity and authentication for one or all keys.

### 2. Scrape (`scrape`)
Scrapes novel chapters from supported websites.

```bash
# Start a new scrape
python tool.py scrape -n "URL" "TITLE"

# Resume a previous scrape from a folder
python tool.py scrape -r "FOLDER_PATH"
```
-   `-n, --new-scrape`: Starts a new scrape. Requires the novel's start URL and a title.
-   `-r, --resume`: Resumes a scrape from a novel folder. Automatically finds the progress file.
-   `-m, --max-chapters`: The maximum number of chapters to scrape in this session (default: 1000).
-   `-o, --output-path`: Custom base directory for output (default: `./Novels`).

### 3. Info (`info`)
Displays detailed statistics about a novel's progress.

```bash
python tool.py info -d "FOLDER_PATH"
```
-   `-d, --novel-dir`: The base directory of the novel.
-   **What it shows**:
    -   Counts of raw and translated chapter files.
    -   Detailed progress from the translation log (translated, failed, and untranslated counts).

### 4. Translate (`translate`)
Translates raw chapters into English using the keys from `secrets.json`.

```bash
python tool.py translate -n "FOLDER_PATH" [-r] [-w WORKERS]
```
-   **Dynamic Discovery**: This command runs continuously, watching for new raw chapters and translating them as they appear. You can run this at the same time as the scraper.
-   `-n, --novel-base-dir`: The base directory of the novel (must contain a `-Raws` subdirectory).
-   `-w, --workers`: Number of parallel threads to use for translation (default: 1).
-   `-r, --retry-failed`: In this mode, only chapters that have previously failed will be retried.
-   `--skip-validation`: Skips the initial API key validation.

### 5. Convert (`convert`)
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
│       ├── Novel_Title_progress.json              # Scraping progress
│       └── Novel_Title_translation_progress.json  # Translation progress
└── scripts/                       # Utility scripts
    └── *.lua                      # Pandoc filters
```

## 🔧 Configuration

### Environment Variables
```bash
# Required for translation - see docs/api-keys.md for setup instructions
export API_KEY="your-api-key"

# Optional: Custom output directory
export NOVELS_DIR="/path/to/novels"
```

**📖 For detailed API key setup instructions, see [docs/api-keys.md](docs/api-keys.md)**

### API Validation
The translation system automatically validates your API configuration before starting any translation work:

#### Validation Checks
1. **API Key Verification**: Ensures your API key is set and not empty
2. **Provider Configuration**: Validates the specified API provider exists and is configured
3. **Connectivity Test**: Performs a simple test call to verify the service is accessible
4. **Clear Error Messages**: Provides specific guidance on how to fix configuration issues

#### Common Validation Errors
- **API key not set**: See [API Key Setup Guide](docs/api-keys.md) for detailed setup instructions
- **Empty API key**: Check that your API key value is correct
- **Unknown provider**: Use `chutes` or `openrouter` as provider names
- **Connectivity issues**: Check internet connection and API service status

### API Providers
Configure in `src/translation/openrouter.py`:
- **Chutes API**: Default provider
- **OpenRouter API**: Alternative provider
- Add custom providers as needed

**📖 For provider-specific setup instructions, see [docs/api-keys.md](docs/api-keys.md)**

## 🚨 Error Handling & Recovery

The pipeline includes comprehensive error handling:

### Scraping
- **SSL Issues**: Automatic SSL bypass for problematic sites
- **Rate Limiting**: Built-in delays between requests
- **Progress Tracking**: Resume from last successful chapter
- **Network Errors**: Automatic retries with exponential backoff

### Translation
- **API Failures**: Tracks failed attempts per chapter
- **Rate Limiting**: Configurable delays between API calls
- **Retry Logic**: Retry-only mode for failed translations
- **Multi-threading**: Parallel processing with error isolation
- **API Validation**: Automatic validation of API keys and connectivity before starting translation

### EPUB Conversion
- **File Validation**: Checks for required input files
- **Pandoc Errors**: Clear error messages for missing dependencies
- **Natural Sorting**: Correct chapter ordering (1, 2, 10 vs 1, 10, 2)

## 📖 Advanced Usage

### Resume Operations
All operations support resuming from progress files:

```bash
# Scraping automatically resumes if progress file exists
python tool.py scrape -n "https://example.com" "Novel Title"

# Translation tracks progress automatically
python tool.py translate -n "./Novels/Novel_Title"

# Retry only failed translations
python tool.py translate -n "./Novels/Novel_Title" -r
```

### Custom Output Paths
```bash
# Custom scraping output
python tool.py scrape -n "URL" "Title" -o "/custom/path"

# Custom EPUB output
python tool.py convert -f "./input/folder" -o "/custom/path/novel.epub"
```

### Parallel Processing
```bash
# Use multiple workers for faster translation
python tool.py translate -n "./Novels/Novel_Title" -w 4

# Balance between speed and API rate limits
python tool.py translate -n "./Novels/Novel_Title" -w 2 -p openrouter
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **API Key Errors**: See [API Key Setup Guide](docs/api-keys.md) for detailed setup instructions
3. **Pandoc Not Found**: Install Pandoc system-wide for EPUB conversion
4. **SSL Errors**: The scraper automatically handles SSL issues
5. **Rate Limiting**: Increase delays or reduce worker count

### Debug Mode
```bash
# Enable verbose output (if implemented)
python tool.py scrape -n "URL" "Title" --verbose

# Check progress files for debugging
cat "./Novels/Novel_Title/Novel_Title_progress.json"
```

## 💡 Tips & Best Practices

1. **Start Small**: Test with `-m 10` for first attempts
2. **Monitor Progress**: Check progress files for status
3. **API Limits**: Respect rate limits, use appropriate delays
4. **Backup**: Keep backups of progress files for long-running operations
5. **Resource Usage**: Balance worker count with system resources

## ⚠️ Disclaimer

- Respect website terms of service when scraping
- Use translation APIs responsibly within usage limits
- Ensure you have rights to process the content
- This tool is for educational and personal use

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review console output for error messages
3. Examine progress files for operation status
4. Ensure all dependencies are properly installed

## ☕ Support the Project

If this project has been helpful to you, consider supporting its development:

[![Buy me a coffee](https://img.shields.io/badge/☕-Buy%20me%20a%20coffee-orange?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://coff.ee/raghavendragaleppa)

Your support helps maintain and improve this open-source novel translation pipeline. Thank you! 🙏
