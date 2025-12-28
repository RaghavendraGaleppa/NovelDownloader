"""
69shuba.com Scraper Implementation

Scrapes novel listings, metadata, and chapter information from 69shuba.com.
Uses Selenium with delays to avoid detection.
"""

import time
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scraping.website_scrapers import (
    WebsiteScraper,
    NovelListItem,
    NovelMetadata,
    ChapterListItem,
    register_scraper
)
from scraping.parse_chapter import SeleniumScraper


@register_scraper('69shuba')
class Shuba69Scraper(WebsiteScraper):
    """Scraper for 69shuba.com"""
    
    BASE_URL = "https://www.69shuba.com"
    CATEGORY_URL_TEMPLATE = "https://www.69shuba.com/novels/class/0/{page}.htm"
    
    def __init__(self):
        self.scraper = None
    
    @property
    def website_name(self) -> str:
        return "69shuba"
    
    def _ensure_scraper(self):
        """Lazy initialization of Selenium scraper"""
        if self.scraper is None:
            self.scraper = SeleniumScraper(timeout=30, headless=True)
    
    def _close_scraper(self):
        """Clean up Selenium resources"""
        if self.scraper is not None:
            self.scraper.close()
            self.scraper = None
    
    def fetch_all_novels(self, max_pages: Optional[int] = None, save_callback=None) -> int:
        """
        Fetch all novels from category listing pages.
        
        Iterates through /novels/class/0/{page}.htm pages until no more novels found.
        Uses Selenium with 3-5 second delays between pages.
        
        Args:
            max_pages: Optional limit on number of pages to scrape
            save_callback: Optional callback function to save novels after each page.
                          Called with a list of NovelListItem objects.
        
        Returns:
            Total number of novels found
        """
        self._ensure_scraper()
        
        total_novels = 0
        page_num = 1
        
        try:
            while True:
                if max_pages and page_num > max_pages:
                    print(f"Reached max_pages limit ({max_pages}). Stopping.")
                    break
                
                url = self.CATEGORY_URL_TEMPLATE.format(page=page_num)
                print(f"Fetching page {page_num}: {url}")
                
                html_content = self.scraper.fetch_url(url)
                if not html_content:
                    print(f"Failed to fetch page {page_num}. Stopping.")
                    break
                
                # Parse the page
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all novel entries
                # Container: ul#article_list_content, Items: li elements
                novel_items = soup.select('ul#article_list_content li')
                
                if not novel_items:
                    print(f"No novels found on page {page_num}. Reached end.")
                    break
                
                page_novels = []
                for item in novel_items:
                    try:
                        # Extract title and URL from .newnav h3 a (skip the empty imgbox link)
                        title_link = item.select_one('.newnav h3 a:not(.imgbox)')
                        if not title_link:
                            continue
                        
                        title = title_link.get_text(strip=True)
                        relative_url = title_link.get('href')
                        
                        if not relative_url or not title:
                            continue
                        
                        # Convert to absolute URL
                        absolute_url = urljoin(self.BASE_URL, relative_url)
                        
                        novel = NovelListItem(
                            title=title,
                            url=absolute_url,
                            source_website=self.website_name
                        )
                        page_novels.append(novel)
                    
                    except Exception as e:
                        print(f"Error parsing novel item: {e}")
                        continue
                
                print(f"Found {len(page_novels)} novels on page {page_num}")
                total_novels += len(page_novels)
                
                # Save this page's novels immediately if callback provided
                if save_callback and page_novels:
                    try:
                        save_callback(page_novels)
                        print(f"Saved {len(page_novels)} novels to database")
                    except Exception as e:
                        print(f"Error saving novels: {e}")
                        # Continue anyway - we'll try to save the next page
                
                # Delay before next page (3-5 seconds)
                delay = 3 + (time.time() % 2)  # Random 3-5 seconds
                print(f"Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)
                
                page_num += 1
        
        finally:
            self._close_scraper()
        
        print(f"\nTotal novels found: {total_novels}")
        return total_novels
    
    def fetch_novel_metadata(self, novel_url: str) -> NovelMetadata:
        """
        Fetch detailed metadata from a novel's detail page.
        
        Args:
            novel_url: URL like https://www.69shuba.com/book/90548.htm
        """
        self._ensure_scraper()
        
        try:
            print(f"Fetching metadata from: {novel_url}")
            
            html_content = self.scraper.fetch_url(novel_url)
            if not html_content:
                raise ValueError(f"Failed to fetch novel page: {novel_url}")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_elem = soup.select_one('.newnav h3') or soup.select_one('h1.bookname')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract author from .labelbox label:nth-of-type(1)
            author_elem = soup.select_one('.labelbox label:nth-of-type(1)')
            author = author_elem.get_text(strip=True) if author_elem else None
            
            # Extract description from ol or .newnav ol
            desc_elem = soup.select_one('.newnav ol') or soup.select_one('div.navtxt')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Extract tags from .labelbox label (skip first which is author)
            tags = []
            tag_elems = soup.select('.labelbox label')
            if len(tag_elems) > 1:
                # Second label is usually category/genre
                tags.append(tag_elems[1].get_text(strip=True))
            
            # Extract status from .labelbox label:nth-of-type(3)
            status = None
            if len(tag_elems) > 2:
                status_text = tag_elems[2].get_text(strip=True)
                if '连载' in status_text:
                    status = 'ongoing'
                elif '完结' in status_text or '完本' in status_text:
                    status = 'completed'
            
            # Extract thumbnail URL from .imgbox img data-src
            thumbnail_url = None
            img_elem = soup.select_one('.imgbox img')
            if img_elem:
                # Try data-src first (lazy loading), then src
                thumbnail_url = img_elem.get('data-src') or img_elem.get('src')
                if thumbnail_url:
                    thumbnail_url = urljoin(self.BASE_URL, thumbnail_url)
            
            # Extract word count
            word_count = None
            word_count_elem = soup.select_one('div.booknav2')
            if word_count_elem:
                word_count_text = word_count_elem.get_text()
                # Look for pattern like "55.26万字"
                match = re.search(r'([\d.]+万字)', word_count_text)
                if match:
                    word_count = match.group(1)
            
            # Determine catalog URL
            # For 69shuba, catalog is typically at /book/{id}/
            catalog_url = novel_url.rstrip('.htm').rstrip('.html') + '/'
            
            metadata = NovelMetadata(
                title=title,
                author=author,
                description=description,
                tags=tags,
                status=status,
                thumbnail_url=thumbnail_url,
                word_count=word_count,
                source_url=novel_url,
                catalog_url=catalog_url,
                source_website=self.website_name
            )
            
            print(f"Successfully fetched metadata for: {title}")
            return metadata
        
        finally:
            self._close_scraper()
    
    def fetch_chapter_list(self, catalog_url: str) -> List[ChapterListItem]:
        """
        Fetch complete chapter list from catalog page.
        
        Args:
            catalog_url: URL like https://www.69shuba.com/book/90548/
        """
        self._ensure_scraper()
        
        try:
            print(f"Fetching chapter list from: {catalog_url}")
            
            html_content = self.scraper.fetch_url(catalog_url)
            if not html_content:
                raise ValueError(f"Failed to fetch catalog page: {catalog_url}")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all chapter links
            # Adjust selector based on actual HTML structure
            chapter_links = soup.select('ul.mulu-list li a')
            
            chapters = []
            for link in chapter_links:
                try:
                    chapter_title = link.get_text(strip=True)
                    chapter_url = link.get('href')
                    
                    if not chapter_url:
                        continue
                    
                    # Convert to absolute URL
                    chapter_url = urljoin(self.BASE_URL, chapter_url)
                    
                    # Extract chapter number from title or URL
                    chapter_num = self._extract_chapter_number(chapter_title, chapter_url)
                    
                    if chapter_num is None:
                        continue
                    
                    chapter = ChapterListItem(
                        chapter_number=chapter_num,
                        title=chapter_title,
                        url=chapter_url
                    )
                    chapters.append(chapter)
                
                except Exception as e:
                    print(f"Error parsing chapter link: {e}")
                    continue
            
            # Sort by chapter number
            chapters.sort(key=lambda c: c.chapter_number)
            
            print(f"Found {len(chapters)} chapters")
            return chapters
        
        finally:
            self._close_scraper()
    
    def _extract_chapter_number(self, title: str, url: str) -> Optional[int]:
        """
        Extract chapter number from title or URL.
        
        Tries multiple patterns:
        - "第123章" in title
        - "Chapter 123" in title
        - Numeric patterns in title
        - Chapter ID from URL
        """
        # Try to find chapter number in title
        patterns = [
            r'第(\d+)章',  # Chinese: 第123章
            r'Chapter\s*(\d+)',  # English: Chapter 123
            r'^(\d+)',  # Starting with number
            r'(\d+)',  # Any number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        # Try to extract from URL (e.g., /txt/90548/12345678)
        url_match = re.search(r'/(\d+)\.html?$', url)
        if url_match:
            # This might be a chapter ID, not chapter number
            # For now, we'll use it as fallback
            try:
                return int(url_match.group(1))
            except ValueError:
                pass
        
        return None
