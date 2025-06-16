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
        
        # Set up args for resume mode
        scrape_args.progress_file = progress_file_path
        scrape_args.new_scrape = None
        
    else:
        # New scrape mode
        args.url, args.title = args.url_title
        scrape_args.new_scrape = [args.url, args.title]
        scrape_args.progress_file = None
    
    # Call the main scraping function
    scrape_main(scrape_args)


def cmd_validate(args):
    """Handle the validate subcommand"""
    print("🔧 Starting API validation...")
    
    # Import the validation function
    from src.translation.translator import perform_api_validation
    
    # Perform validation
    if perform_api_validation(args.provider):
        print(f"\n✅ API validation successful for provider '{args.provider}'!")
        print("You can now proceed with translation operations.")
    else:
        print(f"\n❌ API validation failed for provider '{args.provider}'.")
        print("Please fix the issues above before attempting translation.")


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
        api_provider_name=args.provider,
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
        metavar='{scrape,translate,convert,validate}'
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
        help='The API provider to validate (e.g., "chutes", "openrouter"). Default: chutes'
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
        help='The API provider to use (e.g., "chutes", "openrouter"). Default: chutes'
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
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle the case where no subcommand is provided
    if not args.command:
        parser.print_help()
        print("\n" + "="*60)
        print("EXAMPLES:")
        print("="*60)
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