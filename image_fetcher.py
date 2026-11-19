
import logging
import os
import random
import requests

UTM = "?utm_source=marketpulsenews&utm_medium=referral"


def get_image_for_story(story, used_urls=None):
    """
    Find a relevant Unsplash image.
    Prevent the same Unsplash photo ID from being reused.
    """
    if used_urls is None:
        used_urls = set()

    key = os.getenv("UNSPLASH_API_KEY")

    if not key:
        logging.warning("UNSPLASH_API_KEY is missing")
        return None

    headline = story.get("headline", "")
    category = story.get("category", "")
    keywords = story.get("image_keywords", "")

    query_parts = [
        str(x).strip()
        for x in [keywords, headline, category, "finance business"]
        if x and str(x).strip()
    ]

    query = " ".join(query_parts)

    try:
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": query,
                "per_page": 30,
                "orientation": "landscape"
            },
            headers={"Authorization": f"Client-ID {key}"},
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
            logging.warning(
                "No unique Unsplash image found for: %s",
                headline
            )
            return None

        photo = random.choice(available)
        photo_id = photo["id"]
        image_url = photo["urls"]["regular"]
        user = photo.get("user", {})

        # Store the unique photo ID, not only its URL.
        used_urls.add(photo_id)

        profile = (
            user.get("links", {}).get("html", "https://unsplash.com")
            + UTM
        )

        return {
            "url": image_url,
            "credit": (
                f"Photo by {user.get('name', 'Photographer')} on Unsplash"
            ),
            "credit_html": (
                f'<a href="{profile}" target="_blank" rel="noopener">'
                f'{user.get("name", "Photographer")}</a> / '
                f'<a href="https://unsplash.com{UTM}" target="_blank" '
                f'rel="noopener">Unsplash</a>'
            )
        }

    except Exception as exc:
        logging.warning(
            "Unsplash lookup failed for %s: %s",
            headline,
            exc
        )
        return None
