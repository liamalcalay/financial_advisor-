"""Command-line entry point for the AI Portfolio Analyst."""

from modules.portfolio import Holding, PortfolioError, load_portfolio, portfolio_summary
from modules.market import MarketDataError, MarketQuote, get_stock_quote
from modules.news import get_stock_news
from modules.news import get_stock_news

def format_shares(shares: float) -> str:
    """Display whole shares without a decimal point."""

    return str(int(shares)) if shares.is_integer() else str(shares)


def display_portfolio(
    holdings: list[Holding], quotes: dict[str, MarketQuote]
) -> None:
    
    print("=== Portfolio ===\n")
    if not holdings:
        print("No holdings found.")
    else:
        for holding in holdings:
            ticker = holding["ticker"]
            try:
                quote = get_stock_quote(ticker)
                quotes[quote["ticker"]] = quote
            except MarketDataError as error:
                print(f"Market data warning: {error}")

            news = get_stock_news(ticker)

            print(f"\n{ticker} News:")

            try:
                news = get_stock_news(holding["ticker"], limit=3)

                print("\nTop News")

                for article in news:
                    print(f"• {article['title']}")

            except Exception:
                print("\nNo recent news available.")

    print("=================")


def main() -> None:
    try:
        holdings = load_portfolio()

        quotes: dict[str, MarketQuote] = {}

        for holding in holdings:
            try:
                quote = get_stock_quote(holding["ticker"])
                quotes[quote["ticker"]] = quote
            except MarketDataError as error:
                print(f"Market data warning: {error}")

        display_portfolio(holdings, quotes)
        summary = portfolio_summary(holdings)
        print(f"Positions: {summary['positions']}")
        print(f"Total shares: {summary['total_shares']}")
    except PortfolioError as error:
        print(f"Portfolio error: {error}")


if __name__ == "__main__":
    main()
