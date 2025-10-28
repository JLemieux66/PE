"""
Scraper for Advent International portfolio companies
Website: https://www.adventinternational.com/investments/

Structure:
- 429 companies across ~43 pages (10 per page)
- article elements where first article[0] is filters (skip it)
- Companies start at articles[1]
- Each company has h3 with name
- Each has a link with text "Visit Company Website"
"""
import asyncio
from playwright.async_api import async_playwright
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.logger import log_info, log_success, log_error, log_warning, log_header
import json

OUTPUT_FILE = "data/raw/json/advent_portfolio.json"


async def scrape_advent_portfolio():
    """
    Scrape Advent International's portfolio
    
    429 companies across ~43 pages (10 per page)
    Direct extraction of "Visit Company Website" link from each article element
    """
    
    base_url = "https://www.adventinternational.com/investments/"
    all_companies = []
    
    async with async_playwright() as p:
        log_header("ADVENT INTERNATIONAL PORTFOLIO SCRAPER")
        log_info("🚀 Starting scraper...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Go to first page to determine total pages
            log_info(f"📄 Loading {base_url}")
            await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Calculate total pages (429 companies / 10 per page = 43 pages)
            # We'll try to find the last page number from pagination
            last_page_link = await page.query_selector('a.page-numbers:not(.next):not(.prev):last-of-type')
            if last_page_link:
                last_page_text = await last_page_link.inner_text()
                total_pages = int(last_page_text.strip())
                log_info(f"📊 Found {total_pages} pages from pagination")
            else:
                # Fallback: calculate from known total
                total_pages = 43
                log_info(f"📊 Using calculated total: {total_pages} pages (429 companies / 10 per page)")
            
            # Scrape each page
            for page_num in range(1, total_pages + 1):
                # Build page URL
                if page_num == 1:
                    page_url = base_url
                else:
                    page_url = f"{base_url}?sf_paged={page_num}"
                
                log_info(f"\n{'='*60}")
                log_info(f"📄 PAGE {page_num}/{total_pages}")
                log_info(f"{'='*60}")
                
                try:
                    await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(2000)
                    
                    # Get all article elements
                    articles = await page.query_selector_all('article')
                    log_info(f"   Found {len(articles)} article elements (first is filters)")
                    
                    if len(articles) < 2:
                        log_warning(f"   ⚠️ No company articles found on page {page_num}")
                        continue
                    
                    # Process articles[1:] (skip filters at articles[0])
                    companies_on_page = 0
                    for idx in range(1, len(articles)):
                        try:
                            article = articles[idx]
                            
                            # Extract company name from h3, h2, or h4
                            name_elem = await article.query_selector('h3')
                            if not name_elem:
                                name_elem = await article.query_selector('h2')
                            if not name_elem:
                                name_elem = await article.query_selector('h4')
                            
                            if not name_elem:
                                continue
                            
                            company_name = (await name_elem.inner_text()).strip()
                            
                            # Find "Visit Company Website" link
                            website = None
                            visit_link = await article.query_selector('a:has-text("Visit Company Website")')
                            if not visit_link:
                                visit_link = await article.query_selector('a:has-text("Visit company website")')
                            if not visit_link:
                                visit_link = await article.query_selector('a:has-text("VISIT COMPANY WEBSITE")')
                            
                            if visit_link:
                                website = await visit_link.get_attribute('href')
                                if website:
                                    website = website.strip()
                                    # Filter out Advent's own URLs (news, press releases, etc.)
                                    if 'adventinternational.com' in website:
                                        log_warning(f"   [{company_name}] Advent URL found, skipping: {website[:60]}...")
                                        website = None
                            
                            # Extract any available additional data
                            description = None
                            desc_elem = await article.query_selector('.elementor-post__excerpt p')
                            if desc_elem:
                                description = (await desc_elem.inner_text()).strip()
                            
                            sectors = []
                            sector_links = await article.query_selector_all('a[href*="/topics/sectors/"]')
                            for sector_link in sector_links:
                                sector_text = await sector_link.inner_text()
                                sectors.append(sector_text.strip())
                            
                            company_data = {
                                'name': company_name,
                                'website': website,
                                'description': description,
                                'sectors': sectors if sectors else None,
                                'pe_firm': 'Advent International'
                            }
                            
                            all_companies.append(company_data)
                            companies_on_page += 1
                            
                            if website:
                                log_success(f"   ✅ [{companies_on_page}] {company_name} → {website[:60]}")
                            else:
                                log_warning(f"   ⚠️ [{companies_on_page}] {company_name} → No website")
                            
                        except Exception as e:
                            log_error(f"   ✗ Error processing article {idx}: {str(e)}")
                            continue
                    
                    log_info(f"   📊 Extracted {companies_on_page} companies from page {page_num}")
                    
                except Exception as e:
                    log_error(f"   ❌ Error scraping page {page_num}: {str(e)}")
                    continue
            
            # Save results
            log_header("SCRAPING COMPLETE")
            log_info(f"📊 Total companies extracted: {len(all_companies)}")
            
            companies_with_website = sum(1 for c in all_companies if c.get('website'))
            log_info(f"🌐 Companies with website: {companies_with_website}/{len(all_companies)} ({companies_with_website/len(all_companies)*100:.1f}%)")
            
            # Save to JSON
            output_path = Path(OUTPUT_FILE)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_companies, f, indent=2, ensure_ascii=False)
            
            log_success(f"\n✅ Successfully saved {len(all_companies)} companies to {OUTPUT_FILE}")
            
            # Print sample companies
            log_header("SAMPLE COMPANIES")
            for i, company in enumerate(all_companies[:5], 1):
                log_info(f"{i}. {company['name']}")
                log_info(f"   Website: {company.get('website', 'No website')}")
                if company.get('sectors'):
                    log_info(f"   Sectors: {', '.join(company['sectors'])}")
            
            return all_companies
            
        except Exception as e:
            log_error(f"❌ Fatal error: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_advent_portfolio())
