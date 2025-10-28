"""
Apax Partners Portfolio Scraper (v2)
Scrapes company information from https://www.apax.com/all-investments-listed-alphabetically/
"""
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

async def scrape_apax_portfolio():
    """
    Scrape all portfolio companies from Apax Partners
    """
    print("\n" + "="*80)
    print("🚀 APAX PARTNERS PORTFOLIO SCRAPER")
    print("="*80 + "\n")
    
    companies = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # Load all investments page
            print("📄 Loading https://www.apax.com/all-investments-listed-alphabetically/")
            await page.goto('https://www.apax.com/all-investments-listed-alphabetically/', wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Handle cookie consent popup
            print("🍪 Handling cookie consent...")
            try:
                cookie_selectors = [
                    'button:has-text("Accept")',
                    'button:has-text("Accept All")',
                    'button:has-text("I Accept")',
                    'button:has-text("OK")',
                    '#onetrust-accept-btn-handler',
                    '.cookie-accept',
                    '[id*="accept"]',
                ]
                
                for selector in cookie_selectors:
                    try:
                        cookie_btn = await page.query_selector(selector)
                        if cookie_btn and await cookie_btn.is_visible():
                            await cookie_btn.click()
                            print("   ✅ Cookie consent accepted\n")
                            await page.wait_for_timeout(1000)
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract all company links directly - they're already linked to company websites
            print("🔍 Finding all company links...")
            
            company_data = await page.evaluate('''() => {
                // Get all links - company names link directly to their websites
                const allLinks = Array.from(document.querySelectorAll('a[href^="http"]'));
                
                return allLinks
                    .filter(link => {
                        const href = link.href;
                        const text = link.innerText.trim();
                        // Filter out Apax's own links and social media
                        const skipSites = ['apax.com', 'twitter.com', 'linkedin.com', 'facebook.com', 'instagram.com', 'cookieyes.com'];
                        const isSkip = skipSites.some(site => href.includes(site));
                        // Must have text (company name) and not be a skip site
                        return !isSkip && text.length > 0 && text.length < 100;
                    })
                    .map(link => ({
                        name: link.innerText.trim(),
                        website: link.href
                    }));
            }''')
            
            companies = company_data
            
            total = len(companies)
            print(f"✅ Found {total} companies with websites\n")
            
            await browser.close()
            
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            await browser.close()
            return
    
    # Save results
    print("\n" + "="*80)
    print("💾 SAVING RESULTS")
    print("="*80 + "\n")
    
    output_file = 'data/raw/json/apax_portfolio.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)
    
    # Statistics
    with_website = sum(1 for c in companies if c.get('website'))
    without_website = len(companies) - with_website
    
    if len(companies) > 0:
        print(f"✅ Total companies scraped: {len(companies)}")
        print(f"🌐 Companies with websites: {with_website} ({with_website/len(companies)*100:.1f}%)")
        print(f"⚠️  Companies without websites: {without_website}")
    else:
        print(f"⚠️  No companies found!")
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Show sample companies
    print("\n📋 Sample companies:")
    for company in companies[:10]:
        status = "✅" if company.get('website') else "❌"
        website = company.get('website', 'No website')
        print(f"  {status} {company['name']:30s} → {website}")
    
    print("\n✅ SCRAPING COMPLETE!")
    print("="*80 + "\n")

if __name__ == '__main__':
    asyncio.run(scrape_apax_portfolio())
