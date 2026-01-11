"""
Novel Synchronization Module

Provides high-level functions for syncing novels from external websites into the database.
Handles novel discovery, metadata updates, and chapter list synchronization.
"""

import os
from typing import Optional, Tuple
from datetime import datetime
from bson.objectid import ObjectId

from main import db_client
from scraping.website_scrapers import get_scraper, NovelListItem, NovelMetadata, ChapterListItem
from utils.logging_utils import get_logger

logger = get_logger()


def fetch_all_novels_from_source(
    source: str, 
    max_pages: Optional[int] = None, 
    start_page: int = 1,
    listing_type: str = 'all',
    category_id: Optional[int] = None
) -> int:
    """
    Fetch all novels from a source website and store them in the database.
    
    Novels are saved incrementally after each page is fetched, making this
    resilient to interruptions.
    
    Args:
        source: Website identifier (e.g., '69shuba')
        max_pages: Optional limit on number of pages to scrape (for testing)
        start_page: Page number to start fetching from (default: 1)
        listing_type: Type of listing ('all', 'monthvisit', 'category', etc.)
        category_id: Category ID for category-specific fetching
        
    Returns:
        Number of novels found and stored
        
    Raises:
        ValueError: If source is not a valid website identifier
    """
    logger.info(
        f"Starting fetch_all_novels for source: {source}, "
        f"listing_type: {listing_type}, category_id: {category_id}, start_page: {start_page}"
    )
    
    # Get the appropriate scraper
    scraper = get_scraper(source)
    
    # Database collections
    novels_collection = db_client['novels']
    sources_collection = db_client['novel_sources']
    
    total_saved = 0
    new_count = 0
    updated_count = 0
    
    def save_novel_batch(novels_batch):
        """Callback to save a batch of novels to the database"""
        nonlocal total_saved, new_count, updated_count
        
        for novel_item in novels_batch:
            # Check if novel already exists by title
            existing_novel = novels_collection.find_one({'novel_name': novel_item.title})
            
            if existing_novel:
                novel_id = existing_novel['_id']
                logger.debug(f"Novel '{novel_item.title}' already exists with ID: {novel_id}")
            else:
                # Create new novel entry (minimal info for now)
                novel_doc = {
                    'novel_name': novel_item.title,
                    'added_datetime': datetime.now(),
                    'folder_path': None,  # Will be set when scraping starts
                    'raw_chapters_available': 0,
                    'translated_chapters_available': 0,
                }
                result = novels_collection.insert_one(novel_doc)
                novel_id = result.inserted_id
                new_count += 1
                logger.info(f"Created new novel: {novel_item.title} (ID: {novel_id})")
            
            # Check if this source already exists for this novel
            existing_source = sources_collection.find_one({
                'novel_id': novel_id,
                'source_website': source
            })
            
            if existing_source:
                # Update last_checked timestamp
                sources_collection.update_one(
                    {'_id': existing_source['_id']},
                    {'$set': {'last_checked': datetime.now()}}
                )
                updated_count += 1
            else:
                # Create new source entry
                source_doc = {
                    'novel_id': novel_id,
                    'source_website': source,
                    'source_url': novel_item.url,
                    'catalog_url': None,  # Will be populated during sync
                    'discovered_at': datetime.now(),
                    'last_checked': datetime.now(),
                    'is_active': True,
                    'metadata': {}
                }
                sources_collection.insert_one(source_doc)
                logger.debug(f"Added source for novel: {novel_item.title}")
            
            total_saved += 1
    
    # Fetch novels with incremental saving
    total_novels = scraper.fetch_all_novels(
        max_pages=max_pages,
        start_page=start_page,
        save_callback=save_novel_batch,
        listing_type=listing_type,
        category_id=category_id
    )
    
    logger.info(f"Fetch complete: {total_saved} novels processed, {new_count} new, {updated_count} updated")
    return total_saved


def sync_novel_metadata(
    novel_id: Optional[str] = None,
    novel_title: Optional[str] = None,
    source: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sync detailed metadata and chapter list for a specific novel.
    
    Args:
        novel_id: Novel ID (either this or novel_title required)
        novel_title: Novel title (either this or novel_id required)
        source: Website identifier (optional, auto-detected if not provided)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    novels_collection = db_client['novels']
    sources_collection = db_client['novel_sources']
    raw_chapters_collection = db_client['raw_chapters']
    
    # Find the novel
    if novel_id:
        try:
            novel_object_id = ObjectId(novel_id)
            novel_doc = novels_collection.find_one({'_id': novel_object_id})
        except Exception as e:
            return False, f"Invalid novel ID: {e}"
    elif novel_title:
        novel_doc = novels_collection.find_one({'novel_name': novel_title})
        if novel_doc:
            novel_object_id = novel_doc['_id']
    else:
        return False, "Either novel_id or novel_title must be provided"
    
    if not novel_doc:
        return False, f"Novel not found: {novel_id or novel_title}"
    
    novel_name = novel_doc['novel_name']
    logger.info(f"Syncing novel: {novel_name} (ID: {novel_object_id})")
    
    # Find the source
    if source:
        source_doc = sources_collection.find_one({
            'novel_id': novel_object_id,
            'source_website': source
        })
        if not source_doc:
            return False, f"No source '{source}' found for novel '{novel_name}'"
    else:
        # Auto-detect: use the first active source
        source_doc = sources_collection.find_one({
            'novel_id': novel_object_id,
            'is_active': True
        })
        if not source_doc:
            return False, f"No active source found for novel '{novel_name}'"
        source = source_doc['source_website']
    
    source_url = source_doc['source_url']
    logger.info(f"Using source: {source} ({source_url})")
    
    # Get the scraper
    try:
        scraper = get_scraper(source)
    except ValueError as e:
        return False, str(e)
    
    # Fetch metadata
    try:
        metadata = scraper.fetch_novel_metadata(source_url)
    except Exception as e:
        logger.error(f"Failed to fetch metadata: {e}")
        return False, f"Failed to fetch metadata: {e}"
    
    # Update novel document with metadata
    update_fields = {
        'author': metadata.author,
        'description': metadata.description,
        'tags': metadata.tags,
        'status': metadata.status,
        'thumbnail_url': metadata.thumbnail_url,
        'word_count': metadata.word_count,
        'last_synced': datetime.now()
    }
    
    novels_collection.update_one(
        {'_id': novel_object_id},
        {'$set': update_fields}
    )
    logger.info(f"Updated novel metadata for: {novel_name}")
    
    # Update source document with catalog URL
    sources_collection.update_one(
        {'_id': source_doc['_id']},
        {'$set': {
            'catalog_url': metadata.catalog_url,
            'last_checked': datetime.now()
        }}
    )
    
    # Fetch chapter list
    try:
        chapters = scraper.fetch_chapter_list(metadata.catalog_url)
    except Exception as e:
        logger.error(f"Failed to fetch chapter list: {e}")
        return False, f"Failed to fetch chapter list: {e}"
    
    # Update total chapters count
    novels_collection.update_one(
        {'_id': novel_object_id},
        {'$set': {'total_chapters': len(chapters)}}
    )
    
    # Create/update chapter records
    new_chapters = 0
    for chapter in chapters:
        # Check if chapter already exists
        existing_chapter = raw_chapters_collection.find_one({
            'novel_id': novel_object_id,
            'chapter_number': chapter.chapter_number
        })
        
        if not existing_chapter:
            # Create new chapter record (without content - that's scraped separately)
            chapter_doc = {
                'novel_id': novel_object_id,
                'chapter_number': chapter.chapter_number,
                'title': chapter.title,
                'source_url': chapter.url,
                'source_website': source,
                'saved_at': None,  # Will be set when content is scraped
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'n_parts': 0  # Will be incremented when content is scraped
            }
            raw_chapters_collection.insert_one(chapter_doc)
            new_chapters += 1
    
    logger.info(f"Sync complete: {len(chapters)} total chapters, {new_chapters} new chapters added")
    
    message = (
        f"Successfully synced '{novel_name}' from {source}. "
        f"Total chapters: {len(chapters)}, New chapters: {new_chapters}"
    )
    
    return True, message


def get_novel_sources(novel_id: str) -> list:
    """
    Get all sources for a novel.
    
    Args:
        novel_id: Novel ID
        
    Returns:
        List of source documents
    """
    sources_collection = db_client['novel_sources']
    
    try:
        novel_object_id = ObjectId(novel_id)
    except Exception:
        return []
    
    sources = list(sources_collection.find({'novel_id': novel_object_id}))
    return sources
