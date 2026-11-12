import os
import shutil
from jinja2 import Environment, FileSystemLoader
from config import SITE_DIR
from datetime import datetime

def build_site(daily_data, date_str):
    """Generates the static HTML files using Jinja2 templates."""
    # Create required directories
    os.makedirs(os.path.join(SITE_DIR, "static"), exist_ok=True)
    os.makedirs(os.path.join(SITE_DIR, "archive"), exist_ok=True)

    # Copy CSS file to the site folder
    if os.path.exists("static/style.css"):
        shutil.copy("static/style.css", os.path.join(SITE_DIR, "static/style.css"))

    # Setup Jinja2 template environment
    env = Environment(loader=FileSystemLoader("templates"))
    
    # 1. Render index.html (Today's News)
    index_template = env.get_template("index.html")
    index_html = index_template.render(
        date=date_str,
        overview=daily_data.get("market_overview", ""),
        stories=daily_data.get("stories", [])
    )
    
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # 2. Render an archive page for this specific day
    archive_template = env.get_template("archive.html")
    archive_html = archive_template.render(
        date=date_str,
        overview=daily_data.get("market_overview", ""),
        stories=daily_data.get("stories", [])
    )
    
    archive_filename = f"archive/{date_str}.html"
    with open(os.path.join(SITE_DIR, archive_filename), "w", encoding="utf-8") as f:
        f.write(archive_html)
        
    print(f"Site built successfully in ./{SITE_DIR}")