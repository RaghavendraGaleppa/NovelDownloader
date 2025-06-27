#!/usr/bin/env python3
"""
Migration Script for Novels

This script migrates existing novels from the local file system into the MongoDB
database. It reads each novel's directory, extracts metadata from the
progress file, and creates corresponding entries in the 'novels' and
'scraping_progress' collections.
"""

import os
import sys
import json
from datetime import datetime
import sys
sys.path.append("src")

# Add the project's root directory to the Python path
current_folder = os.path.dirname(os.path.abspath(__file__))
parent_folder = os.path.dirname(current_folder)
sys.path.append(parent_folder)

from src.main import db_client

def migrate_novels():
    """
    Migrates novels from the 'Novels' directory to the MongoDB database.
    """
    print("Starting novel migration...")

    novels_dir = os.path.join(parent_folder, "Novels")
    if not os.path.isdir(novels_dir):
        print(f"Error: 'Novels' directory not found at {novels_dir}")
        return

    novels_collection = db_client["novels"]
    progress_collection = db_client["scraping_progress"]

    for novel_folder_name in os.listdir(novels_dir):
        novel_folder_path = os.path.join(novels_dir, novel_folder_name)
        if not os.path.isdir(novel_folder_path):
            continue

        progress_file_path = os.path.join(novel_folder_path, f"{novel_folder_name}_progress.json")
        
        progress_data = None
        novel_title = None

        if os.path.exists(progress_file_path):
            print(f"Processing '{novel_folder_name}' with progress file...")
            with open(progress_file_path, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            novel_title = progress_data.get('novel_title')
        else:
            print(f"Processing '{novel_folder_name}' without progress file (assuming complete)...")
            # Infer title from folder name, e.g., "My_Novel" -> "My Novel"
            novel_title = novel_folder_name.replace('_', ' ')
            progress_data = {
                'original_start_url': None,
                'output_base_dir_name': novel_folder_name,
                'last_scraped_url': None, # Assumed complete, so no last URL needed
                'next_url_to_scrape': None # Mark as complete
            }

        if not novel_title:
            print(f"Skipping '{novel_folder_name}': Could not determine novel title.")
            continue
            
        print(f"  - Migrating novel: '{novel_title}'")

        if novels_collection.count_documents({'novel_name': novel_title}, limit=1) > 0:
            print(f"  - Skipping '{novel_title}': Already exists in the database.")
            continue

        absolute_folder_path = os.path.abspath(novel_folder_path)
        novel_document = {
            'novel_name': novel_title,
            'added_datetime': datetime.now(),
            'folder_path': absolute_folder_path
        }
        insert_result = novels_collection.insert_one(novel_document)
        novel_id = insert_result.inserted_id
        print(f"    - Created entry in 'novels' collection with ID: {novel_id}")

        progress_document = {
            'novel_id': novel_id,
            'original_start_url': progress_data.get('original_start_url'),
            'output_base_dir_name': progress_data.get('output_base_dir_name'),
            'last_scraped_url': progress_data.get('last_scraped_url'),
            'next_url_to_scrape': progress_data.get('next_url_to_scrape')
        }
        progress_collection.insert_one(progress_document)
        print("    - Created entry in 'scraping_progress' collection.")

    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate_novels() 