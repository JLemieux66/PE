"""
Scraper for Apax Partners portfolio companies
Website: https://www.apax.com/all-investments-listed-alphabetically/
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
from datetime import datetime


async def scrape_apax_portfolio():
    """
    Scrape Apax Partners' portfolio
    
    Structure:
    - Single page: https://www.apax.com/all-investments-listed-alphabetically/
    - Simple table with company names
    - No additional details on this page (just names)
    """
    
    url = "https://www.apax.com/all-investments-listed-alphabetically/"
    all_companies = []
    
    async with async_playwright() as p:
        log_info("🚀 Starting Apax Partners scraper...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Go to investments page
            log_info(f"📄 Loading {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Handle cookie consent if present
            try:
                accept_button = await page.query_selector('button:has-text("Accept All")')
                if accept_button:
                    await accept_button.click()
                    await page.wait_for_timeout(1000)
                    log_info("   ✓ Accepted cookies")
            except:
                pass
            
            # Wait for table to load
            await page.wait_for_selector('table', timeout=10000)
            
            # Get all table cells (td elements contain company names)
            company_cells = await page.query_selector_all('table td')
            log_info(f"📊 Found {len(company_cells)} company entries")
            
            for cell in company_cells:
                try:
                    # Extract company name
                    company_name = await cell.inner_text()
                    
                    if not company_name or company_name.strip() == '':
                        continue
                    
                    company_name = company_name.strip()
                    
                    # Skip if it looks like a header or section title
                    if company_name in ['Company Name', 'Investment', 'Portfolio']:
                        continue
                    
                    company_data = {
                        'name': company_name,
                        'description': None,
                        'website': None,
                        'source_url': url,
                    }
                    
                    all_companies.append(company_data)
                    log_info(f"   ✓ {company_name}")
                    
                except Exception as e:
                    log_error(f"   Error parsing company cell: {e}")
                    continue
            
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
        # Get or create Apax Partners PE firm
        pe_firm = session.query(PEFirm).filter_by(name="Apax Partners").first()
        
        if not pe_firm:
            pe_firm = PEFirm(
                name="Apax Partners",
                total_companies=len(companies_data),
                current_portfolio_count=len(companies_data),
                last_scraped=datetime.utcnow()
            )
            session.add(pe_firm)
            session.flush()
            log_success(f"Created PE firm: Apax Partners")
        else:
            pe_firm.total_companies = len(companies_data)
            pe_firm.last_scraped = datetime.utcnow()
            log_success(f"Updated PE firm: Apax Partners")
        
        # Save companies
        new_count = 0
        updated_count = 0
        
        for company_data in companies_data:
            # Check if company exists (by name since we don't have websites)
            existing_company = session.query(Company).filter_by(
                name=company_data['name']
            ).first()
            
            if existing_company:
                company = existing_company
                updated_count += 1
            else:
                # Create new company
                company = Company(
                    name=company_data['name'],
                    description=company_data['description'],
                    website=company_data['website'],
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
                # Note: Apax page lists ALL investments (current + exited)
                # We'll default to Active since we don't have exit info
                investment = CompanyPEInvestment(
                    company_id=company.id,
                    pe_firm_id=pe_firm.id,
                    raw_status='Current',  # Default assumption
                    source_url=company_data['source_url'],
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
    log_header("APAX PARTNERS PORTFOLIO SCRAPER")
    
    # Scrape portfolio
    companies = await scrape_apax_portfolio()
    
    if companies:
        # Save to database
        log_info(f"\n💾 Saving {len(companies)} companies to database...")
        save_to_database(companies)
        log_success("\nScraping and saving complete!")
    else:
        log_error("No companies found!")


if __name__ == "__main__":
    asyncio.run(main())
