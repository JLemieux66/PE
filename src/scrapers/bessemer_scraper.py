"""
Bessemer Venture Partners Portfolio Scraper
URL: https://www.bvp.com/companies#portfolio
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import asyncio
from playwright.async_api import async_playwright
from src.models.database_models_v2 import get_session, Company, CompanyPEInvestment, PEFirm
from src.utils.logger import log_info, log_success, log_error, log_warning, log_header


async def scrape_bessemer_portfolio():
    """Scrape Bessemer Venture Partners portfolio"""
    url = "https://www.bvp.com/companies#portfolio"
    companies = []
    
    async with async_playwright() as p:
        log_info("🌐 Opening browser...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            log_info(f"📡 Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)  # Wait for JS to load
            
            # Handle cookie consent if present
            try:
                cookie_button = await page.query_selector('button:has-text("Accept")')
                if cookie_button:
                    await cookie_button.click()
                    await page.wait_for_timeout(1000)
                    log_info("✓ Accepted cookies")
            except:
                pass
            
            # Scroll to load all companies
            log_info("📜 Scrolling to load all companies...")
            for i in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
            
            # Find company links - they have href="/companies/[company-name]"
            log_info("🔍 Extracting portfolio companies...")
            
            company_links = await page.query_selector_all('a[href*="/companies/"]')
            log_info(f"✓ Found {len(company_links)} company links")
            
            seen = set()
            
            for link in company_links:
                try:
                    # Get company name from text
                    company_name = await link.inner_text()
                    company_name = company_name.strip()
                    
                    if not company_name:
                        continue
                    
                    # Skip if it's just a ticker or status
                    if company_name.startswith('NASDAQ:') or company_name.startswith('NYSE:'):
                        continue
                    
                    if company_name in ['ACTIVE', 'EXITED', 'IPO', 'ACQUIRED']:
                        continue
                    
                    # Get href for additional context
                    href = await link.get_attribute('href')
                    
                    # Avoid duplicates
                    if company_name.lower() in seen:
                        continue
                    
                    seen.add(company_name.lower())
                    companies.append(company_name)
                    
                    if len(companies) <= 20:  # Show first 20
                        log_info(f"   {len(companies)}. {company_name}")
                
                except Exception as e:
                    continue
            
            log_success(f"✅ Successfully scraped {len(companies)} companies")
            
            await browser.close()
            
        except Exception as e:
            log_error(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()
    
    return companies


def save_to_database(companies):
    """Save scraped companies to database"""
    log_header("SAVING TO DATABASE")
    
    session = get_session()
    
    try:
        # Get or create PE firm
        pe_firm = session.query(PEFirm).filter_by(name="Bessemer Venture Partners").first()
        if not pe_firm:
            pe_firm = PEFirm(name="Bessemer Venture Partners")
            session.add(pe_firm)
            session.commit()
            log_info("✓ Created PE firm: Bessemer Venture Partners")
        
        saved = 0
        skipped = 0
        
        for company_name in companies:
            # Check if company already exists
            company = session.query(Company).filter_by(name=company_name).first()
            
            if not company:
                # Create new company
                company = Company(name=company_name)
                session.add(company)
                session.flush()  # Get the ID
            
            # Check if investment already exists
            existing = session.query(CompanyPEInvestment).filter_by(
                company_id=company.id,
                pe_firm_id=pe_firm.id
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Create investment - we'll mark all as Active for now
            # (Bessemer doesn't clearly distinguish current vs exited on this page)
            investment = CompanyPEInvestment(
                company_id=company.id,
                pe_firm_id=pe_firm.id,
                raw_status='Active'
            )
            investment.normalize_status()  # Set computed_status
            session.add(investment)
            saved += 1
            
            if saved <= 10:  # Show first 10
                log_info(f"   {saved}. {company_name} → Active")
        
        session.commit()
        
        log_success(f"\n✅ Database save complete!")
        log_info(f"   - Saved: {saved} new investments")
        log_info(f"   - Skipped: {skipped} existing investments")
        
    except Exception as e:
        log_error(f"❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


def main():
    log_header("BESSEMER VENTURE PARTNERS SCRAPER")
    
    # Scrape portfolio
    companies = asyncio.run(scrape_bessemer_portfolio())
    
    if not companies:
        log_error("❌ No companies found!")
        return
    
    log_info(f"\n📊 Total companies scraped: {len(companies)}")
    
    # Save to database
    save_to_database(companies)
    
    log_success("\n✅ All done!")


if __name__ == "__main__":
    main()
