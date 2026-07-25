"""Command-line entry point for the AI Portfolio Analyst."""

from modules.ai import AIError, summarize_news
from modules.market import MarketDataError, MarketQuote, get_stock_quote
from modules.news import NewsError, get_stock_news
from modules.portfolio import (
    Holding,
    PortfolioError,
    load_portfolio,
    portfolio_summary,
)


def format_shares(shares: float) -> str:
    """Display whole shares without a decimal point."""

    return str(int(shares)) if shares.is_integer() else str(shares)


def load_quotes(holdings: list[Holding]) -> dict[str, MarketQuote]:
    """Retrieve one market quote for each holding."""

    quotes: dict[str, MarketQuote] = {}

    for holding in holdings:
        ticker = holding["ticker"]

        try:
            quote = get_stock_quote(ticker)
            quotes[ticker] = quote
        except MarketDataError as error:
            print(f"Market data warning for {ticker}: {error}")

    return quotes


def display_portfolio(
    holdings: list[Holding],
    quotes: dict[str, MarketQuote],
) -> None:
    """Display holdings, prices, news, and AI analysis."""

    print("=== Portfolio ===\n")

    if not holdings:
        print("No holdings found.")
        return

    for holding in holdings:
        ticker = holding["ticker"]
        shares = holding["shares"]

        print(ticker)
        print(f"Shares: {format_shares(shares)}")

        quote = quotes.get(ticker)

        if quote:
            print(f"Price: ${quote['price']:.2f}")
        else:
            print("Price: unavailable")

        try:
            news = get_stock_news(ticker, limit=3)

            print("\nTop News")

            if not news:
                print("No recent news available.")
            else:
                for article in news:
                    print(f"• {article['title']}")

                print("\nAI Analysis")

                try:
                    analysis = summarize_news(ticker, news)

                    print(f"Summary: {analysis.summary}")
                    print(f"Sentiment: {analysis.sentiment.title()}")
                    print(f"Risk level: {analysis.risk_level.title()}")
                    print(f"Confidence: {analysis.confidence:.0%}")

                    print("Key points:")
                    for point in analysis.key_points:
                        print(f"• {point}")

                except AIError as error:
                    print(f"AI analysis unavailable: {error}")

        except NewsError as error:
            print(f"\nNews unavailable: {error}")

        print("\n" + "-" * 50 + "\n")


def main() -> None:
    """Run the portfolio analysis application."""

    try:
        holdings = load_portfolio()
        quotes = load_quotes(holdings)

        display_portfolio(holdings, quotes)

        summary = portfolio_summary(holdings)

        print("=================")
        print(f"Positions: {summary['positions']}")
        print(f"Total shares: {summary['total_shares']}")

    except PortfolioError as error:
        print(f"Portfolio error: {error}")


if __name__ == "__main__":
    main()