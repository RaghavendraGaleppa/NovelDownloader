import os
import sys
import argparse
from bson.objectid import ObjectId

# Add project root to sys.path to allow importing from src
sys.path.append("src/")

try:
    from main import db_client
except ImportError:
    print("Error: Could not import db_client from src.main. Make sure the script is run from the project root or the path is set correctly.")
    sys.exit(1)

def backfill_novel(novel_doc):
    """Backfills chapter counts for a single novel."""
    novel_id = novel_doc['_id']
    novel_name = novel_doc['novel_name']
    print(f"Processing novel: {novel_name} ({novel_id})")

    # --- Calculate raw_chapters_available ---
    raw_chapters_available = db_client.raw_chapters.count_documents({'novel_id': novel_id})

    # --- Calculate translated_chapters_available ---
    translated_chapters_available = db_client.translated_chapters.count_documents({
        'novel_id': novel_id, 
        'status': 'completed'
    })

    # --- Update the novel document ---
    update_payload = {
        'raw_chapters_available': raw_chapters_available,
        'translated_chapters_available': translated_chapters_available
    }
    
    db_client.novels.update_one(
        {'_id': novel_id},
        {'$set': update_payload}
    )

    print(f"  - Updated {novel_name}:")
    print(f"    - Raw chapters available: {raw_chapters_available}")
    print(f"    - Translated chapters available: {translated_chapters_available}")
    print("-" * 30)

def main():
    parser = argparse.ArgumentParser(description="Backfill chapter availability counts for novels in the database.")
    parser.add_argument(
        "--novel-title",
        help="The title of a specific novel to backfill. If not provided, all novels will be processed."
    )
    args = parser.parse_args()

    if args.novel_title:
        print(f"Looking for novel: '{args.novel_title}'")
        novel_doc = db_client.novels.find_one({'novel_name': args.novel_title})
        if novel_doc:
            backfill_novel(novel_doc)
        else:
            print(f"Error: Novel with title '{args.novel_title}' not found.")
            return
    else:
        print("Processing all novels in the database...")
        all_novels = db_client.novels.find()
        # count_documents is preferred over count
        novel_count = db_client.novels.count_documents({})
        if novel_count == 0:
            print("No novels found in the database.")
            return
            
        for novel in all_novels:
            backfill_novel(novel)
        
        print(f"\nSuccessfully processed {novel_count} novels.")

if __name__ == "__main__":
    main() 