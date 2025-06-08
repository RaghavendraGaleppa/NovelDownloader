# Novel Processing Tool Usage Guide

The `tool.py` is a unified command-line interface that combines all novel processing functionality into a single tool.

## Quick Start

```bash
# Show help and examples
python tool.py

# Show help for specific commands
python tool.py scrape --help
python tool.py translate --help
python tool.py convert --help
```

## Commands

### 1. Scrape (`scrape`)
Download novel chapters from supported websites.

**Supported Sites:**
- 69shu.com variants (69shu, shu69, 69shuba)
- 1qxs.com

**Usage:**
```bash
python tool.py scrape -n "URL" "TITLE" [-m MAX_CHAPTERS] [-o OUTPUT_PATH]
```

**Examples:**
```bash
# Basic scraping
python tool.py scrape -n "https://www.69shu.com/book/123.htm" "My Novel"

# Limit chapters and custom output
python tool.py scrape -n "https://www.1qxs.com/novel/456" "Another Novel" -m 50 -o "./CustomPath"
```

### 2. Translate (`translate`)
Translate scraped chapters using AI APIs.

**Supported Providers:**
- `chutes` (default)
- `openrouter`

**Usage:**
```bash
python tool.py translate -n NOVEL_DIR [-r] [-p PROVIDER] [-w WORKERS]
```

**Examples:**
```bash
# Basic translation
python tool.py translate -n "./Novels/My_Novel"

# Use different provider with multiple workers
python tool.py translate -n "./Novels/My_Novel" -p openrouter -w 3

# Retry only failed chapters
python tool.py translate -n "./Novels/My_Novel" -r
```

### 3. Convert (`convert`)
Convert translated markdown files to EPUB format.

**Usage:**
```bash
python tool.py convert -f FOLDER_PATH -o OUTPUT.epub [-t TITLE] [-a AUTHOR]
```

**Examples:**
```bash
# Basic conversion
python tool.py convert -f "./Novels/My_Novel/My_Novel-English" -o "my_novel.epub"

# With custom metadata
python tool.py convert -f "./Novels/My_Novel/My_Novel-English" -o "my_novel.epub" -t "My Awesome Novel" -a "Great Author"
```

## Complete Workflow Example

```bash
# Step 1: Scrape chapters
python tool.py scrape -n "https://www.69shu.com/book/123.htm" "Cultivation Master" -m 100

# Step 2: Translate chapters
python tool.py translate -n "./Novels/Cultivation_Master" -p chutes -w 2

# Step 3: Convert to EPUB
python tool.py convert -f "./Novels/Cultivation_Master/Cultivation_Master-English" -o "cultivation_master.epub" -t "Cultivation Master" -a "Unknown Author"
```

## File Structure

After running the complete workflow, you'll have:

```
Novels/
└── Cultivation_Master/
    ├── Cultivation_Master-Raws/          # Original Chinese chapters
    │   ├── Chapter_001.md
    │   ├── Chapter_002.md
    │   └── ...
    ├── Cultivation_Master-English/       # Translated English chapters
    │   ├── Chapter_001.md
    │   ├── Chapter_002.md
    │   └── ...
    ├── Cultivation_Master_progress.json  # Scraping progress
    └── Cultivation_Master_translation_progress.json  # Translation progress
```

## Environment Setup

Make sure you have the required API key set:

```bash
# For Chutes API
export API_KEY="your_chutes_api_key"

# For OpenRouter API  
export API_KEY="your_openrouter_api_key"
```

## Features

- **Multi-website support**: Automatically detects and uses the correct extraction backend
- **Progress tracking**: Resumes from where you left off
- **Multi-threading**: Parallel translation processing
- **Error handling**: Robust error handling and retry mechanisms
- **Rich console output**: Beautiful colored output with progress indicators 