"""
Enhanced Andreessen Horowitz (a16z) Portfolio Scraper
Clicks on company tiles to extract LinkedIn URLs and additional details
"""
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import re


async def scrape_linkedin_hq(page, linkedin_url):
    """
    Scrape headquarters from LinkedIn company page
    
    Args:
        page: Playwright page object
        linkedin_url: LinkedIn company URL
        
    Returns:
        str: Headquarters location or empty string
    """
    try:
        # Navigate to LinkedIn page
        await page.goto(linkedin_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)
        
        # Try to extract headquarters
        # LinkedIn shows HQ in the "About" section or company info
        hq_selectors = [
            'dt:has-text("Headquarters") + dd',
            '[data-test-id="about-us__headquarters"]',
            '.org-top-card-summary-info-list__info-item:has-text("Headquarter")',
        ]
        
        for selector in hq_selectors:
            try:
                hq_element = await page.wait_for_selector(selector, timeout=3000)
                if hq_element:
                    hq = await hq_element.inner_text()
                    return hq.strip()
            except:
                continue
                
        return ""
    except Exception as e:
        print(f"  ⚠️  Failed to scrape LinkedIn: {str(e)[:100]}")
        return ""


async def click_company_tile_and_extract(page, company_index):
    """
    Click on a company tile and extract modal details
    
    Args:
        page: Playwright page object
        company_index: Index of the company tile (0-based)
        
    Returns:
        dict: Company details including LinkedIn URL, website, etc.
    """
    try:
        # Click on the company tile
        tiles = await page.query_selector_all('.company-grid-item')
        if company_index >= len(tiles):
            return {}
            
        await tiles[company_index].click()
        await page.wait_for_timeout(1000)  # Wait for modal to open
        
        # Extract modal data
        modal_data = await page.evaluate("""
            () => {
                // Look for modal or popup with company details
                const modal = document.querySelector('[class*="modal"], [class*="popup"], [class*="overlay"]');
                if (!modal) return {};
                
                // Try to find LinkedIn URL
                const linkedinLink = modal.querySelector('a[href*="linkedin.com/company"]');
                const website = modal.querySelector('a[href*="http"]:not([href*="a16z.com"])');
                const description = modal.querySelector('[class*="description"], p');
                
                return {
                    linkedin_url: linkedinLink ? linkedinLink.href : '',
                    website: website ? website.href : '',
                    description: description ? description.textContent.trim() : ''
                };
            }
        """)
        
        # Close modal (press Escape or click close button)
        await page.keyboard.press('Escape')
        await page.wait_for_timeout(500)
        
        return modal_data
        
    except Exception as e:
        print(f"  ⚠️  Failed to extract from tile {company_index}: {str(e)[:100]}")
        return {}


async def scrape_a16z_portfolio_enhanced():
    """Scrape a16z portfolio with enhanced data extraction"""
    
    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://a16z.com/portfolio/"
        print(f"📄 Navigating to {url}...")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)  # Wait for dynamic content
        
        print("🔍 Extracting portfolio companies...")
        
        # Extract basic company data first
        companies = await page.evaluate("""
            () => {
                const companies = [];
                const companyElements = document.querySelectorAll('.company-grid-item');
                
                companyElements.forEach(element => {
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
                            company_id: companyId,
                            linkedin_url: '',
                            website: '',
                            headquarters: '',
                            investment_year: ''
                        });
                    }
                });
                
                return companies;
            }
        """)
        
        print(f"✅ Found {len(companies)} companies")
        print(f"🔗 Now attempting to extract LinkedIn URLs and HQ (this may take a while)...")
        
        # Limit to first 20 companies for testing (remove this for full scrape)
        sample_size = min(20, len(companies))
        print(f"📊 Processing first {sample_size} companies as a test...")
        
        for i in range(sample_size):
            company = companies[i]
            print(f"  [{i+1}/{sample_size}] {company['name']}...", end=" ")
            
            # Try clicking on tile to get more details
            modal_data = await click_company_tile_and_extract(page, i)
            
            if modal_data.get('linkedin_url'):
                company['linkedin_url'] = modal_data['linkedin_url']
                company['website'] = modal_data.get('website', '')
                print(f"✅ LinkedIn found")
                
                # Optional: Scrape HQ from LinkedIn (slower)
                # company['headquarters'] = await scrape_linkedin_hq(page, company['linkedin_url'])
            else:
                print("⚠️  No modal/LinkedIn")
        
        await browser.close()
        
        return companies


async def main():
    print("=" * 80)
    print("ANDREESSEN HOROWITZ (a16z) - ENHANCED PORTFOLIO SCRAPER")
    print("=" * 80)
    
    companies = await scrape_a16z_portfolio_enhanced()
    
    output = {
        "pe_firm": "Andreessen Horowitz",
        "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_companies": len(companies),
        "companies": companies
    }
    
    output_file = "a16z_portfolio_enhanced.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(companies)} companies to {output_file}")
    
    # Show sample
    print("\n📊 Sample companies with LinkedIn:")
    linkedin_count = sum(1 for c in companies if c.get('linkedin_url'))
    print(f"Companies with LinkedIn URLs: {linkedin_count}/{len(companies)}")
    
    for company in companies[:10]:
        linkedin_status = "✅" if company.get('linkedin_url') else "❌"
        print(f"  {linkedin_status} {company['name']} - {company.get('linkedin_url', 'No LinkedIn')[:50]}")


if __name__ == "__main__":
    asyncio.run(main())
