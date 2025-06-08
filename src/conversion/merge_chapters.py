import os
import re
import shutil
import argparse # Import argparse

def extract_chapter_number(filename):
    """Extracts the chapter number from a filename like 'Chapter_123.md'."""
    match = re.search(r'Chapter_(\d+)\.md', filename)
    if match:
        return int(match.group(1))
    return -1 # Should not happen for valid files, helps in sorting unknowns

def merge_chapter_files(novel_base_directory: str, chapters_per_file: int = 10):
    """
    Merges chapter files from the 'Raws' subdirectory into larger files
    in a 'RawsMerged' subdirectory.

    Args:
        novel_base_directory (str): The base directory of the novel 
                                    (e.g., './My_Awesome_Novel/').
        chapters_per_file (int): Number of chapters to merge into a single file.
    """
    raws_dir = os.path.join(novel_base_directory, "Raws")
    merged_dir = os.path.join(novel_base_directory, "RawsMerged")

    if not os.path.isdir(raws_dir):
        print(f"Error: Raws directory not found at {raws_dir}")
        return

    if not os.path.exists(merged_dir):
        try:
            os.makedirs(merged_dir)
            print(f"Created directory: {merged_dir}")
        except OSError as e:
            print(f"Error creating directory {merged_dir}: {e}")
            return
    else:
        # Optional: Clean up existing merged files if re-running
        # for filename in os.listdir(merged_dir):
        #     file_path = os.path.join(merged_dir, filename)
        #     try:
        #         if os.path.isfile(file_path) or os.path.islink(file_path):
        #             os.unlink(file_path)
        #         elif os.path.isdir(file_path):
        #             shutil.rmtree(file_path)
        #     except Exception as e:
        #         print(f'Failed to delete {file_path}. Reason: {e}')
        print(f"Output directory {merged_dir} already exists. Merged files might be overwritten or appended.")


    chapter_files = [f for f in os.listdir(raws_dir) if f.startswith("Chapter_") and f.endswith(".md")]
    
    # Sort files numerically based on chapter number
    chapter_files.sort(key=extract_chapter_number)

    if not chapter_files:
        print(f"No chapter files found in {raws_dir}.")
        return

    num_chapter_files = len(chapter_files)
    print(f"Found {num_chapter_files} chapter files to process.")

    for i in range(0, num_chapter_files, chapters_per_file):
        chunk = chapter_files[i:i + chapters_per_file]
        
        if not chunk:
            continue

        first_chap_num = extract_chapter_number(chunk[0])
        last_chap_num = extract_chapter_number(chunk[-1])

        merged_filename = f"Chapters_{first_chap_num}-{last_chap_num}.md"
        merged_filepath = os.path.join(merged_dir, merged_filename)
        
        print(f"Merging chapters {first_chap_num} to {last_chap_num} into {merged_filepath}...")

        with open(merged_filepath, 'w', encoding='utf-8') as outfile:
            for chapter_filename in chunk:
                chapter_filepath = os.path.join(raws_dir, chapter_filename)
                try:
                    with open(chapter_filepath, 'r', encoding='utf-8') as infile:
                        # Add a newline before appending next chapter if outfile is not empty
                        # and to ensure separation if chapter files don't end with newlines.
                        if outfile.tell() > 0: # if not the first chapter in this merged file
                             outfile.write("\n\n---\n\n") # Markdown horizontal rule as separator
                        
                        content = infile.read()
                        outfile.write(content)
                        # Ensure each chapter ends with a newline before the next one starts or file ends
                        if not content.endswith('\n'):
                            outfile.write('\n')

                except FileNotFoundError:
                    print(f"  Warning: Chapter file not found: {chapter_filepath}")
                except Exception as e:
                    print(f"  Error reading {chapter_filepath}: {e}")
        
        print(f"Successfully merged into {merged_filepath}")

    print("\nChapter merging process completed.")

if __name__ == "__main__":
    print("Novel Chapter Merger Tool")
    print("-------------------------")

    parser = argparse.ArgumentParser(description="Merge raw chapter files for a novel.")
    parser.add_argument("-n", "--novel-base-dir", 
                        dest="novel_base_directory", # Keep using 'novel_base_directory' in the args namespace
                        required=True, 
                        help="The base directory of the novel (containing the 'Raws' subdirectory).")
    parser.add_argument("-c", "--chapters_per_file", 
                        type=int, 
                        default=10, 
                        help="Number of chapters to merge into a single file (default: 10).")

    args = parser.parse_args()

    if not os.path.isdir(args.novel_base_directory):
        print(f"Error: The provided path '{args.novel_base_directory}' is not a valid directory.")
    else:
        merge_chapter_files(args.novel_base_directory, args.chapters_per_file)

    # Example for a fixed path (uncomment to use, and comment out the input part):
    # fixed_novel_path = "./My_Awesome_Novel"  # Adjust this path
    # if os.path.isdir(fixed_novel_path):
    #     merge_chapter_files(fixed_novel_path)
    # else:
    #     print(f"Error: The fixed path '{fixed_novel_path}' is not a valid directory.")
    #     print("Please ensure the Raws folder exists within it.") 