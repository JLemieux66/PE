"""Configuration for Private Equity firms to crawl for portfolio company information."""

# List of major private equity firms and their websites
PE_FIRMS = [
    {
        "name": "Blackstone",
        "url": "https://www.blackstone.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "KKR",
        "url": "https://www.kkr.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "The Carlyle Group",
        "url": "https://www.carlyle.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "TPG",
        "url": "https://www.tpg.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Warburg Pincus",
        "url": "https://www.warburgpincus.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "CVC Capital Partners",
        "url": "https://www.cvc.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Apollo Global Management",
        "url": "https://www.apollo.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Advent International",
        "url": "https://www.adventinternational.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Bain Capital",
        "url": "https://www.baincapital.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Silver Lake",
        "url": "https://www.silverlake.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Vista Equity Partners",
        "url": "https://www.vistaequitypartners.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Thoma Bravo",
        "url": "https://www.thomabravo.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "General Atlantic",
        "url": "https://www.generalatlantic.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Hellman & Friedman",
        "url": "https://www.hf.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Leonard Green & Partners",
        "url": "https://www.leonardgreen.com",
        "portfolio_page": "/companies"
    },
    {
        "name": "Providence Equity Partners",
        "url": "https://www.provequity.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Francisco Partners",
        "url": "https://www.franciscopartners.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "EQT",
        "url": "https://www.eqtgroup.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Permira",
        "url": "https://www.permira.com",
        "portfolio_page": "/portfolio"
    },
    {
        "name": "Apax Partners",
        "url": "https://www.apax.com",
        "portfolio_page": "/portfolio"
    }
]

# Search instructions optimized for finding portfolio company information
# Keep it concise per Tavily's requirements
PORTFOLIO_SEARCH_INSTRUCTIONS = "Find portfolio companies, investments, and current active portfolio information"
