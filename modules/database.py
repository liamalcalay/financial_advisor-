"""SQLite storage for saved stock analyses."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from models.analysis import StockAnalysis
from models.briefing import PortfolioBriefing


DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "finance_advisor.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Create, configure, and always close a SQLite database connection."""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the analysis history table if it does not exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                summary TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                confidence REAL NOT NULL,
                key_points TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_trading_reports (
                trade_date TEXT PRIMARY KEY,
                market_close TEXT NOT NULL,
                generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                portfolio_value REAL NOT NULL,
                analyses TEXT NOT NULL,
                briefing TEXT NOT NULL DEFAULT '{}'
            )
            """
        )

        report_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(daily_trading_reports)")
        }
        if "briefing" not in report_columns:
            connection.execute(
                "ALTER TABLE daily_trading_reports "
                "ADD COLUMN briefing TEXT NOT NULL DEFAULT '{}'"
            )

        connection.commit()


def save_analysis(analysis: StockAnalysis) -> None:
    """Save one structured stock analysis."""

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO analysis_history (
                ticker,
                summary,
                sentiment,
                risk_level,
                confidence,
                key_points
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                analysis.ticker,
                analysis.summary,
                analysis.sentiment,
                analysis.risk_level,
                analysis.confidence,
                json.dumps(analysis.key_points),
            ),
        )

        connection.commit()


def get_recent_analyses(limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recently saved stock analyses."""

    if limit <= 0:
        return []

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                ticker,
                summary,
                sentiment,
                risk_level,
                confidence,
                key_points,
                created_at
            FROM analysis_history
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    analyses: list[dict[str, Any]] = []

    for row in rows:
        try:
            key_points = json.loads(row["key_points"])
        except (json.JSONDecodeError, TypeError):
            key_points = []

        if not isinstance(key_points, list):
            key_points = []

        analyses.append(
            {
                "id": row["id"],
                "ticker": row["ticker"],
                "summary": row["summary"],
                "sentiment": row["sentiment"],
                "risk_level": row["risk_level"],
                "confidence": row["confidence"],
                "key_points": [str(point) for point in key_points],
                "created_at": row["created_at"],
            }
        )

    return analyses


def get_analysis_dates() -> list[str]:
    """Return dates that have at least one saved stock analysis."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT substr(created_at, 1, 10) AS analysis_date
            FROM analysis_history
            ORDER BY analysis_date DESC
            """
        ).fetchall()

    return [str(row["analysis_date"]) for row in rows]


def get_analyses_for_date(analysis_date: str) -> list[dict[str, Any]]:
    """Return every saved stock analysis for one calendar date."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                ticker,
                summary,
                sentiment,
                risk_level,
                confidence,
                key_points,
                created_at
            FROM analysis_history
            WHERE substr(created_at, 1, 10) = ?
            ORDER BY created_at DESC, id DESC
            """,
            (analysis_date,),
        ).fetchall()

    analyses: list[dict[str, Any]] = []

    for row in rows:
        try:
            key_points = json.loads(row["key_points"])
        except (json.JSONDecodeError, TypeError):
            key_points = []

        if not isinstance(key_points, list):
            key_points = []

        analyses.append(
            {
                "id": row["id"],
                "ticker": row["ticker"],
                "summary": row["summary"],
                "sentiment": row["sentiment"],
                "risk_level": row["risk_level"],
                "confidence": row["confidence"],
                "key_points": [str(point) for point in key_points],
                "created_at": row["created_at"],
            }
        )

    return analyses


def delete_analysis(analysis_id: int) -> None:
    """Delete one saved analysis by database ID."""

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM analysis_history
            WHERE id = ?
            """,
            (analysis_id,),
        )

        connection.commit()


def clear_analysis_history() -> None:
    """Delete all saved stock analyses."""

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM analysis_history
            """
        )

        connection.commit()


def save_daily_trading_report(
    trade_date: str,
    market_close: str,
    portfolio_value: float,
    analyses: list[StockAnalysis],
    briefing: PortfolioBriefing,
) -> bool:
    """Save one immutable end-of-session report for a trading date.

    Returns ``False`` when a report already exists for that date.
    """

    serialized_analyses = [
        {
            "ticker": analysis.ticker,
            "summary": analysis.summary,
            "sentiment": analysis.sentiment,
            "risk_level": analysis.risk_level,
            "confidence": analysis.confidence,
            "key_points": analysis.key_points,
            "recommendation": analysis.recommendation,
            "evidence_score": analysis.evidence_score,
            "evidence": [
                {
                    "article_index": item.article_index,
                    "impact": item.impact,
                    "materiality": item.materiality,
                    "claim": item.claim,
                }
                for item in analysis.evidence
            ],
            "sources": [
                {
                    "title": source.title,
                    "publisher": source.publisher,
                    "url": source.url,
                    "published": source.published,
                }
                for source in analysis.sources
            ],
        }
        for analysis in analyses
    ]
    serialized_briefing = {
        "summary": briefing.summary,
        "attention_tickers": briefing.attention_tickers,
        "key_points": briefing.key_points,
    }

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO daily_trading_reports (
                trade_date,
                market_close,
                portfolio_value,
                analyses,
                briefing
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(trade_date) DO NOTHING
            """,
            (
                trade_date,
                market_close,
                portfolio_value,
                json.dumps(serialized_analyses),
                json.dumps(serialized_briefing),
            ),
        )
        connection.commit()

    return cursor.rowcount == 1


def get_daily_report_dates() -> list[str]:
    """Return saved trading-report dates, newest first."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT trade_date
            FROM daily_trading_reports
            ORDER BY trade_date DESC
            """
        ).fetchall()

    return [str(row["trade_date"]) for row in rows]


def get_portfolio_value_history() -> list[dict[str, float | str]]:
    """Return saved daily portfolio values in chronological order."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT trade_date, portfolio_value
            FROM daily_trading_reports
            ORDER BY trade_date ASC
            """
        ).fetchall()

    return [
        {
            "trade_date": str(row["trade_date"]),
            "portfolio_value": float(row["portfolio_value"]),
        }
        for row in rows
    ]


def get_daily_trading_report(trade_date: str) -> dict[str, Any] | None:
    """Return one saved end-of-session report and its stock analyses."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT trade_date, market_close, generated_at, portfolio_value, analyses, briefing
            FROM daily_trading_reports
            WHERE trade_date = ?
            """,
            (trade_date,),
        ).fetchone()

    if row is None:
        return None

    try:
        analyses = json.loads(row["analyses"])
    except (json.JSONDecodeError, TypeError):
        analyses = []

    if not isinstance(analyses, list):
        analyses = []

    try:
        briefing = json.loads(row["briefing"])
    except (json.JSONDecodeError, TypeError):
        briefing = {}

    if not isinstance(briefing, dict):
        briefing = {}

    return {
        "trade_date": str(row["trade_date"]),
        "market_close": str(row["market_close"]),
        "generated_at": str(row["generated_at"]),
        "portfolio_value": float(row["portfolio_value"]),
        "analyses": analyses,
        "briefing": briefing,
    }
