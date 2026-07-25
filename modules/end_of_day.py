"""Generate one consolidated portfolio report after a NYSE trading session."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas_market_calendars as mcal

from modules.ai import summarize_news
from modules.briefing import build_portfolio_briefing
from modules.database import (
    get_daily_trading_report,
    initialize_database,
    save_daily_trading_report,
)
from modules.market import get_market_context, get_stock_quote
from modules.news import get_stock_news
from modules.portfolio import load_portfolio
from modules.report import build_portfolio_overview


EASTERN_TIME = ZoneInfo("America/New_York")
LOGGER = logging.getLogger(__name__)


class EndOfDayError(RuntimeError):
    """Raised when a trading-day report cannot be generated."""


def get_completed_session(now: datetime) -> tuple[str, datetime] | None:
    """Return today's NYSE session date and close time after it has closed."""

    eastern_now = now.astimezone(EASTERN_TIME)
    calendar = mcal.get_calendar("NYSE")
    schedule = calendar.schedule(
        start_date=eastern_now.date(),
        end_date=eastern_now.date(),
    )

    if schedule.empty:
        return None

    market_close = schedule.iloc[0]["market_close"].to_pydatetime().astimezone(EASTERN_TIME)

    if eastern_now < market_close:
        return None

    return eastern_now.date().isoformat(), market_close


def generate_end_of_day_report(now: datetime | None = None) -> bool:
    """Generate one daily report after the completed NYSE session.

    Returns ``True`` only when a new report is saved. Scheduled retries safely
    exit on non-trading days, before close, or after a report already exists.
    """

    current_time = now or datetime.now(EASTERN_TIME)
    session = get_completed_session(current_time)

    if session is None:
        return False

    trade_date, market_close = session
    initialize_database()

    if get_daily_trading_report(trade_date) is not None:
        return False

    try:
        holdings = load_portfolio()
        quotes = {
            holding["ticker"]: get_stock_quote(holding["ticker"])
            for holding in holdings
        }
        overview = build_portfolio_overview(holdings, quotes)
        analyses = [
            summarize_news(
                holding["ticker"],
                get_stock_news(holding["ticker"], limit=8),
                get_market_context(holding["ticker"]),
            )
            for holding in holdings
        ]
        briefing = build_portfolio_briefing(overview, analyses)
    except Exception as error:
        raise EndOfDayError(f"Could not generate the {trade_date} report.") from error

    return save_daily_trading_report(
        trade_date=trade_date,
        market_close=market_close.isoformat(),
        portfolio_value=overview["total_value"],
        analyses=analyses,
        briefing=briefing,
    )


def main() -> None:
    """Run the scheduled task once and log whether it saved a report."""

    logging.basicConfig(
        filename="data/end_of_day.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    try:
        if generate_end_of_day_report():
            LOGGER.info("Saved end-of-day trading report.")
        else:
            LOGGER.info("No end-of-day report was due.")
    except EndOfDayError:
        LOGGER.exception("End-of-day report generation failed.")
        raise


if __name__ == "__main__":
    main()
