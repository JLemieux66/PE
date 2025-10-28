"""
Website Extractor - Helper functions for extracting company websites from PE firm pages
"""

import re


async def extract_company_website(page, skip_domains=None):
    """
    Extract company website from a page by finding external links
    
    Args:
        page: Playwright page object
        skip_domains: List of domains to skip (PE firm domains, social media, etc.)
    
    Returns:
        str: Company website URL or None
    """
    if skip_domains is None:
        skip_domains = []
    
    # Default domains to always skip
    default_skip = [
        'linkedin.com',
        'twitter.com',
        'x.com',
        'facebook.com',
        'instagram.com',
        'youtube.com',
        'edge.media-server.com',
        'javascript:',
        'mailto:',
    ]
    
    all_skip_domains = default_skip + skip_domains
    
    try:
        # Get all links on the page
        links = await page.query_selector_all('a[href]')
        
        # Priority list: look for links with these keywords first
        priority_keywords = ['website', 'visit', 'home', 'company site', 'official']
        
        # First pass: check for priority links
        for link in links:
            href = await link.get_attribute('href')
            if not href or not href.startswith('http'):
                continue
            
            # Check if should skip
            if any(domain in href.lower() for domain in all_skip_domains):
                continue
            
            # Check link text for priority keywords
            link_text = (await link.inner_text()).lower()
            if any(keyword in link_text for keyword in priority_keywords):
                return href
        
        # Second pass: just find first valid external link
        for link in links:
            href = await link.get_attribute('href')
            if not href or not href.startswith('http'):
                continue
            
            # Check if should skip
            if any(domain in href.lower() for domain in all_skip_domains):
                continue
            
            return href
        
        return None
        
    except Exception as e:
        print(f"      ⚠️  Error extracting website: {e}")
        return None


async def extract_company_description(page, selector=None):
    """
    Extract company description from a page
    
    Args:
        page: Playwright page object
        selector: CSS selector for description element (optional)
    
    Returns:
        str: Company description or None
    """
    try:
        if selector:
            # Use provided selector
            desc_element = await page.query_selector(selector)
            if desc_element:
                return (await desc_element.inner_text()).strip()
        
        # Try common description selectors
        common_selectors = [
            'p',  # First paragraph
            '.description',
            '.about',
            '.company-description',
            '[class*="description"]',
            '[class*="about"]',
        ]
        
        for sel in common_selectors:
            elements = await page.query_selector_all(sel)
            for element in elements:
                text = (await element.inner_text()).strip()
                # Look for substantial paragraphs (50-500 chars)
                if 50 <= len(text) <= 500:
                    return text
        
        return None
        
    except Exception as e:
        print(f"      ⚠️  Error extracting description: {e}")
        return None


def clean_url(url):
    """Clean and normalize URL"""
    if not url:
        return None
    
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Ensure http/https
    if not url.startswith('http'):
        url = 'https://' + url
    
    return url
