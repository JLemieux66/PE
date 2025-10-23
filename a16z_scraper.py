"""
Andreessen Horowitz (a16z) Portfolio Scraper
Scrapes portfolio companies from https://a16z.com/portfolio/
"""
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime


async def scrape_a16z_portfolio():
    """Scrape a16z portfolio companies"""
    
    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = "https://a16z.com/portfolio/"
        print(f"📄 Navigating to {url}...")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)  # Wait for dynamic content to load
        
        print("🔍 Extracting portfolio companies...")
        
        # Extract companies using the correct selector from the page structure
        companies = await page.evaluate("""
            () => {
                const companies = [];
                
                // Find all company grid items - this is the correct selector
                const companyElements = document.querySelectorAll('.company-grid-item');
                console.log(`Found ${companyElements.length} company grid items`);
                
                companyElements.forEach(element => {
                    const name = element.getAttribute('data-name');
                    const dataFilterBy = element.getAttribute('data-filter-by') || '';
                    const companyId = element.getAttribute('data-id');
                    
                    // Extract status text (IPO, Acquired By, etc) from builder-title span
                    const statusElement = element.querySelector('.builder-title span');
                    const statusText = statusElement ? statusElement.textContent.trim() : '';
                    
                    // Determine if Active or Exit based on data-filter-by
                    const status = dataFilterBy.includes('sts_Exits') ? 'Exit' : 
                                   dataFilterBy.includes('sts_Active') ? 'Active' : 'Unknown';
                    
                    // Extract sectors from data-filter-by (can have multiple)
                    const sectors = [];
                    const filterParts = dataFilterBy.split(';');
                    filterParts.forEach(part => {
                        if (part.startsWith('cat_')) {
                            sectors.push(part.substring(4));
                        }
                    });
                    
                    // Extract investment stages
                    const stages = [];
                    filterParts.forEach(part => {
                        if (part.startsWith('stgi_')) {
                            stages.push(part.substring(5));
                        }
                    });
                    
                    if (name) {
                        companies.push({
                            name: name,
                            sector: sectors.join(', '),
                            status: status,
                            exit_details: statusText,
                            stage: stages.join(', '),
                            company_id: companyId
                        });
                    }
                });
                
                return companies;
            }
        """)
        
        print(f"✅ Found {len(companies)} companies")
        
        await browser.close()
        
        return companies


async def main():
    print("=" * 80)
    print("ANDREESSEN HOROWITZ (a16z) - PORTFOLIO SCRAPER")
    print("=" * 80)
    
    companies = await scrape_a16z_portfolio()
    
    # Create output structure
    output = {
        "pe_firm": "Andreessen Horowitz",
        "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_companies": len(companies),
        "companies": companies
    }
    
    # Save to JSON
    output_file = "a16z_portfolio.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(companies)} companies to {output_file}")
    
    # Display sample
    print("\n📊 Sample companies:")
    for company in companies[:10]:
        print(f"  • {company['name']}")
    
    if len(companies) > 10:
        print(f"  ... and {len(companies) - 10} more")


if __name__ == "__main__":
    asyncio.run(main())
