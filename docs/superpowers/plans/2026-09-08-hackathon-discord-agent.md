# Hackathon Discord Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a LangGraph-powered AI agent with automatic Gemini model fallbacks that periodically generates hackathon strategies, checklists, and spoiler-tagged MCQs, posting them as rich embeds to Discord across local, containerized, or GitHub Actions environments.

**Architecture:** A 3-node LangGraph StateGraph (`topic_curator_node` -> `content_generator_node` -> `discord_publisher_node`) combined with a Discord Webhook publisher, configurable interval background scheduler (`POST_INTERVAL_HOURS`), Docker containerization, and GitHub Actions cron runner.

**Tech Stack:** Python 3.10+, LangGraph, `langchain-google-genai` (Gemini 3.6 Flash / 3.5 / 3.7 / 2.5), Pydantic v2, `requests`, `pytest`, Docker, GitHub Actions.

## Global Constraints

- Python 3.10+ compatibility.
- LangGraph state management with deterministic node updates.
- Gemini API fallback order: `gemini-3.6-flash` -> `gemini-3.5-flash` -> `gemini-3.7-flash` -> `gemini-2.5-flash`.
- Correct answers and explanations in Discord MCQs must be spoiler-tagged (`||...||`).
- Topic curation tracks history in `HackathonAgentState` to prevent repetitive content across consecutive executions.
- Flexible post intervals configurable via `POST_INTERVAL_HOURS` env variable or `--interval-hours` CLI argument.

---

### Task 1: Data Models & Pydantic Schemas (`agent/hackathon_state.py`)

**Files:**
- Create: `agent/hackathon_state.py`
- Create/Modify: `tests/test_hackathon_agent.py`

**Interfaces:**
- Consumes: None
- Produces: `MCQOption`, `MCQuestion`, `HackathonPost`, `HackathonAgentState` in `agent/hackathon_state.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_hackathon_agent.py
import pytest

def test_hackathon_pydantic_models():
    from agent.hackathon_state import MCQOption, MCQuestion, HackathonPost, HackathonAgentState
    
    option_a = MCQOption(label="A", text="Focus on MVP")
    option_b = MCQOption(label="B", text="Build full backend")
    
    mcq = MCQuestion(
        question="What is top priority in a 24-hr hackathon?",
        options=[option_a, option_b],
        correct_option="A",
        explanation="MVP delivers a working core."
    )
    
    post = HackathonPost(
        title="Rapid Prototyping",
        category="MVP Architecture",
        strategy_tip="Scope aggressively to core feature.",
        actionable_checklist=["Draft wireframes", "Cut non-essentials", "Lock API specs"],
        mcqs=[mcq]
    )
    
    assert post.title == "Rapid Prototyping"
    assert len(post.mcqs) == 1
    assert post.mcqs[0].correct_option == "A"
    
    state: HackathonAgentState = {
        "messages": [],
        "history_topics": ["Ideation & Scoping"],
        "current_post": post,
        "status": "ready",
        "error": None
    }
    assert state["status"] == "ready"
    assert len(state["history_topics"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_agent.py::test_hackathon_pydantic_models -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agent.hackathon_state'`

- [ ] **Step 3: Write minimal implementation**

```python
# agent/hackathon_state.py
from typing import List, Optional, TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class MCQOption(BaseModel):
    label: str = Field(description="Option label (e.g., A, B, C, D)")
    text: str = Field(description="Option description")

class MCQuestion(BaseModel):
    question: str = Field(description="The multiple-choice question prompt")
    options: List[MCQOption] = Field(description="List of 4 options (A, B, C, D)")
    correct_option: str = Field(description="The correct option label (e.g., A, B, C, or D)")
    explanation: str = Field(description="Detailed explanation of why this option is correct")

class HackathonPost(BaseModel):
    title: str = Field(description="Catchy topic title for the hackathon post")
    category: str = Field(description="Category (e.g., Ideation & Scoping, MVP Architecture, Team Synergy & Git, Presentation & Pitching, Managing Sprint Time, API & Third-Party Integration)")
    strategy_tip: str = Field(description="Actionable strategic advice for hackathon success")
    actionable_checklist: List[str] = Field(description="3-4 step-by-step concrete tasks")
    mcqs: List[MCQuestion] = Field(description="1-2 interactive multiple-choice questions")

class HackathonAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    history_topics: List[str]
    current_post: Optional[HackathonPost]
    status: str
    error: Optional[str]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_agent.py::test_hackathon_pydantic_models -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/hackathon_state.py tests/test_hackathon_agent.py
git commit -m "feat: add hackathon agent state and pydantic models"
```

---

### Task 2: Discord Embed Payload Builder & Webhook Publisher (`Discord/webhook.py`)

**Files:**
- Create: `Discord/webhook.py`
- Modify: `tests/test_hackathon_agent.py`

**Interfaces:**
- Consumes: `HackathonPost`, `MCQuestion`, `MCQOption` from `agent/hackathon_state.py`
- Produces: `build_discord_embed_payload`, `publish_to_discord` in `Discord/webhook.py`

- [ ] **Step 1: Write failing test**

```python
# Add to tests/test_hackathon_agent.py
def test_discord_embed_payload_builder():
    from agent.hackathon_state import MCQOption, MCQuestion, HackathonPost
    from Discord.webhook import build_discord_embed_payload
    
    post = HackathonPost(
        title="Git Workflow Tips",
        category="Team Synergy & Git",
        strategy_tip="Use feature branches and lock main.",
        actionable_checklist=["Create dev branch", "PR reviews before merge"],
        mcqs=[
            MCQuestion(
                question="Why protect main branch?",
                options=[
                    MCQOption(label="A", text="Prevents breaking production"),
                    MCQOption(label="B", text="Makes git slower")
                ],
                correct_option="A",
                explanation="Main protects working code state."
            )
        ]
    )
    
    payload = build_discord_embed_payload(post)
    assert "embeds" in payload
    embed = payload["embeds"][0]
    assert embed["title"] == "🚀 Hackathon Prep: Git Workflow Tips"
    assert embed["color"] == 0x5865F2
    fields = {f["name"]: f["value"] for f in embed["fields"]}
    assert "💡 Strategy Tip" in fields
    assert "📋 Actionable Checklist" in fields
    assert "❓ Quiz Time!" in fields
    assert "||**Answer:** A - Main protects working code state.||" in fields["❓ Quiz Time!"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_agent.py::test_discord_embed_payload_builder -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'Discord.webhook'`

- [ ] **Step 3: Write minimal implementation**

```python
# Discord/webhook.py
import os
import requests
from typing import Optional, Dict, Any
from agent.hackathon_state import HackathonPost

def build_discord_embed_payload(post: HackathonPost) -> Dict[str, Any]:
    checklist_text = "\n".join([f"• {item}" for item in post.actionable_checklist])
    
    mcq_blocks = []
    for idx, q in enumerate(post.mcqs, 1):
        opts = "\n".join([f"**{opt.label}.** {opt.text}" for opt in q.options])
        spoiler_ans = f"||**Answer:** {q.correct_option} - {q.explanation}||"
        mcq_blocks.append(f"**Q{idx}: {q.question}**\n{opts}\n{spoiler_ans}")
    
    mcq_text = "\n\n".join(mcq_blocks)
    
    embed = {
        "title": f"🚀 Hackathon Prep: {post.title}",
        "description": f"**Category:** `{post.category}`",
        "color": 0x5865F2,  # Blurple color banner
        "fields": [
            {
                "name": "💡 Strategy Tip",
                "value": f"> {post.strategy_tip}",
                "inline": False
            },
            {
                "name": "📋 Actionable Checklist",
                "value": checklist_text,
                "inline": False
            },
            {
                "name": "❓ Quiz Time!",
                "value": mcq_text,
                "inline": False
            }
        ],
        "footer": {
            "text": "Hackathon Assistant AI Agent • Powered by LangGraph & Gemini"
        }
    }
    
    return {"embeds": [embed]}

def publish_to_discord(post: HackathonPost, webhook_url: Optional[str] = None) -> bool:
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        print("[Discord Publisher Error]: DISCORD_WEBHOOK_URL not configured.")
        return False
    
    payload = build_discord_embed_payload(post)
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"[Discord Publisher Success]: Published '{post.title}' to Discord.")
        return True
    except Exception as e:
        print(f"[Discord Publisher Error]: Failed to post to Discord: {e}")
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_agent.py::test_discord_embed_payload_builder -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Discord/webhook.py tests/test_hackathon_agent.py
git commit -m "feat: add discord embed builder and webhook publisher"
```

---

### Task 3: LangGraph Nodes & Graph Construction (`agent/hackathon_graph.py`)

**Files:**
- Create: `agent/hackathon_graph.py`
- Modify: `tests/test_hackathon_agent.py`

**Interfaces:**
- Consumes: `HackathonAgentState`, `HackathonPost` from `agent/hackathon_state.py`, `publish_to_discord` from `Discord/webhook.py`
- Produces: `topic_curator_node`, `content_generator_node`, `discord_publisher_node`, `build_hackathon_graph` in `agent/hackathon_graph.py`

- [ ] **Step 1: Write failing test**

```python
# Add to tests/test_hackathon_agent.py
def test_hackathon_graph_flow():
    from agent.hackathon_state import HackathonAgentState
    from agent.hackathon_graph import topic_curator_node
    
    state: HackathonAgentState = {
        "messages": [],
        "history_topics": ["Ideation & Scoping"],
        "current_post": None,
        "status": "init",
        "error": None
    }
    
    new_state = topic_curator_node(state)
    assert new_state["status"] == "topic_curated"
    assert len(new_state["history_topics"]) == 2
    assert new_state["history_topics"][-1] != "Ideation & Scoping"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_agent.py::test_hackathon_graph_flow -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agent.hackathon_graph'`

- [ ] **Step 3: Write minimal implementation**

```python
# agent/hackathon_graph.py
import os
import random
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from agent.hackathon_state import HackathonAgentState, HackathonPost
from Discord.webhook import publish_to_discord

HACKATHON_CATEGORIES = [
    "Ideation & Scoping",
    "MVP Architecture",
    "Team Synergy & Git",
    "Presentation & Pitching",
    "Managing Sprint Time",
    "API & Third-Party Integration"
]

def topic_curator_node(state: HackathonAgentState) -> Dict[str, Any]:
    history = state.get("history_topics", [])
    available = [c for c in HACKATHON_CATEGORIES if c not in history]
    if not available:
        available = HACKATHON_CATEGORIES
        history = []
    
    selected_category = random.choice(available)
    updated_history = list(history) + [selected_category]
    
    return {
        "history_topics": updated_history,
        "status": "topic_curated"
    }

def content_generator_node(state: HackathonAgentState) -> Dict[str, Any]:
    api_key = os.getenv("GOOGLE_API_KEY")
    current_category = state["history_topics"][-1]
    
    candidate_models = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.7-flash",
        "gemini-2.5-flash"
    ]
    
    llm_instances = [
        ChatGoogleGenerativeAI(
            model=m,
            google_api_key=api_key,
            max_retries=1
        ).with_structured_output(HackathonPost)
        for m in candidate_models
    ]
    
    primary_llm = llm_instances[0]
    fallbacks = llm_instances[1:]
    structured_llm = primary_llm.with_fallbacks(fallbacks, exceptions_to_handle=(Exception,))
    
    prompt = f"""You are a top hackathon mentor. Generate a high-value, practical hackathon preparation post for participants.
Category focus: {current_category}

Include:
1. A clear, catchy title.
2. The category ({current_category}).
3. A detailed, actionable strategy tip.
4. An actionable checklist of 3-4 steps.
5. 1-2 interactive multiple-choice questions with 4 options (A, B, C, D), correct answer, and explanation.
"""
    
    try:
        post: HackathonPost = structured_llm.invoke([
            SystemMessage(content="You generate structured hackathon advice."),
            HumanMessage(content=prompt)
        ])
        return {
            "current_post": post,
            "status": "content_generated"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def discord_publisher_node(state: HackathonAgentState) -> Dict[str, Any]:
    post = state.get("current_post")
    if not post:
        return {"status": "publish_skipped", "error": "No current post available"}
    
    success = publish_to_discord(post)
    if success:
        return {"status": "published"}
    else:
        return {"status": "publish_failed", "error": "Discord publish call returned False"}

def build_hackathon_graph():
    workflow = StateGraph(HackathonAgentState)
    
    workflow.add_node("topic_curator", topic_curator_node)
    workflow.add_node("content_generator", content_generator_node)
    workflow.add_node("discord_publisher", discord_publisher_node)
    
    workflow.add_edge(START, "topic_curator")
    workflow.add_edge("topic_curator", "content_generator")
    workflow.add_edge("content_generator", "discord_publisher")
    workflow.add_edge("discord_publisher", END)
    
    return workflow.compile()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_agent.py::test_hackathon_graph_flow -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/hackathon_graph.py tests/test_hackathon_agent.py
git commit -m "feat: add langgraph hackathon nodes and graph builder"
```

---

### Task 4: Configurable Scheduler & Flexible CLI Interface (`Discord/scheduler.py` & `main.py`)

**Files:**
- Create: `Discord/scheduler.py`
- Modify: `main.py`
- Modify: `tests/test_hackathon_agent.py`

**Interfaces:**
- Consumes: `build_hackathon_graph` from `agent/hackathon_graph.py`
- Produces: `run_hackathon_cycle`, `get_post_interval_seconds`, `start_scheduler` in `Discord/scheduler.py` and CLI options (`--hackathon-now`, `--hackathon-schedule`, `--interval-hours`) in `main.py`

- [ ] **Step 1: Write failing test**

```python
# Add to tests/test_hackathon_agent.py
from unittest.mock import patch, MagicMock

def test_hackathon_interval_config():
    import os
    from Discord.scheduler import get_post_interval_seconds
    
    with patch.dict(os.environ, {"POST_INTERVAL_HOURS": "2.5"}):
        assert get_post_interval_seconds() == 9000.0
    
    with patch.dict(os.environ, {}, clear=True):
        assert get_post_interval_seconds() == 18000.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_agent.py::test_hackathon_interval_config -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'Discord.scheduler'`

- [ ] **Step 3: Write minimal implementation**

Create `Discord/scheduler.py`:
```python
import time
import os
import argparse
from typing import List, Optional
from dotenv import load_dotenv
from agent.hackathon_graph import build_hackathon_graph

def get_post_interval_seconds(custom_hours: Optional[float] = None) -> float:
    if custom_hours is not None:
        return float(custom_hours) * 3600.0
    env_val = os.getenv("POST_INTERVAL_HOURS")
    if env_val:
        try:
            return float(env_val) * 3600.0
        except ValueError:
            pass
    return 18000.0  # Default: 5 hours (18000 seconds)

def run_hackathon_cycle(history_topics: Optional[List[str]] = None) -> dict:
    load_dotenv()
    print("\n[Hackathon Scheduler]: Starting execution cycle...")
    app = build_hackathon_graph()
    
    initial_state = {
        "messages": [],
        "history_topics": history_topics or [],
        "current_post": None,
        "status": "started",
        "error": None
    }
    
    final_state = app.invoke(initial_state)
    print(f"[Hackathon Scheduler]: Cycle complete. Status: {final_state.get('status')}")
    return final_state

def start_scheduler(interval_hours: Optional[float] = None):
    load_dotenv()
    interval_seconds = get_post_interval_seconds(interval_hours)
    hours = interval_seconds / 3600.0
    print(f"=== Hackathon Assistant Scheduler Started ===")
    print(f"Interval: Every {hours:.2f} hours ({interval_seconds:.0f} seconds)")
    history_topics = []
    
    try:
        while True:
            final_state = run_hackathon_cycle(history_topics=history_topics)
            history_topics = final_state.get("history_topics", history_topics)
            print(f"Waiting {hours:.2f} hours ({interval_seconds:.0f}s) until next cycle...\n")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n[Hackathon Scheduler]: Stopped by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hackathon Assistant Scheduler")
    parser.add_argument("--interval-hours", type=float, help="Override posting interval in hours")
    args = parser.parse_args()
    start_scheduler(interval_hours=args.interval_hours)
```

Modify `main.py`:
```python
import sys
import argparse
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent.graph import build_graph
from Discord.scheduler import run_hackathon_cycle, start_scheduler

# Configure stdout for UTF-8 on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_cli_research(prompt: str):
    load_dotenv()
    print(f"=== Initializing LangGraph Research Agent ===")
    print(f"Research Topic: {prompt}\n")
    
    app = build_graph()
    config = {"configurable": {"thread_id": "cli_session_1"}}
    
    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "research_topic": prompt,
        "status": "started"
    }
    
    print("--- Graph Execution Trace ---")
    for event in app.stream(initial_state, config=config, stream_mode="updates"):
        for node_name, node_output in event.items():
            print(f"[Node Executed]: [{node_name}]")
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"  -> Tool Call Requested: {tc['name']} with args {tc['args']}")
                    elif msg.type == "tool":
                        print(f"  <- Tool Result received ({len(str(msg.content))} chars)")
    
    final_state = app.get_state(config)
    last_msg = final_state.values["messages"][-1]
    print("\n================ FINAL REPORT ================")
    print(last_msg.content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LangGraph AI Assistant & Hackathon Auto-Poster")
    parser.add_argument("--hackathon-now", action="store_true", help="Trigger single hackathon generation and Discord post immediately")
    parser.add_argument("--hackathon-schedule", action="store_true", help="Run background continuous scheduler")
    parser.add_argument("--interval-hours", type=float, default=None, help="Post interval in hours when running scheduler")
    parser.add_argument("query", nargs="?", default=None, help="Research prompt for default agent")
    
    args, unknown = parser.parse_known_args()
    
    if args.hackathon_now:
        print("=== Triggering Immediate Hackathon Agent Post ===")
        run_hackathon_cycle()
    elif args.hackathon_schedule:
        start_scheduler(interval_hours=args.interval_hours)
    else:
        query_text = args.query or "Explain LangGraph StateGraph, MemorySaver checkpointers, and ToolNode with an example."
        run_cli_research(query_text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_agent.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add Discord/scheduler.py main.py tests/test_hackathon_agent.py
git commit -m "feat: add flexible interval configuration and updated CLI options"
```

---

### Task 5: Containerization & GitHub Actions Deployment (`Dockerfile`, `docker-compose.yml`, `.github/workflows/hackathon_agent.yml`)

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.github/workflows/hackathon_agent.yml`

**Interfaces:**
- Consumes: `main.py`, `requirements.txt`
- Produces: Deployment configuration for Docker and GitHub Actions.

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Prevent Python from writing pyc files to disk & buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "--hackathon-schedule"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  hackathon-agent:
    build: .
    container_name: hackathon_discord_agent
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - POST_INTERVAL_HOURS=${POST_INTERVAL_HOURS:-5}
```

- [ ] **Step 3: Create GitHub Actions Workflow `.github/workflows/hackathon_agent.yml`**

```yaml
name: Hackathon Discord Agent Auto-Poster

on:
  schedule:
    # Runs every 5 hours (00:00, 05:00, 10:00, 15:00, 20:00 UTC)
    - cron: '0 */5 * * *'
  workflow_dispatch:

jobs:
  post-hackathon-tip:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Hackathon Agent Cycle
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
        run: |
          python main.py --hackathon-now
```

- [ ] **Step 4: Verify syntax & test setup**

Run: `pytest tests/test_hackathon_agent.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .github/workflows/hackathon_agent.yml
git commit -m "feat: add docker containerization and github actions scheduled workflow"
```
