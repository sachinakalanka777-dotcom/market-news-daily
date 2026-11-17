
import os

# Official/public RSS feeds.
# A failed feed will not stop the daily build.
FEEDS = {
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
    "SEC Press Releases": "https://www.sec.gov/news/pressreleases.rss",
    "MarketWatch Top Stories": "https://feeds.marketwatch.com/marketwatch/topstories/",
}

# Strong indicators of US stock-market relevance.
HIGH_PRIORITY_KEYWORDS = [
    "s&p 500", "nasdaq", "nyse", "dow jones", "russell 2000",
    "stock market", "stock prices", "equities", "wall street",
    "listed companies", "corporate earnings", "quarterly results",
    "earnings report", "revenue growth", "earnings guidance",
    "initial public offering", "ipo", "share buyback",
    "merger", "acquisition", "stock shares", "market selloff",
    "market rally", "stock futures", "sec investigation",
]

# Important macroeconomic and monetary-policy topics.
MACRO_KEYWORDS = [
    "federal reserve", "interest rate", "rate cut", "rate hike",
    "inflation", "consumer price index", "cpi", "producer price index",
    "ppi", "personal consumption expenditures", "pce",
    "jobs report", "unemployment", "nonfarm payroll",
    "gross domestic product", "gdp", "treasury yield",
    "bond yield", "recession", "consumer spending",
    "economic growth", "monetary policy",
]

# Important sectors and market-moving developments.
SECTOR_KEYWORDS = [
    "artificial intelligence", "semiconductor", "chipmaker",
    "technology stocks", "banking", "financial sector",
    "oil prices", "crude oil", "energy sector",
    "tariff", "trade war", "trade restrictions",
    "sanctions", "antitrust", "regulation",
    "credit market", "geopolitical risk", "dividend",
    "bankruptcy", "debt crisis", "merger agreement",
]

# Combined keyword list for compatibility with existing code.
MARKET_KEYWORDS = list(dict.fromkeys(
    HIGH_PRIORITY_KEYWORDS + MACRO_KEYWORDS + SECTOR_KEYWORDS
))

# AI settings
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Publishing settings
MAX_STORIES = int(os.getenv("MAX_STORIES", "15"))
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "48"))

SITE_DIR = "site"
