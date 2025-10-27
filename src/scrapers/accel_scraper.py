"""
Accel Portfolio Scraper - Extract company data from Accel's portfolio page
"""

import asyncio
import sys
import os
from playwright.async_api import async_playwright

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.database_models import PortfolioCompany, PEFirm, get_session

# Constants
ACCEL_URL = "https://www.accel.com/relationships"
PE_FIRM_NAME = "Accel"


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
            
            # Find all company cards
            company_cards = await page.query_selector_all('.company-card_component')
            print(f"   Found {len(company_cards)} company cards")
            
            for i, card in enumerate(company_cards):
                try:
                    # Extract company name from h3 with accel-content="company-name"
                    name_element = await card.query_selector('h3[accel-content="company-name"]')
                    if not name_element:
                        continue
                    
                    name = (await name_element.inner_text()).strip()
                    
                    # Extract slug from the mobile link
                    link_element = await card.query_selector('a.company-card_mobile-link[param-slug]')
                    slug = await link_element.get_attribute('param-slug') if link_element else None
                    website = f"https://www.accel.com/relationships/{slug}" if slug else None
                    
                    # Extract description from company-short-description
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
                        # Split by newlines and filter empty strings
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
                    
                    company_data = {
                        'name': name,
                        'website': website,
                        'description': description,
                        'founders': ', '.join(founders) if founders else None,
                        'first_investment_type': first_event_type if first_event_type else None,
                        'first_investment_date': first_event_date if first_event_date else None,
                        'slug': slug
                    }
                    
                    companies.append(company_data)
                    
                    if (i + 1) % 100 == 0:
                        print(f"   Processed {i + 1} companies...")
                
                except Exception as e:
                    print(f"   ⚠️  Error processing card {i}: {e}")
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


def save_to_database(companies):
    """Save companies to database."""
    if not companies:
        print("\n⚠️  No companies to save")
        return
    
    print(f"\n💾 Saving {len(companies)} companies to database...")
    
    session = get_session()
    
    try:
        # Get or create PE firm
        firm = session.query(PEFirm).filter_by(name=PE_FIRM_NAME).first()
        if not firm:
            print(f"   Creating new PE firm: {PE_FIRM_NAME}")
            firm = PEFirm(
                name=PE_FIRM_NAME,
                total_companies=0
            )
            session.add(firm)
            session.flush()
        
        saved_count = 0
        updated_count = 0
        
        for company_data in companies:
            # Check if company already exists
            existing = session.query(PortfolioCompany).filter_by(
                name=company_data['name'],
                pe_firm_id=firm.id
            ).first()
            
            if existing:
                # Update existing company
                if company_data.get('description'):
                    existing.description = company_data['description']
                if company_data.get('website'):
                    existing.website = company_data['website']
                updated_count += 1
            else:
                # Create new company
                # Combine description with founders info
                full_description = company_data.get('description', '')
                if company_data.get('founders'):
                    full_description += f"\n\nFounders: {company_data['founders']}"
                
                new_company = PortfolioCompany(
                    name=company_data['name'],
                    pe_firm_id=firm.id,
                    website=company_data.get('website'),
                    description=full_description,
                    status="Active"  # Default status
                )
                session.add(new_company)
                saved_count += 1
        
        # Update firm's total count
        firm.total_companies = session.query(PortfolioCompany).filter_by(pe_firm_id=firm.id).count()
        
        session.commit()
        
        print(f"\n✅ Database updated successfully!")
        print(f"   📈 New companies: {saved_count}")
        print(f"   🔄 Updated companies: {updated_count}")
        print(f"   📊 Total Accel companies: {firm.total_companies}")
        
    except Exception as e:
        print(f"\n❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


async def main():
    """Main execution function."""
    print("=" * 60)
    print("ACCEL PORTFOLIO SCRAPER")
    print("=" * 60)
    
    # Scrape companies
    companies = await scrape_accel_portfolio()
    
    if companies:
        # Save to database
        save_to_database(companies)
        
        print(f"\n{'=' * 60}")
        print(f"SCRAPING COMPLETE - {len(companies)} companies processed")
        print("=" * 60)
    else:
        print("\n⚠️  No companies were extracted")


if __name__ == "__main__":
    asyncio.run(main())
