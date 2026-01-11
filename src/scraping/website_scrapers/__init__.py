"""
Website Scraper Abstraction Layer

This module provides base classes and data structures for scraping novel websites.
Each website should implement the WebsiteScraper interface to provide consistent
access to novel listings, metadata, and chapter information.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NovelListItem:
    """Minimal information for a novel from listing pages"""
    title: str
    url: str
    source_website: str


@dataclass
class NovelMetadata:
    """Detailed metadata for a novel"""
    title: str
    author: Optional[str]
    description: Optional[str]
    tags: List[str]
    status: Optional[str]  # "ongoing" or "completed"
    thumbnail_url: Optional[str]
    word_count: Optional[str]
    source_url: str
    catalog_url: str
    source_website: str


@dataclass
class ChapterListItem:
    """Chapter information from catalog"""
    chapter_number: int
    title: str
    url: str


class WebsiteScraper(ABC):
    """Base class for website-specific scrapers"""
    
    @property
    @abstractmethod
    def website_name(self) -> str:
        """Return identifier for this website (e.g., '69shuba')"""
        pass
    
    @abstractmethod
    def fetch_all_novels(
        self, 
        max_pages: Optional[int] = None, 
        start_page: int = 1, 
        save_callback=None,
        listing_type: str = 'all',
        category_id: Optional[int] = None
    ) -> int:
        """
        Fetch list of all novels from the website.
        
        Args:
            max_pages: Optional limit on number of pages to scrape (for testing)
            start_page: Page number to start from (default: 1)
            save_callback: Optional callback function(novels_batch) to save novels
                          incrementally after each page is fetched
            listing_type: Type of listing to fetch (implementation-specific)
            category_id: Category/genre ID (implementation-specific)
            
        Returns:
            Total number of novels found
        """
        pass
    
    @abstractmethod
    def fetch_novel_metadata(self, novel_url: str) -> NovelMetadata:
        """
        Fetch detailed metadata for a specific novel.
        
        Args:
            novel_url: URL to the novel's detail page
            
        Returns:
            NovelMetadata object with all available information
        """
        pass
    
    @abstractmethod
    def fetch_chapter_list(self, catalog_url: str) -> List[ChapterListItem]:
        """
        Fetch complete chapter list for a novel.
        
        Args:
            catalog_url: URL to the novel's chapter catalog/table of contents
            
        Returns:
            List of ChapterListItem objects sorted by chapter number
        """
        pass


# Registry of available scrapers
_SCRAPER_REGISTRY: Dict[str, type] = {}


def register_scraper(website_name: str):
    """Decorator to register a scraper implementation"""
    def decorator(cls):
        _SCRAPER_REGISTRY[website_name] = cls
        return cls
    return decorator


def get_scraper(website_name: str) -> WebsiteScraper:
    """
    Get a scraper instance for the specified website.
    
    Args:
        website_name: Identifier for the website (e.g., '69shuba')
        
    Returns:
        Instance of the appropriate WebsiteScraper subclass
        
    Raises:
        ValueError: If website_name is not registered
    """
    if website_name not in _SCRAPER_REGISTRY:
        raise ValueError(
            f"No scraper registered for '{website_name}'. "
            f"Available: {list(_SCRAPER_REGISTRY.keys())}"
        )
    
    return _SCRAPER_REGISTRY[website_name]()


__all__ = [
    'NovelListItem',
    'NovelMetadata',
    'ChapterListItem',
    'WebsiteScraper',
    'register_scraper',
    'get_scraper',
]

# Import scraper implementations to trigger registration
from scraping.website_scrapers import shuba69_scraper
