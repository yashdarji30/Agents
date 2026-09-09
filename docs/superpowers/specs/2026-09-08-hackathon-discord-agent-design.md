# Hackathon Assistant AI Agent & Discord Auto-Poster Design

## Overview
An automated AI Agent powered by **LangGraph** and **Google Gemini API** (`gemini-3.6-flash` with automatic fallback models) that generates fresh, high-value hackathon preparation strategies, actionable checklists, and interactive multiple-choice questions (MCQs with spoiler-tagged answers). The agent automatically posts rich formatted embed cards to a designated Discord channel every 5 hours via Discord Webhook.

---

## Requirements & Scope
1. **Core Goal**: Provide hackathon participants with expert strategies on ideation, team coordination, tech stack selection, rapid MVP scoping, pitch deck prep, and interactive quiz MCQs.
2. **Frequency**: Scheduled job execution every 5 hours (18,000 seconds).
3. **Interactive Format**:
   - **Hackathon Strategy Tip**: Detailed actionable insight for hackathon success.
   - **Actionable Checklist**: 3-4 concrete step-by-step tasks.
   - **Interactive MCQs**: 1-2 multiple-choice questions with choices (A/B/C/D) and spoiler-hidden correct answers + explanations (`||Correct Answer: B - ...||`).
4. **Discord Integration**: Webhook URL integration with styled embeds (color banners, field layout, markdown).
5. **State & Topic History**: Track posted topics to ensure non-repetitive fresh advice across consecutive cycles.
6. **Configurable Interval**: Flexible post interval via `POST_INTERVAL_HOURS` environment variable (default: `5` hours, can be set to any hours/days) or `--interval-hours` CLI parameter.
7. **Deployment Modes**:
   - **Continuous background runner**: `Discord/scheduler.py` or `python main.py --hackathon-schedule`.
   - **On-demand / Cron execution**: `python main.py --hackathon-now` (ideal for serverless triggers and GitHub Actions).
   - **GitHub Actions**: `.github/workflows/hackathon_agent.yml` (cron scheduler or manual dispatch).
   - **Docker Container**: `Dockerfile` and `docker-compose.yml` for continuous containerized deployment.

---

## System Architecture

```
+-------------------------------------------------------------------------------+
|                             LangGraph Workflow                                |
|                                                                               |
|  [ START ] ---> ( topic_curator_node ) ---> ( content_generator_node )       |
|                         |                              |                      |
|                  Reads Past Topics             Gemini Pydantic Output         |
|                                                        |                      |
|                                           ( discord_publisher_node )          |
|                                                        |                      |
|                                             POST to Discord Webhook           |
|                                                        |                      |
|                                                     [ END ]                   |
+-------------------------------------------------------------------------------+
                                         ^
                                         |
     +-----------------------------------+-----------------------------------+
     |                                   |                                   |
[Continuous Local/Container]  [GitHub Actions Cron Job]           [On-Demand CLI]
(scheduler.py / Docker)       (workflow_dispatch / cron)          (python main.py --hackathon-now)
```

---

## Component Details

### 1. Data Models (`agent/hackathon_state.py`)
- **`MCQOption`**: `label` (A, B, C, D), `text` (Option description).
- **`MCQuestion`**: `question` (str), `options` (List[MCQOption]), `correct_option` (str), `explanation` (str).
- **`HackathonPost`**: `title` (str), `category` (str), `strategy_tip` (str), `actionable_checklist` (List[str]), `mcqs` (List[MCQuestion]).
- **`HackathonAgentState`**: `messages`, `history_topics` (List[str]), `current_post` (Optional[HackathonPost]), `status` (str), `error` (Optional[str]).

### 2. LangGraph Nodes (`agent/hackathon_graph.py`)
- **`topic_curator_node`**: Inspects `history_topics` state and picks an un-covered topic from categories (*Ideation & Scoping*, *MVP Architecture*, *Team Synergy & Git*, *Presentation & Pitching*, *Managing Sprint Time*, *API & Third-Party Integration*).
- **`content_generator_node`**: Invokes `ChatGoogleGenerativeAI` with structured output (`with_structured_output(HackathonPost)`). Uses model fallbacks (`gemini-3.6-flash` -> `gemini-3.5-flash` -> `gemini-3.7-flash` -> `gemini-2.5-flash`).
- **`discord_publisher_node`**: Takes `HackathonPost` and delegates to `Discord/webhook.py` to publish to `DISCORD_WEBHOOK_URL`.

### 3. Discord Publisher (`Discord/webhook.py`)
- Constructs JSON payload with Discord Embed fields:
  - Title & Category banner (Color code: `0x5865F2` / Blurple).
  - Strategy Tip block quote.
  - Actionable Checklist formatted as bullet points.
  - Interactive MCQs formatted with options A, B, C, D and spoiler tags `||**Answer:** B - Explanation...||`.
- Performs HTTP POST request using `requests` with retry logic.

### 4. Scheduler & CLI Interface (`Discord/scheduler.py` & `main.py`)
- **`Discord/scheduler.py`**: Background runner reading `POST_INTERVAL_HOURS` (default: 5.0) that triggers `build_hackathon_graph()`.
- **`main.py` update**: CLI flag `--hackathon-now` for single-cycle deployment execution, and `--hackathon-schedule` + `--interval-hours <N>` for custom scheduling.

### 5. Deployment Setup (`Dockerfile`, `docker-compose.yml`, `.github/workflows/hackathon_agent.yml`)
- **`Dockerfile`**: Container definition based on `python:3.10-slim`.
- **`docker-compose.yml`**: Compose service loading `.env`.
- **`.github/workflows/hackathon_agent.yml`**: GitHub Actions workflow running on schedule (e.g. `0 */5 * * *`) and `workflow_dispatch`.

### 6. Verification & Tests (`tests/test_hackathon_agent.py`)
- Unit test for Pydantic schema validation.
- Unit test for Discord embed JSON payload builder.
- Integration test for LangGraph execution and topic memory updates.
- Test for configurable interval parsing.

---

## Verification Plan
1. Run `pytest tests/test_hackathon_agent.py` to verify schema generation, payload building, and interval parsing.
2. Run `python main.py --hackathon-now` to test live generation and posting to Discord.
3. Validate Docker container build `docker build -t hackathon-agent .` (if Docker is available).
4. Validate Discord channel received formatted embed with spoiler-tagged answers.

