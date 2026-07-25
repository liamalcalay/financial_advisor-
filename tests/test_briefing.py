import unittest

from models.analysis import StockAnalysis
from modules.briefing import (
    build_portfolio_briefing,
    build_portfolio_direction_feedback,
)


class PortfolioBriefingTests(unittest.TestCase):
    def test_surfaces_concentration_and_attention_flags(self) -> None:
        overview = {
            "total_value": 10_000.0,
            "positions": [
                {
                    "ticker": "VOO",
                    "shares": 10.0,
                    "price": 700.0,
                    "market_value": 7_000.0,
                    "allocation": 0.7,
                },
                {
                    "ticker": "META",
                    "shares": 5.0,
                    "price": 600.0,
                    "market_value": 3_000.0,
                    "allocation": 0.3,
                },
            ],
            "largest_position": {
                "ticker": "VOO",
                "shares": 10.0,
                "price": 700.0,
                "market_value": 7_000.0,
                "allocation": 0.7,
            },
        }
        analyses = [
            StockAnalysis(
                ticker="VOO",
                summary="Neutral coverage.",
                sentiment="neutral",
                risk_level="low",
                confidence=0.7,
                key_points=[],
                evidence_score=2,
            ),
            StockAnalysis(
                ticker="META",
                summary="Material concern.",
                sentiment="negative",
                risk_level="high",
                confidence=0.8,
                key_points=[],
                recommendation="investigate",
                evidence_score=-5,
            ),
        ]

        briefing = build_portfolio_briefing(overview, analyses)

        self.assertIn("VOO is the largest position at 70.0%", briefing.summary)
        self.assertEqual(briefing.attention_tickers, ["META"])
        self.assertIn("META", briefing.key_points[-1])

    def test_builds_weighted_portfolio_direction_feedback(self) -> None:
        overview = {
            "total_value": 10_000.0,
            "positions": [
                {
                    "ticker": "VOO",
                    "shares": 10.0,
                    "price": 700.0,
                    "market_value": 7_000.0,
                    "allocation": 0.7,
                },
                {
                    "ticker": "META",
                    "shares": 5.0,
                    "price": 600.0,
                    "market_value": 3_000.0,
                    "allocation": 0.3,
                },
            ],
            "largest_position": {
                "ticker": "VOO",
                "shares": 10.0,
                "price": 700.0,
                "market_value": 7_000.0,
                "allocation": 0.7,
            },
        }
        contexts = {
            "VOO": {
                "ticker": "VOO",
                "latest_price": 700.0,
                "one_month_change": 0.04,
                "one_month_high": 705.0,
                "one_month_low": 660.0,
            },
            "META": {
                "ticker": "META",
                "latest_price": 600.0,
                "one_month_change": -0.02,
                "one_month_high": 620.0,
                "one_month_low": 580.0,
            },
        }

        feedback = build_portfolio_direction_feedback(overview, contexts, [])

        self.assertEqual(feedback.direction, "upward")
        self.assertAlmostEqual(feedback.weighted_one_month_change, 0.022)
        self.assertEqual(feedback.advancing_positions, 1)
        self.assertEqual(feedback.declining_positions, 1)


if __name__ == "__main__":
    unittest.main()
