#!/usr/bin/env python3
"""
Novel Processing Tool - Unified Command Line Interface

This tool combines scraping, translation, and EPUB conversion functionality
for processing Chinese novels into English EPUB files.

Usage:
    python tool.py scrape -n "URL" "TITLE" [-m MAX_CHAPTERS] [-o OUTPUT_PATH]
    python tool.py translate -n NOVEL_DIR [-r] [-p PROVIDER] [-w WORKERS]
    python tool.py convert -f FOLDER_PATH -o OUTPUT.epub [-t TITLE] [-a AUTHOR]
"""

import argparse
import sys
import os
import json
from rich.console import Console

# Import the main functions from our organized modules
from src.scraping.parse_chapter import main as scrape_main
from src.translation.translator import translate_novel_chapters, perform_api_validation
from src.conversion.epub_converter import convert_folder_md_to_epub


def cmd_scrape(args):
    """Handle the scrape subcommand"""
    print("🕷️  Starting novel scraping...")
    
    # Create a namespace object that matches what parse_chapter.main expects
    scrape_args = argparse.Namespace()
    scrape_args.max_chapters = args.max_chapters
    scrape_args.output_path = args.output_path
    scrape_args.output_dir = None
    scrape_args.start_chapter = None
    scrape_args.no_progress = False  # Enable progress by default
    
    if args.resume:
        # Resume mode - find progress file in the specified folder
        folder_path = args.resume
        
        if not os.path.isdir(folder_path):
            print(f"❌ Error: Folder not found: {folder_path}")
            return
        
        # Look for progress JSON files in the folder
        progress_files = [f for f in os.listdir(folder_path) if f.endswith('_progress.json')]
        
        if not progress_files:
            print(f"❌ Error: No progress file found in {folder_path}")
            print("   Progress files should end with '_progress.json'")
            return
        
        if len(progress_files) > 1:
            print(f"⚠️  Warning: Multiple progress files found in {folder_path}:")
            for i, pf in enumerate(progress_files, 1):
                print(f"   {i}. {pf}")
            print("   Using the first one found.")
        
        progress_file_path = os.path.join(folder_path, progress_files[0])
        print(f"📁 Found progress file: {progress_file_path}")
        
        # For resume mode, we need to extract the URL from the progress file
        try:
            with open(progress_file_path, 'r', encoding='utf-8') as pf:
                progress_data = json.load(pf)
            
            # Get the next URL to scrape from the progress file
            scrape_args.url = progress_data.get('next_url_to_scrape')
            scrape_args.title = progress_data.get('novel_title', 'Unknown Novel')
            
            if not scrape_args.url:
                print("❌ Error: Progress file indicates scraping is already complete.")
                return
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Error reading progress file: {e}")
            return
        
    else:
        # New scrape mode - extract URL and title from url_title
        scrape_args.url, scrape_args.title = args.url_title
    
    # Call the main scraping function
    scrape_main(scrape_args)


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
    print("🔤 Starting novel translation...")
    
    # Validate the novel directory exists
    if not os.path.isdir(args.novel_base_directory):
        print(f"❌ Error: The provided path '{args.novel_base_directory}' is not a valid directory.")
        return
    
    # Import the translate function and create a proper args namespace
    from src.translation.translator import translate_novel_chapters
    
    # Create a mock args object with the workers attribute for compatibility
    import types
    mock_args = types.SimpleNamespace()
    mock_args.workers = args.workers
    
    # Set the global args in the translator module so it can access workers
    import src.translation.translator as translator_module
    translator_module.args = mock_args
    
    # Call the translation function with the specified parameters
    translate_novel_chapters(
        novel_base_directory=args.novel_base_directory,
        retry_failed_only=args.retry_failed,
        skip_validation=args.skip_validation
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
        description='Scrape novel chapters from supported websites (69shu, 1qxs, etc.)',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Create mutually exclusive group for new scrape vs resume
    scrape_group = scrape_parser.add_mutually_exclusive_group(required=True)
    scrape_group.add_argument(
        '-n', '--new-scrape',
        nargs=2,
        metavar=('URL', 'TITLE'),
        dest='url_title',
        help='Start a new scrape. Requires URL and TITLE.\nExample: -n "https://example.com/chapter1" "My Novel Title"'
    )
    scrape_group.add_argument(
        '-r', '--resume',
        metavar='FOLDER_PATH',
        help='Resume scraping from a novel folder. Automatically finds progress file.\nExample: -r "Novels/My_Novel_Title"'
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
        help='Translate novel chapters to English',
        description='Translate raw novel chapters using AI translation APIs',
        formatter_class=argparse.RawTextHelpFormatter
    )
    translate_parser.add_argument(
        '-n', '--novel-base-dir',
        dest='novel_base_directory',
        required=True,
        help='The base directory of the novel (containing the Raws subdirectory)'
    )
    translate_parser.add_argument(
        '-r', '--retry-failed',
        action='store_true',
        help='Only attempt to translate chapters that previously failed'
    )
    translate_parser.add_argument(
        '-p', '--provider',
        default='chutes',
        help='This argument is now ignored. API providers are determined by secrets.json.'
    )
    translate_parser.add_argument(
        '-w', '--workers',
        type=int,
        default=1,
        help='Number of worker threads for parallel processing (default: 1)'
    )
    translate_parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip API validation before starting translation (not recommended)'
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
        print("# Validate API configuration:")
        print('python tool.py validate -p chutes')
        print()
        print("# Scrape a novel from 69shu:")
        print('python tool.py scrape -n "https://www.69shu.com/book/123.htm" "Novel Title"')
        print()
        print("# Resume scraping from a folder:")
        print('python tool.py scrape -r "Novels/Novel_Title"')
        print()
        print("# Translate scraped chapters:")
        print('python tool.py translate -n "./Novels/Novel_Title" -p chutes')
        print()
        print("# Convert to EPUB:")
        print('python tool.py convert -f "./Novels/Novel_Title/Novel_Title-English" -o "novel.epub" -t "Novel Title" -a "Author Name"')
        print()
        print("# Full workflow example:")
        print('python tool.py validate -p chutes  # Test API first')
        print('python tool.py scrape -n "https://www.69shu.com/book/123.htm" "My Novel" -m 50')
        print('python tool.py scrape -r "Novels/My_Novel"  # Resume if needed')
        print('python tool.py info -d "./Novels/My_Novel"  # Check progress')
        print('python tool.py translate -n "./Novels/My_Novel" -p chutes -w 2')
        print('python tool.py convert -f "./Novels/My_Novel/My_Novel-English" -o "my_novel.epub" -t "My Novel" -a "Author"')
        return
    
    # Extract URL and title for scrape command
    if args.command == 'scrape':
        if hasattr(args, 'url_title') and args.url_title:
            args.url, args.title = args.url_title
    
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