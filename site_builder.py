import json
import os
from datetime import datetime

def build_site():
    print("Building site...")
    # Load daily data
    try:
        with open("data/daily_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"market_overview": "Error generating AI summary.", "stories": []}

    date_str = datetime.now().strftime("%Y-%m-%d")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MarketPulse | Daily Financial Brief</title>
    <style>
        :root {{
            --bg-color: #121212;
            --surface-color: #1e1e1e;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --accent-color: #bb86fc;
            --border-color: #333333;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
        }}
        header {{
            background-color: var(--surface-color);
            padding: 30px 20px;
            text-align: center;
            border-bottom: 1px solid var(--border-color);
        }}
        .logo {{
            max-width: 150px;
            margin-bottom: 15px;
        }}
        h1 {{
            margin: 0;
            color: var(--text-primary);
            font-size: 2.5rem;
        }}
        .date {{
            color: var(--accent-color);
            font-weight: bold;
            margin-top: 10px;
        }}
        .container {{
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
        }}
        .executive-summary {{
            background-color: var(--surface-color);
            padding: 25px;
            border-radius: 8px;
            border-left: 5px solid var(--accent-color);
            margin-bottom: 40px;
        }}
        .executive-summary h2 {{
            margin-top: 0;
            color: var(--accent-color);
        }}
        .story {{
            background-color: var(--surface-color);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            border: 1px solid var(--border-color);
        }}
        .story h3 {{
            margin-top: 0;
            color: #ffffff;
        }}
        .story a {{
            color: var(--accent-color);
            text-decoration: none;
        }}
        .story a:hover {{
            text-decoration: underline;
        }}
        .meta {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 15px;
            text-transform: uppercase;
        }}
        footer {{
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
            margin-top: 50px;
        }}
    </style>
</head>
<body>
    <header>
        <!-- Logo Image -->
        <img src="logo.png" alt="MarketPulse Logo" class="logo">
        <h1>MarketPulse</h1>
        <div class="date">{date_str}</div>
    </header>
    
    <div class="container">
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <p>{data.get('market_overview', 'No summary available.')}</p>
        </div>
        
        <h2>Top Market Drivers</h2>
"""
    # Add stories
    for story in data.get('stories', []):
        html += f"""
        <div class="story">
            <h3>{story.get('headline', 'News Story')}</h3>
            <p>{story.get('summary', '')}</p>
            <div class="meta">
                Source: {story.get('source', 'Unknown')} | <a href="{story.get('url', '#')}" target="_blank">Read Full Article</a>
            </div>
        </div>
"""

    html += """
    </div>
    <footer>
        <p>MarketPulse<br>
        Disclaimer: This content is curated by AI for informational purposes only and does not constitute financial advice. 
        Always consult a certified financial planner or read the original sources before making investment decisions.</p>
        <p>&copy; 2026 MarketPulse. All rights reserved.</p>
    </footer>
</body>
</html>
"""

    os.makedirs("site", exist_ok=True)
    with open("site/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Site built successfully.")

if __name__ == "__main__":
    build_site()