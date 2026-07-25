"""Build deterministic portfolio briefings from completed stock research."""

from collections.abc import Sequence

from models.analysis import StockAnalysis
from models.briefing import PortfolioBriefing, PortfolioDirectionFeedback
from modules.market import MarketContext
from modules.report import PortfolioOverview


def build_portfolio_briefing(
    overview: PortfolioOverview,
    analyses: Sequence[StockAnalysis],
) -> PortfolioBriefing:
    """Summarize concentration and research signals without another AI call."""

    if not analyses:
        raise ValueError("At least one stock analysis is required.")

    largest_position = overview["largest_position"]
    attention_analyses = [
        analysis
        for analysis in analyses
        if analysis.recommendation == "investigate"
        or analysis.risk_level == "high"
        or analysis.evidence_score < 0
    ]
    attention_tickers = [analysis.ticker for analysis in attention_analyses]
    strongest_positive = max(analyses, key=lambda analysis: analysis.evidence_score)
    strongest_negative = min(analyses, key=lambda analysis: analysis.evidence_score)

    summary = (
        f"{len(analyses)} holdings were reviewed. "
        f"{largest_position['ticker']} is the largest position at "
        f"{largest_position['allocation']:.1%} of portfolio value."
    )
    if attention_tickers:
        summary += " Review attention flags for " + ", ".join(attention_tickers) + "."
    else:
        summary += " No holdings met the current deterministic attention threshold."

    key_points = [
        (
            f"Concentration: {largest_position['ticker']} represents "
            f"{largest_position['allocation']:.1%} of the portfolio."
        ),
    ]

    if strongest_positive.evidence_score > 0:
        key_points.append(
            f"Strongest supported positive signal: {strongest_positive.ticker} "
            f"(evidence score {strongest_positive.evidence_score:+d})."
        )

    if strongest_negative.evidence_score < 0:
        key_points.append(
            f"Most negative supported signal: {strongest_negative.ticker} "
            f"(evidence score {strongest_negative.evidence_score:+d})."
        )

    if attention_tickers:
        key_points.append(
            "Attention flags: " + ", ".join(attention_tickers) + "."
        )

    return PortfolioBriefing(
        summary=summary,
        attention_tickers=attention_tickers,
        key_points=key_points,
    )


def build_portfolio_direction_feedback(
    overview: PortfolioOverview,
    market_contexts: dict[str, MarketContext],
    analyses: Sequence[StockAnalysis],
) -> PortfolioDirectionFeedback:
    """Describe recent portfolio direction without making a trade recommendation."""

    positions = overview["positions"]
    missing_tickers = [
        position["ticker"]
        for position in positions
        if position["ticker"] not in market_contexts
    ]
    if missing_tickers:
        raise ValueError(
            "Market context is missing for " + ", ".join(missing_tickers) + "."
        )

    weighted_change = sum(
        position["allocation"]
        * market_contexts[position["ticker"]]["one_month_change"]
        for position in positions
    )
    advancing_positions = sum(
        market_contexts[position["ticker"]]["one_month_change"] > 0
        for position in positions
    )
    declining_positions = sum(
        market_contexts[position["ticker"]]["one_month_change"] < 0
        for position in positions
    )

    if weighted_change >= 0.01:
        direction = "upward"
    elif weighted_change <= -0.01:
        direction = "downward"
    else:
        direction = "mixed"

    attention_tickers = [
        analysis.ticker
        for analysis in analyses
        if analysis.recommendation == "investigate"
        or analysis.risk_level == "high"
        or analysis.evidence_score < 0
    ]
    largest_position = overview["largest_position"]
    research_coverage = len({analysis.ticker for analysis in analyses})
    total_positions = len(positions)

    summary = (
        f"The portfolio's weighted one-month price direction is {direction} "
        f"({weighted_change:+.2%}). This is market context, not a trading signal."
    )
    key_points = [
        f"Breadth: {advancing_positions} of {total_positions} positions advanced; "
        f"{declining_positions} declined over one month.",
        f"Concentration: {largest_position['ticker']} is "
        f"{largest_position['allocation']:.1%} of portfolio value.",
        f"Research coverage: {research_coverage} of {total_positions} holdings analyzed in this session.",
    ]
    if attention_tickers:
        key_points.append("Research attention flags: " + ", ".join(attention_tickers) + ".")

    return PortfolioDirectionFeedback(
        direction=direction,
        weighted_one_month_change=weighted_change,
        advancing_positions=advancing_positions,
        declining_positions=declining_positions,
        research_coverage=research_coverage,
        total_positions=total_positions,
        attention_tickers=attention_tickers,
        summary=summary,
        key_points=key_points,
    )
