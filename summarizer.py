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
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")

    client = genai.Client(api_key=api_key)
    
    # Prepare the payload by combining the articles into a single string
    articles_text = ""
    for i, a in enumerate(articles):
        articles_text += f"[{i}] {a['title']} | Source: {a['source']} | URL: {a['link']} | Time: {a['published_time']}\nSnippet: {a['description']}\n\n"

    prompt = f"""
    You are an expert financial analyst. Review the following recent news articles.
    Select the top 5 to 8 most market-moving stories for the US stock market.
    
    Respond STRICTLY with a valid JSON object containing two keys:
    1. "market_overview": A 2-sentence summary of the day's overall news sentiment.
    2. "stories": An array of objects, ranked by importance (1 being most important).
    
    For each story object, provide:
    - "rank": integer (1 to 8)
    - "headline": string (your own words, max 12 words)
    - "summary": string (2-3 sentences, facts only from provided text, your own words)
    - "market_impact": string (one sentence using "may" or "could")
    - "impact_type": string (must be exactly "Positive", "Negative", or "Neutral")
    - "sectors_affected": list of strings (e.g., ["Tech", "Banking"])
    - "source_name": string (exact match from input)
    - "source_url": string (exact match from input, DO NOT INVENT)
    - "published_time": string (exact match from input)
    - "image_keywords": string (3 visual keywords for fetching a stock photo, e.g., "factory, workers, steel")
    
    Do not give investment advice. Do not invent facts or numbers.
    
    Articles:
    {articles_text}
    """

    for attempt in range(retries):
        try:
            logging.info(f"Asking Gemini to summarize (Attempt {attempt + 1}/{retries})...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            data = json.loads(response.text)
            return data
            
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            if attempt < retries - 1:
                time.sleep(900) # Wait 900 seconds before retrying
            else:
                logging.error("Max retries reached for Gemini API.")
                return {"market_overview": "Error generating AI summary.", "stories": []}
