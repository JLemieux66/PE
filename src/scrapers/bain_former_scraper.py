"""
Bain Capital Former Portfolio Scraper
Scrapes /current-and-former-portfolio-companies page
Adds companies that aren't already in DB (those are former investments)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import asyncio
from playwright.async_api import async_playwright
from src.models.database_models_v2 import get_session, Company, CompanyPEInvestment, PEFirm
from src.utils.logger import log_info, log_success, log_error, log_warning, log_header


async def scrape_all_companies():
    """Scrape all companies (current + former) from the list page"""
    url = "https://www.baincapitalprivateequity.com/portfolio/current-and-former-portfolio-companies"
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
            
            # Scroll to load all companies
            log_info("📜 Scrolling to load all companies...")
            for i in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
            
            # This page is a simple bullet list - find all list items
            list_items = await page.query_selector_all('ul li')
            log_info(f"✓ Found {len(list_items)} list items")
            
            # Extract company names
            skipped_items = []
            for i, item in enumerate(list_items, 1):
                try:
                    text = await item.inner_text()
                    if not text or not text.strip():
                        continue
                    
                    company_name = text.strip()
                    
                    # Skip navigation items - only exact matches for navigation
                    skip_exact = [
                        'Our History', 'By the Numbers', 'Japan - 日本', 
                        'Special Situations', 'Venture', 'Tech Opportunities',
                        'Life Sciences', 'Public Equity', 'Partnership Strategies',
                        'Insurance', 'Double Impact', 'Crypto', 'Businesses', 'Corporate',
                        'Portfolio', 'About', 'Team', 'Contact', 'Careers', 'News',
                        'Insights', 'Privacy', 'Terms', 'People', 'Industries', 'Geography',
                        'Sectors', 'Approach', 'Strategy', 'Values', 'Cookie',
                        'About Bain Capital', 'Our Values', 'Private Equity', 'Credit',
                        'Real Estate', 'Ventures', 'Venture Capital'
                    ]
                    
                    if company_name in skip_exact:
                        skipped_items.append(('exact match', company_name))
                        continue
                    
                    # Skip if too short (likely junk)
                    if len(company_name) < 2:
                        skipped_items.append(('too short', company_name))
                        continue
                    
                    # Skip if it looks like a description (very long or ends with period)
                    if len(company_name) > 150:
                        skipped_items.append(('too long', company_name[:50]))
                        log_warning(f"   ⚠️  Skipping (too long): {company_name[:50]}...")
                        continue
                    
                    if company_name.endswith('.') and len(company_name) > 50:
                        skipped_items.append(('description', company_name[:50]))
                        log_warning(f"   ⚠️  Skipping (looks like description): {company_name[:50]}...")
                        continue
                    
                    # Skip common description phrases
                    if any(phrase in company_name.lower() for phrase in [
                        'is a leading', 'is a ', 'is the', 'provider of', 
                        'developer of', 'manufacturer of', 'operator of'
                    ]):
                        skipped_items.append(('description phrase', company_name[:50]))
                        log_warning(f"   ⚠️  Skipping (description phrase): {company_name[:50]}...")
                        continue
                    
                    companies.append(company_name)
                    if len(companies) <= 15:  # Show first 15
                        log_info(f"   {len(companies)}. {company_name}")
                    
                except Exception as e:
                    continue
            
            log_info(f"\n📊 Skipped {len(skipped_items)} items")
            if len(skipped_items) > 0:
                log_info(f"   First 10 skipped:")
                for reason, name in skipped_items[:10]:
                    log_info(f"   - [{reason}] {name[:50] if len(name) > 50 else name}")
            
            await browser.close()
            log_success(f"✅ Successfully scraped {len(companies)} companies")
            
        except Exception as e:
            log_error(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()
    
    return companies


def save_former_companies(all_companies):
    """Save companies that aren't already in DB (those are former investments)"""
    log_header("SAVING FORMER INVESTMENTS")
    
    session = get_session()
    
    try:
        # Get PE firm
        pe_firm = session.query(PEFirm).filter_by(name="Bain Capital Private Equity").first()
        if not pe_firm:
            log_error("❌ Bain Capital Private Equity not found")
            return
        
        # Get current companies already in database
        existing_investments = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id
        ).all()
        
        existing_names = {inv.company.name.lower() for inv in existing_investments}
        log_info(f"✓ Found {len(existing_names)} existing current investments")
        
        # Find companies not in database (those are former)
        former_companies = []
        for company_name in all_companies:
            if company_name.lower() not in existing_names:
                former_companies.append(company_name)
        
        log_info(f"✓ Found {len(former_companies)} former investments to add")
        
        if not former_companies:
            log_success("✅ No new former investments to add!")
            return
        
        # Show sample
        log_info(f"\n📋 Sample former investments:")
        for name in former_companies[:10]:
            log_info(f"   • {name}")
        
        saved = 0
        
        for company_name in former_companies:
            # Check if company already exists (might be in other PE firm's portfolio)
            company = session.query(Company).filter_by(name=company_name).first()
            
            if not company:
                # Create new company
                company = Company(name=company_name)
                session.add(company)
                session.flush()  # Get the ID
            
            # Check if investment already exists (shouldn't happen, but be safe)
            existing_inv = session.query(CompanyPEInvestment).filter_by(
                company_id=company.id,
                pe_firm_id=pe_firm.id
            ).first()
            
            if existing_inv:
                continue  # Skip if already exists
            
            # Create investment as Exit
            investment = CompanyPEInvestment(
                company_id=company.id,
                pe_firm_id=pe_firm.id,
                raw_status='Exit'
            )
            investment.normalize_status()  # Set computed_status
            session.add(investment)
            saved += 1
            
            if saved <= 10:  # Show first 10
                log_info(f"   {saved}. {company_name} → Exit")
        
        session.commit()
        
        log_success(f"\n✅ Database save complete!")
        log_info(f"   - Saved: {saved} former investments")
        
        # Final count
        total_investments = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id
        ).count()
        
        active_count = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id,
            computed_status='Active'
        ).count()
        
        exit_count = session.query(CompanyPEInvestment).filter_by(
            pe_firm_id=pe_firm.id,
            computed_status='Exit'
        ).count()
        
        log_info(f"\n📊 Final Bain Capital Portfolio:")
        log_info(f"   Total: {total_investments}")
        log_info(f"   Active: {active_count} ({active_count/total_investments*100:.1f}%)")
        log_info(f"   Exit: {exit_count} ({exit_count/total_investments*100:.1f}%)")
        
    except Exception as e:
        log_error(f"❌ Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


def main():
    log_header("BAIN CAPITAL FORMER PORTFOLIO SCRAPER")
    
    # Scrape all companies (current + former)
    all_companies = asyncio.run(scrape_all_companies())
    
    if not all_companies:
        log_error("❌ No companies found!")
        return
    
    log_info(f"\n📊 Total companies scraped: {len(all_companies)}")
    
    # Save former companies (those not already in DB)
    save_former_companies(all_companies)
    
    log_success("\n✅ All done!")


if __name__ == "__main__":
    main()
