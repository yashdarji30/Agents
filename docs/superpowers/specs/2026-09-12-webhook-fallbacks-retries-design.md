# Webhook Failure Fallbacks & Retries Design Spec

**Date:** 2026-09-12  
**Status:** Approved  
**Topic:** Webhook Failure Fallbacks & Retries  

---

## 1. Executive Summary & Goal

Currently, if Discord returns a rate-limit (HTTP 429), a temporary server error (HTTP 5xx), or if the `DISCORD_WEBHOOK_URL` environment variable is missing, `publish_to_discord` in `Discord/webhook.py` immediately returns `False`. The `discord_publisher_node` in `agent/hackathon_graph.py` then raises an unhandled `RuntimeError`, causing the entire LangGraph execution pipeline to crash.

The goal of this design is to make Discord publishing resilient by:
1. Implementing smart retries with exponential backoff and Discord 429 `Retry-After` rate-limit header parsing in `publish_to_discord`.
2. Converting hard crashes in `discord_publisher_node` into a graceful degraded state (`status: "publish_failed"`).
3. Adding comprehensive unit test coverage for rate limits, retries, and fallback behaviors.

---

## 2. Architecture & Components

### 2.1 Resilient Discord Publisher (`Discord/webhook.py`)

Modify `publish_to_discord(post: HackathonPost, webhook_url: Optional[str] = None, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0) -> bool`:

- **Missing URL Check**:
  - If `url` is missing or empty, print error warning log `[Discord Webhook Error]: DISCORD_WEBHOOK_URL environment variable is missing.` and return `False`.
- **Retry Loop (Up to `max_retries` attempts)**:
  - Perform `requests.post(url, json=payload, timeout=10)`.
  - **Success (200, 204)**: Log success and return `True`.
  - **Rate Limited (HTTP 429)**:
    - Attempt to extract delay from `response.headers.get("Retry-After")`. If missing, check `response.json().get("retry_after")`.
    - If `retry_after` is in milliseconds (e.g. > 100), convert to seconds (`retry_after / 1000.0`).
    - Sleep for `sleep_time = delay + 0.1` seconds safety margin.
    - Log warning `[Discord Webhook Rate-Limited]: HTTP 429 received. Retrying after {sleep_time:.2f}s...`
  - **Server Errors (5xx) & Request Exceptions (Timeout / Connection Error)**:
    - Compute backoff delay: `delay = initial_delay * (backoff_factor ** attempt)`.
    - Sleep for `delay` seconds.
    - Log warning `[Discord Webhook Warning]: Attempt {attempt + 1}/{max_retries} failed with {error}. Retrying in {delay:.2f}s...`
  - **Client Errors (4xx except 429)**:
    - Log non-retryable error `[Discord Webhook Error]: HTTP {status_code} - {text}` and break loop immediately to return `False`.
- **Failure Return**:
  - If all retries are exhausted, log final error `[Discord Webhook Error]: Failed to publish to Discord after {max_retries} attempts.` and return `False`.

### 2.2 Graceful Graph Node (`agent/hackathon_graph.py`)

Modify `discord_publisher_node(state: HackathonAgentState) -> Dict[str, Any]`:

- If `current_post` is not generated:
  - Raise `RuntimeError` (content generation failure is still considered a hard failure for the post cycle).
- Call `success = publish_to_discord(post)`.
- If `success == True`:
  - Save post history to SQLite database (`save_post_history`).
  - Return `{"status": "published"}`.
- If `success == False`:
  - Log warning `[Discord Publisher Fallback]: Webhook publishing failed or rate-limited after retries. Graph completing with publish_failed status.`
  - Return `{"status": "publish_failed"}`.

---

## 3. Verification & Testing Plan

### 3.1 Unit Tests (`tests/test_webhook_retry.py`)

Create unit tests using `unittest` and `unittest.mock`:

1. **`test_publish_success`**: Mock HTTP 204 response -> verify returns `True` on attempt 1.
2. **`test_publish_rate_limit_retry`**: Mock HTTP 429 with `Retry-After: 0.1` followed by HTTP 204 -> verify sleeps and retries successfully.
3. **`test_publish_500_exponential_backoff`**: Mock HTTP 500 followed by HTTP 204 -> verify backoff delay and retry success.
4. **`test_publish_exhaust_retries`**: Mock HTTP 500 x 3 -> verify returns `False` without throwing exception.
5. **`test_publish_missing_url`**: Mock missing webhook URL -> verify returns `False` immediately.
6. **`test_discord_publisher_node_fallback`**: Mock `publish_to_discord` returning `False` -> verify `discord_publisher_node` returns `{"status": "publish_failed"}` without raising exception.

---

## 4. Risks & Considerations

- **Execution Latency during Rate Limits**: If Discord returns a long `Retry-After` (e.g. 5-10 seconds), the node execution will pause during `time.sleep()`. This is standard for webhook bots and preferable to dropping messages or crashing.
- **Safety Cushion**: Adding `+ 0.1` seconds cushion to `Retry-After` prevents race conditions with Discord's rate limit window resetting.
