"""
General Atlantic Portfolio Scraper
Scrapes company information from https://www.generalatlantic.com/investments/
"""
import asyncio
import json
from playwright.async_api import async_playwright
from pathlib import Path

async def scrape_general_atlantic():
    """
    Scrape General Atlantic portfolio companies with websites
    """
    async with async_playwright() as p:
        # Launch with more human-like settings
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Hide automation indicators
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        print("🌐 Loading General Atlantic investments page...")
        await page.goto('https://www.generalatlantic.com/investments/', wait_until='networkidle')
        
        await asyncio.sleep(2)
        
        # Click "Load More" button until all companies are loaded
        print("\n📄 Loading all companies by clicking 'Load More'...")
        load_more_count = 0
        max_attempts = 100  # Safety limit
        
        while load_more_count < max_attempts:
            try:
                # Count companies before clicking
                before_count = len(await page.query_selector_all('a:has-text("View Site")'))
                
                print(f"  Looking for 'Load More' button (attempt {load_more_count + 1}, companies: {before_count})...")
                
                # Wait for Load More button to appear (with longer timeout)
                try:
                    await page.wait_for_selector('a:has-text("Load More")', timeout=15000, state='visible')
                except:
                    print(f"  ✅ No 'Load More' button appeared within 15 seconds, all content loaded")
                    # Check if we have Chime (last company)
                    page_content = await page.content()
                    if 'chime' in page_content.lower():
                        print("  ✅ Found 'Chime' - confirmed we have all companies")
                    break
                
                # Get the button
                load_more_button = await page.query_selector('a:has-text("Load More")')
                
                if not load_more_button:
                    print(f"  ✅ No 'Load More' button found")
                    break
                
                print(f"  Found button, scrolling and clicking...")
                
                # Scroll to button with human-like behavior
                await load_more_button.scroll_into_view_if_needed()
                await asyncio.sleep(0.3 + (0.2 * load_more_count % 3))  # Variable delay
                
                # Move mouse to button (human-like)
                box = await load_more_button.bounding_box()
                if box:
                    await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    await asyncio.sleep(0.2)
                
                # Click button
                await load_more_button.click()
                print(f"  Clicked! Waiting for content to load...")
                
                # Wait for new content with variable timing
                await asyncio.sleep(3 + (0.5 * load_more_count % 2))
                
                # Gently scroll down a bit (human-like behavior after clicking)
                current_scroll = await page.evaluate('window.pageYOffset')
                await page.evaluate(f'window.scrollTo(0, {current_scroll + 200})')
                await asyncio.sleep(0.5)
                
                # Check if more companies loaded
                after_count = len(await page.query_selector_all('a:has-text("View Site")'))
                
                print(f"     Companies increased from {before_count} to {after_count}")
                
                # Check if we've reached the end (no new companies AND we tried again)
                if after_count == before_count:
                    # Try waiting a bit longer and check again
                    await asyncio.sleep(2)
                    final_count = len(await page.query_selector_all('a:has-text("View Site")'))
                    if final_count == before_count:
                        print("  ✅ No new companies loaded after waiting, stopping")
                        break
                    else:
                        after_count = final_count
                        print(f"     Actually found more: {final_count}")
                
                load_more_count += 1
                
                # Longer delay before looking for next button
                await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"  ℹ️  Error or no more content: {e}")
                break
        
        print(f"\n📊 Clicked 'Load More' {load_more_count} times")
        
        # Now extract all companies
        print("\n🔍 Extracting company data...")
        
        companies = []
        seen_websites = set()  # Track to avoid duplicates
        
        # Find all "View Site" links
        view_site_links = await page.query_selector_all('a:has-text("View Site")')
        
        print(f"  Found {len(view_site_links)} 'View Site' links")
        
        for i, link in enumerate(view_site_links, 1):
            try:
                # Get website URL
                website = await link.get_attribute('href')
                
                if not website or website.startswith('#'):
                    continue
                
                # Skip if we've already seen this website (avoid duplicates)
                if website in seen_websites:
                    continue
                
                seen_websites.add(website)
                
                # Navigate up to find the company card/row
                # The structure appears to be: div containing company name and "View Site" link
                parent = await link.evaluate_handle('element => element.closest("div[class*=\'wp-block\']")')
                
                if parent:
                    # Get all text from the parent
                    text_content = await parent.inner_text()
                    
                    # Parse the text - first line is usually the company name/description
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    
                    # Remove "View Site" from lines
                    lines = [line for line in lines if line != 'View Site']
                    
                    # First substantial line is the description/name
                    company_name = None
                    description = None
                    
                    if len(lines) > 0:
                        # First line is typically the description
                        description = lines[0]
                        
                        # Try to extract company name from description or URL
                        if website:
                            # Extract domain as fallback name
                            from urllib.parse import urlparse
                            domain = urlparse(website).netloc
                            company_name = domain.replace('www.', '').replace('.com', '').replace('.io', '').replace('.co', '').title()
                    
                    if website:
                        company_data = {
                            'name': company_name or description[:50],  # Use description as name if needed
                            'website': website,
                            'description': description
                        }
                        
                        companies.append(company_data)
                        print(f"  [{len(companies)}] {company_data['name'][:40]} → {website}")
                
            except Exception as e:
                print(f"  ⚠️  Error processing link {i}: {e}")
                continue
        
        await browser.close()
        
        # Save results
        print(f"\n💾 Saving {len(companies)} companies...")
        
        output_dir = Path('data/raw/json')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / 'general_atlantic_portfolio.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(companies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved to {output_file}")
        
        # Statistics
        websites_found = len([c for c in companies if c.get('website')])
        
        print("\n" + "="*80)
        print("📊 SCRAPING COMPLETE")
        print("="*80)
        print(f"Total companies found: {len(companies)}")
        print(f"Companies with websites: {websites_found} ({websites_found/len(companies)*100:.1f}%)")
        
        # Show sample
        print("\n📋 Sample companies:")
        for company in companies[:5]:
            print(f"  • {company['name'][:40]}: {company['website']}")
        
        return companies

if __name__ == "__main__":
    asyncio.run(scrape_general_atlantic())
