"""
EUR/USD VisionPulse AI - Fundamental Intelligence Layer
Pulls live headlines related to ECB, Federal Reserve, EUR/USD, and Inflation
from NewsAPI.org (with EODHD as optional fallback).
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "")

# Keywords to track
KEYWORDS = ["ECB", "Federal Reserve", "EUR/USD", "EURUSD", "Inflation", "Interest Rate", "NFP", "CPI"]


def fetch_news_newsapi(max_articles: int = 20) -> list[dict]:
    """
    Fetch relevant financial news from NewsAPI.org.

    Returns:
        List of article dicts with title, source, description, publishedAt, url.
    """
    if not NEWSAPI_KEY:
        print("[FundIntel] Warning: NEWSAPI_KEY not set. Skipping NewsAPI.")
        return []

    query = " OR ".join(KEYWORDS[:5])  # NewsAPI free tier has query length limits
    from_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": max_articles,
        "apiKey": NEWSAPI_KEY,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for art in data.get("articles", []):
            articles.append({
                "title": art.get("title", ""),
                "source": art.get("source", {}).get("name", "Unknown"),
                "description": art.get("description", ""),
                "published_at": art.get("publishedAt", ""),
                "url": art.get("url", ""),
            })

        print(f"[FundIntel] Fetched {len(articles)} articles from NewsAPI")
        return articles

    except requests.RequestException as e:
        print(f"[FundIntel] NewsAPI error: {e}")
        return []


def fetch_news_eodhd(max_articles: int = 20) -> list[dict]:
    """
    Fetch financial news from EODHD as a fallback.

    Returns:
        List of article dicts.
    """
    if not EODHD_API_KEY:
        print("[FundIntel] EODHD_API_KEY not set. Skipping EODHD.")
        return []

    url = "https://eodhd.com/api/news"
    params = {
        "s": "EURUSD.FOREX",
        "offset": 0,
        "limit": max_articles,
        "api_token": EODHD_API_KEY,
        "fmt": "json",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for art in data if isinstance(data, list) else []:
            articles.append({
                "title": art.get("title", ""),
                "source": "EODHD",
                "description": art.get("content", "")[:300],
                "published_at": art.get("date", ""),
                "url": art.get("link", ""),
            })

        print(f"[FundIntel] Fetched {len(articles)} articles from EODHD")
        return articles

    except requests.RequestException as e:
        print(f"[FundIntel] EODHD error: {e}")
        return []


def fetch_all_news(max_articles: int = 20) -> list[dict]:
    """
    Try NewsAPI first, fall back to EODHD if no results.

    Returns:
        Combined list of articles.
    """
    articles = fetch_news_newsapi(max_articles)
    if not articles:
        articles = fetch_news_eodhd(max_articles)
    return articles


def analyze_headline_sentiment(articles: list[dict]) -> dict:
    """
    Basic keyword-based sentiment analysis on headlines.
    Returns a sentiment summary dict.
    """
    bullish_words = [
        "surge", "rally", "gains", "bullish", "rise", "higher", "boost",
        "strong", "recovery", "dovish", "cut rate", "stimulus", "growth",
        "beat", "exceed", "optimism", "upbeat",
    ]
    bearish_words = [
        "drop", "fall", "crash", "bearish", "decline", "lower", "weak",
        "hawkish", "hike rate", "recession", "slowdown", "miss", "concern",
        "fear", "risk", "slump", "plunge",
    ]

    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    key_headlines = []

    for art in articles:
        text = (art.get("title", "") + " " + art.get("description", "")).lower()

        b_score = sum(1 for w in bullish_words if w in text)
        s_score = sum(1 for w in bearish_words if w in text)

        if b_score > s_score:
            bullish_count += 1
        elif s_score > b_score:
            bearish_count += 1
        else:
            neutral_count += 1

        # Track high-impact headlines
        for kw in ["NFP", "CPI", "FOMC", "ECB", "rate decision", "payroll"]:
            if kw.lower() in text:
                key_headlines.append(art["title"])
                break

    total = bullish_count + bearish_count + neutral_count
    if total == 0:
        overall = "Neutral"
    elif bullish_count > bearish_count:
        overall = "Bullish"
    elif bearish_count > bullish_count:
        overall = "Bearish"
    else:
        overall = "Neutral"

    return {
        "overall_sentiment": overall,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,
        "total_articles": total,
        "key_headlines": key_headlines[:5],
    }


def format_news_for_prompt(articles: list[dict]) -> str:
    """Format news data as a text prompt for the AI."""
    sentiment = analyze_headline_sentiment(articles)

    lines = [
        "=== FUNDAMENTAL NEWS INTELLIGENCE ===",
        f"Overall Sentiment: {sentiment['overall_sentiment']}",
        f"Bullish Articles: {sentiment['bullish_count']}",
        f"Bearish Articles: {sentiment['bearish_count']}",
        f"Neutral Articles: {sentiment['neutral_count']}",
        "",
    ]

    if sentiment["key_headlines"]:
        lines.append("--- HIGH-IMPACT Headlines ---")
        for hl in sentiment["key_headlines"]:
            lines.append(f"  * {hl}")
        lines.append("")

    lines.append("--- Recent Headlines ---")
    for art in articles[:10]:
        lines.append(f"  [{art['source']}] {art['title']}")
        if art.get("published_at"):
            lines.append(f"    Published: {art['published_at']}")

    return "\n".join(lines)


if __name__ == "__main__":
    articles = fetch_all_news()
    if articles:
        print(format_news_for_prompt(articles))
    else:
        print("No articles fetched. Check your API keys.")
