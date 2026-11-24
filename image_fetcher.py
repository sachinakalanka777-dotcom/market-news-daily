
import logging
import os
import random
import re

import requests

UTM = "?utm_source=marketpulsenews&utm_medium=referral"

UNSPLASH_URL = "https://api.unsplash.com/search/photos"

FALLBACK_QUERIES = {
    "crypto": "bitcoin cryptocurrency blockchain digital assets",
    "forex": "foreign exchange currency trading financial charts",
    "commodities": "gold silver crude oil commodities trading",
    "technology": "technology innovation semiconductor computers",
    "markets": "international stock exchange global financial markets",
    "economy": "global economy economic data business",
    "energy": "renewable energy solar power electricity",
    "business": "international business corporate office",
    "finance": "global banking financial services investment",
}


def normalize_keywords(value):
    """
    Convert image keywords into a clean search query.
    Supports strings, lists and tuples.
    """

    if isinstance(value, (list, tuple, set)):
        parts = [
            str(item).strip()
            for item in value
            if item
        ]
        text = " ".join(parts)

    elif isinstance(value, str):
        text = value

    else:
        text = ""

    text = re.sub(r"[^a-zA-Z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text[:150]


def is_flag_photo(photo):
    """
    Exclude images whose metadata indicates
    that they mainly feature flags.
    """

    metadata = " ".join([
        photo.get("alt_description") or "",
        photo.get("description") or "",
        photo.get("slug") or "",
    ]).lower()

    flag_terms = [
        "flag",
        "flags",
        "stars and stripes",
        "national flag",
        "american flag",
        "united states flag",
        "usa flag",
        "flag of america",
    ]

    return any(term in metadata for term in flag_terms)


def build_queries(story):
    """
    Build clean, relevant and unique image search queries.
    """

    headline = story.get("headline", "")

    category = str(
        story.get("category", "business")
    ).lower()

    keywords = normalize_keywords(
        story.get("image_keywords", "")
    )

    queries = []

    # 1. Story-specific image keywords.
    if keywords:
        queries.append(keywords)

    # 2. Clean headline keywords.
    clean_headline = re.sub(
        r"[^a-zA-Z0-9 ]",
        " ",
        str(headline)
    )

    words = [
        word
        for word in clean_headline.split()
        if len(word) > 3
    ]

    if words:
        queries.append(" ".join(words[:4]))

    # 3. Category fallback.
    for key_name, fallback in FALLBACK_QUERIES.items():
        if key_name in category:
            queries.append(fallback)
            break
    else:
        queries.append(
            "international financial markets business"
        )

    # Remove empty and duplicate queries.
    cleaned = []
    seen = set()

    for query in queries:
        query = normalize_keywords(query)

        if query and query.lower() not in seen:
            cleaned.append(query)
            seen.add(query.lower())

    # Limit requests per story.
    return cleaned[:3]


def get_image_for_story(story, used_urls=None):
    """
    Fetch a unique landscape image from Unsplash.

    Returns:
        Image details dictionary, or None if unavailable.
    """

    if used_urls is None:
        used_urls = set()

    api_key = os.getenv("UNSPLASH_API_KEY")

    if not api_key:
        logging.warning(
            "UNSPLASH_API_KEY is missing. "
            "Skipping image search."
        )
        return None

    headline = story.get("headline", "Unknown story")

    queries = build_queries(story)

    if not queries:
        logging.warning(
            "No valid image search queries for: %s",
            headline
        )
        return None

    headers = {
        "Authorization": f"Client-ID {api_key}",
        "Accept-Version": "v1",
    }

    for query in queries:

        try:
            response = requests.get(
                UNSPLASH_URL,
                params={
                    "query": query,
                    "per_page": 30,
                    "orientation": "landscape",
                    "content_filter": "high",
                },
                headers=headers,
                timeout=20,
            )

            # API authentication or access problems.
            if response.status_code in (401, 403):
                logging.error(
                    "Unsplash API access denied (HTTP %s). "
                    "Check API key, application status and permissions. "
                    "Stopping image searches.",
                    response.status_code,
                )
                return None

            # Rate limit reached.
            if response.status_code == 429:
                logging.warning(
                    "Unsplash API rate limit reached. "
                    "Skipping remaining image searches."
                )
                return None

            response.raise_for_status()

            data = response.json()

            results = data.get("results", [])

            available = [
                photo
                for photo in results
                if photo.get("id")
                and photo.get("urls", {}).get("regular")
                and photo["id"] not in used_urls
                and not is_flag_photo(photo)
            ]

            if not available:
                logging.info(
                    "No suitable unique images for query: %s",
                    query,
                )
                continue

            photo = random.choice(available)

            photo_id = photo["id"]
            user = photo.get("user", {})

            image_url = photo.get(
                "urls", {}
            ).get("regular")

            if not image_url:
                continue

            # Avoid reusing the same image.
            used_urls.add(photo_id)

            profile_url = (
                user.get("links", {}).get(
                    "html",
                    "https://unsplash.com"
                )
            )

            profile = profile_url + UTM

            photographer = user.get(
                "name",
                "Photographer"
            )

            return {
                "url": image_url,

                "credit": (
                    f"Photo by {photographer} "
                    "on Unsplash"
                ),

                "credit_html": (
                    f'<a href="{profile}" '
                    f'target="_blank" rel="noopener">'
                    f'{photographer}</a> / '
                    f'<a href="https://unsplash.com{UTM}" '
                    f'target="_blank" rel="noopener">'
                    'Unsplash</a>'
                ),
            }

        except requests.exceptions.Timeout:
            logging.warning(
                "Unsplash request timed out for query: %s",
                query,
            )

        except requests.exceptions.RequestException as exc:
            logging.warning(
                "Unsplash request failed for query '%s': %s",
                query,
                exc,
            )

        except (ValueError, KeyError, TypeError) as exc:
            logging.warning(
                "Invalid Unsplash response for query '%s': %s",
                query,
                exc,
            )

    logging.warning(
        "No suitable unique Unsplash image found for: %s",
        headline,
    )

    return None
