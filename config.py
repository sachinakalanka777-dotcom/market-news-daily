import os

# Official/public RSS feeds. A failed feed will not stop the daily build.
FEEDS = {
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
    "SEC Press Releases": "https://www.sec.gov/news/pressreleases.rss",
    "MarketWatch Top Stories": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Yahoo Finance News": "https://finance.yahoo.com/news/rssindex",
}

MARKET_KEYWORDS = [
    "federal reserve", "fed", "interest rate", "rate cut", "rate hike", "inflation",
    "cpi", "ppi", "pce", "jobs report", "unemployment", "nonfarm payroll",
    "gdp", "treasury", "bond yield", "earnings", "quarterly results", "revenue",
    "guidance", "nasdaq", "nyse", "s&p 500", "dow jones", "russell 2000",
    "wall street", "stock market", "equities", "shares", "tariff", "trade war",
    "sanctions", "oil price", "crude oil", "geopolitical", "recession", "ipo",
    "merger", "acquisition", "antitrust", "sec", "regulation", "artificial intelligence",
    "chipmaker", "semiconductor", "banking", "credit", "consumer spending",
]

# Keep these configurable in GitHub Actions repository variables if desired.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_STORIES = int(os.getenv("MAX_STORIES", "15"))
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "48"))
SITE_DIR = "site"
