"""
EUR/USD VisionPulse AI - Multimodal Brain
Uses Gemini 1.5 Flash to process chart screenshots, OHLCV data,
and news headlines simultaneously to produce a Trade Thesis.
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _get_model():
    """Initialize and return the Gemini generative model."""
    import google.generativeai as genai

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model


def _load_image_as_part(image_path: str) -> dict:
    """Load an image file and return it as a Gemini content part."""
    import google.generativeai as genai

    with open(image_path, "rb") as f:
        image_data = f.read()

    return {
        "mime_type": "image/png",
        "data": image_data,
    }


def build_analysis_prompt(
    quant_text: str,
    news_text: str,
    lessons_learned: list[str] | None = None,
) -> str:
    """
    Build the master prompt for Gemini that combines all data sources.
    """
    lessons_section = ""
    if lessons_learned:
        lessons_section = "\n=== LESSONS FROM PAST MISTAKES ===\n"
        for i, lesson in enumerate(lessons_learned, 1):
            lessons_section += f"{i}. {lesson}\n"
        lessons_section += "\nIMPORTANT: Factor these past lessons into your current analysis. Do NOT repeat past mistakes.\n"

    prompt = f"""You are "VisionPulse AI", an expert EUR/USD forex trading analyst.
You have been given THREE data sources to analyze simultaneously:

1. **CHART IMAGE**: A live 30-minute TradingView chart of EUR/USD (attached).
   Analyze: candlestick patterns, support/resistance levels, trend lines, moving averages visible on chart.

2. **QUANTITATIVE DATA**:
{quant_text}

3. **NEWS & SENTIMENT**:
{news_text}
{lessons_section}
=== YOUR TASK ===
Perform a comprehensive multimodal analysis and produce a JSON response with EXACTLY this structure:

{{
    "trade_thesis": "BULLISH" | "BEARISH" | "NEUTRAL",
    "confidence_score": <float 0.0 to 1.0>,
    "entry_price": <suggested entry price or null>,
    "stop_loss": <suggested stop loss or null>,
    "take_profit": <suggested take profit or null>,
    "timeframe": "30m" | "1h" | "4h",
    "chart_analysis": "<what you observe in the chart image>",
    "technical_analysis": "<analysis of the quantitative data>",
    "fundamental_analysis": "<analysis of the news sentiment>",
    "risk_factors": ["<risk 1>", "<risk 2>", ...],
    "reasoning": "<step-by-step reasoning combining all sources>",
    "key_levels": {{
        "support": [<price levels>],
        "resistance": [<price levels>]
    }}
}}

RULES:
- Your confidence_score must reflect genuine uncertainty. Do NOT default to high confidence.
- If chart and news conflict, explain the conflict and lower confidence.
- If you cannot clearly read the chart, say so and rely more on quantitative data.
- Always identify at least 2 risk factors.
- Return ONLY valid JSON, no markdown formatting.
"""
    return prompt


def analyze(
    chart_image_path: str | None,
    quant_text: str,
    news_text: str,
    lessons_learned: list[str] | None = None,
) -> dict:
    """
    Run the full multimodal analysis using Gemini 1.5 Flash.

    Args:
        chart_image_path: Path to the chart screenshot PNG.
        quant_text: Formatted quantitative data string.
        news_text: Formatted news/sentiment string.
        lessons_learned: List of past lesson strings from learning loop.

    Returns:
        Dictionary with the trade thesis and supporting analysis.
    """
    try:
        model = _get_model()
    except ValueError as e:
        print(f"[Brain] {e}")
        return _fallback_analysis(quant_text, news_text)

    prompt = build_analysis_prompt(quant_text, news_text, lessons_learned)

    # Build multimodal content
    content_parts = []

    if chart_image_path and Path(chart_image_path).exists():
        image_part = _load_image_as_part(chart_image_path)
        content_parts.append(image_part)
        print(f"[Brain] Using chart image: {chart_image_path}")
    else:
        prompt += "\n\nNOTE: Chart image is unavailable. Rely on quantitative data and news only."
        print("[Brain] No chart image available, using text-only analysis.")

    content_parts.append(prompt)

    try:
        response = model.generate_content(
            content_parts,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 2048,
            },
        )

        response_text = response.text.strip()

        # Clean up response - remove markdown code block if present
        if response_text.startswith("```"):
            # Remove ```json\n ... \n```
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        result = json.loads(response_text)
        result["timestamp"] = datetime.utcnow().isoformat()
        result["model"] = "gemini-1.5-flash"

        print(f"[Brain] Analysis complete: {result.get('trade_thesis')} (Confidence: {result.get('confidence_score')})")
        return result

    except json.JSONDecodeError as e:
        print(f"[Brain] Failed to parse Gemini response as JSON: {e}")
        print(f"[Brain] Raw response: {response_text[:500]}")
        return _extract_fallback_from_text(response_text)

    except Exception as e:
        print(f"[Brain] Gemini API error: {e}")
        return _fallback_analysis(quant_text, news_text)


def _extract_fallback_from_text(text: str) -> dict:
    """Try to extract meaningful data from non-JSON Gemini response."""
    thesis = "NEUTRAL"
    if "BULLISH" in text.upper():
        thesis = "BULLISH"
    elif "BEARISH" in text.upper():
        thesis = "BEARISH"

    return {
        "trade_thesis": thesis,
        "confidence_score": 0.3,
        "entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "timeframe": "30m",
        "chart_analysis": "Response parsing failed - see raw text",
        "technical_analysis": text[:500],
        "fundamental_analysis": "",
        "risk_factors": ["AI response was not properly structured"],
        "reasoning": text[:1000],
        "key_levels": {"support": [], "resistance": []},
        "timestamp": datetime.utcnow().isoformat(),
        "model": "gemini-1.5-flash (fallback parse)",
    }


def _fallback_analysis(quant_text: str, news_text: str) -> dict:
    """Generate a basic analysis when the Gemini API is unavailable."""
    print("[Brain] Using fallback rule-based analysis.")

    thesis = "NEUTRAL"
    confidence = 0.2

    # Simple keyword-based fallback
    if "Bullish" in quant_text and "Bullish" in news_text:
        thesis = "BULLISH"
        confidence = 0.4
    elif "Bearish" in quant_text and "Bearish" in news_text:
        thesis = "BEARISH"
        confidence = 0.4
    elif "Bullish" in quant_text:
        thesis = "BULLISH"
        confidence = 0.3
    elif "Bearish" in quant_text:
        thesis = "BEARISH"
        confidence = 0.3

    return {
        "trade_thesis": thesis,
        "confidence_score": confidence,
        "entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "timeframe": "30m",
        "chart_analysis": "Gemini API unavailable - no chart analysis",
        "technical_analysis": "Rule-based fallback using keyword matching",
        "fundamental_analysis": "Rule-based fallback using keyword matching",
        "risk_factors": ["AI model unavailable", "Using basic heuristics only"],
        "reasoning": "Fallback analysis based on simple keyword matching of technical and news signals.",
        "key_levels": {"support": [], "resistance": []},
        "timestamp": datetime.utcnow().isoformat(),
        "model": "fallback-rules",
    }


if __name__ == "__main__":
    # Quick test with mock data
    test_quant = "SMA Signal: Bullish\nRSI(14): 55 (Neutral)"
    test_news = "Overall Sentiment: Bullish\nECB holds rates steady"
    result = analyze(None, test_quant, test_news)
    print(json.dumps(result, indent=2))
