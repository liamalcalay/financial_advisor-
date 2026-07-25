"""Load and validate the portfolio data used by the application."""

from __future__ import annotations

import json
import math
from csv import DictReader
from io import StringIO
from pathlib import Path
from typing import TypedDict


class Holding(TypedDict):
    """One position in a portfolio."""

    ticker: str
    shares: float


class PortfolioError(ValueError):
    """Raised when a portfolio file is missing or has invalid contents."""


def _validate_portfolio(portfolio: object) -> list[Holding]:
    """Validate raw portfolio data and return normalized holdings."""

    if not isinstance(portfolio, dict):
        raise PortfolioError("Portfolio data must be a JSON object.")

    holdings = portfolio.get("holdings")
    if not isinstance(holdings, list):
        raise PortfolioError('Portfolio must contain a "holdings" list.')

    validated_holdings: list[Holding] = []
    for index, holding in enumerate(holdings, start=1):
        if not isinstance(holding, dict):
            raise PortfolioError(f"Holding {index} must be an object.")

        ticker = holding.get("ticker")
        shares = holding.get("shares")

        if not isinstance(ticker, str) or not ticker.strip():
            raise PortfolioError(f"Holding {index} needs a non-empty ticker.")
        if (
            isinstance(shares, bool)
            or not isinstance(shares, (int, float))
            or not math.isfinite(shares)
            or shares <= 0
        ):
            raise PortfolioError(f"Holding {index} needs a positive number of shares.")

        validated_holdings.append(
            {"ticker": ticker.strip().upper(), "shares": float(shares)}
        )

    return validated_holdings


def load_portfolio(filename: str | Path = "portfolio.json") -> list[Holding]:
    """Return validated holdings from a JSON portfolio file.

    The expected shape is ``{"holdings": [{"ticker": "VOO", "shares": 12}]}``.
    """

    path = Path(filename)

    try:
        with path.open(encoding="utf-8") as portfolio_file:
            portfolio = json.load(portfolio_file)
    except FileNotFoundError as error:
        raise PortfolioError(f"Portfolio file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise PortfolioError(f"Portfolio file contains invalid JSON: {path}") from error

    return _validate_portfolio(portfolio)


def save_portfolio(
    holdings: list[Holding],
    filename: str | Path = "portfolio.json",
) -> None:
    """Validate and atomically save holdings to the local portfolio file."""

    normalized_holdings = _validate_portfolio({"holdings": holdings})
    path = Path(filename)
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    try:
        temporary_path.write_text(
            json.dumps({"holdings": normalized_holdings}, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    except OSError as error:
        raise PortfolioError(f"Could not save portfolio: {path}") from error


def import_positions_csv(csv_text: str) -> list[Holding]:
    """Extract market-traded holdings from a brokerage positions CSV export.

    The importer requires ``Ticker`` and ``Quantity`` columns, combines duplicate
    tickers, and skips cash or money-market sweep entries because the dashboard
    only retrieves market data for securities.
    """

    reader = DictReader(StringIO(csv_text))
    fieldnames = reader.fieldnames or []

    if "Ticker" not in fieldnames or "Quantity" not in fieldnames:
        raise PortfolioError("CSV must include Ticker and Quantity columns.")

    totals: dict[str, float] = {}
    for row in reader:
        ticker = (row.get("Ticker") or "").strip().upper()
        asset_class = (row.get("Asset Class") or "").strip().lower()
        raw_quantity = (row.get("Quantity") or "").replace(",", "").strip()

        if not ticker or "cash" in asset_class or "money market" in asset_class:
            continue

        try:
            quantity = float(raw_quantity)
        except ValueError as error:
            raise PortfolioError(f"Invalid quantity for {ticker}.") from error

        if not math.isfinite(quantity) or quantity <= 0:
            continue

        totals[ticker] = totals.get(ticker, 0.0) + quantity

    holdings: list[Holding] = [
        {"ticker": ticker, "shares": shares}
        for ticker, shares in totals.items()
    ]

    if not holdings:
        raise PortfolioError("No market-traded positions were found in the CSV.")

    return holdings

def portfolio_summary(holdings: list[Holding]) -> dict[str, int | float]:
    position_count = 0
    total_shares = 0.0

    for holding in holdings:
        position_count += 1
        total_shares += holding["shares"]

    return {"positions": position_count, "total_shares": total_shares}
