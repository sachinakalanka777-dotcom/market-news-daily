
import logging
import os
import random
import re
import requests

UTM = "?utm_source=marketpulsenews&utm_medium=referral"

FALLBACK_QUERIES = {
    "business": "business office corporate",
    "technology": "technology computers innovation",
    "markets": "stock market trading finance",
    "economy": "global economy finance",
    "crypto": "cryptocurrency blockchain",
    "energy": "renewable energy electricity",
    "finance": "financial markets banking",
}


def get_image_for_story(story, used_urls=None):
    if used_urls is None:
        used_urls = set()

    key = os.getenv("UNSPLASH_API_KEY")

    if not key:
        logging.warning("UNSPLASH_API_KEY is missing")
        return None

    headline = story.get("headline", "")
    category = str(story.get("category", "business")).lower()
    keywords = str(story.get("image_keywords", "")).strip()

    # Try focused queries first, then broader fallback queries.
    queries = []

    if keywords:
        queries.append(keywords)

    clean_headline = re.sub(r"[^a-zA-Z0-9 ]", " ", headline)
    words = [
        word for word in clean_headline.split()
        if len(word) > 3
    ]

    if words:
        queries.append(" ".join(words[:4]))

    for key_name, fallback in FALLBACK_QUERIES.items():
        if key_name in category:
            queries.append(fallback)
            break
    else:
        queries.append("business finance")

    # Remove duplicate queries.
    queries = list(dict.fromkeys(queries))

    headers = {"Authorization": f"Client-ID {key}"}

    for query in queries:
        try:
            response = requests.get(
                "https://api.unsplash.com/search/photos",
                params={
                    "query": query,
                    "per_page": 30,
                    "orientation": "landscape",
                    "content_filter": "high"
                },
                headers=headers,
                timeout=20
            )

            response.raise_for_status()
            results = response.json().get("results", [])

            available = [
                photo for photo in results
                if photo.get("id")
                and photo.get("urls", {}).get("regular")
                and photo["id"] not in used_urls
            ]

            if not available:
                continue

            photo = random.choice(available)
            photo_id = photo["id"]
            user = photo.get("user", {})

            used_urls.add(photo_id)

            profile = (
                user.get("links", {}).get(
                    "html", "https://unsplash.com"
                ) + UTM
            )

            return {
                "url": photo["urls"]["regular"],
                "credit": (
                    f"Photo by {user.get('name', 'Photographer')} "
                    "on Unsplash"
                ),
                "credit_html": (
                    f'<a href="{profile}" target="_blank" '
                    f'rel="noopener">'
                    f'{user.get("name", "Photographer")}</a> / '
                    f'<a href="https://unsplash.com{UTM}" '
                    f'target="_blank" rel="noopener">Unsplash</a>'
                )
            }

        except Exception as exc:
            logging.warning(
                "Unsplash lookup failed for query '%s': %s",
                query,
                exc
            )

    logging.warning(
        "No unique Unsplash image found for: %s",
        headline
    )
    return None
