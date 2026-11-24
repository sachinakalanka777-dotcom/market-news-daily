
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA_DIR = ROOT / "data"

BASE_URL = "https://marketpulsenews.online"


# Website category configuration
CATEGORIES = {
    "stocks": {
        "title": "Stocks",
        "description": (
            "Latest global stock market news, company earnings, "
            "IPOs, equity markets and investment developments."
        ),
        "categories": [
            "Markets",
            "IPO",
            "Earnings",
        ],
        "tags": [
            "Stocks",
            "Stock Market",
            "Equities",
        ],
    },

    "bitcoin-crypto": {
        "title": "Bitcoin & Crypto",
        "description": (
            "Latest Bitcoin, cryptocurrency, blockchain "
            "and digital asset market news."
        ),
        "categories": [
            "Crypto",
        ],
        "tags": [
            "Bitcoin",
            "Cryptocurrency",
            "Crypto",
        ],
    },

    "forex": {
        "title": "Forex",
        "description": (
            "Latest foreign exchange market news, currency "
            "movements and global forex developments."
        ),
        "categories": [
            "Forex",
        ],
        "tags": [
            "Forex",
            "Currency",
            "Currencies",
        ],
    },

    "gold-commodities": {
        "title": "Gold & Commodities",
        "description": (
            "Latest gold, precious metals, oil, energy "
            "and global commodities market news."
        ),
        "categories": [
            "Commodities",
        ],
        "tags": [
            "Gold",
            "Silver",
            "Oil",
            "Commodities",
        ],
    },

    "economy": {
        "title": "Economy",
        "description": (
            "Latest global economic news, central bank decisions, "
            "inflation and monetary policy developments."
        ),
        "categories": [
            "Federal Reserve",
            "Economy",
        ],
        "tags": [
            "Economy",
            "Inflation",
            "Federal Reserve",
            "Interest Rates",
        ],
    },

        "business": {
        "title": "Business",
        "description": "Latest global business news, corporate developments, mergers, acquisitions and technology companies.",
        "categories": ["Business", "Merger", "Technology", "Regulation", "Banking", "Geopolitics"],
        "tags": ["Business", "Companies", "Corporate"],
    },
}


def normalize_text(value):
    """Convert a value into normalized lowercase text."""

    return str(value or "").strip().casefold()


def build_sitemap():
    """Generate sitemap.xml and robots.txt."""

    urls = [
        f"{BASE_URL}/",
        f"{BASE_URL}/archive/",
    ]

    # Category pages
    for slug in CATEGORIES:
        category_page = SITE / slug / "index.html"

        if category_page.exists():
            urls.append(f"{BASE_URL}/{slug}/")

    # Dated archive pages
    archive_root = SITE / "archive"

    if archive_root.exists():
        for folder in sorted(
            archive_root.iterdir(),
            reverse=True
        ):
            if (
                folder.is_dir()
                and (folder / "index.html").exists()
            ):
                urls.append(
                    f"{BASE_URL}/archive/{folder.name}/"
                )

    # Remove duplicate URLs
    urls = list(dict.fromkeys(urls))

    namespace = (
        "http://www.sitemaps.org/schemas/sitemap/0.9"
    )

    ET.register_namespace("", namespace)

    root = ET.Element(
        f"{{{namespace}}}urlset"
    )

    for page_url in urls:
        url_element = ET.SubElement(
            root,
            f"{{{namespace}}}url"
        )

        loc = ET.SubElement(
            url_element,
            f"{{{namespace}}}loc"
        )

        loc.text = page_url

    tree = ET.ElementTree(root)

    tree.write(
        SITE / "sitemap.xml",
        encoding="utf-8",
        xml_declaration=True
    )

    # Generate robots.txt
    robots_content = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n"
    )

    (SITE / "robots.txt").write_text(
        robots_content,
        encoding="utf-8"
    )

    print("robots.txt generated successfully")
    print(f"Sitemap generated: {len(urls)} URLs")


def build_category_pages(data, env):
    """Generate individual category pages."""

    template = env.get_template("category.html")

    stories = data.get("stories", [])

    if not isinstance(stories, list):
        stories = []

    for slug, config in CATEGORIES.items():

        selected_stories = []

        allowed_categories = {
            normalize_text(item)
            for item in config["categories"]
        }

        allowed_tags = {
            normalize_text(item)
            for item in config["tags"]
        }

        for story in stories:

            if not isinstance(story, dict):
                continue

            story_category = normalize_text(
                story.get("category", "")
            )

            story_tags = story.get("tags", []) or []

            if isinstance(story_tags, str):
                story_tags = [story_tags]

            if not isinstance(story_tags, list):
                story_tags = []

            normalized_tags = {
                normalize_text(tag)
                for tag in story_tags
            }

            category_match = (
                story_category in allowed_categories
            )

            tag_match = bool(
                normalized_tags.intersection(allowed_tags)
            )

            if category_match or tag_match:
                selected_stories.append(story)

        # Create category directory
        category_dir = SITE / slug

        category_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Render category template
        category_html = template.render(
            category_title=config["title"],
            category_description=config["description"],
            category_slug=slug,
            stories=selected_stories,
        )

        # Save category page
        (category_dir / "index.html").write_text(
            category_html,
            encoding="utf-8"
        )

        print(
            f"Category generated: {config['title']} "
            f"({len(selected_stories)} stories)"
        )


def build_site(data, date_str):
    """Build the complete static website."""

    if data is None:
        raise ValueError(
            "build_site requires generated data; "
            "refusing to silently discard it"
        )

    if not isinstance(data, dict):
        raise TypeError(
            "Website data must be a dictionary"
        )

    SITE.mkdir(
        parents=True,
        exist_ok=True
    )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    env = Environment(
        loader=FileSystemLoader(
            str(ROOT / "templates")
        ),
        autoescape=select_autoescape(
            ["html", "xml"]
        ),
    )

    # -------------------------
    # Main homepage
    # -------------------------

    template = env.get_template("index.html")

    context = dict(data)
    context["date"] = date_str

    html = template.render(**context)

    (SITE / "index.html").write_text(
        html,
        encoding="utf-8"
    )

    # -------------------------
    # Dated archive page
    # -------------------------

    archive_dir = SITE / "archive" / date_str

    archive_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    archive_context = dict(data)

    archive_context["date"] = date_str
    archive_context["archive"] = True

    archive_html = env.get_template(
        "archive.html"
    ).render(**archive_context)

    (archive_dir / "index.html").write_text(
        archive_html,
        encoding="utf-8"
    )

    # -------------------------
    # Archive JSON
    # -------------------------

    archive_json = archive_dir / "data.json"

    archive_json.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # -------------------------
    # Archive listing
    # -------------------------

    archive_root = SITE / "archive"

    all_dates = sorted(
        [
            path.name
            for path in archive_root.iterdir()
            if path.is_dir()
        ],
        reverse=True
    )

    archive_index = env.get_template(
        "archive_list.html"
    ).render(
        dates=all_dates
    )

    (archive_root / "index.html").write_text(
        archive_index,
        encoding="utf-8"
    )

    # -------------------------
    # Latest data JSON
    # -------------------------

    (SITE / "data.json").write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # -------------------------
    # Generate category pages
    # -------------------------

    build_category_pages(data, env)

    # -------------------------
    # Copy stylesheet
    # -------------------------

    static_out = SITE / "static"

    static_out.mkdir(
        parents=True,
        exist_ok=True
    )

    stylesheet = ROOT / "static" / "style.css"

    if stylesheet.exists():

        (static_out / "style.css").write_bytes(
            stylesheet.read_bytes()
        )

        print("Stylesheet copied successfully")

    else:
        print(
            "WARNING: static/style.css was not found"
        )

    # -------------------------
    # Generate sitemap
    # -------------------------

    build_sitemap()

    print(
        f"Site built successfully: {SITE}"
    )
