"""
Bain Capital Current Portfolio Scraper (Clean Version)
Only scrapes /portfolio page (current investments only)
Extracts only company names, no descriptions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import asyncio
from playwright.async_api import async_playwright
from src.models.database_models_v2 import get_session, Company, CompanyPEInvestment, PEFirm
from src.utils.logger import log_info, log_success, log_error, log_warning, log_header


async def scrape_current_portfolio():
    """Scrape current portfolio from /portfolio page"""
    url = "https://www.baincapitalprivateequity.com/portfolio"
    companies = []
    
    async with async_playwright() as p:
        log_info("🌐 Opening browser...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            log_info(f"📡 Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Handle cookie consent if present
            try:
                cookie_button = await page.query_selector('button:has-text("Accept")')
                if cookie_button:
                    await cookie_button.click()
                    await page.wait_for_timeout(1000)
                    log_info("✓ Accepted cookies")
            except:
                pass
            
            # Click "All" filter to show all companies
            try:
                all_button = await page.query_selector('button:has-text("All")')
                if all_button:
                    await all_button.click()
                    await page.wait_for_timeout(2000)
                    log_info("✓ Clicked 'All' filter")
            except Exception as e:
                log_warning(f"Could not click 'All' filter: {e}")
            
            # Scroll to load all companies
            log_info("📜 Scrolling to load all companies...")
            for i in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
            
            # Find company cards
            company_cards = await page.query_selector_all('div[class*="company"]')
            log_info(f"✓ Found {len(company_cards)} company cards")
            
            # Extract company names
            for i, card in enumerate(company_cards, 1):
                try:
                    # Try to find heading tag with company name
                    heading_selectors = ['h3', 'h2', 'h4', '.company-name', '[class*="name"]']
                    
                    company_name = None
                    for selector in heading_selectors:
                        heading = await card.query_selector(selector)
                        if heading:
                            name_text = await heading.inner_text()
                            if name_text and name_text.strip():
                                company_name = name_text.strip()
                                break
                    
                    # Fallback: use first line if it looks like a name (short, no period)
                    if not company_name:
                        full_text = await card.inner_text()
                        if full_text:
                            lines = full_text.strip().split('\n')
                            if lines:
                                first_line = lines[0].strip()
                                # Only use if it's short and doesn't look like a description
                                if len(first_line) < 100 and not first_line.endswith('.'):
                                    company_name = first_line
                    
                    if company_name:
                        # Remove "Name:" prefix if present
                        if company_name.startswith("Name:"):
                            company_name = company_name[5:].strip()
                        
                        # Skip if it looks like a description (too long, ends with period, has common description words)
                        if len(company_name) > 150:
                            log_warning(f"   ⚠️  Skipping (too long): {company_name[:50]}...")
                            continue
                        
                        if company_name.endswith('.') and len(company_name) > 50:
                            log_warning(f"   ⚠️  Skipping (looks like description): {company_name[:50]}...")
                            continue
                        
                        if any(phrase in company_name.lower() for phrase in ['is a leading', 'is a ', 'is the', 'provider of', 'developer of']):
                            log_warning(f"   ⚠️  Skipping (description phrase): {company_name[:50]}...")
                            continue
                        
                        companies.append(company_name)
                        if len(companies) <= 10:  # Show first 10
                            log_info(f"   {len(companies)}. {company_name}")
                    
                except Exception as e:
                    log_warning(f"   ⚠️  Error extracting from card {i}: {e}")
                    continue
            
            await browser.close()
            log_success(f"✅ Successfully scraped {len(companies)} companies")
            
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
        pe_firm = session.query(PEFirm).filter_by(name="Bain Capital Private Equity").first()
        if not pe_firm:
            pe_firm = PEFirm(name="Bain Capital Private Equity")
            session.add(pe_firm)
            session.commit()
            log_info("✓ Created PE firm: Bain Capital Private Equity")
        
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
            
            # Create investment (all are current/active)
            investment = CompanyPEInvestment(
                company_id=company.id,
                pe_firm_id=pe_firm.id,
                raw_status='Current'
            )
            investment.normalize_status()  # Set computed_status
            session.add(investment)
            saved += 1
            
            if saved <= 10:  # Show first 10
                log_info(f"   {saved}. {company_name} → Current")
        
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
    log_header("BAIN CAPITAL CURRENT PORTFOLIO SCRAPER")
    
    # Scrape current portfolio
    companies = asyncio.run(scrape_current_portfolio())
    
    if not companies:
        log_error("❌ No companies found!")
        return
    
    log_info(f"\n📊 Total companies scraped: {len(companies)}")
    
    # Save to database
    save_to_database(companies)
    
    log_success("\n✅ All done!")


if __name__ == "__main__":
    main()
