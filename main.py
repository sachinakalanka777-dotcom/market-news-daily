import argparse
import json
import logging
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from feeds import get_filtered_articles
from summarizer import summarize_articles
from image_fetcher import get_image_for_story
from site_builder import build_site

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s: %(message)s")
LOG = logging.getLogger("marketpulse")


def main():
    parser = argparse.ArgumentParser(description="Build MarketPulse daily US market news.")
    parser.add_argument("--date", help="Archive date YYYY-MM-DD (Sri Lanka time)")
    parser.add_argument("--dry-run", action="store_true", help="Print generated data without writing the site")
    parser.add_argument("--skip-images", action="store_true", help="Skip Unsplash lookups")
    args = parser.parse_args()
    load_dotenv()

    now_utc = datetime.now(timezone.utc)
    local_now = now_utc.astimezone(ZoneInfo("Asia/Colombo"))
    date_str = args.date or local_now.strftime("%Y-%m-%d")
    LOG.info("Starting MarketPulse pipeline for %s (Sri Lanka)", date_str)

    articles, feed_status = get_filtered_articles()
    data = summarize_articles(articles)
    data["date"] = date_str
    data["generated_at_utc"] = now_utc.isoformat()
    data["generated_at_local"] = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")
    data["article_count_collected"] = len(articles)
    data["feed_status"] = feed_status

    if not args.skip_images:
        for story in data.get("stories", []):
            image = get_image_for_story(story.get("image_keywords", "US stock market finance"))
            story["image"] = image["url"]
            story["image_credit"] = image["credit"]
            story["image_credit_html"] = image.get("credit_html", image["credit"])

    if args.dry_run:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    build_site(data, date_str)
    LOG.info("Pipeline completed: %d stories, AI provider=%s", len(data.get("stories", [])), data.get("ai_provider"))

if __name__ == "__main__":
    main()
