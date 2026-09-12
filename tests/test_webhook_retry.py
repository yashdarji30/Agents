import time
import unittest
from unittest.mock import patch, MagicMock
from agent.hackathon_state import HackathonPost
from Discord.webhook import publish_to_discord

class TestWebhookRetry(unittest.TestCase):
    def setUp(self):
        self.sample_post = HackathonPost(
            title="Test Title",
            category="PostgreSQL Schema & Index Optimization",
            post_type="Technical Defense Guide",
            judge_perspective="Testing judge perspective",
            deep_dive_content="Testing deep dive content",
            reviewer_qa_pairs=[],
            actionable_checklist=["Task 1"],
            architecture_diagram=None
        )

    @patch("Discord.webhook.requests.post")
    def test_publish_success_first_try(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_post.return_value = mock_resp

        result = publish_to_discord(self.sample_post, webhook_url="http://example.com/webhook")
        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 1)

    @patch("Discord.webhook.time.sleep")
    @patch("Discord.webhook.requests.post")
    def test_publish_rate_limit_retry_success(self, mock_post, mock_sleep):
        rate_limit_resp = MagicMock()
        rate_limit_resp.status_code = 429
        rate_limit_resp.headers = {"Retry-After": "0.5"}
        rate_limit_resp.json.return_value = {}

        success_resp = MagicMock()
        success_resp.status_code = 200

        mock_post.side_effect = [rate_limit_resp, success_resp]

        result = publish_to_discord(self.sample_post, webhook_url="http://example.com/webhook")
        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_with(0.6)

    @patch("Discord.webhook.time.sleep")
    @patch("Discord.webhook.requests.post")
    def test_publish_500_exponential_backoff_exhausted(self, mock_post, mock_sleep):
        err_resp = MagicMock()
        err_resp.status_code = 500
        err_resp.text = "Internal Server Error"
        mock_post.return_value = err_resp

        result = publish_to_discord(self.sample_post, webhook_url="http://example.com/webhook", max_retries=3, initial_delay=1.0)
        self.assertFalse(result)
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    def test_publish_missing_url(self):
        with patch.dict("os.environ", {}, clear=True):
            result = publish_to_discord(self.sample_post, webhook_url=None)
            self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
