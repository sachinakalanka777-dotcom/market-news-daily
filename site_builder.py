
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA_DIR = ROOT / "data"
BASE_URL = "https://marketpulsenews.online"


def build_sitemap():
    urls = [
        f"{BASE_URL}/",
        f"{BASE_URL}/archive/",
    ]

    archive_root = SITE / "archive"

    if archive_root.exists():
        for folder in sorted(archive_root.iterdir(), reverse=True):
            if folder.is_dir() and (folder / "index.html").exists():
                urls.append(f"{BASE_URL}/archive/{folder.name}/")

    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)

    root = ET.Element(f"{{{namespace}}}urlset")

    for page_url in urls:
        url_element = ET.SubElement(root, f"{{{namespace}}}url")
        loc = ET.SubElement(url_element, f"{{{namespace}}}loc")
        loc.text = page_url

    tree = ET.ElementTree(root)
    tree.write(
        SITE / "sitemap.xml",
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"Sitemap generated: {len(urls)} URLs")


def build_site(data, date_str):
    if data is None:
        raise ValueError(
            "build_site requires generated data; "
            "refusing to silently discard it"
        )

    SITE.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Main homepage
    template = env.get_template("index.html")
    context = dict(data)
    context["date"] = date_str

    html = template.render(**context)
    (SITE / "index.html").write_text(html, encoding="utf-8")

    # Dated archive page
    archive_dir = SITE / "archive" / date_str
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_context = dict(data)
    archive_context["date"] = date_str
    archive_context["archive"] = True

    archive_html = env.get_template("archive.html").render(
        **archive_context
    )
    (archive_dir / "index.html").write_text(
        archive_html, encoding="utf-8"
    )

    # Archive JSON
    archive_json = archive_dir / "data.json"
    archive_json.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Archive listing
    all_dates = sorted(
        [
            p.name
            for p in (SITE / "archive").iterdir()
            if p.is_dir()
        ],
        reverse=True
    )

    archive_index = env.get_template(
        "archive_list.html"
    ).render(dates=all_dates)

    (SITE / "archive" / "index.html").write_text(
        archive_index, encoding="utf-8"
    )

    # Latest data JSON
    (SITE / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Copy stylesheet
    static_out = SITE / "static"
    static_out.mkdir(exist_ok=True)

    stylesheet = ROOT / "static" / "style.css"

    if stylesheet.exists():
        (static_out / "style.css").write_bytes(
            stylesheet.read_bytes()
        )

    # Generate sitemap automatically
    build_sitemap()

    print(f"Site built successfully: {SITE}")
