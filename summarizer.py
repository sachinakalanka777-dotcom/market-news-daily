
import json
import logging
import os
import random
import re
import time

import requests
from google import genai
from google.genai import types

from config import GEMINI_MODEL, GROQ_MODEL, MAX_STORIES

LOG = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a careful US financial-news editor.
Use ONLY the supplied article metadata and snippets.
Never invent facts, dates, quotes, prices, forecasts, or causes.
Do not claim a stock will rise or fall with certainty.
Return valid JSON only, without markdown.
Select distinct stories relevant to US listed markets.
Rank by likely market significance, not sensationalism.
Keep summaries original, factual and concise."""


def build_prompt(articles):
    compact = []

    for article in articles[:60]:
        compact.append({
            "id": article["article_id"],
            "title": article["title"],
            "source": article["source"],
            "published": article["published_time"],
            "snippet": article["description"][:650],
            "relevance": article["relevance_score"],
            "matched_topics": article["matched_keywords"],
        })

    return f"""Review these candidate news items for their potential impact on the US stock market.

Return JSON with keys:
market_overview: 2 concise factual sentences.
stories: array, maximum {MAX_STORIES}.

Each story must contain:
article_id: exact supplied ID.
headline: factual headline.
summary: 2-3 factual sentences.
impact_type: Bullish, Bearish, or Neutral.
market_impact: one cautious sentence.
sectors_affected: array of up to 3 sectors.
category: Economy, Federal Reserve, Earnings, Technology, Geopolitics, Regulation, Commodities, Banking, or Markets.
image_keywords: 2-4 simple English words.

Never invent URLs, sources, or article IDs.
Use Neutral when market direction is unclear.

CANDIDATE ARTICLES:
{json.dumps(compact, ensure_ascii=False)}"""


def extract_json(text):
    text = (text or "").strip()

    text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        text,
        flags=re.I
    )

    start = text.find("{")
    end = text.rfind("}")

    if start < 0 or end <= start:
        raise ValueError("AI response did not contain a JSON object")

    result = json.loads(text[start:end + 1])

    if not isinstance(result, dict):
        raise ValueError("AI response JSON must be an object")

    if not isinstance(result.get("stories"), list):
        raise ValueError("AI response is missing a valid stories array")

    return result


def call_gemini(prompt):
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=key)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response")

    return extract_json(response.text)


def call_groq(prompt):
    key = os.getenv("GROQ_API_KEY")

    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT + " Output only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 7000,
        },
        timeout=90
    )

    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]

    return extract_json(content)


def fallback_data(articles):
    """Safely publish publisher snippets when AI services fail."""

    stories = []

    for article in articles[:MAX_STORIES]:
        description = (
            article.get("description")
            or "The publisher has not supplied a summary. "
               "Open the original article for full details."
        )

        stories.append({
            "article_id": article["article_id"],
            "headline": article["title"],
            "summary": description[:420],
            "impact_type": "Neutral",
            "market_impact": (
                "Potential market relevance is based on the headline "
                "and publisher snippet; direction is not independently established."
            ),
            "sectors_affected": [],
            "category": "Markets",
            "image_keywords": "US stock market finance",
            "summary_method": "Publisher snippet (AI unavailable)",
        })

    overview = (
        "Today's market-relevant headlines are listed below. "
        "AI summarization was unavailable, so publisher-provided "
        "snippets are shown without adding unsupported analysis."
    )

    return {
        "market_overview": overview,
        "stories": stories,
        "ai_provider": "fallback"
    }


def normalize_result(raw, articles, provider):
    by_id = {
        article["article_id"]: article
        for article in articles
    }

    clean_stories = []
    used = set()

    for item in raw.get("stories", []):
        if not isinstance(item, dict):
            continue

        aid = str(item.get("article_id", ""))

        if aid not in by_id or aid in used:
            continue

        source = by_id[aid]

        impact = str(
            item.get("impact_type", "Neutral")
        ).title()

        if impact not in {"Bullish", "Bearish", "Neutral"}:
            impact = "Neutral"

        sectors = item.get("sectors_affected", [])

        if not isinstance(sectors, list):
            sectors = []

        clean_stories.append({
            "rank": len(clean_stories) + 1,
            "headline": str(
                item.get("headline") or source["title"]
            )[:240],
            "summary": str(
                item.get("summary") or source["description"]
            )[:900],
            "source_name": source["source"],
            "source_url": source["link"],
            "published_time": source["published_time"],
            "impact_type": impact,
            "market_impact": str(
                item.get("market_impact")
                or "Market impact is uncertain; review the original source."
            )[:350],
            "sectors_affected": [
                str(sector)[:50]
                for sector in sectors[:3]
            ],
            "category": str(
                item.get("category") or "Markets"
            )[:60],
            "image_keywords": str(
                item.get("image_keywords")
                or "US stock market finance"
            )[:100],
            "image": "",
            "image_credit": "",
            "summary_method": provider,
        })

        used.add(aid)

        if len(clean_stories) >= MAX_STORIES:
            break

    if not clean_stories:
        LOG.warning(
            "%s returned no usable stories; using publisher snippets",
            provider
        )
        return fallback_data(articles)

    return {
        "market_overview": str(
            raw.get("market_overview")
            or "Market overview unavailable."
        )[:1200],
        "stories": clean_stories,
        "ai_provider": provider
    }


def summarize_articles(articles, retries=3):
    if not articles:
        return {
            "market_overview": (
                "No market-relevant stories were found in the selected "
                "time window. Check the source status below."
            ),
            "stories": [],
            "ai_provider": "none"
        }

    prompt = build_prompt(articles)

    providers = []

    if os.getenv("GEMINI_API_KEY"):
        providers.append(("Gemini", call_gemini))

    if os.getenv("GROQ_API_KEY"):
        providers.append(("Groq", call_groq))

    for provider, function in providers:

        for attempt in range(1, retries + 1):
            try:
                LOG.info(
                    "Summarizing with %s (attempt %d/%d)",
                    provider,
                    attempt,
                    retries
                )

                raw = function(prompt)

                return normalize_result(
                    raw,
                    articles,
                    provider
                )

            except Exception as exc:
                LOG.warning(
                    "%s failed on attempt %d/%d: %s",
                    provider,
                    attempt,
                    retries,
                    exc
                )

                if attempt < retries:
                    wait = min(5 * (2 ** (attempt - 1)), 40)
                    wait += random.uniform(0, 2)

                    LOG.info(
                        "Retrying %s in %.1f seconds",
                        provider,
                        wait
                    )

                    time.sleep(wait)

    LOG.error(
        "All configured AI providers failed; using publisher snippets"
    )

    return fallback_data(articles)
