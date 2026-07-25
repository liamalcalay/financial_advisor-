import unittest

from modules.report import build_portfolio_overview, calculate_portfolio_value


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

    def test_calculates_position_allocations(self) -> None:
        holdings = [
            {"ticker": "VOO", "shares": 10.0},
            {"ticker": "QQQ", "shares": 5.0},
        ]
        quotes = {
            "VOO": {"ticker": "VOO", "price": 100.0},
            "QQQ": {"ticker": "QQQ", "price": 100.0},
        }

        overview = build_portfolio_overview(holdings, quotes)

        self.assertEqual(overview["total_value"], 1500.0)
        self.assertEqual(overview["largest_position"]["ticker"], "VOO")
        self.assertEqual(overview["positions"][0]["allocation"], 2 / 3)
        self.assertEqual(overview["positions"][1]["allocation"], 1 / 3)


if __name__ == "__main__":
    unittest.main()
