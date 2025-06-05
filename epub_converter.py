import pypandoc
import os
import glob
from natsort import natsorted
import argparse # Import argparse


def convert_folder_md_to_epub(folder_path, output_epub_name, title="My Awesome Book", author="Unknown Author"):
    """
    Converts all Markdown files in a specified folder (sorted naturally/numerically)
    into a single EPUB file.

    Args:
        folder_path (str): The path to the folder containing Markdown files.
        output_epub_name (str): The desired name for the output EPUB file (e.g., "my_novel.epub").
        title (str, optional): The title of the book for EPUB metadata. Defaults to "My Awesome Book".
        author (str, optional): The author of the book for EPUB metadata. Defaults to "Unknown Author".
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return

    # Find all Markdown files matching the pattern "Chapter_*.md"
    markdown_files_pattern = os.path.join(folder_path, 'Chapter_*.md')
    markdown_files = glob.glob(markdown_files_pattern)

    if not markdown_files:
        print(f"No Markdown files matching '{markdown_files_pattern}' found in '{folder_path}'.")
        return

    print(f"Found {len(markdown_files)} Markdown files initially.")
    # print(f"Unsorted files: {[os.path.basename(f) for f in markdown_files]}") # Optional: for debugging

    # Sort the files using natsorted for natural (numerical) order.
    # This is crucial for correct chapter order (e.g., Chapter_1, Chapter_2, ..., Chapter_10).
    markdown_files = natsorted(markdown_files)

    print("--- Files will be processed in the following (naturally sorted) order ---")
    for i, md_file in enumerate(markdown_files):
        print(f"{i+1}. {os.path.basename(md_file)}")
    print("----------------------------------------------------------------------")

    if os.path.isabs(output_epub_name):
        output_path = output_epub_name
    else:
        output_path = os.path.join(os.getcwd(), output_epub_name)

    try:
        extra_pandoc_args = [
            '--from=markdown-yaml_metadata_block',
            '--lua-filter=prefix_chapter_titles.lua',
            '--toc',
            "--number-sections",
            f'--metadata=title="{title}"',
            f'--metadata=author="{author}"',
        ]

        print(f"\nStarting EPUB conversion to '{output_path}'...")
        pypandoc.convert_file(
            markdown_files,  # This list IS sorted numerically if natsorted worked
            'epub',
            outputfile=output_path,
            extra_args=extra_pandoc_args
        )
        print(f"\nSuccessfully converted Markdown files to '{output_path}'")
        print("Remember to install Pandoc executable on your system for pypandoc to work.")

    except Exception as e:
        print(f"\nAn error occurred during conversion: {e}")
        print("Please ensure Pandoc is installed and accessible in your system's PATH.")
        print("You can download Pandoc from: https://pandoc.org/installing.html")
        print("Or try `pip install pypandoc_binary` if you want to try installing Pandoc via pip (less reliable).")

# --- Command-Line Interface --- 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a folder of Markdown files to a single EPUB.")
    
    parser.add_argument("-f", "--folder-path", 
                        required=True, 
                        help="Path to the folder containing Markdown files.")
    parser.add_argument("-o", "--output-name", 
                        required=True, 
                        help="Desired name for the output EPUB file (e.g., my_novel.epub).")
    parser.add_argument("-t", "--title", 
                        default="My Awesome Book", 
                        help="The title of the book for EPUB metadata (default: My Awesome Book).")
    parser.add_argument("-a", "--author", 
                        default="Unknown Author", 
                        help="The author of the book for EPUB metadata (default: Unknown Author).")

    args = parser.parse_args()

    print(f"--- Converting Markdown files from '{args.folder_path}' to EPUB '{args.output_name}' ---")
    convert_folder_md_to_epub(
        folder_path=args.folder_path,
        output_epub_name=args.output_name,
        title=args.title,
        author=args.author
    )
    # The dummy file creation and cleanup from the original example is removed.
    # If you need to test, you can create dummy files manually or script it separately.
