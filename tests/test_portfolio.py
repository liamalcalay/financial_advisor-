"""Tests for portfolio loading and validation."""

import json
import tempfile
import unittest
from pathlib import Path

from modules.portfolio import (
    PortfolioError,
    load_portfolio,
    portfolio_summary,
    save_portfolio,
)

class LoadPortfolioTests(unittest.TestCase):
    def write_portfolio(self, contents: object) -> Path:
        temporary_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        )
        with temporary_file:
            json.dump(contents, temporary_file)
        self.addCleanup(Path(temporary_file.name).unlink)
        return Path(temporary_file.name)

    def test_loads_and_normalizes_a_valid_holding(self) -> None:
        path = self.write_portfolio({"holdings": [{"ticker": " voo ", "shares": 12}]})

        self.assertEqual(
            load_portfolio(path), [{"ticker": "VOO", "shares": 12.0}]
        )

    def test_rejects_non_positive_share_count(self) -> None:
        path = self.write_portfolio({"holdings": [{"ticker": "VOO", "shares": 0}]})

        with self.assertRaisesRegex(PortfolioError, "positive number"):
            load_portfolio(path)

    def test_rejects_missing_holdings_list(self) -> None:
        path = self.write_portfolio({})

        with self.assertRaisesRegex(PortfolioError, '"holdings" list'):
            load_portfolio(path)

    def test_summarizes_positions_and_shares(self) -> None:
        holdings = [
            {"ticker": "VOO", "shares": 12.0},
            {"ticker": "QQQ", "shares": 7.0},
        ]

        self.assertEqual(
            portfolio_summary(holdings),
            {"positions": 2, "total_shares": 19.0},
        )

    def test_saves_normalized_holdings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            portfolio_path = Path(temporary_directory) / "portfolio.json"
            save_portfolio(
                [
                    {"ticker": " voo ", "shares": 3},
                    {"ticker": "meta", "shares": 2.5},
                ],
                portfolio_path,
            )

            holdings = load_portfolio(portfolio_path)

        self.assertEqual(
            holdings,
            [
                {"ticker": "VOO", "shares": 3.0},
                {"ticker": "META", "shares": 2.5},
            ],
        )

    def test_rejects_non_finite_share_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            portfolio_path = Path(temporary_directory) / "portfolio.json"

            with self.assertRaisesRegex(PortfolioError, "positive number"):
                save_portfolio(
                    [{"ticker": "VOO", "shares": float("nan")}],
                    portfolio_path,
                )

if __name__ == "__main__":
    unittest.main()
