import unittest

from modules.ai import AIError, _parse_analysis


class ParseAnalysisTests(unittest.TestCase):
    def test_retains_source_articles_with_the_analysis(self) -> None:
        raw_response = """
        {
          "ticker": "VOO",
          "summary": "Evidence is limited.",
          "sentiment": "neutral",
          "risk_level": "medium",
          "confidence": 0.6,
          "key_points": ["[1] A supplied headline."],
          "evidence": [{
            "article_index": 1,
            "impact": "neutral",
            "materiality": "medium",
            "claim": "A supplied headline."
          }]
        }
        """
        articles = [
            {
                "title": "A supplied headline",
                "publisher": "Example News",
                "url": "https://example.com/article",
                "published": "2026-07-24",
            }
        ]

        analysis = _parse_analysis(raw_response, articles)

        self.assertEqual(analysis.sources[0].title, "A supplied headline")
        self.assertEqual(analysis.sources[0].url, "https://example.com/article")

    def test_rejects_evidence_that_does_not_reference_a_source(self) -> None:
        raw_response = """
        {
          "ticker": "VOO",
          "summary": "Evidence is limited.",
          "sentiment": "neutral",
          "risk_level": "medium",
          "confidence": 0.6,
          "key_points": [],
          "evidence": [{
            "article_index": 2,
            "impact": "neutral",
            "materiality": "medium",
            "claim": "Unsupported index."
          }]
        }
        """

        with self.assertRaisesRegex(AIError, "invalid article_index"):
            _parse_analysis(raw_response, [{"title": "One source"}])


if __name__ == "__main__":
    unittest.main()
