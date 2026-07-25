"""Tests for deterministic evidence-based research labels."""

import unittest

from models.analysis import StockEvidence
from modules.recommendation import assess_evidence


class RecommendationTests(unittest.TestCase):
    def test_single_headline_stays_monitor(self) -> None:
        assessment = assess_evidence(
            [StockEvidence(1, "positive", "high", "Strong one-off event")],
            confidence=0.9,
        )

        self.assertEqual(assessment, {"recommendation": "monitor", "evidence_score": 3})

    def test_two_material_positive_articles_support_hold(self) -> None:
        assessment = assess_evidence(
            [
                StockEvidence(1, "positive", "high", "Evidence one"),
                StockEvidence(2, "positive", "medium", "Evidence two"),
            ],
            confidence=0.8,
        )

        self.assertEqual(assessment, {"recommendation": "hold", "evidence_score": 5})

    def test_two_material_negative_articles_require_investigation(self) -> None:
        assessment = assess_evidence(
            [
                StockEvidence(1, "negative", "high", "Evidence one"),
                StockEvidence(2, "negative", "medium", "Evidence two"),
            ],
            confidence=0.8,
        )

        self.assertEqual(
            assessment,
            {"recommendation": "investigate", "evidence_score": -5},
        )

    def test_duplicate_article_cannot_inflate_score(self) -> None:
        assessment = assess_evidence(
            [
                StockEvidence(1, "positive", "high", "Primary evidence"),
                StockEvidence(1, "positive", "high", "Repeated evidence"),
                StockEvidence(2, "positive", "low", "Second evidence"),
            ],
            confidence=0.8,
        )

        self.assertEqual(assessment, {"recommendation": "hold", "evidence_score": 4})
