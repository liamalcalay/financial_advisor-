"""Retrieve current market data for portfolio holdings."""

from typing import TypedDict

import pandas as pd
import yfinance as yf


class MarketQuote(TypedDict):
    """The market data our application needs for one ticker."""

    ticker: str
    price: float


class MarketContext(TypedDict):
    """Recent price context used to ground a news analysis."""

    ticker: str
    latest_price: float
    one_month_change: float
    one_month_high: float
    one_month_low: float


class MarketDataError(RuntimeError):
    """Raised when market data cannot be retrieved."""


VALID_HISTORY_PERIODS = {"5d", "1mo", "3mo", "6mo", "1y"}


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


def get_price_history(ticker: str, period: str = "1mo") -> pd.DataFrame:
    """Return a validated daily closing-price series for one ticker.

    The returned DataFrame has one numeric column named after the normalized
    ticker and a date/time index supplied by Yahoo Finance via yfinance.
    """

    clean_ticker = ticker.strip().upper()
    if not clean_ticker:
        raise MarketDataError("Ticker cannot be empty.")
    if period not in VALID_HISTORY_PERIODS:
        raise MarketDataError(f"Unsupported history period: {period}.")

    try:
        history = yf.Ticker(clean_ticker).history(
            period=period,
            auto_adjust=False,
        )
    except Exception as error:
        raise MarketDataError(
            f"Could not retrieve price history for {clean_ticker}."
        ) from error

    if history.empty or "Close" not in history.columns:
        raise MarketDataError(f"No closing-price history was returned for {clean_ticker}.")

    close_prices = history[["Close"]].copy()
    close_prices["Close"] = pd.to_numeric(close_prices["Close"], errors="coerce")
    close_prices = close_prices.dropna()

    if close_prices.empty:
        raise MarketDataError(f"No valid closing prices were returned for {clean_ticker}.")

    return close_prices.rename(columns={"Close": clean_ticker})


def get_market_context(ticker: str) -> MarketContext:
    """Return a small, validated one-month price snapshot for research."""

    history = get_price_history(ticker, period="1mo")
    clean_ticker = ticker.strip().upper()
    prices = history[clean_ticker]
    opening_price = float(prices.iloc[0])
    latest_price = float(prices.iloc[-1])

    if opening_price <= 0:
        raise MarketDataError(f"No valid opening price was returned for {clean_ticker}.")

    return {
        "ticker": clean_ticker,
        "latest_price": latest_price,
        "one_month_change": (latest_price - opening_price) / opening_price,
        "one_month_high": float(prices.max()),
        "one_month_low": float(prices.min()),
    }
