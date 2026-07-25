import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from models.analysis import ResearchSource, StockAnalysis, StockEvidence
from models.briefing import PortfolioBriefing
from modules.database import (
    get_daily_trading_report,
    get_portfolio_value_history,
    initialize_database,
    save_daily_trading_report,
)


class DailyReportStorageTests(unittest.TestCase):
    def test_retains_briefing_and_article_sources(self) -> None:
        analysis = StockAnalysis(
            ticker="VOO",
            summary="Cautious research summary.",
            sentiment="neutral",
            risk_level="medium",
            confidence=0.65,
            key_points=["[1] A supplied headline."],
            evidence=[
                StockEvidence(
                    article_index=1,
                    impact="neutral",
                    materiality="medium",
                    claim="A supplied headline.",
                )
            ],
            sources=[
                ResearchSource(
                    title="A supplied headline",
                    publisher="Example News",
                    url="https://example.com/article",
                    published="2026-07-24",
                )
            ],
        )
        briefing = PortfolioBriefing(
            summary="One holding was reviewed.",
            attention_tickers=[],
            key_points=["Concentration: VOO represents 100.0% of the portfolio."],
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "test.db"
            with patch("modules.database.DATABASE_PATH", database_path):
                initialize_database()
                saved = save_daily_trading_report(
                    trade_date="2026-07-24",
                    market_close="2026-07-24T16:00:00-04:00",
                    portfolio_value=100.0,
                    analyses=[analysis],
                    briefing=briefing,
                )
                report = get_daily_trading_report("2026-07-24")

        self.assertTrue(saved)
        self.assertIsNotNone(report)
        assert report is not None
        self.assertEqual(report["briefing"]["summary"], briefing.summary)
        self.assertEqual(
            report["analyses"][0]["sources"][0]["url"],
            "https://example.com/article",
        )

    def test_returns_portfolio_values_in_date_order(self) -> None:
        analysis = StockAnalysis(
            ticker="VOO",
            summary="Research summary.",
            sentiment="neutral",
            risk_level="low",
            confidence=0.6,
            key_points=[],
        )
        briefing = PortfolioBriefing("Summary.", [], [])

        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "test.db"
            with patch("modules.database.DATABASE_PATH", database_path):
                initialize_database()
                save_daily_trading_report(
                    "2026-07-25",
                    "2026-07-25T16:00:00-04:00",
                    110.0,
                    [analysis],
                    briefing,
                )
                save_daily_trading_report(
                    "2026-07-24",
                    "2026-07-24T16:00:00-04:00",
                    100.0,
                    [analysis],
                    briefing,
                )
                history = get_portfolio_value_history()

        self.assertEqual(
            history,
            [
                {"trade_date": "2026-07-24", "portfolio_value": 100.0},
                {"trade_date": "2026-07-25", "portfolio_value": 110.0},
            ],
        )


if __name__ == "__main__":
    unittest.main()
