import unittest

from modules.report import calculate_portfolio_value


class CalculatePortfolioValueTests(unittest.TestCase):
    def test_calculates_total_market_value(self) -> None:
        holdings = [
            {"ticker": "VOO", "shares": 12.0},
            {"ticker": "QQQ", "shares": 7.0},
        ]
        quotes = {
            "VOO": {"ticker": "VOO", "price": 100.0},
            "QQQ": {"ticker": "QQQ", "price": 68.25},
        }

        total_value = calculate_portfolio_value(holdings, quotes)

        self.assertEqual(total_value, 1677.75)


if __name__ == "__main__":
    unittest.main()
