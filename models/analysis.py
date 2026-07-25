from dataclasses import dataclass, field


@dataclass
class StockEvidence:
    """One article-level piece of evidence extracted from supplied news."""

    article_index: int
    impact: str
    materiality: str
    claim: str


@dataclass
class ResearchSource:
    """One news article retained with an analysis for later verification."""

    title: str
    publisher: str
    url: str
    published: str


@dataclass
class StockAnalysis:
    ticker: str
    summary: str
    sentiment: str
    risk_level: str
    confidence: float
    key_points: list[str]
    recommendation: str = "monitor"
    evidence_score: int = 0
    evidence: list[StockEvidence] = field(default_factory=list)
    sources: list[ResearchSource] = field(default_factory=list)
