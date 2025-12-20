from abc import ABC, abstractmethod
from bs4 import BeautifulSoup, Tag
import re
from typing import Tuple, List, Optional
from urllib.parse import urljoin, urlparse

class ExtractionBackend(ABC):
    """
    Abstract base class for website-specific content extraction backends.
    Each backend handles parsing HTML content from a specific novel website.
    """
    
    @abstractmethod
    def get_next_chapter_url(self, html_content: str, current_url: Optional[str] = None) -> Optional[str]:
        """
        Extract the URL for the next chapter from the given HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for resolving relative URLs
            
        Returns:
            str or None: The URL of the next chapter, or None if not found
        """
        pass
    
    @abstractmethod
    def get_chapter_number(self, html_content: str, current_url: Optional[str] = None) -> Optional[str]:
        """
        Extract the chapter number from the given HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for URL-based extraction fallback
            
        Returns:
            str or None: The chapter number as a string, or None if not found
        """
        pass
    
    @abstractmethod
    def extract_novel_content(self, html_content: str) -> Tuple[str, List[str]]:
        """
        Extract the title and novel text paragraphs from the given HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            
        Returns:
            tuple: A tuple containing (title, paragraphs_list)
        """
        pass
    
    def extract_all_content(self, html_content: str, current_url: Optional[str] = None) -> Tuple[str, List[str], Optional[str], Optional[str]]:
        """
        Extract all content from the HTML: title, paragraphs, next URL, and chapter number.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for resolving relative URLs
            
        Returns:
            tuple: A tuple containing (title, paragraphs_list, next_chapter_url, chapter_number)
        """
        title, paragraphs = self.extract_novel_content(html_content)
        next_url = self.get_next_chapter_url(html_content, current_url)
        chapter_number = self.get_chapter_number(html_content, current_url)
        
        return title, paragraphs, next_url, chapter_number


class EB69Shu(ExtractionBackend):
    """
    Extraction backend for 69shu.com and similar websites.
    Handles the specific HTML structure used by these novel sites.
    """
    
    def get_next_chapter_url(self, html_content: str, current_url: Optional[str] = None) -> Optional[str]:
        """
        Extracts the URL for the next chapter from 69shu HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for resolving relative URLs
            
        Returns:
            str or None: The URL of the next chapter, or None if not found
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the 'div' with class 'page1' which contains navigation links
        page_navigation_div = soup.find('div', class_='page1')

        if page_navigation_div and isinstance(page_navigation_div, Tag):
            # Look for an 'a' tag within this div that has the text "下一章" (Next Chapter)
            # Note: '下一章' is the Chinese text for "Next Chapter"
            next_chapter_link = page_navigation_div.find('a', string="下一章")
            
            if next_chapter_link and isinstance(next_chapter_link, Tag) and next_chapter_link.get('href'):
                href = next_chapter_link.get('href')
                # Convert relative URLs to absolute URLs if current_url is provided
                if current_url and href:
                    return urljoin(current_url, str(href))
                return str(href) if href else None
        
        return None  # Return None if the next chapter link is not found

    def get_chapter_number(self, html_content: str, current_url: Optional[str] = None) -> Optional[str]:
        """
        Extracts the chapter number from 69shu HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for URL-based extraction fallback
            
        Returns:
            str or None: The chapter number as a string, or None if not found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        chapter_number = None

        # Try to find chapter number in <h1> tag within div.txtnav
        txtnav_div = soup.find('div', class_='txtnav')
        if txtnav_div and isinstance(txtnav_div, Tag):
            h1_tag = txtnav_div.find('h1')
            if h1_tag and isinstance(h1_tag, Tag) and h1_tag.string:
                # Regex to find "第<number>章"
                match = re.search(r'第(\d+)章', str(h1_tag.string))
                if match:
                    chapter_number = match.group(1)

        # If not found in <h1>, try to find in <title> tag
        if not chapter_number and soup.title and soup.title.string:
            match = re.search(r'第(\d+)章', str(soup.title.string))
            if match:
                chapter_number = match.group(1)
                
        # Fallback: try to find a pattern like "Chapter <number>" or "第<number>话" etc.
        if not chapter_number:
            # Attempt to find chapter number in h1 tag within div.txtnav if specific pattern failed
            if txtnav_div and isinstance(txtnav_div, Tag):
                h1_tag = txtnav_div.find('h1')
                if h1_tag and isinstance(h1_tag, Tag) and h1_tag.string:
                    # Regex for "第" followed by digits, then "章" or "话" or space or end of string
                    match = re.search(r'第\s*(\d+)\s*章|第\s*(\d+)\s*话|Chapter\s*(\d+)|第\s*(\d+)', str(h1_tag.string), re.IGNORECASE)
                    if match:
                        # match.groups() will return a tuple like (None, '5', None, None)
                        # We need to find the first non-None group
                        chapter_number = next((g for g in match.groups() if g is not None), None)

            # If still not found, try in <title> tag with the more generic regex
            if not chapter_number and soup.title and soup.title.string:
                match = re.search(r'第\s*(\d+)\s*章|第\s*(\d+)\s*话|Chapter\s*(\d+)|第\s*(\d+)', str(soup.title.string), re.IGNORECASE)
                if match:
                    chapter_number = next((g for g in match.groups() if g is not None), None)
        
        # URL-based fallback extraction if HTML parsing failed
        if not chapter_number and current_url:
            chapter_number = self._extract_chapter_from_url(current_url)
                    
        return chapter_number
    
    def _extract_chapter_from_url(self, url: str) -> Optional[str]:
        """
        Extract chapter number from URL as fallback.
        Common patterns: /chapter-123.html, /123.html, /chap123/, etc.
        """
        # Common URL patterns for chapter numbers
        patterns = [
            r'/(?:chapter|chap|ch)[-_]?(\d+)',  # /chapter-123, /chap123, /ch_123
            r'/(\d+)\.html?$',                 # /123.html
            r'/(\d+)/?$',                      # /123/
            r'chapter=(\d+)',                  # ?chapter=123
            r'ch=(\d+)',                       # ?ch=123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def extract_novel_content(self, html_content: str) -> Tuple[str, List[str]]:
        """
        Extracts the title and novel text paragraphs from 69shu HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            
        Returns:
            tuple: A tuple containing (title, paragraphs_list)
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract the title from the <title> tag in the <head> section
        page_title = soup.title.string.strip() if soup.title and soup.title.string else "No Title Found"

        # Extract the novel text paragraphs
        novel_text_container = soup.find('div', class_='txtnav')
        final_paragraphs = []

        if novel_text_container and isinstance(novel_text_container, Tag):
            # Get the chapter title from the <h1> tag inside 'txtnav' to remove potential duplication in text
            chapter_title_in_h1 = ""
            h1_tag = novel_text_container.find('h1')
            if h1_tag and isinstance(h1_tag, Tag):
                chapter_title_in_h1 = h1_tag.get_text(strip=True)

            # Remove advertisement, info, and navigation divs before extracting text
            for div_id in ['txtright', 'baocuo', 'tuijian']:
                div_to_remove = novel_text_container.find('div', id=div_id)
                if div_to_remove and isinstance(div_to_remove, Tag):
                    div_to_remove.extract()
            for div_class in ['bottom-ad', 'contentadv', 'txtinfo', 'page1']:
                for div_to_remove in novel_text_container.find_all('div', class_=div_class):
                    if isinstance(div_to_remove, Tag):
                        div_to_remove.extract()
            
            # Extract the entire text content from the cleaned novel_text_container
            # We need to preserve <br> tags as they indicate line/paragraph breaks.
            # Get the inner HTML of the container after removing unwanted elements.
            raw_text_html = str(novel_text_container)

            # Clean up specific HTML entities (like &emsp;)
            raw_text_html = raw_text_html.replace('&emsp;', '')
            
            # Replace <br> tags with a unique temporary placeholder for easier processing later
            # Use regex to catch variations like <br/>, <br > etc.
            raw_text_html = re.sub(r'<br\s*?/?>', '__BR__', raw_text_html)

            # Now, parse this modified HTML snippet to get the text content.
            # BeautifulSoup's get_text() with a separator helps here.
            cleaned_text = BeautifulSoup(raw_text_html, 'html.parser').get_text(separator='').strip()
            
            # Replace sequences of two or more '__BR__' with a standardized paragraph break (\n\n)
            # This treats `<br><br>` (or more) as a new paragraph.
            cleaned_text = cleaned_text.replace('__BR____BR__', '\n\n')
            # Remove single '__BR__' which typically represent line breaks within a paragraph, not new paragraphs.
            cleaned_text = cleaned_text.replace('__BR__', '').strip()
            
            # Remove the duplicated chapter title from the beginning of the text content if it exists
            if chapter_title_in_h1 and cleaned_text.startswith(chapter_title_in_h1):
                cleaned_text = cleaned_text[len(chapter_title_in_h1):].strip()

            # Normalize any remaining sequences of multiple newlines into a single paragraph break
            cleaned_text = re.sub(r'\n{2,}', '\n\n', cleaned_text).strip()
            
            # Split the cleaned text into paragraphs based on the double newline separator
            final_paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]

        return page_title, final_paragraphs


class EB1QXS(ExtractionBackend):
    """
    Extraction backend for 1qxs.com (一七小说) website.
    Handles the specific HTML structure used by this novel site.
    """
    
    def get_next_chapter_url(self, html_content: str, current_url: Optional[str] = None) -> Optional[str]:
        """
        Extracts the URL for the next chapter from 1qxs HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for resolving relative URLs
            
        Returns:
            str or None: The URL of the next chapter, or None if not found
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # First try to find the next page link in the page navigation div
        page_div = soup.find('div', class_='page')
        if page_div and isinstance(page_div, Tag):
            next_link = page_div.find('a', id='next')
            if next_link and isinstance(next_link, Tag) and next_link.get('href'):
                href = next_link.get('href')
                # Convert relative URLs to absolute URLs if current_url is provided
                if current_url and href:
                    return urljoin(current_url, str(href))
                return str(href) if href else None
        
        # Fallback: try to find in footer navigation
        footer_div = soup.find('div', class_='footer')
        if footer_div and isinstance(footer_div, Tag):
            next_div = footer_div.find('div', class_='next')
            if next_div and isinstance(next_div, Tag):
                next_link = next_div.find('a')
                if next_link and isinstance(next_link, Tag) and next_link.get('href'):
                    href = next_link.get('href')
                    # Convert relative URLs to absolute URLs if current_url is provided
                    if current_url and href:
                        return urljoin(current_url, str(href))
                    return str(href) if href else None
        
        return None  # Return None if the next chapter link is not found

    def get_chapter_number(self, html_content: str, current_url: Optional[str] = None) -> Optional[str]:
        """
        Extracts the chapter number from 1qxs HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for URL-based extraction fallback
            
        Returns:
            str or None: The chapter number as a string, or None if not found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        chapter_number = None

        # Try to find chapter number in <h1> tag within div.title
        title_div = soup.find('div', class_='title')
        if title_div and isinstance(title_div, Tag):
            h1_tag = title_div.find('h1')
            if h1_tag and isinstance(h1_tag, Tag) and h1_tag.string:
                # Pattern for "1：尸解转生，重头再来(1/3)" - extract the first number
                match = re.search(r'^(\d+)：', str(h1_tag.string))
                if match:
                    chapter_number = match.group(1)

        # If not found in <h1>, try to find in <title> tag
        if not chapter_number and soup.title and soup.title.string:
            # Pattern for "1：尸解转生，重头再来 - 剑出仙山小说 - 一七小说"
            match = re.search(r'^(\d+)：', str(soup.title.string))
            if match:
                chapter_number = match.group(1)
                
        # Fallback: try to find other chapter number patterns
        if not chapter_number:
            # Try in title again with different patterns
            if soup.title and soup.title.string:
                # Try patterns like "第X章", "Chapter X", etc.
                match = re.search(r'第\s*(\d+)\s*章|第\s*(\d+)\s*话|Chapter\s*(\d+)', str(soup.title.string), re.IGNORECASE)
                if match:
                    chapter_number = next((g for g in match.groups() if g is not None), None)
        
        # URL-based fallback extraction if HTML parsing failed
        if not chapter_number and current_url:
            chapter_number = self._extract_chapter_from_url(current_url)
                    
        return chapter_number
    
    def _extract_chapter_from_url(self, url: str) -> Optional[str]:
        """
        Extract chapter number from URL as fallback.
        For 1qxs.com: 
        - https://www.1qxs.com/xs/88547/2.html -> chapter "2"
        - https://www.1qxs.com/xs/88547/2/3.html -> chapter "2" (all parts go to same chapter file)
        """
        # Specific pattern for 1qxs.com URLs with parts: /xs/ID/CHAPTER/PART.html
        match = re.search(r'/xs/\d+/(\d+)/(\d+)\.html?$', url)
        if match:
            chapter_num = match.group(1)
            # Return only the chapter number, ignore part number for file naming
            return chapter_num  # e.g., "2" for chapter 2, any part
        
        # Specific pattern for 1qxs.com URLs without parts: /xs/ID/CHAPTER.html
        match = re.search(r'/xs/\d+/(\d+)\.html?$', url)
        if match:
            return match.group(1)  # e.g., "2" for chapter 2, part 1
        
        # General fallback patterns
        patterns = [
            r'/(?:chapter|chap|ch)[-_]?(\d+)',  # /chapter-123, /chap123, /ch_123
            r'/(\d+)\.html?$',                 # /123.html
            r'/(\d+)/?$',                      # /123/
            r'chapter=(\d+)',                  # ?chapter=123
            r'ch=(\d+)',                       # ?ch=123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def extract_novel_content(self, html_content: str) -> Tuple[str, List[str]]:
        """
        Extracts the title and novel text paragraphs from 1qxs HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            
        Returns:
            tuple: A tuple containing (title, paragraphs_list)
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract the title from the <title> tag in the <head> section
        page_title = soup.title.string.strip() if soup.title and soup.title.string else "No Title Found"

        # Extract the novel text paragraphs from div.content
        content_div = soup.find('div', class_='content')
        final_paragraphs = []

        if content_div and isinstance(content_div, Tag):
            # Extract all paragraph tags
            paragraph_tags = content_div.find_all('p')
            
            for p_tag in paragraph_tags:
                if p_tag and isinstance(p_tag, Tag):
                    paragraph_text = p_tag.get_text(strip=True)
                    # Skip empty paragraphs and common footer text
                    if (paragraph_text and 
                        not paragraph_text.startswith('【剑出仙山】小说免费阅读') and
                        not paragraph_text.startswith('本章未完，点击')):
                        # Clean up the paragraph text
                        # Remove excessive whitespace characters like &nbsp;
                        cleaned_paragraph = re.sub(r'\s+', ' ', paragraph_text).strip()
                        if cleaned_paragraph:
                            final_paragraphs.append(cleaned_paragraph)

        return page_title, final_paragraphs


class EBNovel543(ExtractionBackend):
    """
    Extraction backend for novel543.com website.
    Handles the specific HTML structure used by this novel site.
    
    URL patterns:
    - Chapter: /{novel_id}/{prefix}_{chapter}.html (e.g., /0624601529/8096_1.html)
    - Multi-part: /{novel_id}/{prefix}_{chapter}_{part}.html (e.g., /0624601529/8096_1_2.html)
    - TOC: /{novel_id}/dir
    """
    
    def get_next_chapter_url(self, html_content: str, current_url: Optional[str] = None) -> Optional[str]:
        """
        Extracts the URL for the next chapter from novel543 HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for resolving relative URLs
            
        Returns:
            str or None: The URL of the next chapter, or None if not found
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the navigation link with text "下一章" (Next Chapter)
        # The navigation is in a generic div containing links for 上一章, 目錄, 下一章
        next_chapter_link = soup.find('a', string="下一章")
        
        if next_chapter_link and isinstance(next_chapter_link, Tag) and next_chapter_link.get('href'):
            href = next_chapter_link.get('href')
            
            # Check if this is a "no next chapter" link (links back to the same page)
            if current_url and href:
                # Parse current URL to compare
                current_path = urlparse(current_url).path
                href_path = str(href)
                
                # If next chapter links to the same page, there's no next chapter
                if current_path == href_path:
                    return None
            
            # Convert relative URLs to absolute URLs if current_url is provided
            if current_url and href:
                return urljoin(current_url, str(href))
            return str(href) if href else None
        
        return None  # Return None if the next chapter link is not found

    def get_chapter_number(self, html_content: str, current_url: Optional[str] = None) -> Optional[str]:
        """
        Extracts the chapter number from novel543 HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            current_url (str, optional): The current page URL for URL-based extraction fallback
            
        Returns:
            str or None: The chapter number as a string, or None if not found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        chapter_number = None

        # Try to find chapter number in <h1> tag
        # Format: "第1章 青梅竹馬是未來女帝？ (1/2)"
        h1_tag = soup.find('h1')
        if h1_tag and isinstance(h1_tag, Tag):
            h1_text = h1_tag.get_text(strip=True)
            # Pattern for "第X章"
            match = re.search(r'第(\d+)章', h1_text)
            if match:
                chapter_number = match.group(1)

        # If not found in <h1>, try to find in <title> tag
        if not chapter_number and soup.title and soup.title.string:
            match = re.search(r'第(\d+)章', str(soup.title.string))
            if match:
                chapter_number = match.group(1)
                
        # Fallback: try other common chapter patterns
        if not chapter_number:
            if h1_tag and isinstance(h1_tag, Tag):
                h1_text = h1_tag.get_text(strip=True)
                # Try patterns like "Chapter X", "第X话", etc.
                match = re.search(r'第\s*(\d+)\s*章|第\s*(\d+)\s*话|Chapter\s*(\d+)', h1_text, re.IGNORECASE)
                if match:
                    chapter_number = next((g for g in match.groups() if g is not None), None)

            if not chapter_number and soup.title and soup.title.string:
                match = re.search(r'第\s*(\d+)\s*章|第\s*(\d+)\s*话|Chapter\s*(\d+)', str(soup.title.string), re.IGNORECASE)
                if match:
                    chapter_number = next((g for g in match.groups() if g is not None), None)
        
        # URL-based fallback extraction if HTML parsing failed
        if not chapter_number and current_url:
            chapter_number = self._extract_chapter_from_url(current_url)
                    
        return chapter_number
    
    def _extract_chapter_from_url(self, url: str) -> Optional[str]:
        """
        Extract chapter number from URL as fallback.
        
        For novel543.com:
        - https://www.novel543.com/0624601529/8096_1.html -> chapter "1"
        - https://www.novel543.com/0624601529/8096_1_2.html -> chapter "1" (part 2)
        - https://www.novel543.com/0624601529/8096_123.html -> chapter "123"
        """
        # Specific pattern for novel543.com URLs: /novel_id/prefix_chapter.html or /novel_id/prefix_chapter_part.html
        # Match pattern like /8096_123.html or /8096_123_2.html
        match = re.search(r'/\d+_(\d+)(?:_\d+)?\.html?$', url)
        if match:
            return match.group(1)
        
        # General fallback patterns
        patterns = [
            r'/(?:chapter|chap|ch)[-_]?(\d+)',  # /chapter-123, /chap123, /ch_123
            r'/(\d+)\.html?$',                 # /123.html
            r'/(\d+)/?$',                      # /123/
            r'chapter=(\d+)',                  # ?chapter=123
            r'ch=(\d+)',                       # ?ch=123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def extract_novel_content(self, html_content: str) -> Tuple[str, List[str]]:
        """
        Extracts the title and novel text paragraphs from novel543 HTML content.
        
        Args:
            html_content (str): The HTML content of the novel chapter page
            
        Returns:
            tuple: A tuple containing (title, paragraphs_list)
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract the title from the <title> tag in the <head> section
        page_title = soup.title.string.strip() if soup.title and soup.title.string else "No Title Found"

        # Get the chapter title from h1 if available (for deduplication)
        chapter_title_in_h1 = ""
        h1_tag = soup.find('h1')
        if h1_tag and isinstance(h1_tag, Tag):
            chapter_title_in_h1 = h1_tag.get_text(strip=True)

        final_paragraphs = []
        
        # Find all paragraph tags in the document
        # novel543.com uses <p> tags for content, typically within a container div
        # We need to find the content area which contains the h1 and paragraphs
        
        # First, try to find the content container (the div that contains h1 and paragraphs)
        content_container = None
        if h1_tag:
            # The content is typically in the parent or sibling of h1
            content_container = h1_tag.find_parent()
        
        if content_container and isinstance(content_container, Tag):
            paragraph_tags = content_container.find_all('p')
        else:
            # Fallback: get all p tags from body
            paragraph_tags = soup.find_all('p')
        
        # Common footer/advertisement text patterns to skip
        skip_patterns = [
            '溫馨提示',
            '温馨提示',
            '登錄用戶',
            '登录用户',
            '站內信',
            '站内信',
            '本章未完',
            '點擊下一頁',
            '点击下一页',
            'VIP會員',
            'VIP会员',
            '免廣告',
            '免广告',
            '應廣大讀者',
            '应广大读者',
        ]
        
        for p_tag in paragraph_tags:
            if p_tag and isinstance(p_tag, Tag):
                paragraph_text = p_tag.get_text(strip=True)
                
                # Skip empty paragraphs
                if not paragraph_text:
                    continue
                
                # Skip paragraphs that contain advertisement/footer text
                should_skip = False
                for pattern in skip_patterns:
                    if pattern in paragraph_text:
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                # Clean up the paragraph text
                # Remove excessive whitespace characters
                cleaned_paragraph = re.sub(r'\s+', ' ', paragraph_text).strip()
                
                if cleaned_paragraph:
                    final_paragraphs.append(cleaned_paragraph)

        return page_title, final_paragraphs