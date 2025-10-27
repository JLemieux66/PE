"""
Scraper for Advent International portfolio companies
Website: https://www.adventinternational.com/investments/
"""
import asyncio
from playwright.async_api import async_playwright
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.models.database_models_v2 import (
    get_session, PEFirm, Company, CompanyPEInvestment
)
from src.utils.logger import log_info, log_success, log_error, log_warning, log_header
import re
from datetime import datetime


async def scrape_advent_portfolio():
    """
    Scrape Advent International's portfolio
    
    Structure:
    - Main page: https://www.adventinternational.com/investments/
    - 429 companies across 43 pages (10 per page)
    - Each company card has: name, date, description, sector tags, press release, website
    """
    
    base_url = "https://www.adventinternational.com/investments/"
    all_companies = []
    
    async with async_playwright() as p:
        log_info("🚀 Starting Advent International scraper...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Go to investments page
            log_info(f"📄 Loading {base_url}")
            await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Get total pages - check the "Last Page" link
            last_page_element = await page.query_selector('a[href*="sf_paged="]:has-text("Last")')
            if last_page_element:
                last_page_href = await last_page_element.get_attribute('href')
                total_pages = int(re.search(r'sf_paged=(\d+)', last_page_href).group(1))
                log_info(f"📊 Found {total_pages} pages to scrape")
            else:
                total_pages = 43  # Fallback from webpage content
                log_info(f"📊 Using fallback: {total_pages} pages")
            
            # Scrape each page
            for page_num in range(1, total_pages + 1):
                page_url = f"{base_url}?sf_paged={page_num}" if page_num > 1 else base_url
                
                log_info(f"\n📄 Scraping page {page_num}/{total_pages}")
                await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2000)
                
                # Wait for company cards to load
                await page.wait_for_selector('h3', timeout=10000)
                
                # Try multiple selectors to find company cards
                company_cards = await page.query_selector_all('article.elementor-post')
                if not company_cards:
                    company_cards = await page.query_selector_all('article')
                if not company_cards:
                    company_cards = await page.query_selector_all('.elementor-post')
                    
                log_info(f"   Found {len(company_cards)} companies on this page")
                
                # Debug: if no cards found, let's see what's on the page
                if len(company_cards) == 0 and page_num == 1:
                    log_warning("   No companies found - debugging selectors...")
                    # Try to find all h3 elements
                    all_h3 = await page.query_selector_all('h3')
                    log_info(f"   Found {len(all_h3)} h3 elements on page")
                    if len(all_h3) > 0:
                        # Get parent structure of first h3
                        first_h3 = all_h3[0]
                        parent = await first_h3.evaluate_handle('el => el.parentElement')
                        parent_tag = await parent.evaluate('el => el.tagName')
                        parent_class = await parent.evaluate('el => el.className')
                        log_info(f"   First h3 parent: <{parent_tag} class='{parent_class}'>")
                
                for card in company_cards:
                    try:
                        # Extract company name (h3 tag)
                        name_elem = await card.query_selector('h3')
                        company_name = await name_elem.inner_text() if name_elem else None
                        
                        if not company_name:
                            continue
                        
                        company_name = company_name.strip()
                        
                        # Extract investment date (before the h3)
                        date_elem = await card.query_selector('.elementor-post__meta-data')
                        investment_date = await date_elem.inner_text() if date_elem else None
                        if investment_date:
                            investment_date = investment_date.strip()
                        
                        # Extract description
                        desc_elem = await card.query_selector('.elementor-post__excerpt p')
                        description = await desc_elem.inner_text() if desc_elem else None
                        if description:
                            description = description.strip()
                        
                        # Extract topics/sectors (all links with topic in href)
                        topic_links = await card.query_selector_all('a[href*="/topics/"]')
                        topics = []
                        sectors = []
                        deal_types = []
                        countries = []
                        
                        for topic_link in topic_links:
                            href = await topic_link.get_attribute('href')
                            text = await topic_link.inner_text()
                            text = text.strip()
                            
                            if '/topics/sectors/' in href:
                                sectors.append(text)
                            elif '/topics/deals/' in href:
                                deal_types.append(text)
                            elif '/topics/countries/' in href:
                                countries.append(text)
                            else:
                                topics.append(text)
                        
                        # Extract website link
                        website = None
                        website_link = await card.query_selector('a[href*="company website"]')
                        if website_link:
                            website = await website_link.get_attribute('href')
                        
                        # Extract press release link
                        press_release = None
                        press_link = await card.query_selector('a[href*="press release"]')
                        if press_link:
                            press_release = await press_link.get_attribute('href')
                        
                        company_data = {
                            'name': company_name,
                            'investment_date': investment_date,
                            'description': description,
                            'sectors': ', '.join(sectors) if sectors else None,
                            'deal_type': ', '.join(deal_types) if deal_types else None,
                            'countries': ', '.join(countries) if countries else None,
                            'website': website,
                            'press_release': press_release,
                            'source_url': page_url,
                        }
                        
                        all_companies.append(company_data)
                        log_info(f"   ✓ {company_name}")
                        
                    except Exception as e:
                        log_error(f"   Error parsing company card: {e}")
                        continue
                
                # Rate limiting
                await page.wait_for_timeout(1000)
            
            log_success(f"\nScraping complete! Found {len(all_companies)} companies")
            
        except Exception as e:
            log_error(f"Scraping failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
    
    return all_companies


def save_to_database(companies_data):
    """Save scraped companies to database"""
    session = get_session()
    
    try:
        # Get or create Advent International PE firm
        pe_firm = session.query(PEFirm).filter_by(name="Advent International").first()
        
        if not pe_firm:
            pe_firm = PEFirm(
                name="Advent International",
                total_companies=len(companies_data),
                current_portfolio_count=len(companies_data),
                last_scraped=datetime.utcnow()
            )
            session.add(pe_firm)
            session.flush()
            log_success(f"Created PE firm: Advent International")
        else:
            pe_firm.total_companies = len(companies_data)
            pe_firm.last_scraped = datetime.utcnow()
            log_success(f"Updated PE firm: Advent International")
        
        # Save companies
        new_count = 0
        updated_count = 0
        
        for company_data in companies_data:
            # Check if company exists (by name and website)
            existing_company = None
            if company_data['website']:
                existing_company = session.query(Company).filter_by(
                    website=company_data['website']
                ).first()
            
            if not existing_company:
                existing_company = session.query(Company).filter_by(
                    name=company_data['name']
                ).first()
            
            # Parse country from countries list
            country = None
            if company_data['countries']:
                country = company_data['countries'].split(',')[0].strip()
            
            if existing_company:
                # Update existing company
                if not existing_company.description and company_data['description']:
                    existing_company.description = company_data['description']
                if not existing_company.website and company_data['website']:
                    existing_company.website = company_data['website']
                if not existing_company.country and country:
                    existing_company.country = country
                
                company = existing_company
                updated_count += 1
            else:
                # Create new company
                company = Company(
                    name=company_data['name'],
                    description=company_data['description'],
                    website=company_data['website'],
                    country=country,
                )
                session.add(company)
                session.flush()
                new_count += 1
            
            # Check if investment relationship already exists
            existing_investment = session.query(CompanyPEInvestment).filter_by(
                company_id=company.id,
                pe_firm_id=pe_firm.id
            ).first()
            
            if not existing_investment:
                # Create investment relationship
                investment = CompanyPEInvestment(
                    company_id=company.id,
                    pe_firm_id=pe_firm.id,
                    raw_status='Active',  # All listed are current investments
                    investment_year=company_data['investment_date'],
                    source_url=company_data['source_url'],
                    sector_page=company_data['sectors'],
                    company=company,
                    pe_firm=pe_firm,
                )
                investment.normalize_status()
                session.add(investment)
        
        session.commit()
        
        log_info(f"\n📊 Database Summary:")
        log_info(f"   New companies: {new_count}")
        log_info(f"   Updated companies: {updated_count}")
        log_info(f"   Total companies: {len(companies_data)}")
        
    except Exception as e:
        log_error(f"Database save failed: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()


async def main():
    """Main execution"""
    log_header("ADVENT INTERNATIONAL PORTFOLIO SCRAPER")
    
    # Scrape portfolio
    companies = await scrape_advent_portfolio()
    
    if companies:
        # Save to database
        log_info(f"\n💾 Saving {len(companies)} companies to database...")
        save_to_database(companies)
        log_success("\nScraping and saving complete!")
    else:
        log_error("No companies found!")


if __name__ == "__main__":
    asyncio.run(main())
