# Novel Translation Pipeline

A complete Python-based pipeline for scraping, translating, and converting Chinese novels into EPUB format. This project automates the entire workflow from web scraping to final EPUB generation using a unified command-line interface.

## 🚀 Features

- **Unified Tool Interface**: Single `tool.py` command for all operations
- **Multi-Website Support**: Extract chapters from 69shu.com, 1qxs.com, and variants
- **Progress Tracking**: Resume scraping and translation from where you left off
- **AI Translation**: Translate Chinese text to English using multiple AI providers
- **EPUB Generation**: Convert translated chapters into professional EPUB format
- **Parallel Processing**: Multi-threaded translation for faster processing
- **Robust Error Handling**: Automatic retries and comprehensive error recovery

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
- API key for translation service (OpenRouter, Chutes, etc.)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Pandoc**:
   - **Ubuntu/Debian**: `sudo apt-get install pandoc`
   - **macOS**: `brew install pandoc`
   - **Windows**: Download from [pandoc.org](https://pandoc.org/installing.html)

4. **Set up API key** (for translation):
   ```bash
   export API_KEY="your-api-key"
   ```

## 🎯 Quick Start

The unified `tool.py` provides four main commands for the complete workflow:

```bash
# Show help and examples
python tool.py

# Individual command help
python tool.py validate --help
python tool.py scrape --help
python tool.py translate --help
python tool.py convert --help
```

## 📚 Complete Workflow

### Option 1: Step-by-Step Workflow

```bash
# Step 0: Validate API configuration (recommended)
python tool.py validate -p chutes

# Step 1: Scrape novel chapters
python tool.py scrape -n "https://www.69shu.com/book/123.htm" "Cultivation Master" -m 100

# Step 2: Translate chapters to English
python tool.py translate -n "./Novels/Cultivation_Master" -p chutes -w 2

# Step 3: Convert to EPUB
python tool.py convert -f "./Novels/Cultivation_Master/Cultivation_Master-English" -o "cultivation_master.epub" -t "Cultivation Master" -a "Unknown Author"
```

### Option 2: One-Line Examples

```bash
# Validate API before starting
python tool.py validate -p openrouter

# Quick scraping (first 10 chapters)
python tool.py scrape -n "https://www.1qxs.com/novel/456" "Test Novel" -m 10

# Translate with multiple workers
python tool.py translate -n "./Novels/Test_Novel" -p openrouter -w 3

# Create EPUB with custom metadata
python tool.py convert -f "./Novels/Test_Novel/Test_Novel-English" -o "test_novel.epub" -t "Test Novel" -a "Great Author"
```

## 🔧 Detailed Command Usage

### 0. Validate Command
Test API configuration and connectivity before starting translation work.

```bash
python tool.py validate [-p PROVIDER]

# Examples:
python tool.py validate  # Test default (chutes) provider
python tool.py validate -p openrouter  # Test OpenRouter provider
```

**Options:**
- `-p, --provider`: API provider to validate (default: chutes)

**What it checks:**
- API key environment variable is set and not empty
- Provider configuration exists and is valid
- API connectivity with a simple test call
- Provides clear error messages and solutions

### 1. Scrape Command
Extract novel chapters from supported websites.

**Supported Sites:**
- 69shu.com variants (69shu, shu69, 69shuba)
- 1qxs.com

```bash
python tool.py scrape -n "URL" "TITLE" [-m MAX_CHAPTERS] [-o OUTPUT_PATH]

# Examples:
python tool.py scrape -n "https://www.69shu.com/book/123.htm" "My Novel"
python tool.py scrape -n "https://www.1qxs.com/novel/456" "Another Novel" -m 50 -o "./CustomPath"
```

**Options:**
- `-n, --new-scrape`: Start new scrape (requires URL and title)
- `-m, --max-chapters`: Maximum chapters per session (default: 1000)
- `-o, --output-path`: Custom output directory (default: ./Novels/novel_title)

### 2. Translate Command
Translate scraped chapters using AI APIs.

**Supported Providers:**
- `chutes` (default)
- `openrouter`

```bash
python tool.py translate -n NOVEL_DIR [-r] [-p PROVIDER] [-w WORKERS]

# Examples:
python tool.py translate -n "./Novels/My_Novel"
python tool.py translate -n "./Novels/My_Novel" -p openrouter -w 3
python tool.py translate -n "./Novels/My_Novel" -r  # Retry failed only
python tool.py translate -n "./Novels/My_Novel" --skip-validation  # Skip API validation (not recommended)
```

**Options:**
- `-n, --novel-base-dir`: Novel directory containing Raws subdirectory
- `-r, --retry-failed`: Only retry previously failed translations
- `-p, --provider`: API provider (default: chutes)
- `-w, --workers`: Number of worker threads (default: 1)
- `--skip-validation`: Skip API validation before starting (not recommended)

### 3. Convert Command
Convert translated markdown files to EPUB format.

```bash
python tool.py convert -f FOLDER_PATH -o OUTPUT.epub [-t TITLE] [-a AUTHOR]

# Examples:
python tool.py convert -f "./Novels/My_Novel/My_Novel-English" -o "my_novel.epub"
python tool.py convert -f "./Novels/My_Novel/My_Novel-English" -o "my_novel.epub" -t "My Awesome Novel" -a "Great Author"
```

**Options:**
- `-f, --folder-path`: Path to folder with translated markdown files
- `-o, --output-name`: Output EPUB filename
- `-t, --title`: Book title for metadata (default: "My Awesome Book")
- `-a, --author`: Author name for metadata (default: "Unknown Author")

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
# Required for translation
export API_KEY="your-api-key"

# Optional: Custom output directory
export NOVELS_DIR="/path/to/novels"
```

### API Validation
The translation system automatically validates your API configuration before starting any translation work:

#### Validation Checks
1. **API Key Verification**: Ensures your API key is set and not empty
2. **Provider Configuration**: Validates the specified API provider exists and is configured
3. **Connectivity Test**: Performs a simple API call to verify the service is accessible
4. **Clear Error Messages**: Provides specific guidance on how to fix configuration issues

#### Common Validation Errors
- **API key not set**: `export API_KEY="your-api-key-here"`
- **Empty API key**: Check that your API key value is correct
- **Unknown provider**: Use `chutes` or `openrouter` as provider names
- **Connectivity issues**: Check internet connection and API service status

### API Providers
Configure in `src/translation/openrouter.py`:
- **Chutes API**: Default provider
- **OpenRouter API**: Alternative provider
- Add custom providers as needed

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
2. **API Key Errors**: Set `API_KEY` environment variable
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

## CONTACT
