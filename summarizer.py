
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

CATEGORIES = {
    "Economy",
    "Federal Reserve",
    "Earnings",
    "IPO",
    "Merger",
    "Business",
    "Technology",
    "Geopolitics",
    "Regulation",
    "Commodities",
    "Banking",
    "Crypto",
    "Forex",
    "Markets",
}

SYSTEM_PROMPT = """You are a careful global financial-news editor.

Use ONLY the supplied article metadata and snippets.
Never invent facts, dates, quotes, prices, forecasts, or causes.
Do not claim an asset or stock will rise or fall with certainty.

Select distinct stories relevant to global financial markets.
Rank stories by likely market significance, not sensationalism.

Maintain category diversity when selecting stories.
Avoid selecting too many stories from the same category
when other important categories are available.

Consider Stocks, IPOs, Business, Bitcoin, Crypto, Forex,
Commodities, Gold, Economy and Banking when relevant.

Do not force irrelevant stories into the selection.
Do not select duplicate or substantially similar stories.

Keep summaries original, factual and concise.
Return valid JSON only, without markdown."""


def build_prompt(articles):
    compact = []

    for article in articles[:30]:
        compact.append({
            "id": article.get("article_id", ""),
            "title": article.get("title", "")[:200],
            "source": article.get("source", ""),
            "published": article.get("published_time", ""),
            "snippet": article.get("description", "")[:350],
            "relevance": article.get("relevance_score", 0),
            "matched_topics": article.get(
                "matched_keywords", []
            )[:5],
        })

    return f"""Review these candidate news items for their potential
impact on global financial markets.

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
category: choose exactly ONE from:
Economy, Federal Reserve, Earnings, IPO, Merger, Business,
Technology, Geopolitics, Regulation, Commodities, Banking,
Crypto, Forex, or Markets.
image_keywords: 2-4 simple English words describing a relevant image.

STORY SELECTION RULES:

1. Select the most important and relevant financial news stories.
2. Maintain category diversity across selected stories.
3. Avoid selecting too many stories from the same category
   when other important categories are available.
4. Give consideration to Stocks, IPOs, Business, Crypto,
   Bitcoin, Forex, Commodities, Gold, Banking and Economy
   when relevant candidate articles exist.
5. When stories have similar market significance, prefer
   categories that are less represented in the selection.
6. Do not force a category into the selection if its available
   news is not sufficiently relevant or important.
7. Do not select duplicate or substantially similar stories.
8. Prefer recent and significant developments when relevance
   and market impact are comparable.

CATEGORY CLASSIFICATION:

- Markets: General stock market movements and market updates.
- Earnings: Company financial results and earnings reports.
- IPO: Initial public offerings and stock exchange listings.
- Merger: Mergers, acquisitions and major corporate deals.
- Business: General company and corporate developments.
- Technology: Technology-sector developments.
- Crypto: Bitcoin and cryptocurrency developments.
- Forex: Foreign exchange, currencies and exchange rates.
- Commodities: Gold, silver, oil and other commodities.
- Economy: General economic developments and economic data.
- Federal Reserve: Federal Reserve policy and announcements.
- Banking: Banks and financial institutions.
- Geopolitics: Geopolitical developments affecting markets.
- Regulation: Financial and market regulations.

IMPORTANT:

Never invent URLs, sources or article IDs.
Use Neutral when market direction is unclear.
Use only the supplied candidate information.
Return valid JSON only, without markdown.

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
        raise ValueError(
            "AI response did not contain a JSON object"
        )

    result = json.loads(text[start:end + 1])

    if not isinstance(result, dict):
        raise ValueError(
            "AI response JSON must be an object"
        )

    if not isinstance(result.get("stories"), list):
        raise ValueError(
            "AI response is missing a valid stories array"
        )

    return result


def call_gemini(prompt):
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

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
        raise ValueError(
            "Gemini returned an empty response"
        )

    return extract_json(response.text)


def call_groq(prompt):
    key = os.getenv("GROQ_API_KEY")

    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    LOG.info("Groq: sending summarization request")

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
                    "content": (
                        SYSTEM_PROMPT
                        + " Output only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "response_format": {
                "type": "json_object"
            },
            "max_tokens": 7000,
        },
        timeout=(15, 90)
    )

    LOG.info(
        "Groq: HTTP response received (status %d)",
        response.status_code
    )

    if response.status_code != 200:
        LOG.error(
            "Groq API error %d: %s",
            response.status_code,
            response.text[:500]
        )

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError(
            "Groq returned invalid response JSON"
        ) from exc

    choices = data.get("choices")

    if not isinstance(choices, list) or not choices:
        raise ValueError(
            "Groq response contains no choices"
        )

    message = choices[0].get("message", {})
    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            "Groq returned empty message content"
        )

    LOG.info(
        "Groq: response content received (%d characters)",
        len(content)
    )

    return extract_json(content)


def detect_category_and_image_keywords(title):
    """Detect a likely financial news category from its headline."""

    title_lower = str(title or "").lower()

    # Cryptocurrency
    if any(term in title_lower for term in [
        "bitcoin", "btc", "ethereum", "eth",
        "cryptocurrency", "crypto", "blockchain",
        "digital asset", "digital assets",
        "crypto exchange", "crypto market"
    ]):
        return (
            "Crypto",
            "bitcoin cryptocurrency blockchain digital assets"
        )

    # Forex and currencies
    forex_terms = [
        "forex", "foreign exchange", "currency pair",
        "exchange rate", "exchange rates",
        "currency market", "currency markets",
        "currencies", "currency", "fx market",
        "fx trading", "fx market",
        "us dollar", "u.s. dollar",
        "euro", "yen", "sterling",
        "british pound", "pound sterling",
        "swiss franc", "chinese yuan",
        "japanese yen", "dollar strengthens",
        "dollar weakens", "dollar rises",
        "dollar falls", "dollar gains",
        "dollar loses", "currency trading"
    ]

    currency_pair = re.search(
        r"\b(?:usd|eur|gbp|jpy|chf|cad|aud|nzd)"
        r"\s*[/\-]\s*"
        r"(?:usd|eur|gbp|jpy|chf|cad|aud|nzd)\b",
        title_lower
    )

    if (
        any(term in title_lower for term in forex_terms)
        or currency_pair
    ):
        return (
            "Forex",
            "foreign exchange currency trading financial charts"
        )

    # Commodities
    if any(term in title_lower for term in [
        "gold", "silver", "crude oil", "oil prices",
        "oil market", "natural gas", "copper",
        "commodity", "commodities", "platinum",
        "palladium", "brent crude", "wti crude",
        "iron ore", "wheat prices"
    ]):
        return (
            "Commodities",
            "gold silver oil commodities trading"
        )

    # Federal Reserve
    if any(term in title_lower for term in [
        "federal reserve", "fed policy",
        "fed rate", "fed rates",
        "fed chair", "fomc",
        "federal open market committee",
        "jerome powell"
    ]):
        return (
            "Federal Reserve",
            "federal reserve central bank monetary policy"
        )

    # IPO
    if any(term in title_lower for term in [
        "ipo", "initial public offering",
        "goes public", "going public",
        "stock market debut", "market debut",
        "public listing", "stock listing",
        "shares debut", "ipo filing"
    ]):
        return (
            "IPO",
            "initial public offering stock exchange listing"
        )

    # Mergers and acquisitions
    if any(term in title_lower for term in [
        "merger", "acquisition", "acquires",
        "acquired", "takeover", "buyout",
        "to buy", "to acquire",
        "deal to acquire", "merges with",
        "merging with", "combines with"
    ]):
        return (
            "Merger",
            "corporate merger acquisition business deal"
        )

    # Earnings
    if any(term in title_lower for term in [
        "earnings", "quarterly results",
        "revenue", "profit", "net income",
        "earnings report", "earnings per share",
        "eps beats", "eps misses",
        "financial results"
    ]):
        return (
            "Earnings",
            "corporate earnings financial results"
        )

    # Economy
    if any(term in title_lower for term in [
        "inflation", "interest rate",
        "central bank", "gdp",
        "unemployment", "economic growth",
        "jobs report", "consumer price index",
        "cpi", "producer price index",
        "pce", "treasury yields",
        "bond yields", "retail sales",
        "manufacturing data", "economic data",
        "recession", "consumer spending"
    ]):
        return (
            "Economy",
            "global economy economic data financial markets"
        )

    # Technology
    if any(term in title_lower for term in [
        "artificial intelligence",
        "semiconductor", "semiconductors",
        "chip stocks", "technology",
        "tech stocks", "software",
        "cloud computing", "cybersecurity"
    ]) or re.search(r"\bAI\b", title, flags=re.I):
        return (
            "Technology",
            "technology innovation semiconductor computers"
        )

    # Banking
    if any(term in title_lower for term in [
        "banking sector", "commercial bank",
        "commercial banks", "bank stocks",
        "bank shares", "bank earnings",
        "bank collapse", "bank failure",
        "bank crisis", "lending"
    ]):
        return (
            "Banking",
            "banking financial institutions banking sector"
        )

    # Business
    if any(term in title_lower for term in [
        "company", "corporate", "business",
        "ceo", "chief executive",
        "expansion", "layoffs",
        "workforce", "partnership",
        "subsidiary", "corporate strategy"
    ]):
        return (
            "Business",
            "global business corporate companies"
        )

    # General markets
    if any(term in title_lower for term in [
        "shares", "stock", "stocks",
        "equities", "market rally",
        "market decline", "investors",
        "wall street", "nasdaq",
        "s&p 500", "dow jones",
        "stock exchange"
    ]):
        return (
            "Markets",
            "international stock exchange global financial markets"
        )

    return (
        "Markets",
        "international financial markets global business"
    )


def normalize_category(category, title):
    """Validate AI category and use headline detection if necessary."""

    category = str(category or "").strip()

    aliases = {
        "Stock Market": "Markets",
        "Stock Markets": "Markets",
        "Stocks": "Markets",
        "Cryptocurrency": "Crypto",
        "Bitcoin": "Crypto",
        "Foreign Exchange": "Forex",
        "Currencies": "Forex",
        "Gold": "Commodities",
        "Oil": "Commodities",
        "Mergers and Acquisitions": "Merger",
        "Acquisitions": "Merger",
        "Company News": "Business",
        "Economic News": "Economy",
        "Fed": "Federal Reserve",
    }

    category = aliases.get(category, category)

    if category in CATEGORIES:
        return category

    detected, _ = detect_category_and_image_keywords(title)

    return detected


def fallback_data(articles):
    """Safely publish publisher snippets when AI services fail."""

    stories = []

    for article in articles[:MAX_STORIES]:

        description = (
            article.get("description")
            or "The publisher has not supplied a summary. "
               "Open the original article for full details."
        )

        title = article.get("title", "")

        category, image_keywords = (
            detect_category_and_image_keywords(title)
        )

        stories.append({
            "rank": len(stories) + 1,
            "article_id": article.get("article_id", ""),
            "headline": title,
            "summary": description[:420],
            "source_name": article.get("source", ""),
            "source_url": article.get("link", ""),
            "published_time": article.get(
                "published_time",
                "Date not supplied by source"
            ),
            "impact_type": "Neutral",
            "market_impact": (
                "Potential market relevance is based on the headline "
                "and publisher snippet; direction is not independently "
                "established."
            ),
            "sectors_affected": [],
            "category": category,
            "image_keywords": image_keywords,
            "image": "",
            "image_credit": "",
            "summary_method": (
                "Publisher snippet (AI unavailable)"
            ),
        })

    overview = (
        "Today's global market-relevant headlines are listed below. "
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

        title = str(
            item.get("headline") or source.get("title", "")
        )[:240]

        category = normalize_category(
            item.get("category"),
            title
        )

        clean_stories.append({
            "rank": len(clean_stories) + 1,
            "article_id": aid,
            "headline": title,
            "summary": str(
                item.get("summary")
                or source.get("description", "")
            )[:900],
            "source_name": source.get("source", ""),
            "source_url": source.get("link", ""),
            "published_time": source.get(
                "published_time",
                "Date not supplied by source"
            ),
            "impact_type": impact,
            "market_impact": str(
                item.get("market_impact")
                or "Market impact is uncertain; review the original source."
            )[:350],
            "sectors_affected": [
                str(sector)[:50]
                for sector in sectors[:3]
            ],
            "category": category,
            "image_keywords": str(
                item.get("image_keywords")
                or detect_category_and_image_keywords(title)[1]
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

    if not providers:
        LOG.error("No AI providers are configured")
        return fallback_data(articles)

    for provider, function in providers:

        LOG.info("%s provider selected", provider)

        for attempt in range(1, retries + 1):

            try:
                LOG.info(
                    "Summarizing with %s (attempt %d/%d)",
                    provider,
                    attempt,
                    retries
                )

                raw = function(prompt)

                result = normalize_result(
                    raw,
                    articles,
                    provider
                )

                if result.get("ai_provider") == "fallback":
                    LOG.warning(
                        "%s returned no usable stories; "
                        "publisher snippets selected",
                        provider
                    )
                else:
                    LOG.info(
                        "%s summarization successful: %d stories",
                        provider,
                        len(result["stories"])
                    )

                    LOG.info(
                        "Market overview generated successfully by %s",
                        provider
                    )

                return result

            except Exception:

                LOG.exception(
                    "%s failed on attempt %d/%d",
                    provider,
                    attempt,
                    retries
                )

                if attempt < retries:
                    wait = min(
                        5 * (2 ** (attempt - 1)),
                        40
                    )

                    wait += random.uniform(0, 2)

                    LOG.info(
                        "Retrying %s in %.1f seconds",
                        provider,
                        wait
                    )

                    time.sleep(wait)

    LOG.error(
        "All configured AI providers failed; "
        "using publisher snippets"
    )

    return fallback_data(articles)
