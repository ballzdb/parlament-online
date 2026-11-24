import json
import os
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from moderation.ai import review_idea


class AIReviewTests(SimpleTestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_screening_is_disabled_by_default(self):
        self.assertEqual(review_idea("Title", "Body")["status"], "disabled")

    @patch.dict(os.environ, {"GEMINI_AI_SCREENING_ENABLED": "true"}, clear=True)
    def test_missing_api_key_does_not_call_provider(self):
        with patch("urllib.request.urlopen") as urlopen:
            self.assertEqual(review_idea("Title", "Body")["status"], "not_configured")
            urlopen.assert_not_called()

    @patch.dict(os.environ, {
        "GEMINI_AI_SCREENING_ENABLED": "true",
        "GEMINI_API_KEY": "test-key",
    }, clear=True)
    @patch("urllib.request.urlopen")
    def test_valid_provider_response_is_normalised(self, urlopen):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "candidates": [{
                "content": {"parts": [{"text": json.dumps({
                    "flagged": True,
                    "categories": ["bullying"],
                    "explanation": "Possible targeted abuse.",
                    "confidence": 0.91,
                })}]}
            }]
        }).encode()
        urlopen.return_value = response

        result = review_idea("Title", "Body")

        self.assertEqual(result["status"], "complete")
        self.assertIs(result["flagged"], True)
        self.assertEqual(result["categories"], ["bullying"])
        self.assertEqual(result["confidence"], 0.91)
        urlopen.assert_called_once()

    @patch.dict(os.environ, {
        "GEMINI_AI_SCREENING_ENABLED": "true",
        "GEMINI_API_KEY": "test-key",
    }, clear=True)
    @patch("urllib.request.urlopen")
    def test_invalid_provider_schema_fails_closed(self, urlopen):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "candidates": [{
                "content": {"parts": [{"text": json.dumps({
                    "flagged": "false",
                    "categories": "none",
                    "confidence": 0.5,
                })}]}
            }]
        }).encode()
        urlopen.return_value = response

        self.assertEqual(review_idea("Title", "Body")["status"], "unavailable")

    @patch.dict(os.environ, {
        "GEMINI_AI_SCREENING_ENABLED": "true",
        "GEMINI_API_KEY": "test-key",
    }, clear=True)
    @patch("urllib.request.urlopen", side_effect=TimeoutError)
    def test_provider_timeout_does_not_raise(self, _urlopen):
        self.assertEqual(review_idea("Title", "Body")["status"], "unavailable")
