"""
Andreessen Horowitz (a16z) Portfolio Scraper
Two-pass approach: Extract company links → Visit detail pages → Extract websites
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Output file
OUTPUT_FILE = "data/raw/json/a16z_portfolio.json"


async def scrape_a16z_portfolio():
    """
    Scrape a16z portfolio with real company websites
    Two-pass approach:
    1. Extract all company tiles with basic info from main page
    2. Click each tile to open modal/detail page and extract website
    """
    
    async with async_playwright() as p:
        logger.info("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        url = "https://a16z.com/portfolio/"
        logger.info(f"📄 Navigating to {url}...")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)  # Wait for dynamic content to load
            
            # Scroll to load all companies
            logger.info("📜 Scrolling to load all companies...")
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
            
            # PASS 1: Extract all company basic info
            logger.info("🔍 PASS 1: Extracting company basic info...")
            
            companies = await page.evaluate("""
                () => {
                    const companies = [];
                    const companyElements = document.querySelectorAll('.company-grid-item');
                    
                    companyElements.forEach((element, index) => {
                        const name = element.getAttribute('data-name');
                        const dataFilterBy = element.getAttribute('data-filter-by') || '';
                        const companyId = element.getAttribute('data-id');
                        
                        const statusElement = element.querySelector('.builder-title span');
                        const statusText = statusElement ? statusElement.textContent.trim() : '';
                        
                        const status = dataFilterBy.includes('sts_Exits') ? 'Exit' : 
                                       dataFilterBy.includes('sts_Active') ? 'Active' : 'Unknown';
                        
                        const sectors = [];
                        const stages = [];
                        const filterParts = dataFilterBy.split(';');
                        
                        filterParts.forEach(part => {
                            if (part.startsWith('cat_')) sectors.push(part.substring(4));
                            if (part.startsWith('stgi_')) stages.push(part.substring(5));
                        });
                        
                        if (name) {
                            companies.push({
                                name: name,
                                sector: sectors.join(', '),
                                status: status,
                                exit_details: statusText,
                                stage: stages.join(', '),
                                tile_index: index,
                                website: '',
                                linkedin_url: ''
                            });
                        }
                    });
                    
                    return companies;
                }
            """)
            
            logger.info(f"✅ Found {len(companies)} companies")
            
            # PASS 2: Click each tile and extract website
            logger.info(f"🔗 PASS 2: Clicking tiles to extract websites...")
            
            successful_extractions = 0
            failed_extractions = 0
            
            for i, company_data in enumerate(companies):
                company_name = company_data['name']
                tile_index = company_data['tile_index']
                
                logger.info(f"  [{i+1}/{len(companies)}] Processing: {company_name}")
                
                try:
                    # Get all tiles again (fresh query)
                    tiles = await page.query_selector_all('.company-grid-item')
                    
                    if tile_index >= len(tiles):
                        logger.warning(f"    ⚠️  Tile index {tile_index} out of range")
                        failed_extractions += 1
                        continue
                    
                    # Click the tile
                    await tiles[tile_index].click()
                    await page.wait_for_timeout(1500)  # Wait for modal to open
                    
                    # Wait for modal to be visible
                    await page.wait_for_selector('.portfolio-modal.show', timeout=3000)
                    
                    # Extract website and LinkedIn from modal
                    modal_data = await page.evaluate("""
                        () => {
                            const modal = document.querySelector('.portfolio-modal.show');
                            if (!modal) return { website: '', linkedin_url: '' };
                            
                            // Find all links in the modal
                            const links = modal.querySelectorAll('a[href]');
                            let website = '';
                            let linkedin_url = '';
                            
                            for (const link of links) {
                                const href = link.href;
                                
                                // Skip a16z domain links
                                if (href.includes('a16z.com')) continue;
                                
                                // Check for LinkedIn
                                if (href.includes('linkedin.com/company') && !linkedin_url) {
                                    linkedin_url = href;
                                }
                                // Check for company website (http/https, not social media)
                                else if ((href.startsWith('http://') || href.startsWith('https://')) && 
                                        !href.includes('linkedin.com') &&
                                        !href.includes('twitter.com') &&
                                        !href.includes('facebook.com') &&
                                        !href.includes('instagram.com') &&
                                        !website) {
                                    website = href;
                                }
                            }
                            
                            return { website, linkedin_url };
                        }
                    """)
                    
                    website = modal_data.get('website', '')
                    linkedin_url = modal_data.get('linkedin_url', '')
                    
                    if website:
                        company_data['website'] = website
                        logger.info(f"    ✅ Website: {website}")
                        successful_extractions += 1
                    else:
                        logger.info(f"    ⚠️  No website found")
                        failed_extractions += 1
                    if linkedin_url:
                        company_data['linkedin_url'] = linkedin_url
                        logger.info(f"    ✅ LinkedIn: {linkedin_url}")
                    
                    # Close modal (press Escape)
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    
                except Exception as e:
                    logger.error(f"    ❌ Error: {str(e)[:100]}")
                    failed_extractions += 1
                    
                    # Try to close any open modal
                    try:
                        await page.keyboard.press('Escape')
                        await page.wait_for_timeout(500)
                    except:
                        pass
            
            logger.info(f"\n✅ Extraction complete!")
            logger.info(f"   Successful: {successful_extractions}/{len(companies)}")
            logger.info(f"   Failed: {failed_extractions}/{len(companies)}")
            
            await browser.close()
            return companies
            
        except Exception as e:
            logger.error(f"❌ Error during scraping: {str(e)}")
            await browser.close()
            raise


def save_to_json(companies, output_file=OUTPUT_FILE):
    """Save companies to JSON file"""
    output = {
        "pe_firm": "Andreessen Horowitz",
        "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_companies": len(companies),
        "companies": companies
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Saved {len(companies)} companies to {output_file}")


async def main():
    logger.info("=" * 80)
    logger.info("ANDREESSEN HOROWITZ (a16z) - PORTFOLIO SCRAPER")
    logger.info("=" * 80)
    
    companies = await scrape_a16z_portfolio()
    save_to_json(companies)
    
    # Show stats
    website_count = sum(1 for c in companies if c.get('website'))
    linkedin_count = sum(1 for c in companies if c.get('linkedin_url'))
    
    logger.info("\n📊 Extraction Statistics:")
    logger.info(f"   Total companies: {len(companies)}")
    logger.info(f"   With websites: {website_count} ({website_count/len(companies)*100:.1f}%)")
    logger.info(f"   With LinkedIn: {linkedin_count} ({linkedin_count/len(companies)*100:.1f}%)")
    
    # Show sample
    logger.info("\n📋 Sample companies:")
    for company in companies[:10]:
        status = "✅" if company.get('website') else "❌"
        logger.info(f"  {status} {company['name']} → {company.get('website', 'No website')}")


if __name__ == "__main__":
    asyncio.run(main())
