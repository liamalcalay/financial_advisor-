"""Deterministic recommendation rules for extracted news evidence."""

from typing import Literal, TypedDict

from models.analysis import StockEvidence


RecommendationName = Literal["monitor", "hold", "investigate"]


class RecommendationAssessment(TypedDict):
    """A stable assessment calculated from article-level evidence."""

    recommendation: RecommendationName
    evidence_score: int


MATERIALITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3}
IMPACT_DIRECTIONS = {"negative": -1, "neutral": 0, "positive": 1}


def assess_evidence(
    evidence: list[StockEvidence], confidence: float
) -> RecommendationAssessment:
    """Convert corroborated article evidence into a stable research label.

    Only the strongest item for each article counts. This prevents a model from
    inflating a score by repeating the same article in multiple evidence items.
    """

    strongest_by_article: dict[int, int] = {}

    for item in evidence:
        value = MATERIALITY_WEIGHTS[item.materiality] * IMPACT_DIRECTIONS[item.impact]
        existing_value = strongest_by_article.get(item.article_index)

        if existing_value is None or abs(value) > abs(existing_value):
            strongest_by_article[item.article_index] = value

    evidence_score = sum(strongest_by_article.values())

    # Low-confidence or single-headline evidence stays in the neutral zone.
    if confidence < 0.60 or len(strongest_by_article) < 2:
        recommendation: RecommendationName = "monitor"
    elif evidence_score <= -4:
        recommendation = "investigate"
    elif evidence_score >= 4:
        recommendation = "hold"
    else:
        recommendation = "monitor"

    return {
        "recommendation": recommendation,
        "evidence_score": evidence_score,
    }
