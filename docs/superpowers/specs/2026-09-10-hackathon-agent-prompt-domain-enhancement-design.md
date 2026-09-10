# Hackathon AI Agent Prompt & Domain Enhancement Design

## Overview
Enhance the Hackathon AI Agent to generate deep-dive technical posts, judge interrogation guides, and architectural defense strategies tailored specifically for hackathon participants using the **PERN stack (PostgreSQL, Express.js, React, Node.js)**. 

The interactive MCQ model is removed and replaced by **3 Rotating Post Archetypes** featuring an **Experienced Hackathon Judge & Senior Full-Stack Architect Persona**.

---

## Key Enhancements & Scope

1. **Remove MCQs**: Eliminate MCQ pydantic models (`MCQOption`, `MCQuestion`) and Discord spoiler MCQ formatting.
2. **Tech Stack Specialization**: Focus deeply on **PostgreSQL, Express.js, React, and Node.js** (schema design, indexing, middleware, async workers, state management, render optimization).
3. **Experienced Reviewer / Judge Persona**: Adopt the persona of a veteran Hackathon Judge & Technical Director who critiques problem statement validation, edge cases, system bottlenecks, and pitch defense.
4. **3 Rotating Post Archetypes**:
   - **Technical Defense Guide** (Deep-dive architecture, code snippets, trade-offs).
   - **Case Study Walkthrough** (Sample hackathon problem statement, step-by-step PERN solution, mock judge interrogation script).
   - **Reviewer Cheat Sheet** (Scoping pitfalls, essential PERN code/schema patterns, top 5 judge questions & winning answers).
5. **Spoiler-Tagged Reviewer Q&A**: Each post features 2-3 tough judge questions with spoiler-hidden winning answers (`||**Judge Question:** ... \n **Winning Answer:** ...||`).
6. **Dynamic Discord Embed Styling**: Archetype-specific color coding, syntax-highlighted code blocks (`sql`, `javascript`), and character limit protection.

---

## Component Specifications

### 1. Data Models (`agent/hackathon_state.py`)

- **`ReviewerQA`**:
  - `question` (str): Tough technical question asked by a hackathon reviewer/judge.
  - `winning_answer` (str): Technical defense, architectural reasoning, and trade-off justification.

- **`HackathonPost`**:
  - `title` (str): Catchy, high-impact technical title.
  - `post_type` (str): `"Technical Defense Guide" | "Case Study Walkthrough" | "Reviewer Cheat Sheet"`.
  - `category` (str): Target domain category (*PostgreSQL Schema & Index Optimization*, *Express API Architecture & Middleware Defense*, *React State & Render Performance*, *Node.js Async Architecture*, *Judge Interrogation & Problem Statement Defense*, *Full-Stack System Design & Edge Cases*).
  - `judge_perspective` (str): Insights on what judges look for and critique.
  - `deep_dive_content` (str): Comprehensive markdown content with SQL and Express/React JavaScript code snippets.
  - `reviewer_qa_pairs` (List[ReviewerQA]): 2-3 judge Q&A items.
  - `actionable_checklist` (List[str]): 3-5 concrete technical execution steps.

- **`HackathonAgentState`**:
  - `messages` (list[AnyMessage])
  - `history_topics` (List[str])
  - `history_archetypes` (List[str])
  - `current_post` (Optional[HackathonPost])
  - `status` (str)
  - `error` (Optional[str])

---

### 2. Graph Nodes & Prompts (`agent/hackathon_graph.py`)

- **`topic_curator_node`**:
  - Selects an unvisited `category` from the expanded PERN & Judge Defense categories.
  - Selects an unvisited `archetype` from the 3 post types.
  - Updates `history_topics` and `history_archetypes` in state. Resets when all items are visited.

- **`content_generator_node`**:
  - Persona System Message: *"You are a Principal Hackathon Judge, Veteran Tech Lead, and PERN Stack Architect (PostgreSQL, Express.js, React, Node.js). You provide deep technical, battle-tested advice to help hackathon teams build rock-solid MVPs and defend their architecture against tough judge questions."*
  - Injects target archetype guidelines into the prompt to drive deep technical content, code snippets (SQL, JS/TS), judge interrogation insights, and spoiler Q&A pairs.

---

### 3. Discord Webhook Publisher (`Discord/webhook.py`)

- Embed Banner Colors:
  - `Technical Defense Guide` -> Deep Blue (`0x2980B9`)
  - `Case Study Walkthrough` -> Emerald Green (`0x27AE60`)
  - `Reviewer Cheat Sheet` -> Purple (`0x8E44AD`)
- Format Description: Header with Archetype badge & Category, Judge's Perspective blockquote, and Technical Deep Dive with code blocks.
- Format Embed Fields:
  - **🎯 Reviewer Interrogation & Winning Answers**: Renders spoiler-tagged Q&A pairs.
  - **📋 Actionable Execution Checklist**: Bulleted checklist.
- Safe truncation to fit within Discord's 4096 character description limit.

---

### 4. Tests & Verification (`tests/test_hackathon_agent.py`)

- Verify Pydantic schema serialization for `ReviewerQA` and updated `HackathonPost`.
- Verify Discord embed payload generation for all 3 post archetypes.
- Verify category and archetype state tracking in `topic_curator_node`.
- End-to-end dry-run test with `main.py --hackathon-now`.

---

## Verification Plan

### Automated Tests
```bash
pytest tests/test_hackathon_agent.py
pytest tests/test_graph.py
```

### Manual Verification
1. Run `python main.py --hackathon-now` with test webhook environment.
2. Inspect Discord embed output to confirm:
   - Proper archetype color banner.
   - Code snippet syntax highlighting (SQL / JS).
   - Clickable spoiler tags on Reviewer Q&A answers (`||...||`).
