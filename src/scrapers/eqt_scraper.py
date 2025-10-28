"""
EQT Portfolio Scraper
Extracts current portfolio companies from EQT Group's website
Uses Playwright for JavaScript-rendered content
Clicks on each company to extract detailed information including website
"""

import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from typing import List, Dict, Optional
import re

async def extract_company_details(page, company_link: str) -> Dict[str, str]:
    """
    Navigate to company detail page and extract information
    
    Args:
        page: Playwright page object
        company_link: URL to the company detail page
    
    Returns:
        Dictionary with company details (website, description, etc.)
    """
    details = {}
    
    try:
        # Navigate to company page
        await page.goto(company_link, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        # Get all external links on the page
        all_links = await page.query_selector_all('a[href^="http"]')
        
        for link_element in all_links:
            try:
                href = await link_element.get_attribute('href')
                text = await link_element.inner_text()
                
                # Skip EQT's own links and common non-company domains
                skip_domains = ['eqtgroup.com', 'linkedin.com', 'twitter.com', 'facebook.com', 
                               'instagram.com', 'youtube.com', 'edge.media-server.com',
                               'mailto:', 'tel:']
                
                if href and not any(domain in href.lower() for domain in skip_domains):
                    # This is likely the company website
                    # Prioritize links with text like "website", "visit", or the first external link
                    if any(keyword in text.lower() for keyword in ['website', 'visit', 'home']):
                        details['website'] = href
                        break
                    elif not details.get('website'):
                        # Store first valid external link as fallback
                        details['website'] = href
            except:
                continue
        
        # Extract description from page text
        try:
            # Look for main content paragraphs
            paragraphs = await page.query_selector_all('p')
            for p in paragraphs:
                text = await p.inner_text()
                # Look for substantial paragraphs (likely description)
                if text and len(text) > 50 and len(text) < 500:
                    # Skip navigation/footer text
                    lower_text = text.lower()
                    if not any(skip in lower_text for skip in ['cookie', 'privacy', 'terms', 'all rights', '©']):
                        details['description'] = text.strip()
                        break
        except:
            pass
        
        # Extract sector/industry if shown on page
        try:
            # Look for sector badges or labels
            page_text = await page.inner_text('body')
            
            # Common patterns for sector info
            sector_patterns = [
                r'Sector[:\s]+([^\n]+)',
                r'Industry[:\s]+([^\n]+)',
                r'Segment[:\s]+([^\n]+)'
            ]
            
            for pattern in sector_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    sector = match.group(1).strip()
                    if len(sector) < 50:  # Reasonable length for a sector name
                        details['sector_detail'] = sector
                        break
        except:
            pass
        
    except Exception as e:
        print(f"      ⚠️  Could not extract details: {str(e)[:50]}")
    
    return details

async def scrape_eqt_portfolio(headless: bool = True, max_companies: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Scrape portfolio companies from EQT Group website
    
    Args:
        headless: Whether to run browser in headless mode
        max_companies: Maximum number of companies to scrape (None for all)
    
    Returns:
        List of portfolio companies with details
    """
    companies = []
    
    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        
        url = "https://eqtgroup.com/about/current-portfolio"
        print(f"📂 Navigating to: {url}")
        
        try:
            # Navigate to the page
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            print("⏳ Waiting for portfolio table to load...")
            
            # Wait for the table/grid to appear
            await page.wait_for_selector("table, [role='table'], .portfolio-grid", timeout=30000)
            
            # Give extra time for all content to load
            await asyncio.sleep(3)
            
            print("🔍 Extracting companies and their links...")
            
            # Find all company links first
            company_links = []
            
            # Try to find links to company detail pages
            # Look for rows that are clickable or contain links to company pages
            rows = await page.query_selector_all("table tr, [role='row']")
            
            if rows:
                print(f"   Found {len(rows)} rows, extracting company information...")
                
                for row in rows:
                    try:
                        # Look for a link in the row (usually first cell)
                        link = await row.query_selector('a[href*="/portfolio/"]')
                        if not link:
                            # Try finding any link in the row
                            link = await row.query_selector('a')
                        
                        if link:
                            href = await link.get_attribute('href')
                            company_name = await link.inner_text()
                            
                            if href and company_name:
                                # Make absolute URL
                                if href.startswith('/'):
                                    href = f"https://eqtgroup.com{href}"
                                
                                # Get other details from the row
                                cells = await row.query_selector_all("td, [role='cell']")
                                sector = ""
                                fund = ""
                                country = ""
                                year = ""
                                
                                if len(cells) >= 2:
                                    sector = await cells[1].inner_text() if len(cells) > 1 else ""
                                    fund = await cells[2].inner_text() if len(cells) > 2 else ""
                                    country = await cells[3].inner_text() if len(cells) > 3 else ""
                                    year = await cells[4].inner_text() if len(cells) > 4 else ""
                                
                                company_links.append({
                                    'name': company_name.strip(),
                                    'url': href,
                                    'industry': sector.strip(),
                                    'fund': fund.strip(),
                                    'country': country.strip(),
                                    'investment_year': year.strip(),
                                })
                    except Exception as e:
                        continue
            
            # If no links found in table, try alternative approach
            if not company_links:
                print("   No table links found, trying alternative selectors...")
                
                # Look for company cards or links
                links = await page.query_selector_all('a[href*="/portfolio/"], a[href*="/companies/"]')
                
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        company_name = await link.inner_text()
                        
                        if href and company_name and len(company_name.strip()) > 2:
                            if href.startswith('/'):
                                href = f"https://eqtgroup.com{href}"
                            
                            company_links.append({
                                'name': company_name.strip(),
                                'url': href,
                                'industry': '',
                                'fund': '',
                                'country': '',
                                'investment_year': '',
                            })
                    except:
                        continue
            
            print(f"✅ Found {len(company_links)} companies")
            
            # Limit if specified
            if max_companies:
                company_links = company_links[:max_companies]
                print(f"   Limiting to first {max_companies} companies for testing")
            
            # Now visit each company page to get details
            print(f"\n📄 Extracting details from company pages...")
            
            for i, company_info in enumerate(company_links, 1):
                print(f"   {i}/{len(company_links)}: {company_info['name']}")
                
                try:
                    # Get detailed information
                    details = await extract_company_details(page, company_info['url'])
                    
                    # Merge with basic info
                    full_info = {
                        'name': company_info['name'],
                        'pe_firm': 'EQT',
                        'status': 'Active',
                        'industry': company_info.get('industry', ''),
                        'fund': company_info.get('fund', ''),
                        'country': company_info.get('country', ''),
                        'investment_year': company_info.get('investment_year', ''),
                        **details  # Add website, description, etc.
                    }
                    
                    companies.append(full_info)
                    
                    if details.get('website'):
                        print(f"      ✓ Website: {details['website']}")
                    
                    # Small delay to be respectful
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Error: {str(e)[:50]}")
                    # Still add basic info even if details fail
                    companies.append({
                        'name': company_info['name'],
                        'pe_firm': 'EQT',
                        'status': 'Active',
                        'industry': company_info.get('industry', ''),
                        'fund': company_info.get('fund', ''),
                        'country': company_info.get('country', ''),
                        'investment_year': company_info.get('investment_year', ''),
                    })
            
            print(f"\n✅ Extracted {len(companies)} companies with details")
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
        
        finally:
            await browser.close()
    
    return companies

def deduplicate_companies(companies: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate companies, keeping first occurrence"""
    seen = set()
    unique = []
    
    for company in companies:
        key = f"{company['name'].lower()}_{company.get('fund', '')}"
        if key not in seen:
            seen.add(key)
            unique.append(company)
    
    return unique

async def main():
    """Main function"""
    import sys
    
    print("🏢 EQT Portfolio Scraper (with detailed company info)")
    print("=" * 60)
    
    # Check for test mode argument
    max_companies = None
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        max_companies = 5
        print("🧪 TEST MODE: Will scrape first 5 companies only\n")
    
    # Scrape the portfolio
    companies = await scrape_eqt_portfolio(headless=True, max_companies=max_companies)
    
    # Deduplicate
    companies = deduplicate_companies(companies)
    
    print(f"\n📊 Total unique companies: {len(companies)}")
    
    # Count companies with websites
    with_website = sum(1 for c in companies if c.get('website'))
    print(f"   Companies with website: {with_website}")
    print(f"   Companies with description: {sum(1 for c in companies if c.get('description'))}\n")
    
    # Save to file
    output_path = Path("data/raw/json/eqt_portfolio.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to: {output_path}\n")
    
    # Display sample
    if companies:
        print("📋 Sample Companies:")
        print("-" * 60)
        for i, company in enumerate(companies[:10], 1):
            sector_str = f" | {company.get('industry', 'N/A')}" if company.get('industry') else ""
            year_str = f" | {company.get('investment_year', 'N/A')}" if company.get('investment_year') else ""
            website_str = f"\n      🌐 {company.get('website')}" if company.get('website') else ""
            print(f"   {i:2d}. {company['name']}{sector_str}{year_str}{website_str}")
        
        if len(companies) > 10:
            print(f"   ... and {len(companies) - 10} more")
    
    print(f"\n✨ Done!")
    print("\nTip: Run with --test flag to scrape only 5 companies for testing:")
    print("     pipenv run python src/scrapers/eqt_scraper.py --test")

if __name__ == "__main__":
    asyncio.run(main())
