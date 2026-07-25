"""AI provider functions for generating structured stock analysis."""

import json
import os
from collections.abc import Sequence
from typing import Any

from dotenv import load_dotenv

from models.analysis import ResearchSource, StockAnalysis, StockEvidence
from modules.market import MarketContext
from modules.recommendation import assess_evidence


load_dotenv()


class AIError(Exception):
    """Raised when an AI provider cannot generate or parse a response."""


ANALYSIS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "summary": {"type": "string"},
        "sentiment": {
            "type": "string",
            "enum": ["positive", "neutral", "negative"],
        },
        "risk_level": {
            "type": "string",
            "enum": ["low", "medium", "high"],
        },
        "confidence": {"type": "number"},
        "key_points": {
            "type": "array",
            "items": {"type": "string"},
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "article_index": {"type": "integer"},
                    "impact": {
                        "type": "string",
                        "enum": ["positive", "neutral", "negative"],
                    },
                    "materiality": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "claim": {"type": "string"},
                },
                "required": ["article_index", "impact", "materiality", "claim"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "ticker",
        "summary",
        "sentiment",
        "risk_level",
        "confidence",
        "key_points",
        "evidence",
    ],
    "additionalProperties": False,
}


def _build_analysis_prompt(
    ticker: str,
    articles: Sequence[dict[str, Any]],
    market_context: MarketContext | None = None,
) -> str:
    """Build a prompt requesting structured JSON analysis."""

    if not articles:
        raise AIError("At least one news article is required.")

    headlines = "\n".join(
        (
            f"[{index}] {article.get('title', 'Untitled article')}\n"
            f"    Source: {article.get('publisher', 'Unknown')}\n"
            f"    Published: {article.get('published', 'Unknown')}\n"
            f"    URL: {article.get('url', 'Unavailable')}"
        )
        for index, article in enumerate(articles, start=1)
    )

    if market_context is None:
        market_snapshot = "No market-price snapshot was available."
    else:
        market_snapshot = (
            f"Latest price: ${market_context['latest_price']:.2f}\n"
            f"One-month change: {market_context['one_month_change']:+.2%}\n"
            f"One-month range: ${market_context['one_month_low']:.2f} "
            f"to ${market_context['one_month_high']:.2f}"
        )

    return f"""
You are a cautious financial research assistant.

Analyze recent news and the supplied market snapshot for {ticker}.

Market snapshot:
{market_snapshot}

Headlines:
{headlines}

Return valid JSON only.
Do not use markdown.
Do not include explanations outside the JSON.
Do not invent information beyond the supplied headlines.
Do not give personalized financial advice.
Do not use outside knowledge.
Only make claims directly supported by the supplied headlines or market snapshot.
If the supplied information does not provide enough evidence, say that clearly.
Do not describe what the company, fund, or ticker tracks unless a supplied
headline explicitly states it.
Every news-based key point must cite the supporting headline number in brackets,
such as "[2] Earnings guidance was reduced." A market-price statement must be
labelled "[Market snapshot]". Do not infer a recommendation from a single
low-materiality headline or from price movement alone.

Use exactly this structure:

{{
  "ticker": "{ticker}",
  "summary": "A cautious summary based only on the supplied headlines. State when evidence is limited.",
  "sentiment": "positive",
  "risk_level": "low",
  "confidence": 0.75,
  "key_points": [
    "First important point",
    "Second important point"
  ],
  "evidence": [
    {{
      "article_index": 1,
      "impact": "positive",
      "materiality": "medium",
      "claim": "A claim directly supported by headline [1]."
    }}
  ]
}}

Requirements:
- sentiment must be "positive", "neutral", or "negative"
- risk_level must be "low", "medium", or "high"
- confidence must be between 0.0 and 1.0
- key_points must be a JSON list of strings
- evidence must contain only claims directly supported by one supplied article
- article_index must refer to the numbered headline that supports the claim
""".strip()


def _analyze_with_ollama(prompt: str) -> str:
    """Generate structured JSON using Ollama."""

    try:
        from ollama import chat

        model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

        response = chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return only valid JSON. "
                        "Do not use markdown or explanatory text."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            format={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "summary": {"type": "string"},
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "neutral", "negative"],
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                    },
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "ticker",
                    "summary",
                    "sentiment",
                    "risk_level",
                    "confidence",
                    "key_points",
                ],
            },
            options={
                "temperature": 0,
                "num_predict": 300,
                "num_ctx": 2048,
            },
            keep_alive="10m",
        )

        content = response.message.content

        if not content:
            raise AIError("Ollama returned an empty response.")

        return content.strip()

    except AIError:
        raise

    except Exception as exc:
        raise AIError(f"Ollama request failed: {exc}") from exc


def _analyze_with_gemini(prompt: str) -> str:
    """Generate schema-constrained analysis using the Gemini API."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise AIError("GEMINI_API_KEY is missing from the .env file.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=ANALYSIS_RESPONSE_SCHEMA,
            ),
        )

        if not response.text:
            raise AIError("Gemini returned an empty response.")

        return response.text.strip()

    except AIError:
        raise
    except Exception as exc:
        raise AIError(f"Gemini request failed: {exc}") from exc


def _parse_analysis(
    raw_response: str,
    articles: Sequence[dict[str, Any]],
) -> StockAnalysis:
    """Parse and validate an AI response."""

    cleaned_response = raw_response.strip()

    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response.replace("```json", "")
        cleaned_response = cleaned_response.replace("```", "")
        cleaned_response = cleaned_response.strip()

    start = cleaned_response.find("{")
    end = cleaned_response.rfind("}")

    if start == -1 or end == -1:
        raise AIError(
            f"AI response did not contain JSON:\n{raw_response}"
        )

    cleaned_response = cleaned_response[start : end + 1]

    try:
        data = json.loads(cleaned_response)
    except json.JSONDecodeError as error:
        raise AIError(
            f"AI returned invalid JSON:\n{raw_response}"
        ) from error

    if not isinstance(data, dict):
        raise AIError("AI response must be a JSON object.")

    required_fields = {
        "ticker",
        "summary",
        "sentiment",
        "risk_level",
        "confidence",
        "key_points",
        "evidence",
    }

    missing_fields = required_fields - data.keys()

    if missing_fields:
        raise AIError(
            f"AI response is missing fields: {sorted(missing_fields)}"
        )

    sentiment = str(data["sentiment"]).strip().lower()
    risk_level = str(data["risk_level"]).strip().lower()

    try:
        confidence = float(data["confidence"])
    except (TypeError, ValueError) as exc:
        raise AIError("Confidence must be a number.") from exc

    key_points = data["key_points"]
    raw_evidence = data["evidence"]

    if sentiment not in {"positive", "neutral", "negative"}:
        raise AIError(f"Invalid sentiment: {sentiment}")

    if risk_level not in {"low", "medium", "high"}:
        raise AIError(f"Invalid risk level: {risk_level}")

    if not 0.0 <= confidence <= 1.0:
        raise AIError("Confidence must be between 0.0 and 1.0.")

    if not isinstance(key_points, list):
        raise AIError("key_points must be a list.")

    if not isinstance(raw_evidence, list):
        raise AIError("evidence must be a list.")

    evidence: list[StockEvidence] = []
    for index, item in enumerate(raw_evidence, start=1):
        if not isinstance(item, dict):
            raise AIError(f"Evidence item {index} must be an object.")

        article_index = item.get("article_index")
        impact = str(item.get("impact", "")).lower()
        materiality = str(item.get("materiality", "")).lower()
        claim = item.get("claim")

        if (
            isinstance(article_index, bool)
            or not isinstance(article_index, int)
            or not 1 <= article_index <= len(articles)
        ):
            raise AIError(f"Evidence item {index} has an invalid article_index.")
        if impact not in {"positive", "neutral", "negative"}:
            raise AIError(f"Evidence item {index} has an invalid impact.")
        if materiality not in {"low", "medium", "high"}:
            raise AIError(f"Evidence item {index} has an invalid materiality.")
        if not isinstance(claim, str) or not claim.strip():
            raise AIError(f"Evidence item {index} needs a non-empty claim.")

        evidence.append(
            StockEvidence(
                article_index=article_index,
                impact=impact,
                materiality=materiality,
                claim=claim.strip(),
            )
        )

    assessment = assess_evidence(evidence, confidence)
    sources = [
        ResearchSource(
            title=str(article.get("title", "Untitled article")),
            publisher=str(article.get("publisher", "Unknown")),
            url=str(article.get("url", "")),
            published=str(article.get("published", "Unknown")),
        )
        for article in articles
    ]

    return StockAnalysis(
        ticker=str(data["ticker"]).strip(),
        summary=str(data["summary"]).strip(),
        sentiment=sentiment,
        risk_level=risk_level,
        confidence=confidence,
        key_points=[str(point).strip() for point in key_points],
        recommendation=assessment["recommendation"],
        evidence_score=assessment["evidence_score"],
        evidence=evidence,
        sources=sources,
    )


def summarize_news(
    ticker: str,
    articles: Sequence[dict[str, Any]],
    market_context: MarketContext | None = None,
) -> StockAnalysis:
    """Generate and return structured analysis for recent news."""

    prompt = _build_analysis_prompt(ticker, articles, market_context)
    provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()

    for attempt in range(2):
        if provider == "ollama":
            raw_response = _analyze_with_ollama(prompt)
        elif provider == "gemini":
            raw_response = _analyze_with_gemini(prompt)
        elif provider == "openai":
            raw_response = _analyze_with_openai(prompt)
        else:
            raise AIError(
                f"Unsupported AI provider: {provider}. "
                "Use 'ollama' or 'openai'."
            )

        try:
            return _parse_analysis(raw_response, articles)
        except AIError:
            if attempt == 1:
                raise

    raise AIError("Unable to generate analysis.")


def test_connection() -> StockAnalysis:
    """Send a minimal test request through the selected provider."""

    test_articles = [
        {
            "title": (
                "Example company announces a new product while "
                "warning about higher operating costs."
            )
        }
    ]

    return summarize_news("TEST", test_articles)


if __name__ == "__main__":
    print(test_connection())
