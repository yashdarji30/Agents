# Webhook Failure Fallbacks & Retries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement exponential backoff, Discord HTTP 429 `Retry-After` header parsing, and graceful degraded execution (`status: "publish_failed"`) for Discord webhook integration to prevent crashes on network errors or rate limits.

**Architecture:** Update `publish_to_discord` in `Discord/webhook.py` to wrap webhook HTTP POST requests in a retry loop with exponential backoff and rate-limit header parsing. Update `discord_publisher_node` in `agent/hackathon_graph.py` to return `{"status": "publish_failed"}` instead of raising `RuntimeError` when publishing fails after retries.

**Tech Stack:** Python 3.10+, `requests`, `unittest`, `unittest.mock`, `langgraph`

## Global Constraints

- Retries: Default `max_retries=3`, `initial_delay=1.0`, `backoff_factor=2.0`.
- Rate Limit: Parse `Retry-After` header or `retry_after` JSON field (in seconds or ms) and sleep required time + 0.1s safety margin.
- Node behavior: When publish fails or URL is missing, return `{"status": "publish_failed"}` cleanly without raising `RuntimeError`.

---

### Task 1: Resilient `publish_to_discord` with Retries & Rate-Limit Handling

**Files:**
- Modify: `Discord/webhook.py`
- Test: `tests/test_webhook_retry.py`

**Interfaces:**
- Consumes: `HackathonPost` dataclass from `agent.hackathon_state`, `requests`
- Produces: `publish_to_discord(post: HackathonPost, webhook_url: Optional[str] = None, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0) -> bool`

- [ ] **Step 1: Write the failing unit tests for `publish_to_discord` retries and rate limit handling**

Create `tests/test_webhook_retry.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run command: `python -m unittest tests/test_webhook_retry.py`
Expected output: FAIL or ERROR due to missing signature parameters/retry logic.

- [ ] **Step 3: Implement exponential backoff & rate limit handling in `Discord/webhook.py`**

Modify `Discord/webhook.py`:
```python
import os
import time
import requests
import base64
from typing import Optional, Dict, Any
from agent.hackathon_state import HackathonPost

ARCHETYPE_COLORS = {
    "Technical Defense Guide": 0x2980B9,  # Cobalt Blue
    "Case Study Walkthrough": 0x27AE60,   # Emerald Green
    "Reviewer Cheat Sheet": 0x8E44AD      # Vivid Purple
}

def generate_mermaid_image_url(mermaid_code: Optional[str]) -> Optional[str]:
    if not mermaid_code or not mermaid_code.strip():
        return None
    try:
        clean_code = mermaid_code.strip()
        encoded = base64.b64encode(clean_code.encode('utf-8')).decode('utf-8')
        return f"https://mermaid.ink/img/{encoded}"
    except Exception as e:
        print(f"[Mermaid Encoder Warning]: Failed to encode diagram: {e}")
        return None

def build_discord_embed_payload(post: HackathonPost) -> Dict[str, Any]:
    color = ARCHETYPE_COLORS.get(post.post_type, 0x5865F2)
    
    description_parts = []
    description_parts.append(f"**Category:** `{post.category}`")
    description_parts.append(f"**Post Type:** `{post.post_type}`\n")
    description_parts.append(f"> **💡 Judge's Lens:**\n> {post.judge_perspective}\n")
    description_parts.append(f"### ⚡ Technical Deep Dive\n{post.deep_dive_content}")
    
    full_description = "\n".join(description_parts)
    if len(full_description) > 3900:
        full_description = full_description[:3900] + "\n\n*(Content truncated for Discord limit)*"
        
    qa_text_items = []
    for i, qa in enumerate(post.reviewer_qa_pairs, 1):
        qa_block = (
            f"**Q{i}: {qa.question}**\n"
            f"||**Winning Answer:** {qa.winning_answer}||"
        )
        qa_text_items.append(qa_block)
    qa_value = "\n\n".join(qa_text_items) if qa_text_items else "No Q&A generated."
    if len(qa_value) > 1024:
        qa_value = qa_value[:1000] + "...||"

    checklist_items = [f"- [ ] {item}" for item in post.actionable_checklist]
    checklist_value = "\n".join(checklist_items) if checklist_items else "No tasks specified."
    if len(checklist_value) > 1024:
        checklist_value = checklist_value[:1000] + "..."

    embed = {
        "title": f"🚀 [{post.post_type}] {post.title}",
        "description": full_description,
        "color": color,
        "fields": [
            {
                "name": "🎯 Reviewer Interrogation & Winning Answers",
                "value": qa_value,
                "inline": False
            },
            {
                "name": "📋 Actionable Execution Checklist",
                "value": checklist_value,
                "inline": False
            }
        ],
        "footer": {
            "text": "PERN Hackathon Mentor AI Agent • Powered by Gemini 3.6 Flash"
        }
    }

    if getattr(post, "architecture_diagram", None):
        image_url = generate_mermaid_image_url(post.architecture_diagram)
        if image_url:
            embed["image"] = {"url": image_url}
    
    return {
        "content": "@everyone 🚀 **New Hackathon Insights & Guide Posted!**",
        "embeds": [embed]
    }

def publish_to_discord(
    post: HackathonPost,
    webhook_url: Optional[str] = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> bool:
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        print("[Discord Webhook Error]: DISCORD_WEBHOOK_URL environment variable is missing.")
        return False
        
    payload = build_discord_embed_payload(post)
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                print(f"[Discord Webhook Success]: Post '{post.title}' published successfully.")
                return True
            
            if response.status_code == 429:
                retry_after_str = response.headers.get("Retry-After")
                retry_after = None
                if retry_after_str:
                    try:
                        retry_after = float(retry_after_str)
                    except ValueError:
                        pass
                
                if retry_after is None:
                    try:
                        resp_json = response.json()
                        retry_after = float(resp_json.get("retry_after", 1.0))
                    except Exception:
                        retry_after = 1.0
                
                if retry_after > 100:
                    retry_after = retry_after / 1000.0
                
                sleep_duration = retry_after + 0.1
                print(f"[Discord Webhook Rate-Limited]: HTTP 429 received. Retrying after {sleep_duration:.2f}s (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(sleep_duration)
                continue
                
            if response.status_code >= 500:
                delay = initial_delay * (backoff_factor ** attempt)
                print(f"[Discord Webhook Warning]: Server error HTTP {response.status_code}. Retrying in {delay:.2f}s (Attempt {attempt + 1}/{max_retries})...")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                continue
            
            print(f"[Discord Webhook Error]: HTTP {response.status_code} - {response.text}")
            return False

        except requests.exceptions.RequestException as e:
            delay = initial_delay * (backoff_factor ** attempt)
            print(f"[Discord Webhook Exception]: Network/request error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                
    print(f"[Discord Webhook Error]: Failed to publish to Discord after {max_retries} attempts.")
    return False
```

- [ ] **Step 4: Run test to verify it passes**

Run command: `python -m unittest tests/test_webhook_retry.py`
Expected output: OK (4 tests passed).

- [ ] **Step 5: Commit changes**

Run command: `git add Discord/webhook.py tests/test_webhook_retry.py && git commit -m "feat: add exponential backoff and 429 rate limit retries for discord webhook"`

---

### Task 2: Update `discord_publisher_node` for Graceful Degraded Execution

**Files:**
- Modify: `agent/hackathon_graph.py`
- Test: `tests/test_webhook_retry.py`

**Interfaces:**
- Consumes: `publish_to_discord` from `Discord.webhook`
- Produces: `discord_publisher_node(state: HackathonAgentState) -> Dict[str, Any]` returning `{"status": "published"}` or `{"status": "publish_failed"}`

- [ ] **Step 1: Add unit test for `discord_publisher_node` fallback behavior**

Append to `tests/test_webhook_retry.py`:
```python
from agent.hackathon_graph import discord_publisher_node

class TestDiscordPublisherNode(unittest.TestCase):
    @patch("agent.hackathon_graph.publish_to_discord")
    def test_discord_publisher_node_success(self, mock_publish):
        mock_publish.return_value = True
        post = MagicMock()
        post.category = "Test Cat"
        post.post_type = "Technical Defense Guide"
        post.title = "Test Post"

        state = {"current_post": post, "db_path": ":memory:"}
        res = discord_publisher_node(state)
        self.assertEqual(res["status"], "published")

    @patch("agent.hackathon_graph.publish_to_discord")
    def test_discord_publisher_node_fallback(self, mock_publish):
        mock_publish.return_value = False
        post = MagicMock()

        state = {"current_post": post}
        res = discord_publisher_node(state)
        self.assertEqual(res["status"], "publish_failed")
```

- [ ] **Step 2: Run test to verify it fails**

Run command: `python -m unittest tests/test_webhook_retry.py`
Expected output: FAIL because `discord_publisher_node` raises `RuntimeError` on failure.

- [ ] **Step 3: Update `discord_publisher_node` in `agent/hackathon_graph.py`**

Modify `discord_publisher_node` in `agent/hackathon_graph.py`:
```python
def discord_publisher_node(state: HackathonAgentState) -> Dict[str, Any]:
    post = state.get("current_post")
    if not post:
        error_msg = state.get("error", "No current post generated")
        print(f"[Discord Publisher Skipped]: Skipping publish because no post is available. Cause: {error_msg}")
        raise RuntimeError(f"Hackathon Agent cycle failed during content generation: {error_msg}")
    
    success = publish_to_discord(post)
    if success:
        db_path = state.get("db_path") or DEFAULT_DB_PATH
        try:
            save_post_history(
                category=post.category,
                archetype=post.post_type,
                title=post.title,
                db_path=db_path
            )
            print(f"[SQLite Persistence]: Saved published post '{post.title}' ({post.category} - {post.post_type}) to SQLite database.")
        except Exception as db_err:
            print(f"[SQLite Persistence Warning]: Failed to save post history: {db_err}")
            
        return {"status": "published"}
    else:
        print(f"[Discord Publisher Fallback]: Webhook publishing failed or rate-limited after retries. Graph completing with publish_failed status.")
        return {"status": "publish_failed"}
```

- [ ] **Step 4: Run all tests to verify they pass**

Run command: `python -m unittest discover tests`
Expected output: OK (All tests pass).

- [ ] **Step 5: Commit changes**

Run command: `git add agent/hackathon_graph.py tests/test_webhook_retry.py && git commit -m "feat: handle discord webhook publish failure gracefully in graph node"`
