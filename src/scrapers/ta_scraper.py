"""
Scrape TA Associates portfolio - get company URLs from sector pages,
then visit each company page for detailed information.
"""
import asyncio
import sys
import json
from datetime import datetime
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


async def get_company_urls_from_sector(page, sector_name: str, url: str) -> list:
    """Get all company URLs from a sector page."""
    
    print(f"  📂 {sector_name:20s} ", end='', flush=True)
    
    try:
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        
        # Get all company links
        company_urls = await page.evaluate('''
            () => {
                const links = Array.from(document.querySelectorAll('a[href*="/portfolio/investments/"]'));
                const urls = links
                    .map(a => a.href)
                    .filter(href => href.includes('/portfolio/investments/') && !href.endsWith('/investments/'));
                
                // Deduplicate
                return Array.from(new Set(urls));
            }
        ''')
        
        print(f"→ {len(company_urls):3d} companies")
        return [(sector_name, url_item) for url_item in company_urls]
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        return []


async def scrape_company_page(page, sector: str, url: str) -> dict:
    """Scrape detailed data from a company's individual page."""
    
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        await asyncio.sleep(2)
        
        # Extract company data
        data = await page.evaluate('''
            () => {
                const result = {
                    name: '',
                    description: '',
                    website: '',
                    sector: '',
                    hq: '',
                    status: 'current',
                    investment_year: '',
                    exit_info: ''
                };
                
                // Get name from h1 - but it's often the description, so we'll use the URL slug
                const h1 = document.querySelector('h1');
                if (h1) {
                    const h1Text = h1.textContent.trim();
                    // If h1 is short enough, it's probably the name
                    if (h1Text.length < 100 && !h1Text.includes('.')) {
                        result.name = h1Text;
                    }
                }
                
                // Get all text for parsing
                const bodyText = document.body.innerText;
                const lines = bodyText.split('\\n').map(l => l.trim()).filter(l => l);
                
                // Parse line by line for structured data
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];
                    const lower = line.toLowerCase();
                    const nextLine = i + 1 < lines.length ? lines[i + 1] : '';
                    
                    // Sector
                    if (lower === 'sector' && nextLine) {
                        result.sector = nextLine;
                    }
                    
                    // Investment Year
                    if (lower === 'investment year' && nextLine) {
                        result.investment_year = nextLine;
                    }
                    
                    // Status
                    if (lower === 'status' && nextLine) {
                        result.status = nextLine.toLowerCase();
                    }
                    
                    // Headquarters
                    if (lower === 'headquarters' && nextLine) {
                        result.hq = nextLine;
                    }
                    
                    // Description (usually first paragraph or h1)
                    if (!result.description && line.length > 50 && line.length < 500 && line.includes('.')) {
                        result.description = line;
                    }
                    
                    // Exit info
                    if (line.includes('Acquired by') || line.includes('IPO') || line.includes('Merged with')) {
                        result.exit_info = line;
                        if (!result.status || result.status === 'current') {
                            result.status = 'exited';
                        }
                    }
                }
                
                // Get website link
                const websiteLink = document.querySelector('a[href^="http"]:not([href*="ta.com"]):not([href*="altareturn"])');
                if (websiteLink) result.website = websiteLink.href;
                
                // If no name found, extract from URL
                if (!result.name) {
                    const urlParts = window.location.pathname.split('/');
                    const slug = urlParts[urlParts.length - 2] || urlParts[urlParts.length - 1];
                    result.name = slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                }
                
                return result;
            }
        ''')
        
        data['url'] = url
        data['sector_page'] = sector
        
        return data
        
    except Exception as e:
        return {
            'url': url,
            'sector_page': sector,
            'error': str(e)[:100]
        }


async def main():
    print("="*80)
    print("TA ASSOCIATES - COMPREHENSIVE PORTFOLIO SCRAPER")
    print("="*80)
    print()

    # Define sector pages
    sectors = {
        'Business Services': 'https://www.ta.com/portfolio/business-services/',
        'Consumer': 'https://www.ta.com/portfolio/consumer/',
        'Financial Services': 'https://www.ta.com/portfolio/financial-services/',
        'Healthcare': 'https://www.ta.com/portfolio/healthcare/',
        'Technology': 'https://www.ta.com/portfolio/technology/'
    }

    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("✓ Browser ready")
        print()

        start_time = datetime.now()
        
        # Step 1: Get all company URLs from sector pages
        print("STEP 1: Collecting company URLs from sector pages")
        print("-" * 80)
        
        all_company_urls = []
        for sector_name, sector_url in sectors.items():
            urls = await get_company_urls_from_sector(page, sector_name, sector_url)
            all_company_urls.extend(urls)
            await asyncio.sleep(1)
        
        print(f"\n✓ Total company pages found: {len(all_company_urls)}")
        print()
        
        # Step 2: Scrape each company page
        print("STEP 2: Scraping individual company pages")
        print("-" * 80)
        
        companies = []
        for i, (sector, company_url) in enumerate(all_company_urls, 1):
            # Extract company slug from URL for display
            slug = company_url.split('/')[-2] if company_url.endswith('/') else company_url.split('/')[-1]
            
            # Progress
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = i / elapsed if elapsed > 0 else 0
            eta_min = int((len(all_company_urls) - i) / rate / 60) if rate > 0 else 0
            
            print(f"[{i:3d}/{len(all_company_urls)}] {slug:35s} ", end='', flush=True)
            
            data = await scrape_company_page(page, sector, company_url)
            
            if 'error' in data:
                print(f"❌ {data['error'][:30]}")
            else:
                status_icon = "✓" if data.get('status') == 'current' else "⚠"
                year = data.get('investment_year', 'N/A')[:4]
                print(f"{status_icon} {year:4s} | ETA: {eta_min:2d}m")
            
            companies.append(data)
            await asyncio.sleep(0.3)  # Be polite
        
        await browser.close()

        # Stats
        total_time = (datetime.now() - start_time).total_seconds()
        
        print()
        print("="*80)
        print("EXTRACTION COMPLETE!")
        print("="*80)
        print(f"⏱  Time: {total_time/60:.1f} minutes")
        print(f"📊 Total companies: {len(companies)}")
        print()
        
        # Status breakdown
        current = sum(1 for c in companies if c.get('status') == 'current' and 'error' not in c)
        exited = sum(1 for c in companies if c.get('status') in ['exited', 'former'] and 'error' not in c)
        errors = sum(1 for c in companies if 'error' in c)
        
        print("Status breakdown:")
        print(f"  ✓ Current: {current}")
        print(f"  ⚠ Exited:  {exited}")
        if errors > 0:
            print(f"  ❌ Errors:  {errors}")
        print()
        
        # Coverage stats
        valid_companies = [c for c in companies if 'error' not in c]
        stats = {
            'name': sum(1 for c in valid_companies if c.get('name')),
            'sector': sum(1 for c in valid_companies if c.get('sector')),
            'headquarters': sum(1 for c in valid_companies if c.get('hq')),
            'investment_year': sum(1 for c in valid_companies if c.get('investment_year')),
            'website': sum(1 for c in valid_companies if c.get('website')),
            'description': sum(1 for c in valid_companies if c.get('description'))
        }
        
        print("Field coverage:")
        for field, count in stats.items():
            pct = count/len(valid_companies)*100 if len(valid_companies) > 0 else 0
            print(f"  {field:20s}: {count:3d}/{len(valid_companies)} ({pct:5.1f}%)")
        print()

        # Save results
        output = {
            'pe_firm': 'TA Associates',
            'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_companies': len(companies),
            'current_portfolio': current,
            'exited_portfolio': exited,
            'extraction_time_minutes': round(total_time/60, 1),
            'sectors': list(sectors.keys()),
            'companies': companies,
            'coverage_stats': {k: f"{v}/{len(valid_companies)}" for k, v in stats.items()}
        }

        with open('ta_portfolio_complete.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved to: ta_portfolio_complete.json")
        print()

        # Show sample companies
        print("Sample companies:")
        print("-" * 80)
        
        # Current companies
        current_companies = [c for c in valid_companies if c.get('status') == 'current'][:3]
        if current_companies:
            print("\n✓ CURRENT Portfolio:")
            for c in current_companies:
                print(f"  • {c.get('name', 'N/A'):30s} | {c.get('sector', 'N/A')[:30]:30s} | {c.get('investment_year', 'N/A')}")
        
        # Exited companies
        exited_companies = [c for c in valid_companies if c.get('status') in ['exited', 'former']][:3]
        if exited_companies:
            print("\n⚠ EXITED Portfolio:")
            for c in exited_companies:
                exit_info = c.get('exit_info', 'N/A')[:50]
                print(f"  • {c.get('name', 'N/A'):30s} | {exit_info}")

        print()
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
