"""
Scrape Vista Equity Partners portfolio from their main portfolio page table.
The page has all companies in a table with Status (Current/Former), Industry, HQ, and Fund.
"""

import asyncio
import sys
import json
from datetime import datetime
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


async def scrape_vista_portfolio_table(page) -> list:
    """Scrape the portfolio table from Vista's main portfolio page."""
    
    url = "https://www.vistaequitypartners.com/companies/portfolio"
    
    print(f"🌐 Loading: {url}")
    await page.goto(url, wait_until='networkidle', timeout=30000)
    print("✓ Page loaded, waiting for dynamic content...")
    
    # Wait for content to load
    await asyncio.sleep(5)
    
    # Extract all companies from the table structure
    companies = await page.evaluate('''
        () => {
            const results = [];
            
            // Find the table section
            const tableSection = document.querySelector('.table.company-detail, section.table');
            if (!tableSection) {
                console.log('Table section not found');
                return results;
            }
            
            // Find all company rows
            const rows = tableSection.querySelectorAll('.row[data-status]');
            console.log('Found rows:', rows.length);
            
            rows.forEach((row, idx) => {
                try {
                    // Get data attributes
                    const status = row.getAttribute('data-status') || '';
                    const industry = row.getAttribute('data-industry') || '';
                    const area = row.getAttribute('data-area') || '';
                    const fund = row.getAttribute('data-fund') || '';
                    
                    // Get company name from the row
                    const nameSpan = row.querySelector('.company span.company, .info .company');
                    const name = nameSpan ? nameSpan.textContent.trim() : '';
                    
                    // Get headquarters from visible text
                    const hqDiv = row.querySelector('[data-type="area"], .area');
                    const headquarters = hqDiv ? hqDiv.textContent.trim() : area;
                    
                    // Get website link
                    const websiteLink = row.querySelector('a[href^="http"]:not([href*="vista"])');
                    const website = websiteLink ? websiteLink.href : '';
                    
                    if (name && name.length > 0) {
                        const company = {
                            name: name,
                            status: status.toLowerCase() === 'former' || status.toLowerCase().includes('exit') ? 'former' : 'current',
                            industry: industry || '',
                            headquarters: headquarters || '',
                            fund: fund || '',
                            website: website
                        };
                        
                        results.push(company);
                    }
                } catch (e) {
                    console.error('Error processing row:', e);
                }
            });
            
            console.log('Extracted companies:', results.length);
            return results;
        }
    ''')
    
    print(f"✓ Extracted {len(companies)} companies from page")
    return companies


async def main():
    print("="*80)
    print("VISTA EQUITY PARTNERS - PORTFOLIO SCRAPER")
    print("="*80)
    print()

    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("✓ Browser ready")
        print()

        start_time = datetime.now()
        
        # Scrape the portfolio table
        companies = await scrape_vista_portfolio_table(page)
        
        await browser.close()

        # Stats
        total_time = (datetime.now() - start_time).total_seconds()
        
        print()
        print("="*80)
        print("EXTRACTION COMPLETE!")
        print("="*80)
        print(f"⏱  Time: {total_time:.1f} seconds")
        print(f"📊 Total companies: {len(companies)}")
        print()
        
        # Status breakdown
        current = sum(1 for c in companies if c.get('status') == 'current')
        former = sum(1 for c in companies if c.get('status') == 'former')
        
        print("Status breakdown:")
        print(f"  ✓ Current: {current}")
        print(f"  ⚠ Former:  {former}")
        print()
        
        # Coverage stats
        stats = {
            'name': sum(1 for c in companies if c.get('name')),
            'status': sum(1 for c in companies if c.get('status')),
            'industry': sum(1 for c in companies if c.get('industry')),
            'headquarters': sum(1 for c in companies if c.get('headquarters')),
            'fund': sum(1 for c in companies if c.get('fund')),
            'website': sum(1 for c in companies if c.get('website'))
        }
        
        print("Field coverage:")
        for field, count in stats.items():
            pct = count/len(companies)*100 if len(companies) > 0 else 0
            print(f"  {field:15s}: {count:3d}/{len(companies)} ({pct:5.1f}%)")
        print()

        # Save results
        output = {
            'pe_firm': 'Vista Equity Partners',
            'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_companies': len(companies),
            'current_portfolio': current,
            'former_portfolio': former,
            'extraction_time_seconds': round(total_time, 1),
            'companies': companies,
            'coverage_stats': {k: f"{v}/{len(companies)}" for k, v in stats.items()}
        }

        with open('vista_portfolio_with_status.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved to: vista_portfolio_with_status.json")
        print()

        # Show sample companies
        print("Sample companies:")
        print("-" * 80)
        
        # Show some current companies
        current_companies = [c for c in companies if c.get('status') == 'current'][:3]
        if current_companies:
            print("\n✓ CURRENT Portfolio:")
            for c in current_companies:
                print(f"  • {c.get('name', 'N/A'):30s} | {c.get('industry', 'N/A'):25s} | {c.get('headquarters', 'N/A')}")
        
        # Show some former companies
        former_companies = [c for c in companies if c.get('status') == 'former'][:3]
        if former_companies:
            print("\n⚠ FORMER Portfolio:")
            for c in former_companies:
                print(f"  • {c.get('name', 'N/A'):30s} | {c.get('industry', 'N/A'):25s} | {c.get('headquarters', 'N/A')}")

        print()
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
