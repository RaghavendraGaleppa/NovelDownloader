#!/usr/bin/env python3
"""
Novel Processing Tool - Unified Command Line Interface

This tool combines scraping, translation, and EPUB conversion functionality
for processing Chinese novels into English EPUB files.

Usage:
    python tool.py scrape --novel-title "TITLE" [--start-url "URL"] [-m MAX_CHAPTERS] [-o OUTPUT_PATH]
    python tool.py translate -n NOVEL_DIR [-r] [-p PROVIDER] [-w WORKERS]
    python tool.py convert -f FOLDER_PATH -o OUTPUT.epub [-t TITLE] [-a AUTHOR]
"""

import argparse
import sys
import os
import json
from rich.console import Console
import sys

# Doing this temporarily since I will migrating to server and no more command line tools will be used
current_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_folder, "src"))

# Import the main functions from our organized modules
from src.scraping.parse_chapter import main as scrape_main
from src.translation.translator import perform_api_validation, translate_novel_by_id
from src.conversion.epub_converter import convert_folder_md_to_epub
from src.main import db_client


def cmd_scrape(args):
    """Handle the scrape subcommand"""
    print("🕷️  Starting novel scraping...")
    
    # The args object from argparse now directly matches what parse_chapter.main expects.
    scrape_main(args)


def cmd_validate(args):
    """Handle the validate subcommand"""
    print("🔧 Starting API validation...")
    
    # Import the validation function
    from src.translation.translator import perform_api_validation
    
    # Perform validation
    if perform_api_validation(test_all_keys=args.all):
        print(f"\n✅ API validation successful!")
        print("Secrets file is valid and connectivity test passed.")
        print("You can now proceed with translation operations.")
    else:
        print(f"\n❌ API validation failed.")
        print("Please fix the issues reported above before attempting translation.")


def cmd_translate(args):
    """Handle the translate subcommand"""
    if not args.novel_title:
        print("❌ Error: You must provide --novel-title.", file=sys.stderr)
        sys.exit(1)

    print(f"🔤 Looking up novel '{args.novel_title}' in the database...")
    novel = db_client.novels.find_one({"novel_name": args.novel_title})

    if not novel:
        print(f"❌ Error: Novel '{args.novel_title}' not found in the database.", file=sys.stderr)
        sys.exit(1)

    novel_id = str(novel["_id"])
    print(f"✅ Found novel with ID: {novel_id}. Starting translation using database records...")

    translate_novel_by_id(
        novel_id=novel_id,
        workers=args.workers,
        skip_validation=args.skip_validation ,
        wait_for_new_chapters=True,
        retry_from_chapter=args.retry_from_chapter
    )


def cmd_convert(args):
    """Handle the convert subcommand"""
    print("📚 Starting EPUB conversion...")
    
    # Call the EPUB conversion function
    convert_folder_md_to_epub(
        folder_path=args.folder_path,
        output_epub_name=args.output_name,
        title=args.title,
        author=args.author
    )


def cmd_info(args):
    """Handle the info subcommand"""
    console = Console()
    
    novel_base_directory = args.novel_base_directory
    
    if not os.path.isdir(novel_base_directory):
        console.print(f"❌ Error: The provided path '{novel_base_directory}' is not a valid directory.", style="red")
        return

    novel_name_from_dir = os.path.basename(os.path.normpath(novel_base_directory))
    
    console.print(f"\n📊 [bold]Novel Statistics for '{novel_name_from_dir}'[/bold]", style="cyan")
    console.print("-" * 60)
    console.print(f"[bold]Novel Directory:[/bold] {os.path.abspath(novel_base_directory)}")

    # --- Raw File Stats ---
    raws_dir = os.path.join(novel_base_directory, f"{novel_name_from_dir}-Raws")
    num_raw_chapters = 0
    if os.path.isdir(raws_dir):
        try:
            raw_files = [f for f in os.listdir(raws_dir) if f.startswith("Chapter_") and f.endswith(".md")]
            num_raw_chapters = len(raw_files)
        except OSError as e:
            console.print(f"Could not read Raws directory: {e}", style="red")
    
    # --- Translated File Stats ---
    translated_raws_dir = os.path.join(novel_base_directory, f"{novel_name_from_dir}-English")
    num_translated_files = 0
    if os.path.isdir(translated_raws_dir):
        try:
            translated_files = [f for f in os.listdir(translated_raws_dir) if f.startswith("Chapter_") and f.endswith(".md")]
            num_translated_files = len(translated_files)
        except OSError as e:
            console.print(f"Could not read English directory: {e}", style="red")

    console.print("\n[bold]--- File System Counts ---[/bold]")
    console.print(f"Raw Chapters:      [bold green]{num_raw_chapters}[/bold green]")
    console.print(f"Translated Files:  [bold blue]{num_translated_files}[/bold blue]")

    # --- Progress File Stats ---
    progress_file_path = os.path.join(novel_base_directory, f"{novel_name_from_dir}_translation_progress.json")
    if os.path.exists(progress_file_path):
        console.print("\n[bold]--- Translation Progress (from progress.json) ---[/bold]")
        try:
            with open(progress_file_path, 'r', encoding='utf-8') as pf:
                progress_data = json.load(pf)
            
            last_provider = progress_data.get("last_used_provider", "N/A")
            translated_in_progress = progress_data.get("translated_files", [])
            failed_in_progress = progress_data.get("failed_translation_attempts", {})
            
            num_translated_progress = len(translated_in_progress)
            num_failed_progress = len(failed_in_progress)
            
            # This is a more accurate count of what's left for the translator
            untranslated_count = num_raw_chapters - num_translated_progress
            
            console.print(f"Last Used Provider: [yellow]{last_provider}[/yellow]")
            console.print(f"✅ Translated Chapters: [bold green]{num_translated_progress}[/bold green]")
            console.print(f"❌ Failed Chapters:     [bold red]{num_failed_progress}[/bold red]")
            
            if failed_in_progress:
                console.print("   [dim]Failed chapters:[/dim]")
                for fname, count in list(failed_in_progress.items())[:5]: # Show first 5
                    console.print(f"   - {fname}: {count} attempts", style="dim yellow")
                if len(failed_in_progress) > 5:
                    console.print("   ...", style="dim yellow")

            console.print(f"🤔 Untranslated:        [bold yellow]{untranslated_count}[/bold yellow] (based on raw files vs progress file)")

        except (json.JSONDecodeError, IOError) as e:
            console.print(f"Error reading progress file: {e}", style="red")
    else:
        console.print("\n[dim]No translation progress file found.[/dim]")

    console.print("-" * 60)


def cmd_list(args):
    """Handle the list subcommand"""
    console = Console()
    console.print("\n📚 [bold]Listing all novels in the database...[/bold]", style="cyan")
    
    novels_collection = db_client["novels"]
    
    try:
        # Fetch all novels, sorting by name for consistency
        novel_docs = list(novels_collection.find({}, {'novel_name': 1}).sort('novel_name', 1))
        
        if not novel_docs:
            console.print("  No novels found in the database.", style="yellow")
            return
            
        console.print("-" * 40)
        for i, doc in enumerate(novel_docs, 1):
            console.print(f"  {i}. {doc['novel_name']}")
        console.print("-" * 40)

    except Exception as e:
        console.print(f"❌ Error fetching novels from database: {e}", style="red")


def main():
    """Main entry point for the unified tool"""
    parser = argparse.ArgumentParser(
        description="Novel Processing Tool - Scrape, Translate, and Convert Chinese novels",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='{scrape,translate,convert,validate,info}'
    )
    
    # ===== SCRAPE SUBCOMMAND =====
    scrape_parser = subparsers.add_parser(
        'scrape',
        help='Scrape novel chapters from websites',
        description='Scrape novel chapters from supported websites. Progress is now tracked in MongoDB.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    scrape_parser.add_argument(
        "-n", '--novel-title',
        required=True,
        help='Title of the novel. Used to identify the novel in the database for new scrapes or resuming.'
    )
    scrape_parser.add_argument(
        "-s", '--start-url',
        help='The starting URL for a scrape. Required only for new novels not yet in the database.'
    )
    
    scrape_parser.add_argument(
        '-m', '--max-chapters',
        type=int,
        default=1000,
        help='Maximum number of chapters to scrape (default: 1000)'
    )
    scrape_parser.add_argument(
        '-o', '--output-path',
        help='Custom output directory path. If not specified, uses Novels/novel_title'
    )
    scrape_parser.add_argument(
        '--use-selenium', 
        action="store_true",
        help="Use Selenium WebDriver instead of CloudScraper for bypassing Cloudflare"
    )
    scrape_parser.set_defaults(func=cmd_scrape)
    
    # ===== VALIDATE SUBCOMMAND =====
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate API configuration and connectivity',
        description='Test API key and provider connectivity without starting translation',
        formatter_class=argparse.RawTextHelpFormatter
    )
    validate_parser.add_argument(
        '-p', '--provider',
        default='chutes',
        help='This argument is now ignored. API providers are determined by secrets.json.'
    )
    validate_parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Validate all keys in secrets.json instead of just the first one.'
    )
    validate_parser.set_defaults(func=cmd_validate)
    
    # ===== TRANSLATE SUBCOMMAND =====
    translate_parser = subparsers.add_parser(
        'translate',
        help='Translate novel chapters using database records',
        description='Translate novel chapters from the raw_chapters collection into English.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    translate_parser.add_argument(
        '-n', '--novel-title',
        required=True,
        help='The title of the novel to translate (must exist in the database).'
    )
    translate_parser.add_argument(
        '-w', '--workers',
        type=int,
        default=1,
        help='Number of parallel worker threads to use for translation (default: 1).'
    )
    translate_parser.add_argument(
        "-sv", "--skip-validation",
        action="store_true",
        default=False,
        help="Skip API validation and use the last used provider."
    )
    translate_parser.add_argument(
        "-r", "--retry-from-chapter",
        type=int,
        help="Retry from a specific chapter number. This will resume the translation from the given chapter number."
    )
    translate_parser.set_defaults(func=cmd_translate)
    
    # ===== CONVERT SUBCOMMAND =====
    convert_parser = subparsers.add_parser(
        'convert',
        help='Convert markdown chapters to EPUB',
        description='Convert a folder of translated markdown files to a single EPUB file',
        formatter_class=argparse.RawTextHelpFormatter
    )
    convert_parser.add_argument(
        '-f', '--folder-path',
        required=True,
        help='Path to the folder containing markdown files'
    )
    convert_parser.add_argument(
        '-o', '--output-name',
        required=True,
        help='Desired name for the output EPUB file (e.g., my_novel.epub)'
    )
    convert_parser.add_argument(
        '-t', '--title',
        default='My Awesome Book',
        help='The title of the book for EPUB metadata (default: My Awesome Book)'
    )
    convert_parser.add_argument(
        '-a', '--author',
        default='Unknown Author',
        help='The author of the book for EPUB metadata (default: Unknown Author)'
    )
    convert_parser.set_defaults(func=cmd_convert)
    
    # ===== INFO SUBCOMMAND =====
    info_parser = subparsers.add_parser(
        'info',
        help='Get statistics for a novel folder',
        description='Display statistics about raw, translated, and failed chapters for a novel.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    info_parser.add_argument(
        '-d', '--novel-dir',
        dest='novel_base_directory',
        required=True,
        help='The base directory of the novel to get stats for.'
    )
    info_parser.set_defaults(func=cmd_info)
    
    # ===== LIST SUBCOMMAND =====
    list_parser = subparsers.add_parser(
        'list',
        help='List all novels currently tracked in the database',
        description='Fetches and displays a numbered list of all novel titles from the database.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    list_parser.set_defaults(func=cmd_list)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle the case where no subcommand is provided
    if not args.command:
        parser.print_help()
        print("\n" + "="*60)
        print("EXAMPLES:")
        print("="*60)
        print("# Get info about a novel:")
        print('python tool.py info -d "./Novels/My_Novel"')
        print()
        print("# List all novels in the database:")
        print('python tool.py list')
        print()
        print("# Validate API configuration:")
        print('python tool.py validate')
        print()
        print("# Scrape a new novel from a URL:")
        print('python tool.py scrape --novel-title "My Awesome Novel" --start-url "https://www.69shu.com/book/123.htm"')
        print()
        print("# Resume scraping an existing novel:")
        print('python tool.py scrape --novel-title "My Awesome Novel"')
        print()
        print("# Translate scraped chapters by title:")
        print('python tool.py translate -n "My Awesome Novel" -w 2')
        print()
        print("# Convert to EPUB:")
        print('python tool.py convert -f "./Novels/Novel_Title/Novel_Title-English" -o "novel.epub" -t "Novel Title" -a "Author Name"')
        print()
        print("# Full workflow example:")
        print('python tool.py validate -p chutes  # Test API first')
        print('python tool.py scrape --novel-title "My Novel" --start-url "https://www.69shu.com/book/123.htm" -m 50')
        print('python tool.py scrape --novel-title "My Novel"  # Resume if needed')
        print('python tool.py info -d "./Novels/My_Novel"  # Check progress')
        print('python tool.py list  # See all novels in DB')
        print('python tool.py translate -n "My Novel" -w 2')
        print('python tool.py convert -f "./Novels/My_Novel/My_Novel-English" -o "my_novel.epub" -t "My Novel" -a "Author"')
        return
    
    # Call the appropriate function
    try:
        args.func(args)
        print(f"\n✅ {args.command.title()} operation completed successfully!")
    except KeyboardInterrupt:
        print(f"\n🛑 {args.command.title()} operation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during {args.command} operation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 