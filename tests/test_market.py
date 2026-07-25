import unittest
from unittest.mock import patch

import pandas as pd

from modules.market import (
    MarketDataError,
    get_market_context,
    get_price_history,
    get_stock_quote,
)


class GetStockQuoteTests(unittest.TestCase):
    @patch("modules.market.yf.Ticker")
    def test_returns_a_normalized_quote(self, mock_ticker) -> None:
        mock_ticker.return_value.fast_info = {"lastPrice": 123.45}

        quote = get_stock_quote(" voo ")

        self.assertEqual(quote, {"ticker": "VOO", "price": 123.45})
        mock_ticker.assert_called_once_with("VOO")

    def test_rejects_an_empty_ticker(self) -> None:
        with self.assertRaisesRegex(MarketDataError, "cannot be empty"):
            get_stock_quote("   ")

    @patch("modules.market.yf.Ticker")
    def test_returns_clean_closing_price_history(self, mock_ticker) -> None:
        raw_history = pd.DataFrame(
            {"Close": [100.0, None, 102.5]},
            index=pd.to_datetime(["2026-07-20", "2026-07-21", "2026-07-22"]),
        )
        mock_ticker.return_value.history.return_value = raw_history

        history = get_price_history(" voo ", "1mo")

        self.assertEqual(list(history.columns), ["VOO"])
        self.assertEqual(history["VOO"].tolist(), [100.0, 102.5])
        mock_ticker.return_value.history.assert_called_once_with(
            period="1mo",
            auto_adjust=False,
        )

    def test_rejects_an_unsupported_history_period(self) -> None:
        with self.assertRaisesRegex(MarketDataError, "Unsupported history period"):
            get_price_history("VOO", "10y")

    @patch("modules.market.get_price_history")
    def test_builds_one_month_market_context(self, mock_history) -> None:
        mock_history.return_value = pd.DataFrame({"VOO": [100.0, 110.0, 105.0]})

        context = get_market_context(" voo ")

        self.assertEqual(context["ticker"], "VOO")
        self.assertEqual(context["latest_price"], 105.0)
        self.assertEqual(context["one_month_change"], 0.05)
        self.assertEqual(context["one_month_low"], 100.0)
        self.assertEqual(context["one_month_high"], 110.0)
        mock_history.assert_called_once_with(" voo ", period="1mo")


if __name__ == "__main__":
    unittest.main()
