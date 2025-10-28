"""
Accel Portfolio Scraper - Extract company data from Accel's portfolio page
"""

import asyncio
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import json
from src.scrapers.website_extractor import extract_company_website

# Constants
ACCEL_URL = "https://www.accel.com/relationships"
PE_FIRM_NAME = "Accel"
OUTPUT_FILE = "data/raw/json/accel_portfolio.json"


async def extract_company_details(page, company_url, company_name):
    """Extract detailed company information from company's Accel page"""
    try:
        print(f"      🔗 Visiting: {company_url}")
        await page.goto(company_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)
        
        # Extract website using helper
        website = await extract_company_website(page, skip_domains=['accel.com'])
        
        if website:
            print(f"      ✅ Website: {website}")
        else:
            print(f"      ⚠️  No website found")
        
        return website
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None


async def scrape_accel_portfolio():
    """Scrape Accel's portfolio page and extract company data."""
    print(f"\n🎯 Scraping Accel Portfolio from {ACCEL_URL}")
    
    companies = []
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to the portfolio page
            print("📄 Loading page...")
            await page.goto(ACCEL_URL, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for initial page load
            print("⏳ Waiting for content to load...")
            await asyncio.sleep(5)
            
            # Scroll to load all content (infinite scroll)
            print("📜 Scrolling to load all companies...")
            for i in range(10):
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)
            
            print("🔍 Extracting company data...")
            
            # Find all company cards and extract basic data first
            company_cards = await page.query_selector_all('.company-card_component')
            print(f"   Found {len(company_cards)} company cards")
            
            # First pass: extract all basic data and URLs
            basic_company_data = []
            for i, card in enumerate(company_cards):
                try:
                    # Extract company name
                    name_element = await card.query_selector('h3[accel-content="company-name"]')
                    if not name_element:
                        continue
                    
                    name = (await name_element.inner_text()).strip()
                    
                    # Extract slug
                    link_element = await card.query_selector('a.company-card_mobile-link[param-slug]')
                    slug = await link_element.get_attribute('param-slug') if link_element else None
                    company_url = f"https://www.accel.com/relationships/{slug}" if slug else None
                    
                    # Extract description
                    description = ""
                    desc_element = await card.query_selector('[accel-content="company-short-description"]')
                    if desc_element:
                        desc_text = await desc_element.inner_text()
                        description = desc_text.strip()
                    
                    # Extract founders
                    founders = []
                    founders_element = await card.query_selector('[accel-content="company-founders-richtext"]')
                    if founders_element:
                        founders_text = await founders_element.inner_text()
                        founders = [f.strip() for f in founders_text.split('\n') if f.strip()]
                    
                    # Extract investment info
                    first_event_type = ""
                    first_event_date = ""
                    
                    event_type_element = await card.query_selector('[accel-content="company-first-event-type"]')
                    if event_type_element:
                        first_event_type = (await event_type_element.inner_text()).strip()
                    
                    event_date_element = await card.query_selector('[accel-content="company-first-event-date"]')
                    if event_date_element:
                        first_event_date = (await event_date_element.inner_text()).strip()
                    
                    basic_company_data.append({
                        'name': name,
                        'company_url': company_url,
                        'description': description,
                        'founders': ', '.join(founders) if founders else None,
                        'first_investment_type': first_event_type if first_event_type else None,
                        'first_investment_date': first_event_date if first_event_date else None,
                        'slug': slug
                    })
                
                except Exception as e:
                    print(f"   ⚠️  Error extracting card {i}: {e}")
                    continue
            
            print(f"   Extracted {len(basic_company_data)} companies' basic data")
            
            # Second pass: visit each company page to get real website
            print(f"\n🔗 Visiting company pages to extract websites...")
            for i, company_data in enumerate(basic_company_data):
                try:
                    print(f"   [{i+1}/{len(basic_company_data)}] {company_data['name']}")
                    
                    website = None
                    if company_data['company_url']:
                        website = await extract_company_details(page, company_data['company_url'], company_data['name'])
                    
                    # Add website to company data
                    company_data['website'] = website
                    companies.append(company_data)
                    
                    if (i + 1) % 100 == 0:
                        print(f"   Processed {i + 1} companies...")
                
                except Exception as e:
                    print(f"   ⚠️  Error processing {company_data['name']}: {e}")
                    # Still add the company without website
                    company_data['website'] = None
                    companies.append(company_data)
                    continue
            
            print(f"\n✅ Successfully extracted {len(companies)} companies")
            
            # Display first few companies as samples
            print("\n📊 Sample companies:")
            for company in companies[:10]:
                print(f"\n   🏢 {company['name']}")
                if company['description']:
                    desc_preview = company['description'][:80] + "..." if len(company['description']) > 80 else company['description']
                    print(f"      📝 {desc_preview}")
                if company['founders']:
                    print(f"      👥 {company['founders']}")
                if company['first_investment_type'] and company['first_investment_date']:
                    print(f"      💰 {company['first_investment_type']} {company['first_investment_date']}")
            
            await browser.close()
            return companies
            
        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()
            return []


def save_to_json(companies):
    """Save companies to JSON file."""
    if not companies:
        print("\n⚠️  No companies to save")
        return
    
    print(f"\n💾 Saving {len(companies)} companies to {OUTPUT_FILE}...")
    
    try:
        # Ensure directory exists
        output_path = Path(OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(companies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved successfully to {OUTPUT_FILE}")
        print(f"   📊 Total companies: {len(companies)}")
        
    except Exception as e:
        print(f"❌ Error saving to JSON: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main execution function."""
    print("=" * 60)
    print("ACCEL PORTFOLIO SCRAPER")
    print("=" * 60)
    
    # Scrape companies
    companies = await scrape_accel_portfolio()
    
    if companies:
        # Save to JSON
        save_to_json(companies)
        
        print(f"\n{'=' * 60}")
        print(f"SCRAPING COMPLETE - {len(companies)} companies processed")
        print("=" * 60)
    else:
        print("\n⚠️  No companies were extracted")


if __name__ == "__main__":
    asyncio.run(main())
