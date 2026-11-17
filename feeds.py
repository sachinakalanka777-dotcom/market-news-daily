
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from time import mktime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import feedparser
import requests

from config import (
    FEEDS,
    MARKET_KEYWORDS,
    HIGH_PRIORITY_KEYWORDS,
    MACRO_KEYWORDS,
    SECTOR_KEYWORDS,
    LOOKBACK_HOURS,
)

LOG = logging.getLogger(__name__)

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign",
    "utm_term", "utm_content", "fbclid", "gclid"
}


def clean_html(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def canonical_url(url):
    if not url:
        return ""

    parts = urlsplit(url.strip())
    query = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]

    return urlunsplit((
        parts.scheme or "https",
        parts.netloc.lower(),
        parts.path.rstrip("/"),
        urlencode(query),
        ""
    ))


def parse_entry_date(entry):
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)

        if parsed:
            try:
                return datetime.fromtimestamp(
                    mktime(parsed),
                    tz=timezone.utc
                )
            except (TypeError, ValueError, OverflowError):
                pass

    return None


def relevance_score(title, description):
    text = f"{title} {description}".lower()

    score = 0
    hits = []

    keyword_groups = [
        (HIGH_PRIORITY_KEYWORDS, 15),
        (MACRO_KEYWORDS, 10),
        (SECTOR_KEYWORDS, 6),
    ]

    for keywords, points in keyword_groups:
        for keyword in keywords:
            if keyword.lower() in text and keyword not in hits:
                score += points
                hits.append(keyword)

    return min(100, score), hits


def fetch_feed(url, headers, retries=2):
    last_error = None

    for attempt in range(retries + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=(10, 25)
            )
            response.raise_for_status()
            return response.content

        except requests.RequestException as exc:
            last_error = exc

            if attempt < retries:
                wait = 2 ** attempt
                LOG.warning(
                    "Feed request failed. Retry %d/%d in %d seconds: %s",
                    attempt + 1,
                    retries,
                    wait,
                    exc
                )
                time.sleep(wait)

    raise last_error


def get_filtered_articles(hours=None):
    hours = hours or LOOKBACK_HOURS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    articles = []
    seen = set()
    feed_status = []

    headers = {
        "User-Agent": "MarketPulseNews/3.0 (+https://marketpulsenews.online)"
    }

    for source_name, feed_url in FEEDS.items():

        try:
            content = fetch_feed(feed_url, headers)
            parsed = feedparser.parse(content)

            if parsed.bozo and not parsed.entries:
                raise ValueError(str(parsed.bozo_exception))

            added = 0

            for entry in parsed.entries:

                title = clean_html(entry.get("title", ""))
                link = canonical_url(entry.get("link", ""))

                description = clean_html(
                    entry.get("summary", entry.get("description", ""))
                )

                if not title or not link or link in seen:
                    continue

                published = parse_entry_date(entry)

                if published and published < cutoff:
                    continue

                score, hits = relevance_score(title, description)

                # Preserve official regulatory and central bank announcements.
                if source_name in ("Federal Reserve", "SEC Press Releases"):
                    score = max(score, 15)

                # Filter low-relevance articles.
                if score < 10:
                    continue

                articles.append({
                    "title": title[:300],
                    "description": description[:1200],
                    "link": link,
                    "source": source_name,
                    "published_time": (
                        published.isoformat()
                        if published
                        else "Date not supplied by source"
                    ),
                    "relevance_score": score,
                    "matched_keywords": hits[:8],
                    "article_id": f"a{len(articles)}",
                })

                seen.add(link)
                added += 1

            feed_status.append({
                "source": source_name,
                "status": "ok",
                "items": added
            })

            LOG.info(
                "Fetched %s: %s relevant items",
                source_name,
                added
            )

        except Exception as exc:
            LOG.warning("Feed failed (%s): %s", source_name, exc)

            feed_status.append({
                "source": source_name,
                "status": "error",
                "error": str(exc)[:240]
            })

    # Highest relevance first, then newest known publication date.
    articles.sort(
        key=lambda x: (
            x["relevance_score"],
            x["published_time"]
        ),
        reverse=True
    )

    # Reassign IDs after sorting to keep IDs consistent with final order.
    for index, article in enumerate(articles):
        article["article_id"] = f"a{index}"

    LOG.info(
        "Collected %d unique market-relevant stories",
        len(articles)
    )

    return articles, feed_status
