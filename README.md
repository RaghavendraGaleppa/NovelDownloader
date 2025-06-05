# Novel Translation Pipeline

A complete Python-based pipeline for scraping, translating, and converting Chinese novels into EPUB format. This project automates the entire workflow from web scraping to final EPUB generation.

## 🚀 Features

- **Web Scraping**: Extract novel chapters from Chinese novel websites
- **Progress Tracking**: Resume scraping and translation from where you left off
- **AI Translation**: Translate Chinese text to English using OpenRouter API
- **EPUB Generation**: Convert translated chapters into professional EPUB format
- **Batch Processing**: Handle multiple chapters efficiently with retry logic
- **Custom Output Paths**: Flexible directory structure for organized output

## 📋 Prerequisites

- Python 3.8 or higher
- Pandoc (for EPUB conversion)
- OpenRouter API key (for translation)

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
   export API_KEY="your-openrouter-api-key"
   ```

## 📚 Usage Workflow

Follow these steps in order to complete the full pipeline:

### Step 1: Parse/Scrape Chapters

Extract novel chapters from websites using the parser:

```bash
# Start a new scrape
python parse_chapter.py -n "https://example.com/chapter1" "Novel Title"

# Resume from progress file
python parse_chapter.py -p "Novel_Title/Novel_Title_progress.json"

# Limit chapters per session
python parse_chapter.py -n "https://example.com/chapter1" "Novel Title" -m 50

# Use custom output directory
python parse_chapter.py -n "https://example.com/chapter1" "Novel Title" -o "/path/to/output"
```

**Output**: Creates `Novel_Title/Raws/` directory with `Chapter_XX.md` files

#### Parser Arguments:
- `-n, --new-scrape`: Start new scrape (requires URL and title)
- `-p, --progress-file`: Resume from progress file
- `-m, --max-chapters`: Maximum chapters per session (default: 1000)
- `-o, --output-path`: Custom output directory path

### Step 2: Translate Chapters

Translate the scraped chapters from Chinese to English:

```bash
# Translate all chapters in a novel directory
python translator.py -n "Novel_Title" -p "openrouter"

# Use different API provider
python translator.py -n "Novel_Title" -p "chutes"

# Retry only failed translations
python translator.py -n "Novel_Title" -p "openrouter" -r
```

**Output**: Creates `Novel_Title/TranslatedRaws/` directory with translated `Chapter_XX.md` files

#### Translator Arguments:
- `-n, --novel-base-dir`: Novel directory containing 'Raws' folder
- `-p, --provider`: API provider (default: "chutes")
- `-r, --retry-failed`: Only retry previously failed translations

#### Supported API Providers:
- `openrouter`: OpenRouter API
- `chutes`: Chutes API
- Additional providers can be configured in `openrouter.py`

### Step 3: Convert to EPUB

Convert translated chapters into a single EPUB file:

```bash
# Basic EPUB conversion
python epub_converter.py -f "Novel_Title/TranslatedRaws" -o "novel.epub"

# With custom metadata
python epub_converter.py -f "Novel_Title/TranslatedRaws" -o "novel.epub" -t "My Novel Title" -a "Author Name"
```

**Output**: Creates `novel.epub` file ready for reading

#### EPUB Converter Arguments:
- `-f, --folder-path`: Path to folder with translated markdown files
- `-o, --output-name`: Output EPUB filename
- `-t, --title`: Book title for metadata (default: "My Awesome Book")
- `-a, --author`: Author name for metadata (default: "Unknown Author")

## 📁 Directory Structure

After running the full pipeline, your directory structure will look like:

```
Novel_Title/
├── Raws/                          # Original scraped chapters
│   ├── Chapter_001.md
│   ├── Chapter_002.md
│   └── ...
├── TranslatedRaws/                # Translated chapters
│   ├── Chapter_001.md
│   ├── Chapter_002.md
│   └── ...
├── Novel_Title_progress.json      # Scraping progress
├── Novel_Title_translation_progress.json  # Translation progress
└── novel.epub                     # Final EPUB (if generated here)
```

## 🔧 Configuration

### Environment Variables
- `API_KEY`: Your OpenRouter API key for translation services

### Translation Providers
Configure additional providers in `openrouter.py`:
- Add provider configurations
- Set API endpoints and authentication
- Customize translation parameters

## 🚨 Error Handling

The pipeline includes robust error handling:

- **Scraping**: Retries failed requests, saves progress
- **Translation**: Tracks failed attempts, supports retry-only mode
- **EPUB**: Validates input files, provides clear error messages

## 📖 Example Complete Workflow

```bash
# 1. Scrape a novel (limit to 10 chapters for testing)
python parse_chapter.py -n "https://example.com/novel/chapter1" "Test Novel" -m 10

# 2. Translate the chapters
python translator.py -n "Test_Novel" -p "openrouter"

# 3. Convert to EPUB
python epub_converter.py -f "Test_Novel/TranslatedRaws" -o "test_novel.epub" -t "Test Novel" -a "Original Author"
```

## 🔍 Troubleshooting

### Common Issues:

1. **Pandoc not found**: Install Pandoc system-wide
2. **API key errors**: Ensure `API_KEY` environment variable is set
3. **Rate limiting**: Translation script includes automatic delays
4. **File not found**: Check directory paths and file permissions

### Logs and Progress:
- Progress files track completion status
- Console output shows detailed processing information
- Failed operations are logged for retry

## ⚠️ Disclaimer

- Respect website terms of service when scraping
- Use translation APIs responsibly
- Ensure you have rights to content being processed 