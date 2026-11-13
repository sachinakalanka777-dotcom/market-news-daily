import logging
import os
import requests
from urllib.parse import quote

PLACEHOLDER = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1000&q=80"
UTM = "?utm_source=marketpulsenews&utm_medium=referral"


def get_image_for_story(keywords):
    key = os.getenv("UNSPLASH_API_KEY")
    if key:
        try:
            response = requests.get(
                "https://api.unsplash.com/search/photos",
                params={"query": keywords or "US stock market finance", "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {key}"}, timeout=20,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if results:
                photo = results[0]
                user = photo.get("user", {})
                profile = user.get("links", {}).get("html", "https://unsplash.com") + UTM
                return {
                    "url": photo.get("urls", {}).get("regular", PLACEHOLDER),
                    "credit_html": f'<a href="{profile}" target="_blank" rel="noopener">{user.get("name", "Photographer")}</a> / <a href="https://unsplash.com{UTM}" target="_blank" rel="noopener">Unsplash</a>',
                    "credit": f"Photo by {user.get('name', 'Photographer')} on Unsplash",
                }
        except Exception as exc:
            logging.warning("Unsplash lookup failed: %s", exc)
    return {"url": PLACEHOLDER, "credit": "MarketPulse image placeholder", "credit_html": "MarketPulse"}
