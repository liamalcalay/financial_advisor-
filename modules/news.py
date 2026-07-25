from typing import TypedDict

import yfinance as yf


class NewsArticle(TypedDict):
    title: str
    publisher: str
    url: str
    published: str


class NewsError(Exception):
    """Raised when news cannot be retrieved."""


def get_stock_news(ticker: str, limit: int = 3) -> list[NewsArticle]:
    """Return recent Yahoo Finance articles for a ticker."""

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker cannot be empty.")

    if limit <= 0:
        raise ValueError("Limit must be greater than zero.")

    try:
        raw_articles = yf.Ticker(ticker).get_news(count=limit)
    except Exception as exc:
        raise NewsError(f"Could not retrieve news for {ticker}.") from exc

    articles: list[NewsArticle] = []

    for item in raw_articles:
        # Newer yfinance versions place article data inside "content".
        content = item.get("content", item)

        title = content.get("title", "Untitled article")
        publisher = content.get("provider", {}).get("displayName", "Unknown")

        canonical_url = content.get("canonicalUrl", {})
        clickthrough_url = content.get("clickThroughUrl", {})

        url = (
            canonical_url.get("url")
            or clickthrough_url.get("url")
            or content.get("link")
            or ""
        )

        published = (
            content.get("pubDate")
            or content.get("providerPublishTime")
            or "Unknown"
        )

        articles.append(
            {
                "title": title,
                "publisher": publisher,
                "url": url,
                "published": str(published),
            }
        )

    return articles

if __name__ == "__main__":
    news = get_stock_news("META", limit=3)

    for number, article in enumerate(news, start=1):
        print(f"\n{number}. {article['title']}")
        print(f"   Publisher: {article['publisher']}")
        print(f"   Published: {article['published']}")
        print(f"   URL: {article['url']}")
