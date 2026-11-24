
import os

# Official/public RSS feeds.
# A failed feed will not stop the daily build.

FEEDS = {
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
    "SEC Press Releases": "https://www.sec.gov/news/pressreleases.rss",
    "MarketWatch Top Stories": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Bloomberg Markets": "https://www.bloomberg.com/feeds/markets/news.rss",
    "Investing.com Markets": "https://www.investing.com/rss/news_25.rss",

    # Cryptocurrency
    "Investing.com Crypto": "https://www.investing.com/rss/news_301.rss",

    # Foreign exchange
    "Investing.com Forex": "https://www.investing.com/rss/news_1.rss",

    # Commodities: Gold, Silver, Oil, Natural Gas
    "Investing.com Commodities": "https://www.investing.com/rss/news_11.rss",
}

# Stock market and company news.
HIGH_PRIORITY_KEYWORDS = [
    "s&p 500", "nasdaq", "nyse", "dow jones", "russell 2000",
    "stock market", "stock prices", "equities", "wall street",
    "listed companies", "corporate earnings", "quarterly results",
    "earnings report", "revenue growth", "earnings guidance",
    "initial public offering", "ipo", "share buyback",
    "merger", "acquisition", "stock shares", "market selloff",
    "market rally", "stock futures", "sec investigation",

    # Cryptocurrency
    "bitcoin", "btc", "ethereum", "cryptocurrency",
    "crypto market", "crypto markets", "digital assets",
    "blockchain", "crypto exchange", "bitcoin etf",
    "ethereum etf", "stablecoin",

    # Forex
    "forex", "foreign exchange", "currency pair",
    "exchange rate", "eur/usd", "gbp/usd", "usd/jpy",
    "usd/chf", "usd/cad", "aud/usd", "dollar index",

    # Commodities
    "gold prices", "silver prices", "crude oil",
    "oil prices", "brent crude", "wti crude",
    "natural gas", "copper prices", "commodity market",
    "commodities market",
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
    "central bank", "economic outlook", "government debt",
]

# Important sectors and market-moving developments.
SECTOR_KEYWORDS = [
    "artificial intelligence", "semiconductor", "chipmaker",
    "technology stocks", "banking", "financial sector",
    "energy sector", "tariff", "trade war",
    "trade restrictions", "sanctions", "antitrust",
    "regulation", "credit market", "geopolitical risk",
    "dividend", "bankruptcy", "debt crisis",
    "merger agreement", "precious metals",
    "gold market", "silver market", "oil market",
    "currency market", "exchange markets",
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
