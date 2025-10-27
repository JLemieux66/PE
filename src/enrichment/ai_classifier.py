"""
AI-based industry classification for companies missing industry_category
Uses company descriptions to classify into our 19 standardized categories
"""
import os
from openai import OpenAI
from src.models.database_models import get_session, PortfolioCompany, PEFirm
import time

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

INDUSTRY_CATEGORIES = [
    "Technology & Software",
    "Financial Services",
    "Healthcare & Biotech",
    "E-commerce & Retail",
    "Media & Entertainment",
    "Marketing & Advertising",
    "Education & HR",
    "Manufacturing & Industrial",
    "Energy & Sustainability",
    "Transportation & Automotive",
    "Real Estate & Construction",
    "Communication & Collaboration",
    "Artificial Intelligence & Data",
    "Blockchain & Crypto",
    "Consulting & Services",
    "Legal & Compliance",
    "Government & Public Sector",
    "Agriculture & Food",
    "Other"
]

def classify_company_industry(company_name, description):
    """Use GPT to classify company into one of our industry categories"""
    
    prompt = f"""You are a business analyst classifying companies into industry categories.

Company: {company_name}
Description: {description}

Based on the description, classify this company into ONE of these categories:
{', '.join(INDUSTRY_CATEGORIES)}

Rules:
- Choose the MOST specific category that fits
- If multiple categories apply, choose the primary business focus
- Only respond with the exact category name, nothing else
- If truly unclear, respond with "Other"

Category:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise business analyst. Respond with only the category name."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        category = response.choices[0].message.content.strip()
        
        # Validate it's one of our categories
        if category in INDUSTRY_CATEGORIES:
            return category
        else:
            # Try to find a close match
            category_lower = category.lower()
            for cat in INDUSTRY_CATEGORIES:
                if cat.lower() in category_lower or category_lower in cat.lower():
                    return cat
            return "Other"
            
    except Exception as e:
        print(f"      Error with AI classification: {e}")
        return None

def enrich_missing_industries():
    """Enrich companies missing industry_category using AI"""
    
    session = get_session()
    
    # Get companies missing industry_category
    companies = session.query(PortfolioCompany).filter(
        PortfolioCompany.industry_category == None
    ).all()
    
    total = len(companies)
    
    if total == 0:
        print("\n✅ All companies already have industry_category!")
        return
    
    print("=" * 80)
    print("AI-BASED INDUSTRY CLASSIFICATION")
    print("=" * 80)
    print(f"\n📊 Found {total} companies to classify")
    print(f"🤖 Using GPT-4o-mini for classification")
    print(f"📋 Categories: {len(INDUSTRY_CATEGORIES)}\n")
    
    classified = 0
    failed = 0
    
    for i, company in enumerate(companies, 1):
        print(f"[{i}/{total}] {company.name}")
        
        if not company.description:
            print(f"   ⚠️  No description available, skipping")
            failed += 1
            continue
        
        # Classify using AI
        category = classify_company_industry(company.name, company.description)
        
        if category:
            company.industry_category = category
            session.commit()
            classified += 1
            print(f"   ✅ Classified as: {category}")
        else:
            failed += 1
            print(f"   ❌ Classification failed")
        
        # Small delay to avoid rate limits
        time.sleep(0.5)
        
        # Progress update every 25
        if i % 25 == 0:
            print(f"\n📈 Progress: {i}/{total} processed")
            print(f"   ✅ Classified: {classified}")
            print(f"   ❌ Failed: {failed}\n")
    
    session.close()
    
    print("\n" + "=" * 80)
    print("CLASSIFICATION COMPLETE")
    print("=" * 80)
    print(f"✅ Successfully classified: {classified}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success rate: {classified/total*100:.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not set in environment")
        print("   Please set it in your .env file or environment variables")
        exit(1)
    
    enrich_missing_industries()
