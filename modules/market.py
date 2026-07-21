"""Retrieve current market data for portfolio holdings."""

from typing import TypedDict

import yfinance as yf


class MarketQuote(TypedDict):
    """The market data our application needs for one ticker."""

    ticker: str
    price: float


class MarketDataError(RuntimeError):
    """Raised when market data cannot be retrieved."""

def get_stock_quote(ticker: str) -> MarketQuote:
    """Return the latest available price for one stock or ETF ticker."""

    clean_ticker = ticker.strip().upper()
    if not clean_ticker:
        raise MarketDataError("Ticker cannot be empty.")

    try:
        raw_price = yf.Ticker(clean_ticker).fast_info["lastPrice"]
    except Exception as error:
        raise MarketDataError(
            f"Could not retrieve a price for {clean_ticker}."
        ) from error

    if isinstance(raw_price, bool) or not isinstance(raw_price, (int, float)):
        raise MarketDataError(f"No valid price was returned for {clean_ticker}.")

    return {"ticker": clean_ticker, "price": float(raw_price)}