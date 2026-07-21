import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class AIError(Exception):
    """Raised when an AI provider cannot generate a response."""


def _build_news_prompt(ticker: str, articles: list[dict[str, Any]]) -> str:
    """Create the prompt used by every AI provider."""

    if not articles:
        raise ValueError("At least one news article is required.")

    headlines = "\n".join(
        f"- {article.get('title', 'Untitled article')}"
        for article in articles
    )

    return f"""
You are a cautious financial research assistant.

Analyze the following recent headlines related to {ticker}.

Headlines:
{headlines}

Return:

1. Summary: Two or three sentences explaining the important developments.
2. Positive developments: A concise list.
3. Risks: A concise list.
4. Sentiment: Positive, Neutral, or Negative.
5. Confidence: A number from 0 to 100.

Do not claim certainty.
Do not invent information beyond the supplied headlines.
Do not give personalized financial advice.
""".strip()


def _analyze_with_ollama(prompt: str) -> str:
    """Generate analysis using a locally running Ollama model."""

    try:
        from ollama import chat

        model = os.getenv("OLLAMA_MODEL", "llama3")

        response = chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Supports both object-style and dictionary-style responses.
        if hasattr(response, "message"):
            return response.message.content

        return response["message"]["content"]

    except Exception as exc:
        raise AIError(
            "Ollama request failed. Make sure Ollama is running and "
            "the configured model has been downloaded."
        ) from exc


def _analyze_with_openai(prompt: str) -> str:
    """Generate analysis using the OpenAI API."""

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise AIError(
            "OPENAI_API_KEY is missing from the .env file."
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

        response = client.responses.create(
            model=model,
            input=prompt,
        )

        return response.output_text

    except Exception as exc:
        raise AIError("OpenAI API request failed.") from exc


def summarize_news(
    ticker: str,
    articles: list[dict[str, Any]],
) -> str:
    """Analyze news using the provider selected in the environment."""

    provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()
    prompt = _build_news_prompt(ticker, articles)

    if provider == "ollama":
        return _analyze_with_ollama(prompt)

    if provider == "openai":
        return _analyze_with_openai(prompt)

    raise AIError(
        f"Unsupported AI provider: {provider}. "
        "Choose 'ollama' or 'openai'."
    )


def test_connection() -> str:
    """Send a minimal request through the selected provider."""

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
