"""Portfolio-level calculations built from holdings and market quotes."""

from typing import TypedDict

from modules.market import MarketQuote
from modules.portfolio import Holding


class ReportError(ValueError):
    """Raised when a complete portfolio report cannot be calculated."""


class PositionValue(TypedDict):
    """The current value and allocation of one portfolio holding."""

    ticker: str
    shares: float
    price: float
    market_value: float
    allocation: float


class PortfolioOverview(TypedDict):
    """Current portfolio-level metrics and position values."""

    total_value: float
    positions: list[PositionValue]
    largest_position: PositionValue


def build_portfolio_overview(
    holdings: list[Holding], quotes: dict[str, MarketQuote]
) -> PortfolioOverview:
    """Calculate current value and allocation using a quote for every holding."""

    if not holdings:
        raise ReportError("Cannot calculate an overview for an empty portfolio.")

    positions: list[PositionValue] = []

    for holding in holdings:
        ticker = holding["ticker"]
        quote = quotes.get(ticker)

        if quote is None:
            raise ReportError(f"No market quote is available for {ticker}.")

        positions.append(
            {
                "ticker": ticker,
                "shares": holding["shares"],
                "price": quote["price"],
                "market_value": holding["shares"] * quote["price"],
                "allocation": 0.0,
            }
        )

    total_value = sum(position["market_value"] for position in positions)

    if total_value <= 0:
        raise ReportError("Portfolio value must be greater than zero.")

    for position in positions:
        position["allocation"] = position["market_value"] / total_value

    return {
        "total_value": total_value,
        "positions": positions,
        "largest_position": max(positions, key=lambda position: position["market_value"]),
    }


def calculate_portfolio_value(
    holdings: list[Holding], quotes: dict[str, MarketQuote]
) -> float:
    """Return the complete current market value of all holdings."""

    return build_portfolio_overview(holdings, quotes)["total_value"]
