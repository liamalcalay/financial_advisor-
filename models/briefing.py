"""Models used for a stable, portfolio-level daily research briefing."""

from dataclasses import dataclass


@dataclass
class PortfolioBriefing:
    """A deterministic summary of saved stock-level research."""

    summary: str
    attention_tickers: list[str]
    key_points: list[str]


@dataclass
class PortfolioDirectionFeedback:
    """Current market-context feedback for the whole local portfolio."""

    direction: str
    weighted_one_month_change: float
    advancing_positions: int
    declining_positions: int
    research_coverage: int
    total_positions: int
    attention_tickers: list[str]
    summary: str
    key_points: list[str]
