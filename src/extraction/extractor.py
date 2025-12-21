"""
Extraction Module - Combined Scraping and Translation

This module provides functionality to scrape and translate novel chapters
in a single synchronized process. It ensures that multi-part chapters are
fully scraped before translation begins.

Usage:
    python tool.py extract -n "Novel Title" -s "TOC_URL" -m 50 -w 2
"""

import os
import re
import time
import random
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag

from rich.console import Console

from src.main import db_client
from src.scraping.parse_chapter import (
    NovelScraper,
    scrape_chapter,
    detect_extraction_backend,
    _ensure_output_directory
)
from src.scraping.extraction_backends import EBNovel543
from src.translation.translator import translate, perform_api_validation
from bson import ObjectId

console = Console()


def parse_novel543_toc(html_content: str, base_url: str) -> List[dict]:
    """
    Parse the Novel543 TOC page to extract all chapter URLs.
    
    Args:
        html_content: HTML content of the TOC page
        base_url: Base URL for resolving relative links
        
    Returns:
        List of dicts with 'chapter_num', 'url', 'title' keys, sorted by chapter number
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    chapters = []
    
    # Find all chapter links - they're in <li> or <a> elements with chapter patterns
    # Pattern: 第X章 Title
    chapter_pattern = re.compile(r'第(\d+)章')
    
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        match = chapter_pattern.search(text)
        
        if match:
            chapter_num = int(match.group(1))
            href = link.get('href')
            
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            
            # Only include novel543.com URLs
            if 'novel543.com' in full_url:
                chapters.append({
                    'chapter_num': chapter_num,
                    'url': full_url,
                    'title': text
                })
    
    # Sort by chapter number and remove duplicates
    seen = set()
    unique_chapters = []
    for ch in sorted(chapters, key=lambda x: x['chapter_num']):
        if ch['chapter_num'] not in seen:
            seen.add(ch['chapter_num'])
            unique_chapters.append(ch)
    
    return unique_chapters


def is_same_chapter_continuation(current_url: str, next_url: str) -> bool:
    """
    Check if next_url is a continuation (next part) of the current chapter.
    
    Novel543 URL patterns:
    - Chapter 1 part 1: /0624601529/8096_1.html
    - Chapter 1 part 2: /0624601529/8096_1_2.html
    - Chapter 2: /0624601529/8096_2.html
    
    Returns True if next_url is a continuation of the same chapter.
    """
    # Extract chapter identifiers from URLs
    # Pattern: /{novel_id}/{prefix}_{chapter}.html or /{novel_id}/{prefix}_{chapter}_{part}.html
    current_pattern = re.search(r'/(\d+_\d+)(?:_\d+)?\.html?$', current_url)
    next_pattern = re.search(r'/(\d+_\d+)(?:_\d+)?\.html?$', next_url)
    
    if not current_pattern or not next_pattern:
        return False
    
    current_chapter_id = current_pattern.group(1)  # e.g., "8096_1"
    next_chapter_id = next_pattern.group(1)  # e.g., "8096_1" or "8096_2"
    
    # If the chapter identifiers match, it's a continuation
    return current_chapter_id == next_chapter_id


def scrape_complete_chapter(
    starting_url: str,
    use_selenium: bool = False
) -> Tuple[str, str, Optional[str]]:
    """
    Scrape a complete chapter including all parts.
    
    Args:
        starting_url: URL of the first part of the chapter
        use_selenium: Whether to use Selenium instead of CloudScraper
        
    Returns:
        Tuple of (chapter_title, combined_content, next_chapter_url)
        - chapter_title: Title extracted from the first part
        - combined_content: All parts combined with separators
        - next_chapter_url: URL of the next chapter (or None if no next chapter)
    """
    backend = EBNovel543()
    all_paragraphs = []
    chapter_title = ""
    chapter_number = None
    current_url = starting_url
    part_count = 0
    next_chapter_url = None
    
    console.print(f"  📖 Scraping from: {starting_url}", style="dim")
    
    while current_url:
        part_count += 1
        console.print(f"    Part {part_count}: {current_url}", style="dim")
        
        # Scrape the current part
        html_content = scrape_chapter(current_url, use_selenium=use_selenium)
        
        if not html_content:
            console.print(f"    ❌ Failed to fetch: {current_url}", style="red")
            break
        
        # Extract content
        title, paragraphs, next_url, ch_num = backend.extract_all_content(html_content, current_url)
        
        if part_count == 1:
            chapter_title = title
            chapter_number = ch_num
        
        if paragraphs:
            if part_count > 1:
                # Add separator between parts
                all_paragraphs.append("---")
            all_paragraphs.extend(paragraphs)
        
        # Check if next URL exists and is a continuation
        if next_url:
            if is_same_chapter_continuation(current_url, next_url):
                # Continue to next part
                current_url = next_url
                # Small delay between parts
                time.sleep(random.uniform(0.5, 1.5))
            else:
                # This is the next chapter, not a continuation
                next_chapter_url = next_url
                break
        else:
            # No next URL, chapter complete
            break
    
    # Combine all content
    if chapter_number:
        combined_content = f"# {chapter_title}\n\n" + "\n\n".join(all_paragraphs)
    else:
        combined_content = f"# {chapter_title}\n\n" + "\n\n".join(all_paragraphs)
    
    console.print(f"    ✅ Scraped {part_count} part(s), {len(all_paragraphs)} paragraphs", style="green")
    
    return chapter_title, combined_content, next_chapter_url


def extract_single_chapter(
    chapter_info: dict,
    novel_folder_path: str,
    db,
    novel_id: ObjectId,
    use_selenium: bool = False,
    skip_existing: bool = True
) -> bool:
    """
    Extract (scrape + translate) a single chapter.
    
    Args:
        chapter_info: Dict with 'chapter_num', 'url', 'title'
        novel_folder_path: Base path for the novel
        db: Database client
        novel_id: MongoDB ObjectId for the novel
        use_selenium: Use Selenium for scraping
        skip_existing: Skip if already translated
        
    Returns:
        True if successful, False otherwise
    """
    chapter_num = chapter_info['chapter_num']
    chapter_url = chapter_info['url']
    
    console.print(f"\n{'='*60}", style="blue")
    console.print(f"📚 Processing Chapter {chapter_num}: {chapter_info['title'][:50]}...", style="bold blue")
    
    # Check if already translated
    if skip_existing:
        existing = db.translated_chapters.find_one({
            'novel_id': novel_id,
            'chapter_number': chapter_num,
            'status': 'completed'
        })
        if existing:
            console.print(f"  ⏭️  Already translated, skipping", style="yellow")
            return True
    
    try:
        # 1. SCRAPE - Get complete chapter including all parts
        start_time = time.time()
        chapter_title, raw_content, _ = scrape_complete_chapter(chapter_url, use_selenium)
        scrape_time = time.time() - start_time
        
        if not raw_content or raw_content.startswith("# No"):
            console.print(f"  ❌ Failed to scrape chapter {chapter_num}", style="red")
            return False
        
        # 2. SAVE RAW - Save the raw content
        raws_dir = os.path.join(novel_folder_path, "Raws")
        _ensure_output_directory(raws_dir)
        
        raw_filename = f"Chapter_{chapter_num:05d}.md"
        raw_filepath = os.path.join(raws_dir, raw_filename)
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            f.write(raw_content)
        
        console.print(f"  💾 Saved raw: {raw_filename} ({scrape_time:.1f}s)", style="dim")
        
        # Create/update raw chapter record in DB
        raw_chapter_record = {
            'novel_id': novel_id,
            'chapter_number': chapter_num,
            'title': chapter_title,
            'saved_at': raw_filepath,
            'updated_at': datetime.now()
        }
        
        raw_result = db.raw_chapters.update_one(
            {'novel_id': novel_id, 'chapter_number': chapter_num},
            {'$set': raw_chapter_record, '$setOnInsert': {'created_at': datetime.now()}},
            upsert=True
        )
        raw_chapter_id = raw_result.upserted_id if raw_result.upserted_id else db.raw_chapters.find_one(
            {'novel_id': novel_id, 'chapter_number': chapter_num}
        )['_id']
        
        # 3. TRANSLATE - Translate the complete chapter
        console.print(f"  🔄 Translating...", style="cyan")
        translate_start = time.time()
        
        translated_content, provider = translate(raw_content)
        translate_time = time.time() - translate_start
        
        if translated_content.startswith("Error:"):
            console.print(f"  ❌ Translation failed: {translated_content[:100]}", style="red")
            # Record failed translation
            db.translated_chapters.update_one(
                {'novel_id': novel_id, 'chapter_number': chapter_num},
                {'$set': {
                    'novel_id': novel_id,
                    'raw_chapter_id': raw_chapter_id,
                    'chapter_number': chapter_num,
                    'status': 'failed',
                    'error': translated_content,
                    'updated_at': datetime.now()
                }},
                upsert=True
            )
            return False
        
        # 4. SAVE TRANSLATED - Save the translated content
        translations_dir = os.path.join(novel_folder_path, "Translations")
        _ensure_output_directory(translations_dir)
        
        translated_filename = f"Chapter_{chapter_num:05d}.md"
        translated_filepath = os.path.join(translations_dir, translated_filename)
        
        with open(translated_filepath, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        
        # Extract translated title
        lines = translated_content.splitlines()
        translated_title = lines[0] if lines else chapter_title
        if translated_title.startswith('#'):
            translated_title = translated_title.lstrip('# ').strip()
        
        # Update translation record
        db.translated_chapters.update_one(
            {'novel_id': novel_id, 'chapter_number': chapter_num},
            {'$set': {
                'novel_id': novel_id,
                'raw_chapter_id': raw_chapter_id,
                'chapter_number': chapter_num,
                'title': translated_title,
                'saved_at': translated_filepath,
                'status': 'completed',
                'provider': provider,
                'pickup_epoch': translate_start,
                'end_epoch': time.time(),
                'time_taken_epoch': translate_time,
                'updated_at': datetime.now()
            }},
            upsert=True
        )
        
        # Update novel stats
        _update_novel_stats(db, novel_id)
        
        total_time = time.time() - start_time
        console.print(f"  ✅ Completed: {translated_filename} (scrape: {scrape_time:.1f}s, translate: {translate_time:.1f}s, total: {total_time:.1f}s)", style="green")
        
        # Rate limiting - if too fast, add delay
        if total_time < 10:
            delay = 10 - total_time
            console.print(f"  ⏳ Rate limit delay: {delay:.1f}s", style="dim")
            time.sleep(delay)
        
        return True
        
    except Exception as e:
        console.print(f"  ❌ Error processing chapter {chapter_num}: {e}", style="red")
        import traceback
        traceback.print_exc()
        return False


def _update_novel_stats(db, novel_id: ObjectId):
    """Update raw and translated chapter counts for the novel."""
    raw_count = db.raw_chapters.count_documents({'novel_id': novel_id})
    translated_count = db.translated_chapters.count_documents({
        'novel_id': novel_id,
        'status': 'completed'
    })
    
    db.novels.update_one(
        {'_id': novel_id},
        {'$set': {
            'raw_chapters_available': raw_count,
            'translated_chapters_available': translated_count
        }}
    )


def fetch_toc(toc_url: str, use_selenium: bool = False) -> List[dict]:
    """
    Fetch and parse the TOC page.
    
    Args:
        toc_url: URL of the TOC page (or a chapter URL to derive TOC URL)
        use_selenium: Whether to use Selenium
        
    Returns:
        List of chapter info dicts
    """
    # If this is a chapter URL, convert to TOC URL
    if '/dir' not in toc_url:
        # Extract novel ID and construct TOC URL
        # Pattern: https://www.novel543.com/0624601529/8096_1.html
        match = re.search(r'novel543\.com/(\d+)/', toc_url)
        if match:
            novel_id = match.group(1)
            toc_url = f"https://www.novel543.com/{novel_id}/dir"
            console.print(f"📋 Derived TOC URL: {toc_url}", style="cyan")
    
    console.print(f"📥 Fetching Table of Contents from: {toc_url}", style="bold cyan")
    
    html_content = scrape_chapter(toc_url, use_selenium=use_selenium)
    
    if not html_content:
        console.print("❌ Failed to fetch TOC page", style="red")
        return []
    
    chapters = parse_novel543_toc(html_content, toc_url)
    console.print(f"✅ Found {len(chapters)} chapters in TOC", style="green")
    
    return chapters


def run_extraction(args: argparse.Namespace):
    """
    Main entry point for the extract command.
    
    Args:
        args: Parsed command line arguments
    """
    novel_title = args.novel_title
    start_url = args.start_url
    workers = args.workers
    max_chapters = args.max_chapters
    
    # Selenium is default, use CloudScraper only if explicitly requested
    use_cloudscraper = getattr(args, 'use_cloudscraper', False)
    use_selenium = not use_cloudscraper
    
    skip_validation = getattr(args, 'skip_validation', False)
    
    scraper_type = "CloudScraper" if use_cloudscraper else "Selenium"
    
    console.print(f"\n{'='*60}", style="bold magenta")
    console.print(f"🚀 Starting Extraction for: {novel_title}", style="bold magenta")
    console.print(f"   Workers: {workers}, Max Chapters: {max_chapters}", style="magenta")
    console.print(f"   Scraper: {scraper_type}", style="magenta")
    console.print(f"{'='*60}\n", style="bold magenta")
    
    # Validate API before starting (unless skipped)
    if not skip_validation:
        if not perform_api_validation():
            console.print("❌ API validation failed. Cannot proceed.", style="red")
            return
    else:
        console.print("⏭️  Skipping API validation as requested", style="yellow")
    
    # Setup paths
    safe_title = novel_title.replace(' ', '_').replace('/', '_').replace('\\', '_')
    
    if args.output_path:
        base_path = args.output_path
    else:
        base_path = os.path.join("Novels", safe_title)
    
    absolute_path = os.path.abspath(base_path)
    
    # Database setup
    db = db_client
    novels_collection = db.novels
    
    # Check if novel exists
    novel_doc = novels_collection.find_one({'novel_name': novel_title})
    
    if novel_doc:
        novel_id = novel_doc['_id']
        console.print(f"📚 Found existing novel: {novel_title} (ID: {novel_id})", style="cyan")
    else:
        if not start_url:
            console.print("❌ Novel not found. Please provide --start-url for new novels.", style="red")
            return
        
        # Create new novel record
        novel_doc = {
            'novel_name': novel_title,
            'added_datetime': datetime.now(),
            'folder_path': absolute_path
        }
        result = novels_collection.insert_one(novel_doc)
        novel_id = result.inserted_id
        console.print(f"📚 Created new novel: {novel_title} (ID: {novel_id})", style="green")
    
    # Ensure directories exist
    _ensure_output_directory(os.path.join(absolute_path, "Raws"))
    _ensure_output_directory(os.path.join(absolute_path, "Translations"))
    
    # Fetch TOC
    if not start_url:
        # Try to get start URL from existing progress
        progress = db.scraping_progress.find_one({'novel_id': novel_id})
        if progress:
            start_url = progress.get('original_start_url')
    
    if not start_url:
        console.print("❌ No start URL available. Please provide --start-url.", style="red")
        return
    
    chapters = fetch_toc(start_url, use_selenium=use_selenium)
    
    if not chapters:
        console.print("❌ No chapters found in TOC.", style="red")
        return
    
    # Limit to max_chapters
    chapters_to_process = chapters[:max_chapters]
    console.print(f"\n📖 Processing {len(chapters_to_process)} chapters (out of {len(chapters)} total)\n", style="bold cyan")
    
    # Process chapters
    if workers == 1:
        # Sequential processing
        success_count = 0
        for chapter_info in chapters_to_process:
            result = extract_single_chapter(
                chapter_info, absolute_path, db, novel_id, use_selenium
            )
            if result:
                success_count += 1
            # Small delay between chapters
            time.sleep(random.uniform(1, 3))
        
        console.print(f"\n{'='*60}", style="bold green")
        console.print(f"✅ Extraction Complete! {success_count}/{len(chapters_to_process)} chapters processed.", style="bold green")
    else:
        # Parallel processing with ThreadPoolExecutor
        success_count = 0
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for chapter_info in chapters_to_process:
                future = executor.submit(
                    extract_single_chapter,
                    chapter_info, absolute_path, db, novel_id, use_selenium
                )
                futures[future] = chapter_info['chapter_num']
            
            for future in as_completed(futures):
                chapter_num = futures[future]
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    console.print(f"❌ Worker error for chapter {chapter_num}: {e}", style="red")
                    failed_count += 1
        
        console.print(f"\n{'='*60}", style="bold green")
        console.print(f"✅ Extraction Complete!", style="bold green")
        console.print(f"   Success: {success_count}, Failed: {failed_count}, Total: {len(chapters_to_process)}", style="green")
    
    # Update final stats
    _update_novel_stats(db, novel_id)
    console.print(f"{'='*60}\n", style="bold green")
