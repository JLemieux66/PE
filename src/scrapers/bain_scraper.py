"""
Scraper for Bain Capital Private Equity portfolio companies
Website: https://www.baincapitalprivateequity.com/portfolio
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
import re


async def scrape_bain_portfolio():
    """
    Scrape Bain Capital Private Equity's portfolio
    
    Structure:
    - Main page: https://www.baincapitalprivateequity.com/portfolio/current-and-former-portfolio-companies
    - Includes both current and former (exited) portfolio companies
    - Portfolio companies displayed in cards/grid with search/filter
    """
    
    url = "https://www.baincapitalprivateequity.com/portfolio/current-and-former-portfolio-companies"
    all_companies = []
    
    async with async_playwright() as p:
        log_header("BAIN CAPITAL PRIVATE EQUITY PORTFOLIO SCRAPER")
        log_info("🚀 Starting Bain Capital scraper...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Go to portfolio page
            log_info(f"📄 Loading {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Handle cookie consent if present
            try:
                cookie_selectors = [
                    'button:has-text("Accept")',
                    'button:has-text("Accept All")',
                    'button:has-text("I Accept")',
                    '.cookie-accept',
                    '#cookie-accept'
                ]
                for selector in cookie_selectors:
                    accept_button = await page.query_selector(selector)
                    if accept_button:
                        await accept_button.click()
                        await page.wait_for_timeout(1000)
                        log_info("   ✓ Accepted cookies")
                        break
            except:
                pass
            
            # Look for search/filter interface
            # Try to select "All" or remove filters to show all companies
            filter_selectors = [
                'button:has-text("All")',
                'input[type="checkbox"][value="all"]',
                '.filter-all',
                '[data-filter="all"]',
                'button:has-text("Show All")',
                'select option[value="all"]'
            ]
            
            for selector in filter_selectors:
                try:
                    filter_elem = await page.query_selector(selector)
                    if filter_elem:
                        await filter_elem.click()
                        await page.wait_for_timeout(2000)
                        log_info("   ✓ Selected 'All' filter")
                        break
                except:
                    pass
            
            # If there's a dropdown for status (Current/Exited), try selecting "All" or both
            try:
                status_dropdown = await page.query_selector('select[name*="status"], select[name*="filter"]')
                if status_dropdown:
                    await status_dropdown.select_option(value='all')
                    await page.wait_for_timeout(2000)
                    log_info("   ✓ Selected all from dropdown")
            except:
                pass
            
            # Wait for results to load
            await page.wait_for_timeout(5000)
            
            # Debug: Take a screenshot and log page title
            page_title = await page.title()
            log_info(f"   📄 Page title: {page_title}")
            
            # Try clicking a "Show All" or "View All" button
            try:
                show_all_selectors = [
                    'button:has-text("Show All")',
                    'button:has-text("View All")',
                    'a:has-text("Show All")',
                    'a:has-text("View All")',
                    '.show-all',
                    '.view-all'
                ]
                for selector in show_all_selectors:
                    btn = await page.query_selector(selector)
                    if btn:
                        await btn.click()
                        await page.wait_for_timeout(2000)
                        log_info(f"   ✓ Clicked Show All button")
                        break
            except:
                pass
            
            # Scroll down multiple times to trigger lazy loading
            log_info("   ⏳ Scrolling to load all companies...")
            for i in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
            
            # Check if we need to click "Load More" repeatedly
            load_more_clicked = 0
            while load_more_clicked < 10:  # Max 10 clicks
                try:
                    load_more_selectors = [
                        'button:has-text("Load More")',
                        'a:has-text("Load More")',
                        'button:has-text("Show More")',
                        '.load-more',
                        '[class*="load-more"]',
                        'button.btn-load-more'
                    ]
                    clicked = False
                    for selector in load_more_selectors:
                        load_button = await page.query_selector(selector)
                        if load_button and await load_button.is_visible():
                            log_info(f"   ✓ Clicking Load More (#{load_more_clicked + 1})...")
                            await load_button.click()
                            await page.wait_for_timeout(2000)
                            load_more_clicked += 1
                            clicked = True
                            break
                    if not clicked:
                        break
                except:
                    break
            
            # Simple bullet list - just find all list items
            company_cards = []
            
            # Try different list selectors
            list_selectors = [
                'ul li',
                'ol li',
                '.companies-list li',
                '[class*="list"] li',
                'li'
            ]
            
            for selector in list_selectors:
                company_cards = await page.query_selector_all(selector)
                if company_cards and len(company_cards) > 50:  # Should have many companies
                    log_info(f"   ✓ Found {len(company_cards)} items using selector: {selector}")
                    break
            
            log_info(f"📊 Found {len(company_cards)} company entries")
            
            # Extract company information from simple bullet list
            for idx, card in enumerate(company_cards, 1):
                try:
                    company_data = {}
                    
                    # For a simple bullet list, the text is probably just the company name
                    text = await card.inner_text()
                    if not text or not text.strip():
                        continue
                    
                    # Clean up the text - just take the company name
                    company_name = text.strip().split('\n')[0].strip()
                    company_name_lower = company_name.lower()
                    
                    # Skip if it's too short or looks like a navigation item
                    skip_words = ['portfolio', 'current', 'former', 'companies', 'about', 'our values', 
                                  'our history', 'by the numbers', 'private equity', 'credit', 'ventures',
                                  'real estate', 'life sciences', 'tech opportunities', 'special situations',
                                  'impact', 'double impact', 'businesses', 'japan', 'contact', 'careers',
                                  'press', 'news', 'esg', 'dei', 'home', 'search', 'team', 'insights',
                                  'all', 'menu', 'login', 'sign in', 'sign up']
                    
                    # Skip navigation items that start with certain phrases
                    skip_starts = ['about ', 'our ', 'the ', 'contact ', 'all ', 'japan -', 'sign ']
                    
                    if len(company_name) < 2:
                        continue
                    
                    if company_name_lower in skip_words:
                        continue
                    
                    if any(company_name_lower.startswith(phrase) for phrase in skip_starts):
                        continue
                    
                    company_data['name'] = company_name
                    
                    # Try to get any link in the list item
                    link = await card.query_selector('a[href*="http"]')
                    if link:
                        href = await link.get_attribute('href')
                        if href and ('http' in href) and ('baincapital' not in href):
                            company_data['website'] = href
                    
                    # For simple lists, default to Current unless marked otherwise
                    if any(word in text.lower() for word in ['exit', 'sold', 'divested', 'former']):
                        company_data['raw_status'] = 'Exit'
                    else:
                        company_data['raw_status'] = 'Current'
                    
                    # Store source URL
                    company_data['source_url'] = url
                    company_data['last_scraped'] = datetime.now()
                    
                    all_companies.append(company_data)
                    
                    # Only log every 20th company to avoid clutter
                    if idx % 20 == 0 or idx <= 5:
                        log_info(f"   ✓ [{idx}] {company_data['name']}")
                    
                except Exception as e:
                    log_error(f"   ✗ Error extracting company {idx}: {str(e)}")
                    continue
            
            log_success(f"✅ Scraping complete! Found {len(all_companies)} companies")
            
        except Exception as e:
            log_error(f"❌ Error during scraping: {str(e)}")
            
        finally:
            await browser.close()
    
    return all_companies


def save_to_database(companies):
    """Save companies to database v2"""
    log_info(f"💾 Saving {len(companies)} companies to database...")
    
    session = get_session()
    stats = {
        'new_companies': 0,
        'updated_companies': 0,
        'total': 0
    }
    
    try:
        # Get or create PE firm
        pe_firm = session.query(PEFirm).filter_by(name="Bain Capital Private Equity").first()
        if not pe_firm:
            pe_firm = PEFirm(
                name="Bain Capital Private Equity"
            )
            session.add(pe_firm)
            session.commit()
            log_success("✅ Created PE firm: Bain Capital Private Equity")
        
        # Process each company
        for company_data in companies:
            try:
                # Check if company exists
                company = session.query(Company).filter_by(
                    name=company_data['name']
                ).first()
                
                if not company:
                    # Create new company
                    company = Company(
                        name=company_data['name'],
                        description=company_data.get('description'),
                        website=company_data.get('website')
                    )
                    session.add(company)
                    session.flush()  # Get the company ID
                    stats['new_companies'] += 1
                else:
                    # Update existing company if we have new data
                    if company_data.get('description') and not company.description:
                        company.description = company_data['description']
                    if company_data.get('website') and not company.website:
                        company.website = company_data['website']
                    stats['updated_companies'] += 1
                
                # Check if investment relationship already exists
                investment = session.query(CompanyPEInvestment).filter_by(
                    company_id=company.id,
                    pe_firm_id=pe_firm.id
                ).first()
                
                if not investment:
                    # Create new investment relationship
                    investment = CompanyPEInvestment(
                        company_id=company.id,
                        pe_firm_id=pe_firm.id,
                        raw_status=company_data.get('raw_status', 'Current'),
                        investment_year=company_data.get('investment_year'),
                        sector_page=company_data.get('sector_page'),
                        source_url=company_data.get('source_url'),
                        last_scraped=company_data.get('last_scraped')
                    )
                    session.add(investment)
                else:
                    # Update existing investment
                    if company_data.get('raw_status'):
                        investment.raw_status = company_data['raw_status']
                    if company_data.get('sector_page'):
                        investment.sector_page = company_data['sector_page']
                    investment.last_scraped = company_data.get('last_scraped')
                
                stats['total'] += 1
                session.commit()
                
            except Exception as e:
                log_error(f"   ✗ Error saving {company_data.get('name', 'unknown')}: {str(e)}")
                session.rollback()
                continue
        
        log_info("\n📊 Database Summary:")
        log_info(f"   New companies: {stats['new_companies']}")
        log_info(f"   Updated companies: {stats['updated_companies']}")
        log_info(f"   Total companies: {stats['total']}")
        log_success("✅ Scraping and saving complete!")
        
    except Exception as e:
        log_error(f"❌ Database error: {str(e)}")
        session.rollback()
    finally:
        session.close()


async def main():
    companies = await scrape_bain_portfolio()
    if companies:
        save_to_database(companies)
    else:
        log_warning("⚠️ No companies found to save")


if __name__ == "__main__":
    asyncio.run(main())
