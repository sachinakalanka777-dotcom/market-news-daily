
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA_DIR = ROOT / "data"


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

    print(f"Site built successfully: {SITE}")
