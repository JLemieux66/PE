"""
Standardize 288 unique industries into ~15 broad categories
"""
from database_models import get_session, PortfolioCompany
from sqlalchemy import func

# Industry category mappings - maps specific industries to broad categories
INDUSTRY_CATEGORIES = {
    "Technology & Software": [
        "software", "saas", "enterprise software", "apps", "cloud computing",
        "information technology", "it services", "it consulting", "computer",
        "cloud infrastructure", "platform as a service", "paas", "iaas",
        "it system custom software", "application software", "system software",
        "productivity tools", "collaboration software", "project management",
        "cloud security", "devops", "api", "web development", "mobile",
        "customer service", "crm", "service management", "helpdesk",
        "cloud management", "cloud data services", "network hardware",
        "hardware", "systems and information", "ios", "android", "web services",
        "digital signage", "b2b", "vertical software", "server", "hosting",
        "internet", "enterprise applications", "enterprise resource planning", "erp",
        "application performance", "fleet management", "performance management",
        "application", "tech", "it", "web", "online platform",
        "skout", "dating", "automation", "a/b testing", "electronic equipment",
        "machinery", "commercial", "bpo", "outsource services",
        "opengov", "data visualization", "executive office",
    ],
    
    "Artificial Intelligence & Data": [
        "artificial intelligence", "ai", "machine learning", "analytics",
        "data analytics", "big data", "data science", "business intelligence",
        "predictive analytics", "data management", "database", "data infrastructure",
        "natural language processing", "nlp", "computer vision", "deep learning",
    ],
    
    "Cybersecurity": [
        "cyber security", "cybersecurity", "security", "information security",
        "network security", "endpoint security", "identity management",
        "threat detection", "security software", "privacy", "data security",
    ],
    
    "Healthcare & Biotech": [
        "health care", "healthcare", "biotechnology", "biopharma", "medical",
        "pharmaceuticals", "life sciences", "clinical trials", "medical devices",
        "health insurance", "telemedicine", "digital health", "wellness",
        "hospital", "diagnostics", "therapeutics", "genomics", "health tech",
        "healthtech", "fertility", "department stores", "cedar",
    ],
    
    "Financial Services": [
        "financial services", "fintech", "banking", "finance", "insurance",
        "payments", "lending", "wealth management", "asset management",
        "capital markets", "trading", "investment", "accounting", "tax",
        "billing", "financial technology", "regtech", "insurtech", "payment systems",
        "wealth", "association",
    ],
    
    "E-commerce & Retail": [
        "e-commerce", "ecommerce", "retail", "shopping", "marketplace",
        "consumer goods", "fashion", "apparel", "clothing", "footwear",
        "luxury goods", "beauty", "cosmetics", "jewelry", "food delivery",
        "grocery", "consumer", "direct-to-consumer", "d2c",
        "commercial services", "business supplies", "equipment",
    ],
    
    "Marketing & Advertising": [
        "marketing", "advertising", "adtech", "marketing automation",
        "digital marketing", "social media marketing", "content marketing",
        "seo", "sem", "marketing analytics", "brand management", "public relations",
        "customer relationship management", "sales enablement",
        "ad server", "advertising platform", "digital advertising",
    ],
    
    "Media & Entertainment": [
        "media", "entertainment", "gaming", "video games", "streaming",
        "music", "video", "content", "publishing", "news", "social media",
        "social network", "creator economy", "influencer", "esports",
        "film", "graphic design", "communities", "spectator sports",
        "reddit", "sports", "leisure", "casual games", "recipes", "cooking",
    ],
    
    "Real Estate & Construction": [
        "real estate", "construction", "property", "buildings", "proptech",
        "property management", "commercial real estate", "residential",
        "architecture", "engineering", "infrastructure", "facilities",
    ],
    
    "Manufacturing & Industrial": [
        "manufacturing", "industrial", "supply chain", "logistics", "warehousing",
        "distribution", "procurement", "inventory management", "3d printing",
        "robotics", "automation", "iot", "internet of things", "smart manufacturing",
        "electronics", "advanced materials", "bakery", "materials",
        "synthetic textiles", "textiles",
    ],
    
    "Transportation & Automotive": [
        "transportation", "automotive", "mobility", "logistics", "shipping",
        "freight", "delivery", "ridesharing", "car sharing", "electric vehicles",
        "ev", "autonomous vehicles", "drone", "aerospace", "aviation",
        "lyft", "road",
    ],
    
    "Energy & Sustainability": [
        "energy", "renewable energy", "clean energy", "solar", "wind",
        "sustainability", "cleantech", "climate tech", "carbon", "environmental",
        "green technology", "battery", "energy storage", "oil & gas", "utilities",
        "oil and gas", "fal",
    ],
    
    "Education & HR": [
        "education", "edtech", "e-learning", "online learning", "training",
        "learning management", "human resources", "hr", "recruiting",
        "talent management", "workforce", "payroll", "employee engagement",
        "professional development", "corporate training", "employee benefits",
        "children", "assisted living", "child care", "non-profit",
        "glossbird", "language learning", "employment", "career planning",
    ],
    
    "Communication & Collaboration": [
        "communication", "collaboration", "messaging", "video conferencing",
        "unified communications", "voip", "telecommunications", "telecom",
        "networking", "workflow", "productivity", "workplace",
    ],
    
    "Agriculture & Food": [
        "agriculture", "agtech", "farming", "food", "food and beverage",
        "restaurant", "hospitality", "travel", "tourism", "hotel",
        "animal feed", "catering", "brewing",
    ],
    
    "Legal & Compliance": [
        "legal", "legaltech", "compliance", "regulatory", "contract management",
        "intellectual property", "patent", "governance", "risk management",
        "advice",
    ],
    
    "Blockchain & Crypto": [
        "blockchain", "cryptocurrency", "crypto", "web3", "defi",
        "decentralized finance", "nft", "digital assets", "bitcoin", "ethereum",
    ],
    
    "Government & Public Sector": [
        "government", "public sector", "civic tech", "govtech", "defense",
        "military", "national security", "public safety", "emergency",
    ],
    
    "Consulting & Services": [
        "consulting", "professional services", "business services",
        "advisory", "management consulting", "strategy", "outsourcing",
        "information services", "holding companies",
    ],
    
    "Other": [
        # Catch-all for anything that doesn't fit
    ]
}


def categorize_industry(industry_name):
    """
    Categorize an industry into one of the broad categories
    
    Args:
        industry_name: The specific industry name from Swarm
        
    Returns:
        str: The broad category name
    """
    if not industry_name:
        return "Other"
    
    industry_lower = industry_name.lower().strip()
    
    # Check each category's keywords
    for category, keywords in INDUSTRY_CATEGORIES.items():
        for keyword in keywords:
            if keyword in industry_lower:
                return category
    
    # If no match found, return Other
    return "Other"


def standardize_all_industries():
    """Add standardized industry categories to all companies"""
    session = get_session()
    
    try:
        # Get all companies with industries
        companies = session.query(PortfolioCompany).filter(
            PortfolioCompany.swarm_industry != None,
            PortfolioCompany.swarm_industry != ''
        ).all()
        
        total = len(companies)
        print(f"\n📊 Standardizing industries for {total} companies...\n")
        
        # Track category distribution
        category_counts = {}
        
        for i, company in enumerate(companies, 1):
            original_industry = company.swarm_industry
            category = categorize_industry(original_industry)
            
            # Store in existing swarm_industry field (we'll keep original in new field)
            company.industry_category = category
            
            # Count categories
            category_counts[category] = category_counts.get(category, 0) + 1
            
            if i % 100 == 0:
                print(f"  Processed {i}/{total} companies...")
        
        session.commit()
        
        print(f"\n✅ Standardization complete!\n")
        print("Category distribution:")
        print("=" * 60)
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"{category:40} {count:4} ({percentage:.1f}%)")
        
        print("=" * 60)
        print(f"Total categories: {len(category_counts)}")
        print(f"Total companies: {total}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
    finally:
        session.close()


def show_category_examples():
    """Show example companies in each category"""
    session = get_session()
    
    categories = list(INDUSTRY_CATEGORIES.keys())
    
    print("\n📋 Example companies by category:\n")
    
    for category in categories[:5]:  # Show first 5 categories as examples
        print(f"\n{category}:")
        print("-" * 60)
        
        companies = session.query(PortfolioCompany).filter(
            PortfolioCompany.swarm_industry != None
        ).limit(100).all()
        
        examples = []
        for c in companies:
            if categorize_industry(c.swarm_industry) == category:
                examples.append((c.name, c.swarm_industry))
                if len(examples) >= 5:
                    break
        
        for name, orig_industry in examples:
            print(f"  • {name:30} (was: {orig_industry})")
    
    session.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        show_category_examples()
    else:
        print("\n⚠️  This will standardize all industries into ~19 categories.")
        print("Original industry names will be preserved in 'swarm_industry' field.")
        print("Standardized categories will be added to 'industry_category' field.")
        
        response = input("\nContinue? (yes/no): ")
        if response.lower() == 'yes':
            standardize_all_industries()
        else:
            print("Cancelled.")
