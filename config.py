import os

# RSS Feeds for news sources
# Note: RSS URLs can occasionally change. If one stops working, search the source's website for "RSS feeds".
FEEDS = {
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
    "SEC Press Releases": "https://www.sec.gov/news/pressreleases.rss"
}

# Keywords to filter out noise and only keep market-relevant news
MARKET_KEYWORDS = [
    "Fed", "rates", "inflation", "jobs", "GDP", "earnings", "tariffs", 
    "oil", "bond yields", "stocks", "market", "economy", "sanctions", 
    "trade", "regulation", "NYSE", "NASDAQ", "S&P 500", "Dow Jones"
]

# Output directory for the static site
SITE_DIR = "site"