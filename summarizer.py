import os
import json
import time
import logging
from google import genai
from google.genai import types

def summarize_articles(articles, retries=3):
    """Sends articles to Gemini AI to select, rank, and summarize the top market-moving stories."""
    if not articles:
        return {"market_overview": "No significant market news found today.", "stories": []}

    api_key = os.environ.get("GEMINI_API_KEY")
    # Using the updated gemini-3.8-pro model
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-pro")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")

    client = genai.Client(api_key=api_key)

    articles_text = ""
    for i, a in enumerate(articles):
        articles_text += f"[{i}] {a['title']} | Source: {a['source']} | URL: {a['link']} | Time: {a.get('published_time', '')}\nSnippet: {a.get('description', '')}\n\n"

    prompt = f"""
You are an expert financial analyst. Review the following recent news articles.
Select the top 15 to 30 most market-moving stories for the US stock market.

Respond STRICTLY with a valid JSON object containing two keys:
1. "market_overview": A 2-sentence summary of the day's overall news sentiment.
2. "stories": An array of objects, ranked by importance (1 being most important).
Each object in "stories" must have:
- "headline": A punchy, clear title.
- "summary": A 2-3 sentence explanation of why it matters to markets.
- "source": The publisher name.
- "url": The original link.

Articles:
{articles_text}
"""
    
    for attempt in range(1, retries + 1):
        logging.info(f"Asking Gemini to summarize (Attempt {attempt}/{retries})...")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            if attempt < retries:
                # 503 Error ආවොත් විනාඩි 15ක් (තත්පර 900ක්) රැඳී සිටී
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    logging.info("Server is busy. Waiting 15 minutes before retrying...")
                    time.sleep(200) 
                else:
                    logging.info("Waiting 10 seconds before retrying...")
                    time.sleep(10)
            else:
                logging.error("Max retries reached for Gemini API.")
                
    return {"market_overview": "Error generating AI summary.", "stories": []}
