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
python tool.py validate --help
python tool.py info --help
```

## Commands

### 1. Validate (`validate`)
Tests your API keys configured in `secrets.json`.

**Usage:**
```bash
# Quick test using the first key
python tool.py validate

# Test all keys
python tool.py validate -a
```

### 2. Scrape (`scrape`)
Download novel chapters from supported websites.

**Supported Sites:**
- 69shu.com variants (69shu, shu69, 69shuba)
- 1qxs.com

**Usage:**
```bash
# Start a new scrape
python tool.py scrape -n "URL" "TITLE" [-m MAX_CHAPTERS] [-o OUTPUT_PATH]

# Resume a previous scrape
python tool.py scrape -r "FOLDER_PATH" [-m MAX_CHAPTERS]
```

**Examples:**
```bash
# Basic scraping
python tool.py scrape -n "https://www.69shu.com/book/123.htm" "My Novel"

# Limit chapters and custom output
python tool.py scrape -n "https://www.1qxs.com/novel/456" "Another Novel" -m 50 -o "./CustomPath"
```

### 3. Info (`info`)
Displays statistics about a novel's progress.

**Usage:**
```bash
python tool.py info -d "FOLDER_PATH"
```

### 4. Translate (`translate`)
Translate scraped chapters using the API keys from `secrets.json`. This command runs continuously to translate new chapters as they are added.

**Usage:**
```bash
python tool.py translate -n NOVEL_DIR [-r] [-w WORKERS]
```
-   `-r, --retry-failed`: Only retry previously failed chapters.

### 5. Convert (`convert`)
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
# Step 1: Validate your API keys
python tool.py validate --all

# Step 2: Start scraping chapters
python tool.py scrape -n "https://www.69shu.com/book/123.htm" "Cultivation Master" -m 100

# Step 3: Check the scraping and translation progress
python tool.py info -d "./Novels/Cultivation_Master"

# Step 4: Translate chapters (can be run while scraping)
python tool.py translate -n "./Novels/Cultivation_Master" -w 4

# Step 5: Convert the final translated files to EPUB
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

## API Key Setup (`secrets.json`)

The tool now uses a `secrets.json` file to manage API keys.

1.  **Create the file**: Copy `secrets.example.json` to `secrets.json`.
2.  **Add your keys**: Edit the file to add your API keys. You can add multiple keys. The tool will automatically try the next one if a key fails.

```json
{
  "api_keys": [
    {
      "name": "My Primary Key",
      "provider": "chutes",
      "key": "YOUR_API_KEY_HERE"
    },
    {
      "name": "My Backup Key",
      "provider": "openrouter",
      "key": "ANOTHER_API_KEY_HERE"
    }
  ]
}
```

## Features

- **Dynamic API Fallback**: Automatically cycles through keys in `secrets.json` on failure.
- **Dynamic Chapter Discovery**: Translator "hot-reloads" new chapters as they are scraped.
- **Resume Anywhere**: Resume scraping from a folder path.
- **Progress Tracking**: Use the `info` command to get detailed statistics.
- **Multi-threading**: Parallel translation processing.
- **Rich Console Output**: Beautiful colored output with progress indicators. 