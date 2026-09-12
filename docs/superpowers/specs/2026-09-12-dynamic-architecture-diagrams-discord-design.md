# Design Spec: Dynamic Architecture Diagrams in Discord Embeds

Date: 2026-09-12
Status: Approved

## 1. Overview & Context
The PERN Hackathon Mentor AI Agent generates high-impact, technical post guides and publishes them to Discord channels via webhooks. Currently, posts consist of text-based deep dives, judge perspective insights, Q&A pairs, and checklists.

To enhance visual defense strategy and system architecture clarity, this feature introduces **Dynamic Architecture Diagrams** rendered visually in Discord Embeds.

## 2. Key Requirements
1. **Dynamic & Autonomous Decision**: The agent dynamically evaluates whether a post category or archetype requires a visual diagram (e.g. system flowcharts, database index access paths, middleware sequence diagrams). If not required, the diagram is omitted (`None`).
2. **Preserve Existing Prompt Structure**: The addition of diagram generation must append to the existing prompt requirements without modifying or breaking existing prompt requirements 1–7.
3. **Lightweight & High Performance**: Use `mermaid.ink` Base64 encoding to generate direct image URLs without adding heavy local rendering tools (e.g. Puppeteer/Mermaid CLI) or extra LLM nodes.
4. **Clean Fallbacks**: If a diagram is omitted or fails encoding, Discord embeds will publish cleanly as text without broken image icons or failing execution cycles.

## 3. Technical Design Breakdown

### 3.1 Data Model (`agent/hackathon_state.py`)
Add an optional field `architecture_diagram` to the `HackathonPost` Pydantic model:

```python
class HackathonPost(BaseModel):
    title: str = Field(...)
    post_type: str = Field(...)
    category: str = Field(...)
    judge_perspective: str = Field(...)
    deep_dive_content: str = Field(...)
    reviewer_qa_pairs: List[ReviewerQA] = Field(...)
    actionable_checklist: List[str] = Field(...)
    architecture_diagram: Optional[str] = Field(
        default=None,
        description=(
            "Optional raw Mermaid JS diagram syntax (e.g. 'flowchart TD' or 'sequenceDiagram'). "
            "ONLY include if the post topic/archetype visually benefits from an architecture diagram. "
            "Set to None if no diagram is needed."
        )
    )
```

### 3.2 LLM Content Generation & Prompting (`agent/hackathon_graph.py`)
Preserve exact existing prompt structure and append requirement #8:

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

### 3.3 Base64 Encoder & Webhook Integration (`Discord/webhook.py`)
Add Base64 URL encoder helper:

```python
import base64

def generate_mermaid_image_url(mermaid_code: str) -> Optional[str]:
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

Update `build_discord_embed_payload(post)`:
```python
if post.architecture_diagram:
    image_url = generate_mermaid_image_url(post.architecture_diagram)
    if image_url:
        embed["image"] = {"url": image_url}
```

## 4. Error Handling & Edge Cases
- **Syntax Errors in Mermaid**: If `mermaid.ink` cannot parse invalid syntax sent by Discord's client embed fetcher, Discord handles it gracefully by omitting the image.
- **Base64 Encoding Exception**: Trapped cleanly with warning print and returns `None`, skipping the embed image field.
- **Database Persistence Compatibility**: Existing SQLite persistence in `agent/db.py` remains unaffected as `save_post_history` records title, category, and archetype.

## 5. Verification Plan
1. **Unit Tests**: Add tests in `tests/` verifying `generate_mermaid_image_url` handles valid Mermaid strings, empty strings, and `None`.
2. **Schema Verification**: Validate `HackathonPost` instantiates cleanly with and without `architecture_diagram`.
3. **Integration Cycle**: Execute `main.py` locally and verify generated embed payload structure.
