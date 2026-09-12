# Dynamic Architecture Diagrams in Discord Embeds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the PERN Hackathon Mentor AI Agent to dynamically evaluate hackathon topics and optionally include base64-encoded visual Mermaid architecture diagrams in Discord embeds.

**Architecture:** Extend `HackathonPost` model with an optional `architecture_diagram` field, append requirement #8 to Gemini 3.6 Flash prompt in `hackathon_graph.py`, and implement a Base64 `mermaid.ink` URL encoder in `Discord/webhook.py` to embed images seamlessly without heavy dependencies.

**Tech Stack:** Python 3.10+, Pydantic v2, Base64 standard library, Pytest, LangChain / LangGraph, Discord Webhooks.

## Global Constraints
- Preserve exact existing prompt requirements 1–7 in `agent/hackathon_graph.py`.
- Base64 encoding must fail gracefully to `None` on invalid inputs, keeping embed publishing operational.
- All code changes must follow TDD: write failing test first, verify failure, implement minimal code, verify pass, commit.

---

### Task 1: Extend `HackathonPost` Schema (`agent/hackathon_state.py`)

**Files:**
- Modify: `agent/hackathon_state.py`
- Test: `tests/test_hackathon_state.py`

**Interfaces:**
- Consumes: Pydantic `BaseModel`, `Field`, `Optional`
- Produces: `HackathonPost` schema with optional `architecture_diagram: Optional[str]`

- [ ] **Step 1: Write the failing test**

Create or update `tests/test_hackathon_state.py`:
```python
import pytest
from agent.hackathon_state import HackathonPost, ReviewerQA

def test_hackathon_post_schema_with_architecture_diagram():
    qa = ReviewerQA(question="Why PostgreSQL?", winning_answer="ACID compliance and JSONB flexibility.")
    
    # Test without architecture diagram (defaults to None)
    post_without_diagram = HackathonPost(
        title="PostgreSQL Indexing Defense",
        post_type="Technical Defense Guide",
        category="PostgreSQL Schema & Index Optimization",
        judge_perspective="Judges check index utilization.",
        deep_dive_content="Use B-Tree and GIN indexes.",
        reviewer_qa_pairs=[qa],
        actionable_checklist=["Run EXPLAIN ANALYZE"]
    )
    assert post_without_diagram.architecture_diagram is None

    # Test with architecture diagram
    post_with_diagram = HackathonPost(
        title="PostgreSQL Indexing Defense",
        post_type="Technical Defense Guide",
        category="PostgreSQL Schema & Index Optimization",
        judge_perspective="Judges check index utilization.",
        deep_dive_content="Use B-Tree and GIN indexes.",
        reviewer_qa_pairs=[qa],
        actionable_checklist=["Run EXPLAIN ANALYZE"],
        architecture_diagram="flowchart TD\n  Client --> DB[(PostgreSQL)]"
    )
    assert post_with_diagram.architecture_diagram == "flowchart TD\n  Client --> DB[(PostgreSQL)]"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_state.py -v`
Expected: FAIL if `architecture_diagram` is missing or unexpected parameter.

- [ ] **Step 3: Write minimal implementation**

In `agent/hackathon_state.py`:
```python
class HackathonPost(BaseModel):
    title: str = Field(description="Catchy, high-impact technical title")
    post_type: str = Field(description="Type of post: 'Technical Defense Guide', 'Case Study Walkthrough', or 'Reviewer Cheat Sheet'")
    category: str = Field(description="Target category (e.g. PostgreSQL Schema & Index Optimization, Express API Architecture & Middleware Defense, React State & Render Performance, Node.js Async Architecture, Judge Interrogation & Problem Statement Defense, Full-Stack System Design & Edge Cases)")
    judge_perspective: str = Field(description="Insights into what judges test, measure, and critique regarding this topic")
    deep_dive_content: str = Field(description="Comprehensive markdown content with real code/schema snippets in SQL, Express, React, or Node")
    reviewer_qa_pairs: List[ReviewerQA] = Field(description="2-3 tough reviewer questions paired with winning technical answers")
    actionable_checklist: List[str] = Field(description="3-5 concrete step-by-step technical execution items")
    architecture_diagram: Optional[str] = Field(
        default=None,
        description="Optional raw Mermaid JS diagram syntax (e.g. 'flowchart TD' or 'sequenceDiagram'). ONLY include if the topic visually benefits from an architecture diagram. Set to None if no diagram is needed."
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/hackathon_state.py tests/test_hackathon_state.py
git commit -m "feat: add architecture_diagram field to HackathonPost schema"
```

---

### Task 2: Base64 Encoder & Embed Payload Update (`Discord/webhook.py`)

**Files:**
- Modify: `Discord/webhook.py`
- Test: `tests/test_discord_webhook.py`

**Interfaces:**
- Consumes: `HackathonPost.architecture_diagram`
- Produces: `generate_mermaid_image_url(mermaid_code: str) -> Optional[str]`, updated `build_discord_embed_payload` with `embed["image"]`

- [ ] **Step 1: Write the failing test**

Create or update `tests/test_discord_webhook.py`:
```python
import base64
import pytest
from Discord.webhook import generate_mermaid_image_url, build_discord_embed_payload
from agent.hackathon_state import HackathonPost, ReviewerQA

def test_generate_mermaid_image_url():
    assert generate_mermaid_image_url(None) is None
    assert generate_mermaid_image_url("") is None
    assert generate_mermaid_image_url("   ") is None
    
    diagram = "flowchart TD\n  A --> B"
    url = generate_mermaid_image_url(diagram)
    assert url is not None
    assert url.startswith("https://mermaid.ink/img/")
    
    # Verify base64 content
    encoded_part = url.replace("https://mermaid.ink/img/", "")
    decoded = base64.b64encode(diagram.encode('utf-8')).decode('utf-8')
    assert encoded_part == decoded

def test_build_discord_embed_payload_with_image():
    qa = ReviewerQA(question="Q", winning_answer="A")
    post_with_diagram = HackathonPost(
        title="System Design",
        post_type="Technical Defense Guide",
        category="Full-Stack System Design & Edge Case Handling",
        judge_perspective="Perspective",
        deep_dive_content="Content",
        reviewer_qa_pairs=[qa],
        actionable_checklist=["Task 1"],
        architecture_diagram="flowchart TD\n  React --> Express"
    )
    
    payload = build_discord_embed_payload(post_with_diagram)
    embed = payload["embeds"][0]
    assert "image" in embed
    assert embed["image"]["url"].startswith("https://mermaid.ink/img/")

def test_build_discord_embed_payload_without_image():
    qa = ReviewerQA(question="Q", winning_answer="A")
    post_no_diagram = HackathonPost(
        title="System Design",
        post_type="Technical Defense Guide",
        category="Full-Stack System Design & Edge Case Handling",
        judge_perspective="Perspective",
        deep_dive_content="Content",
        reviewer_qa_pairs=[qa],
        actionable_checklist=["Task 1"],
        architecture_diagram=None
    )
    
    payload = build_discord_embed_payload(post_no_diagram)
    embed = payload["embeds"][0]
    assert "image" not in embed
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_discord_webhook.py -v`
Expected: FAIL with `ImportError: cannot import name 'generate_mermaid_image_url'`.

- [ ] **Step 3: Write minimal implementation**

In `Discord/webhook.py`:
```python
import base64

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
```

And in `build_discord_embed_payload(post: HackathonPost)`:
```python
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

    if post.architecture_diagram:
        image_url = generate_mermaid_image_url(post.architecture_diagram)
        if image_url:
            embed["image"] = {"url": image_url}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_discord_webhook.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Discord/webhook.py tests/test_discord_webhook.py
git commit -m "feat: add generate_mermaid_image_url and attach embed image payload"
```

---

### Task 3: LLM Prompt Tuning (`agent/hackathon_graph.py`)

**Files:**
- Modify: `agent/hackathon_graph.py`
- Test: `tests/test_hackathon_graph.py`

**Interfaces:**
- Consumes: Gemini prompt template
- Produces: Updated prompt requirement #8 in `content_generator_node`

- [ ] **Step 1: Write the failing test**

Create or update `tests/test_hackathon_graph.py`:
```python
import pytest
from agent.hackathon_graph import content_generator_node

def test_prompt_contains_architecture_diagram_requirement():
    # Verify by inspecting prompt template structure in source or testing helper
    from agent import hackathon_graph
    import inspect
    
    source = inspect.getsource(hackathon_graph.content_generator_node)
    assert "8. Architecture Diagram (Optional)" in source
    assert "1. Title: High-impact, technical title." in source
    assert "7. Actionable Checklist: 3-5 concrete step-by-step execution items for the team." in source
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hackathon_graph.py -v`
Expected: FAIL with `AssertionError: assert '8. Architecture Diagram (Optional)' in source`.

- [ ] **Step 3: Write minimal implementation**

In `agent/hackathon_graph.py`, update prompt in `content_generator_node`:
```python
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
8. Architecture Diagram (Optional): Evaluate if this topic/archetype visually benefits from a dynamic system flowchart or sequence diagram. If beneficial, provide clean raw Mermaid JS syntax without backticks. If not needed, set to null.
"""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hackathon_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/hackathon_graph.py tests/test_hackathon_graph.py
git commit -m "feat: add dynamic architecture diagram requirement to Gemini prompt"
```

---

### Task 4: Full Suite Verification & Final Check

**Files:**
- Test: All tests in `tests/`

- [ ] **Step 1: Run complete test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 2: Final Commit**

```bash
git add .
git commit -m "chore: complete implementation plan for dynamic architecture diagrams"
```
