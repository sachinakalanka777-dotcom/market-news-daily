import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
import logging

from feeds import get_filtered_articles
from summarizer import summarize_articles
from image_fetcher import get_image_for_story
from site_builder import build_site

def main():
    # Setup command line arguments
    parser = argparse.ArgumentParser(description="Build daily market news site.")
    parser.add_argument("--date", type=str, help="Override date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run", action="store_true", help="Run without building the site")
    args = parser.parse_args()

    # Load API keys from .env file (if running locally)
    load_dotenv()
    
    logging.info(f"Starting news pipeline for date: {args.date}")

    # 1. Fetch and filter articles
    articles = get_filtered_articles(hours=72)

    # 2. Summarize with Gemini
    ai_data = summarize_articles(articles)
    
    # 3. Fetch images for each story
    for story in ai_data.get("stories", []):
        keywords = story.get("image_keywords", "market, finance")
        image_data = get_image_for_story(keywords)
        story["image"] = image_data["url"]
        story["image_credit"] = image_data["credit"]

    if args.dry_run:
        logging.info("Dry run complete. Generated Data:")
        import json
        print(json.dumps(ai_data, indent=2))
        return

    # 4. Build static HTML site
    build_site(ai_data, args.date)
    logging.info("Pipeline finished successfully.")

if __name__ == "__main__":
    main()