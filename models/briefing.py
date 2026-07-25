"""Models used for a stable, portfolio-level daily research briefing."""

from dataclasses import dataclass


@dataclass
class PortfolioBriefing:
    """A deterministic summary of saved stock-level research."""

    summary: str
    attention_tickers: list[str]
    key_points: list[str]
