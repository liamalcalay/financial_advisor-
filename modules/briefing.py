"""Build deterministic portfolio briefings from completed stock research."""

from collections.abc import Sequence

from models.analysis import StockAnalysis
from models.briefing import PortfolioBriefing
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
