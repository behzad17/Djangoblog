"""
Content utilities for reading time calculation and TOC generation.

This module provides lightweight functions for:
- Calculating reading time from HTML/text content
- Extracting headings and generating table of contents
- Adding anchor IDs to headings for smooth scrolling
"""
import re
from django.utils.text import slugify


def compute_reading_time(content_html):
    """
    Calculate reading time in minutes from HTML content.
    
    Args:
        content_html: HTML string containing the post content
        
    Returns:
        int: Reading time in minutes (minimum 1)
    """
    if not content_html:
        return 1
    
    # Strip HTML tags to get plain text
    # Simple regex to remove HTML tags (safe for sanitized content)
    text = re.sub(r'<[^>]+>', ' ', content_html)
    
    # Remove extra whitespace and split into words
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split by whitespace (works for both Persian and English)
    words = text.split()
    word_count = len(words)
    
    # Calculate reading time: ~200 words per minute
    # Minimum 1 minute
    reading_time = max(1, round(word_count / 200))
    
    return reading_time


def build_toc_and_anchors(content_html):
    """
    Extract headings from HTML and generate TOC with anchor IDs.
    
    Args:
        content_html: HTML string containing the post content
        
    Returns:
        tuple: (toc_items, updated_html)
            - toc_items: List of dicts with {level: int, title: str, anchor: str}
            - updated_html: HTML with anchor IDs added to headings
    """
    if not content_html:
        return [], content_html
    
    toc_items = []
    updated_html = content_html
    heading_counter = {}
    
    # Pattern to match h2 and h3 tags
    # Match: <h2>Title</h2> or <h3>Title</h3>
    pattern = r'<(h[23])[^>]*>(.*?)</\1>'
    
    def replace_heading(match):
        """Replace heading with version that includes anchor ID."""
        tag = match.group(1)  # h2 or h3
        title = match.group(2).strip()
        
        # Remove any HTML inside the heading title (keep only text)
        title_text = re.sub(r'<[^>]+>', '', title)
        
        if not title_text:
            return match.group(0)  # Return original if no text
        
        # Generate unique anchor ID
        base_slug = slugify(title_text, allow_unicode=True)
        if not base_slug:
            base_slug = 'section'
        
        # Ensure uniqueness
        if base_slug in heading_counter:
            heading_counter[base_slug] += 1
            anchor = f"{base_slug}-{heading_counter[base_slug]}"
        else:
            heading_counter[base_slug] = 0
            anchor = base_slug
        
        # Extract level (2 or 3)
        level = int(tag[1])
        
        # Add to TOC
        toc_items.append({
            'level': level,
            'title': title_text,
            'anchor': anchor
        })
        
        # Return heading with anchor ID
        # Preserve any existing attributes in the opening tag
        opening_tag = match.group(0)[:match.start(2) - len(match.group(2))]
        if 'id=' in opening_tag:
            # If ID already exists, replace it
            opening_tag = re.sub(r'id="[^"]*"', f'id="{anchor}"', opening_tag)
        else:
            # Add ID attribute
            opening_tag = opening_tag.replace(f'<{tag}', f'<{tag} id="{anchor}"')
        
        return f'{opening_tag}{title}</{tag}>'
    
    # Process all headings
    updated_html = re.sub(pattern, replace_heading, updated_html, flags=re.IGNORECASE | re.DOTALL)
    
    return toc_items, updated_html


def should_show_toc(content_html, toc_items, min_headings=3, min_words=600):
    """
    Determine if TOC should be displayed.
    
    Args:
        content_html: HTML string containing the post content
        toc_items: List of TOC items
        min_headings: Minimum number of headings required
        min_words: Minimum word count required (if headings < min_headings)
        
    Returns:
        bool: True if TOC should be shown
    """
    # Must have at least some headings
    if len(toc_items) < min_headings:
        # Check word count as alternative
        text = re.sub(r'<[^>]+>', ' ', content_html)
        text = re.sub(r'\s+', ' ', text).strip()
        word_count = len(text.split())
        
        # Show TOC if content is long enough even with fewer headings
        if word_count < min_words:
            return False
    
    return True

