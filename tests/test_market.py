import unittest
from unittest.mock import patch

from modules.market import MarketDataError, get_stock_quote


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


if __name__ == "__main__":
    unittest.main()
