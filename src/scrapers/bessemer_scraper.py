"""
Bessemer Venture Partners Portfolio Scraper
URL: https://www.bvp.com/companies#portfolio
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import asyncio
from playwright.async_api import async_playwright
from src.utils.logger import log_info, log_success, log_error, log_warning, log_header
from src.scrapers.website_extractor import extract_company_website
from datetime import datetime
import json

OUTPUT_FILE = "data/raw/json/bessemer_portfolio.json"


async def scrape_bessemer_portfolio():
    """
    Scrape Bessemer Venture Partners portfolio with real websites
    Two-pass approach:
    1. Extract all company links from main page
    2. Visit each detail page to extract real website
    """
    url = "https://www.bvp.com/companies#portfolio"
    all_companies = []
    
    async with async_playwright() as p:
        log_header("BESSEMER VENTURE PARTNERS PORTFOLIO SCRAPER")
        log_info("🚀 Starting Bessemer scraper...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # PASS 1: Extract all company links
            log_info(f"� Loading {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Handle cookie consent
            try:
                cookie_button = await page.query_selector('button:has-text("Accept")')
                if cookie_button:
                    await cookie_button.click()
                    await page.wait_for_timeout(1000)
                    log_info("   ✓ Accepted cookies")
            except:
                pass
            
            # Scroll to load all companies
            log_info("📜 Scrolling to load all companies...")
            for i in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
            
            # Extract company links
            log_info("🔍 Extracting company links...")
            company_links = await page.query_selector_all('a[href*="/companies/"]')
            log_info(f"✓ Found {len(company_links)} company links")
            
            # Build list of unique companies with their detail URLs
            seen = set()
            company_data_list = []
            
            for link in company_links:
                try:
                    company_name = (await link.inner_text()).strip()
                    href = await link.get_attribute('href')
                    
                    if not company_name or not href:
                        continue
                    
                    # Skip status labels
                    if company_name in ['ACTIVE', 'EXITED', 'IPO', 'ACQUIRED']:
                        continue
                    
                    # Skip tickers
                    if company_name.startswith('NASDAQ:') or company_name.startswith('NYSE:'):
                        continue
                    
                    # Avoid duplicates
                    if company_name.lower() in seen:
                        continue
                    
                    seen.add(company_name.lower())
                    
                    # Build full URL
                    detail_url = href if href.startswith('http') else f"https://www.bvp.com{href}"
                    
                    company_data_list.append({
                        'name': company_name,
                        'detail_url': detail_url
                    })
                    
                except Exception as e:
                    continue
            
            log_success(f"✅ Found {len(company_data_list)} unique companies")
            
            # PASS 2: Visit each detail page to extract website
            log_info(f"\n🌐 Extracting websites from detail pages...")
            log_info(f"   This will take ~{len(company_data_list) * 0.25:.0f} seconds...")
            
            for idx, company_data in enumerate(company_data_list, 1):
                try:
                    log_info(f"\n[{idx}/{len(company_data_list)}] {company_data['name']}")
                    log_info(f"   🔗 Visiting: {company_data['detail_url']}")
                    
                    # Navigate to detail page
                    await page.goto(company_data['detail_url'], wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(1000)
                    
                    # Extract website from the page
                    website = await extract_company_website(page, skip_domains=['bvp.com'])
                    
                    if website:
                        company_data['website'] = website
                        log_success(f"   ✅ Website: {website}")
                    else:
                        company_data['website'] = None
                        log_warning(f"   ⚠️  No website found")
                    
                    # Add metadata
                    company_data['raw_status'] = 'Current'  # Bessemer doesn't distinguish clearly
                    company_data['source_url'] = url
                    company_data['last_scraped'] = datetime.now()
                    
                    all_companies.append(company_data)
                    
                    # Progress indicator every 100 companies
                    if idx % 100 == 0:
                        log_info(f"   Processed {idx} companies...")
                    
                except Exception as e:
                    log_error(f"   ✗ Error processing {company_data['name']}: {str(e)}")
                    continue
            
            log_success(f"\n✅ Successfully extracted {len(all_companies)} companies")
            
        except Exception as e:
            log_error(f"❌ Error during scraping: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
    
    return all_companies


def save_to_json(companies):
    """Save companies to JSON file"""
    log_info(f"💾 Saving {len(companies)} companies to {OUTPUT_FILE}...")
    
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, ensure_ascii=False, default=str)
    
    log_success(f"✅ Saved successfully to {OUTPUT_FILE}")
    log_info(f"   📊 Total companies: {len(companies)}")


async def main():
    companies = await scrape_bessemer_portfolio()
    if companies:
        save_to_json(companies)
    else:
        log_warning("⚠️ No companies found to save")


if __name__ == "__main__":
    asyncio.run(main())

