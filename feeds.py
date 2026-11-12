import feedparser
import logging
from datetime import datetime, timedelta, timezone
from config import FEEDS, MARKET_KEYWORDS

# Set up simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_filtered_articles(hours=24):
    """Fetches articles from RSS feeds, filters by time and keywords."""
    articles = []
    seen_urls = set()
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    for source_name, url in FEEDS.items():
        logging.info(f"Fetching feeds from {source_name}...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.get("link", "")
                
                # Prevent duplicates
                if link in seen_urls:
                    continue
                
                # Try to parse the published date, fallback to now if missing
                try:
                    # feedparser handles various date formats automatically
                    from time import mktime
                    dt = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
                except (AttributeError, TypeError):
                    dt = datetime.now(timezone.utc)

                # Filter: Only keep articles from the last 24 hours
                if dt < cutoff_time:
                    continue

                title = entry.get("title", "")
                description = entry.get("summary", "")
                text_to_search = (title + " " + description).lower()

                # Filter: Only keep articles matching our keywords
                if any(keyword.lower() in text_to_search for keyword in MARKET_KEYWORDS):
                    articles.append({
                        "title": title,
                        "description": description,
                        "link": link,
                        "source": source_name,
                        "published_time": dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    })
                    seen_urls.add(link)
        except Exception as e:
            logging.error(f"Error fetching {source_name}: {e}")

    logging.info(f"Found {len(articles)} market-relevant articles in the last {hours} hours.")
    return articles