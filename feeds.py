import logging
import re
from datetime import datetime, timedelta, timezone
from time import mktime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import feedparser
import requests

from config import FEEDS, MARKET_KEYWORDS, LOOKBACK_HOURS

LOG = logging.getLogger(__name__)
TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}


def clean_html(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def canonical_url(url):
    if not url:
        return ""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    return urlunsplit((parts.scheme or "https", parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))


def parse_entry_date(entry):
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass
    # Missing dates are retained but marked unknown; do not falsely claim they are current.
    return None


def relevance_score(title, description):
    text = f"{title} {description}".lower()
    hits = [kw for kw in MARKET_KEYWORDS if kw in text]
    return min(100, len(hits) * 12), hits


def get_filtered_articles(hours=None):
    hours = hours or LOOKBACK_HOURS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles, seen = [], set()
    feed_status = []
    headers = {"User-Agent": "MarketPulseNews/2.0 (+https://marketpulsenews.online)"}

    for source_name, feed_url in FEEDS.items():
        try:
            response = requests.get(feed_url, headers=headers, timeout=20)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            if parsed.bozo and not parsed.entries:
                raise ValueError(str(parsed.bozo_exception))
            added = 0
            for entry in parsed.entries:
                title = clean_html(entry.get("title", ""))
                link = canonical_url(entry.get("link", ""))
                description = clean_html(entry.get("summary", entry.get("description", "")))
                if not title or not link or link in seen:
                    continue
                published = parse_entry_date(entry)
                if published and published < cutoff:
                    continue
                score, hits = relevance_score(title, description)
                # Keep authoritative Fed/SEC releases even if they do not contain a keyword.
                if score < 12 and source_name not in ("Federal Reserve", "SEC Press Releases"):
                    continue
                articles.append({
                    "title": title[:300], "description": description[:1200],
                    "link": link, "source": source_name,
                    "published_time": published.isoformat() if published else "Date not supplied by source",
                    "relevance_score": score, "matched_keywords": hits[:8],
                    "article_id": f"a{len(articles)}",
                })
                seen.add(link)
                added += 1
            feed_status.append({"source": source_name, "status": "ok", "items": added})
            LOG.info("Fetched %s: %s relevant items", source_name, added)
        except Exception as exc:
            LOG.warning("Feed failed (%s): %s", source_name, exc)
            feed_status.append({"source": source_name, "status": "error", "error": str(exc)[:240]})

    articles.sort(key=lambda x: (x["relevance_score"], x["published_time"]), reverse=True)
    LOG.info("Collected %d unique market-relevant stories", len(articles))
    return articles, feed_status
