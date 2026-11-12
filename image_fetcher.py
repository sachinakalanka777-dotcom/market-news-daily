import os
import requests
import logging

def get_image_for_story(keywords):
    """Fetches a free stock photo using Unsplash, falls back to Pexels, then a placeholder."""
    unsplash_key = os.environ.get("UNSPLASH_API_KEY")
    pexels_key = os.environ.get("PEXELS_API_KEY")
    
    # 1. Try Unsplash
    if unsplash_key:
        try:
            url = f"https://api.unsplash.com/search/photos?query={keywords}&per_page=1&orientation=landscape"
            headers = {"Authorization": f"Client-ID {unsplash_key}"}
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            data = res.json()
            if data["results"]:
                img = data["results"][0]
                return {
                    "url": img["urls"]["regular"],
                    "credit": f"Photo by {img['user']['name']} on Unsplash"
                }
        except Exception as e:
            logging.warning(f"Unsplash failed for '{keywords}': {e}")

    # 2. Try Pexels (Backup)
    if pexels_key:
        try:
            url = f"https://api.pexels.com/v1/search?query={keywords}&per_page=1&orientation=landscape"
            headers = {"Authorization": pexels_key}
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            data = res.json()
            if data["photos"]:
                img = data["photos"][0]
                return {
                    "url": img["src"]["large"],
                    "credit": f"Photo by {img['photographer']} on Pexels"
                }
        except Exception as e:
            logging.warning(f"Pexels failed for '{keywords}': {e}")

    # 3. Fallback Placeholder (using a free reliable placeholder service)
    logging.info(f"Using default placeholder for '{keywords}'")
    return {
        "url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80",
        "credit": "Stock Photo"
    }