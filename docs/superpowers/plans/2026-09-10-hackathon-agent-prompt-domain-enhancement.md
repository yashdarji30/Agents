# Hackathon AI Agent Prompt & Domain Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Hackathon AI Agent from simple MCQ generation into an in-depth PERN Stack (PostgreSQL, Express.js, React, Node.js) judge defense guide generator, rotating across 3 post archetypes with spoiler-tagged reviewer Q&As and rich Discord formatting.

**Architecture:** Update Pydantic data schemas in `agent/hackathon_state.py`, expand category & archetype curation memory in `agent/hackathon_graph.py`, build a PERN Judge & Technical Director LLM system prompt in `agent/hackathon_graph.py`, and style dynamic multi-color Discord embeds with spoiler Q&As in `Discord/webhook.py`.

**Tech Stack:** Python 3.10+, LangGraph, LangChain Google GenAI (`gemini-3.6-flash`), Pydantic v2, Discord Webhooks, Pytest.

## Global Constraints
- Target Tech Stack: PostgreSQL, Express.js, React, Node.js (PERN stack).
- Post Archetypes: `Technical Defense Guide`, `Case Study Walkthrough`, `Reviewer Cheat Sheet`.
- Model: `gemini-3.6-flash` with structured output via Pydantic.
- Discord Webhook Embed limits: <= 4096 chars description, <= 1024 chars per field.

---

### Task 1: Update Data Schema and State Definition (`agent/hackathon_state.py`)

**Files:**
- Modify: `agent/hackathon_state.py`
- Test: `tests/test_hackathon_agent.py`

**Interfaces:**
- Consumes: None
- Produces: `ReviewerQA`, `HackathonPost` (with `post_type`, `judge_perspective`, `deep_dive_content`, `reviewer_qa_pairs`, `actionable_checklist`), `HackathonAgentState` (with `history_archetypes`).

- [ ] **Step 1: Write failing test for new Pydantic schema in tests/test_hackathon_agent.py**

```python
import pytest
from agent.hackathon_state import ReviewerQA, HackathonPost, HackathonAgentState

def test_hackathon_post_schema_validation():
    qa = ReviewerQA(
        question="Why choose PostgreSQL over MongoDB for a hackathon MVP?",
        winning_answer="PostgreSQL provides relational integrity for transactions, ACID compliance, and JSONB support if document flexibility is needed."
    )
    post = HackathonPost(
        title="PostgreSQL Indexing & DB Defense Strategy",
        post_type="Technical Defense Guide",
        category="PostgreSQL Schema & Index Optimization",
        judge_perspective="Judges check if database queries slow down under load and if foreign key constraints exist.",
        deep_dive_content="### PostgreSQL Query Optimization\nUse `EXPLAIN ANALYZE` on Express API endpoints.",
        reviewer_qa_pairs=[qa],
        actionable_checklist=["Add B-tree index on foreign keys", "Use connection pooling with pg-pool"]
    )
    assert post.post_type == "Technical Defense Guide"
    assert post.category == "PostgreSQL Schema & Index Optimization"
    assert len(post.reviewer_qa_pairs) == 1
    assert post.reviewer_qa_pairs[0].question.startswith("Why choose PostgreSQL")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_agent.py::test_hackathon_post_schema_validation -v`
Expected: FAIL with `ImportError` or `ValidationError` because `ReviewerQA` is missing and `HackathonPost` fields differ.

- [ ] **Step 3: Update agent/hackathon_state.py**

```python
from typing import List, Optional, TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class ReviewerQA(BaseModel):
    question: str = Field(description="The tough technical question asked by a hackathon judge or reviewer")
    winning_answer: str = Field(description="The precise technical defense, architectural trade-off, and winning answer")

class HackathonPost(BaseModel):
    title: str = Field(description="Catchy, high-impact technical title")
    post_type: str = Field(description="Type of post: 'Technical Defense Guide', 'Case Study Walkthrough', or 'Reviewer Cheat Sheet'")
    category: str = Field(description="Target category (e.g. PostgreSQL Schema & Index Optimization, Express API Architecture & Middleware Defense, React State & Render Performance, Node.js Async Architecture, Judge Interrogation & Problem Statement Defense, Full-Stack System Design & Edge Cases)")
    judge_perspective: str = Field(description="Insights into what judges test, measure, and critique regarding this topic")
    deep_dive_content: str = Field(description="Comprehensive markdown content with real code/schema snippets in SQL, Express, React, or Node")
    reviewer_qa_pairs: List[ReviewerQA] = Field(description="2-3 tough reviewer questions paired with winning technical answers")
    actionable_checklist: List[str] = Field(description="3-5 concrete step-by-step technical execution items")

class HackathonAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    history_topics: List[str]
    history_archetypes: List[str]
    current_post: Optional[HackathonPost]
    status: str
    error: Optional[str]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_agent.py::test_hackathon_post_schema_validation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/hackathon_state.py tests/test_hackathon_agent.py
git commit -m "feat(agent): update HackathonPost schema for PERN judge guides and reviewer Q&A"
```

---

### Task 2: Update Category & Archetype Curator Node (`agent/hackathon_graph.py`)

**Files:**
- Modify: `agent/hackathon_graph.py:11-34`
- Test: `tests/test_hackathon_agent.py`

**Interfaces:**
- Consumes: `HackathonAgentState` with `history_topics` and `history_archetypes`
- Produces: Updated state with selected `category` and `archetype` added to history

- [ ] **Step 1: Write test for topic and archetype curation in tests/test_hackathon_agent.py**

```python
from agent.hackathon_graph import topic_curator_node, HACKATHON_CATEGORIES, HACKATHON_ARCHETYPES

def test_topic_curator_node_tracks_categories_and_archetypes():
    state = {"history_topics": [], "history_archetypes": []}
    res = topic_curator_node(state)
    
    assert "history_topics" in res
    assert "history_archetypes" in res
    assert len(res["history_topics"]) == 1
    assert len(res["history_archetypes"]) == 1
    assert res["history_topics"][0] in HACKATHON_CATEGORIES
    assert res["history_archetypes"][0] in HACKATHON_ARCHETYPES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_agent.py::test_topic_curator_node_tracks_categories_and_archetypes -v`
Expected: FAIL because `HACKATHON_ARCHETYPES` is missing and `topic_curator_node` does not track `history_archetypes`.

- [ ] **Step 3: Update HACKATHON_CATEGORIES, HACKATHON_ARCHETYPES, and topic_curator_node in agent/hackathon_graph.py**

```python
HACKATHON_CATEGORIES = [
    "PostgreSQL Schema & Index Optimization",
    "Express API Architecture & Middleware Defense",
    "React State & Render Performance",
    "Node.js Async Architecture & Event Loop",
    "Judge Interrogation & Problem Statement Defense",
    "Full-Stack System Design & Edge Case Handling"
]

HACKATHON_ARCHETYPES = [
    "Technical Defense Guide",
    "Case Study Walkthrough",
    "Reviewer Cheat Sheet"
]

def topic_curator_node(state: HackathonAgentState) -> Dict[str, Any]:
    topic_history = state.get("history_topics", [])
    archetype_history = state.get("history_archetypes", [])
    
    available_topics = [c for c in HACKATHON_CATEGORIES if c not in topic_history]
    if not available_topics:
        available_topics = HACKATHON_CATEGORIES
        topic_history = []
        
    available_archetypes = [a for a in HACKATHON_ARCHETYPES if a not in archetype_history]
    if not available_archetypes:
        available_archetypes = HACKATHON_ARCHETYPES
        archetype_history = []
        
    selected_category = random.choice(available_topics)
    selected_archetype = random.choice(available_archetypes)
    
    return {
        "history_topics": list(topic_history) + [selected_category],
        "history_archetypes": list(archetype_history) + [selected_archetype],
        "status": "topic_curated"
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_agent.py::test_topic_curator_node_tracks_categories_and_archetypes -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/hackathon_graph.py tests/test_hackathon_agent.py
git commit -m "feat(agent): enhance topic_curator_node to rotate PERN categories and archetypes"
```

---

### Task 3: Update LLM Content Generator Node with PERN Judge Persona (`agent/hackathon_graph.py`)

**Files:**
- Modify: `agent/hackathon_graph.py:35-86`
- Test: `tests/test_hackathon_agent.py`

**Interfaces:**
- Consumes: State with `history_topics` and `history_archetypes`
- Produces: `current_post` (`HackathonPost`) generated via `gemini-3.6-flash`

- [ ] **Step 1: Write test for content_generator_node prompt construction logic in tests/test_hackathon_agent.py**

```python
from unittest.mock import patch, MagicMock
from agent.hackathon_graph import content_generator_node
from agent.hackathon_state import HackathonPost, ReviewerQA

@patch("agent.hackathon_graph.ChatGoogleGenerativeAI")
def test_content_generator_node_invokes_llm(mock_llm_cls):
    mock_instance = MagicMock()
    mock_structured = MagicMock()
    mock_llm_cls.return_value.with_structured_output.return_value = mock_structured
    
    fake_post = HackathonPost(
        title="Express Middleware Security",
        post_type="Technical Defense Guide",
        category="Express API Architecture & Middleware Defense",
        judge_perspective="Judges test input validation and CORS settings.",
        deep_dive_content="Use express-validator and helmet.",
        reviewer_qa_pairs=[
            ReviewerQA(question="How do you stop SQL injection?", winning_answer="Parameterized queries with pg-promise or Prisma.")
        ],
        actionable_checklist=["Add express-rate-limit"]
    )
    mock_structured.invoke.return_value = fake_post
    
    state = {
        "history_topics": ["Express API Architecture & Middleware Defense"],
        "history_archetypes": ["Technical Defense Guide"]
    }
    result = content_generator_node(state)
    assert result["status"] == "content_generated"
    assert result["current_post"].title == "Express Middleware Security"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_agent.py::test_content_generator_node_invokes_llm -v`
Expected: FAIL because `content_generator_node` does not read `history_archetypes` or uses old prompt.

- [ ] **Step 3: Update content_generator_node in agent/hackathon_graph.py**

```python
def content_generator_node(state: HackathonAgentState) -> Dict[str, Any]:
    api_key = os.getenv("GOOGLE_API_KEY")
    current_category = state["history_topics"][-1]
    current_archetype = state.get("history_archetypes", ["Technical Defense Guide"])[-1]
    print(f"[Content Generator]: Generating hackathon post for category '{current_category}' [Archetype: '{current_archetype}']...")
    
    candidate_models = [
        "gemini-3.6-flash"
    ]

    llm_instances = [
        ChatGoogleGenerativeAI(
            model=m,
            google_api_key=api_key,
            max_retries=3
        ).with_structured_output(HackathonPost)
        for m in candidate_models
    ]
    
    primary_llm = llm_instances[0]
    fallbacks = llm_instances[1:]
    if fallbacks:
        structured_llm = primary_llm.with_fallbacks(fallbacks, exceptions_to_handle=(Exception,))
    else:
        structured_llm = primary_llm
    
    system_prompt = (
        "You are a Principal Hackathon Judge, Veteran Technical Director, and PERN Stack Architect (PostgreSQL, Express.js, React, Node.js). "
        "Your mission is to provide deep-dive technical guidance, system architecture patterns, and defense strategies to help hackathon teams "
        "build rock-solid MVPs and effortlessly defend their tech stack when grilled by judges."
    )
    
    prompt = f"""Generate an in-depth hackathon technical post.

Post Archetype: {current_archetype}
Category Focus: {current_category}
Target Tech Stack: PostgreSQL, Express.js, React, Node.js (PERN Stack)

Requirements for Archetype '{current_archetype}':
1. Title: High-impact, technical title.
2. Category: {current_category}.
3. Post Type: {current_archetype}.
4. Judge Perspective: Detailed breakdown of what judges test, critique, and question regarding {current_category}.
5. Deep Dive Content: Lengthy, comprehensive technical markdown guide. Include actual code/schema snippets (e.g. SQL queries, Express middleware, React custom hooks) relevant to the PERN stack.
6. Reviewer QA Pairs: 2-3 tough questions a judge will ask about this topic/stack with bulletproof, winning answers.
7. Actionable Checklist: 3-5 concrete step-by-step execution items for the team.
"""
    
    try:
        post: HackathonPost = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ])
        print(f"[Content Generator Success]: Post '{post.title}' ({post.post_type}) generated successfully.")
        return {
            "current_post": post,
            "status": "content_generated"
        }
    except Exception as e:
        print(f"[Content Generator Error]: Failed to generate content: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_agent.py::test_content_generator_node_invokes_llm -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/hackathon_graph.py tests/test_hackathon_agent.py
git commit -m "feat(agent): update content_generator_node with PERN Judge persona and archetype prompts"
```

---

### Task 4: Update Discord Webhook Embed Builder (`Discord/webhook.py`)

**Files:**
- Modify: `Discord/webhook.py`
- Test: `tests/test_hackathon_agent.py`

**Interfaces:**
- Consumes: `HackathonPost`
- Produces: Discord Webhook JSON Payload sent to Discord API

- [ ] **Step 1: Write test for Discord payload building in tests/test_hackathon_agent.py**

```python
from agent.hackathon_state import HackathonPost, ReviewerQA
from Discord.webhook import build_discord_embed_payload

def test_build_discord_embed_payload_structures_correctly():
    qa = ReviewerQA(
        question="How do you optimize React render cycles?",
        winning_answer="Use React.memo, useParam hooks, and defer expensive state computations to worker threads."
    )
    post = HackathonPost(
        title="React Render Optimization",
        post_type="Reviewer Cheat Sheet",
        category="React State & Render Performance",
        judge_perspective="Judges look for UI responsiveness during live demos.",
        deep_dive_content="### React Performance\nAvoid inline functions in JSX.",
        reviewer_qa_pairs=[qa],
        actionable_checklist=["Profile with React DevTools", "Memoize context providers"]
    )
    
    payload = build_discord_embed_payload(post)
    embed = payload["embeds"][0]
    
    assert "Reviewer Cheat Sheet" in embed["title"]
    assert embed["color"] == 0x8E44AD  # Purple for Reviewer Cheat Sheet
    assert "🎯 Reviewer Interrogation & Winning Answers" in [f["name"] for f in embed["fields"]]
    
    # Check spoiler tag formatting in Q&A field
    qa_field = next(f for f in embed["fields"] if "Reviewer Interrogation" in f["name"])
    assert "||" in qa_field["value"]
    assert "Winning Answer:" in qa_field["value"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_agent.py::test_build_discord_embed_payload_structures_correctly -v`
Expected: FAIL because `build_discord_embed_payload` function does not exist or uses old `mcqs` logic.

- [ ] **Step 3: Update Discord/webhook.py**

```python
import os
import requests
from typing import Dict, Any
from agent.hackathon_state import HackathonPost

ARCHETYPE_COLORS = {
    "Technical Defense Guide": 0x2980B9,  # Cobalt Blue
    "Case Study Walkthrough": 0x27AE60,   # Emerald Green
    "Reviewer Cheat Sheet": 0x8E44AD      # Vivid Purple
}

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
    
    return {"embeds": [embed]}

def publish_to_discord(post: HackathonPost) -> bool:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[Discord Webhook Error]: DISCORD_WEBHOOK_URL environment variable is missing.")
        return False
        
    payload = build_discord_embed_payload(post)
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            print(f"[Discord Webhook Success]: Post '{post.title}' published successfully.")
            return True
        else:
            print(f"[Discord Webhook Error]: HTTP {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[Discord Webhook Exception]: Failed to publish to Discord: {e}")
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_agent.py::test_build_discord_embed_payload_structures_correctly -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Discord/webhook.py tests/test_hackathon_agent.py
git commit -m "feat(discord): update webhook embed payload builder with spoiler Q&As and archetype colors"
```

---

### Task 5: End-to-End Verification and Test Suite Suite Refresh (`tests/test_hackathon_agent.py`)

**Files:**
- Modify: `tests/test_hackathon_agent.py`
- Test: All tests

**Interfaces:**
- Consumes: All updated modules
- Produces: Clean pytest run across the entire codebase

- [ ] **Step 1: Update all test functions in tests/test_hackathon_agent.py to match new schemas**

Ensure tests cover:
1. `test_hackathon_post_schema_validation`
2. `test_topic_curator_node_tracks_categories_and_archetypes`
3. `test_content_generator_node_invokes_llm`
4. `test_build_discord_embed_payload_structures_correctly`
5. `test_full_hackathon_graph_workflow` (mocking LLM & Discord webhook)

- [ ] **Step 2: Run pytest to verify all tests pass**

Run: `pytest tests/test_hackathon_agent.py tests/test_graph.py -v`
Expected: ALL PASS

- [ ] **Step 3: Dry run CLI command**

Run: `python main.py --hackathon-now` (or dry-run with mock/env key)
Expected: Workflow completes topic curation, content generation, and webhook dispatch without errors.

- [ ] **Step 4: Commit**

```bash
git add tests/test_hackathon_agent.py
git commit -m "test: refresh hackathon agent test suite for PERN judge guides"
```
