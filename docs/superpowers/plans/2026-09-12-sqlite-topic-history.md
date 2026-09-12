# SQLite Topic History Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist generated hackathon categories and archetypes in a local SQLite database (`hackathon_history.db`) to eliminate duplicate post generation across agent executions.

**Architecture:** Create a lightweight `agent/db.py` SQLite manager. Update `topic_curator_node` in `agent/hackathon_graph.py` to query past history from SQLite, and `discord_publisher_node` to record successfully published posts.

**Tech Stack:** Python 3.10+, `sqlite3` (standard library), `pytest`.

## Global Constraints
- Use Python's built-in `sqlite3` module (no heavy ORM dependencies).
- Ensure DB path is configurable via function parameter defaulting to `hackathon_history.db`.
- Add `*.db` to `.gitignore`.

---

### Task 1: Create SQLite Database Module (`agent/db.py`) and Unit Tests

**Files:**
- Create: `agent/db.py`
- Test: `tests/test_db.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces:
  - `init_db(db_path: str = "hackathon_history.db") -> None`
  - `get_posted_history(db_path: str = "hackathon_history.db") -> Tuple[List[str], List[str]]`
  - `save_post_history(category: str, archetype: str, title: str, db_path: str = "hackathon_history.db") -> None`

- [ ] **Step 1: Write the failing unit tests for SQLite database operations**

Create `tests/test_db.py`:
```python
import os
import pytest
from agent.db import init_db, get_posted_history, save_post_history

@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_history.db")
    init_db(db_file)
    return db_file

def test_init_db_creates_table(temp_db):
    categories, archetypes = get_posted_history(temp_db)
    assert categories == []
    assert archetypes == []

def test_save_and_retrieve_history(temp_db):
    save_post_history("React State", "Technical Defense Guide", "React State Deep Dive", db_path=temp_db)
    categories, archetypes = get_posted_history(temp_db)
    assert categories == ["React State"]
    assert archetypes == ["Technical Defense Guide"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'agent.db'`

- [ ] **Step 3: Implement `agent/db.py`**

Create `agent/db.py`:
```python
import sqlite3
from typing import List, Tuple

DEFAULT_DB_PATH = "hackathon_history.db"

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posted_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                archetype TEXT NOT NULL,
                title TEXT NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

def get_posted_history(db_path: str = DEFAULT_DB_PATH) -> Tuple[List[str], List[str]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category, archetype FROM posted_history ORDER BY id ASC")
        rows = cursor.fetchall()
        categories = [r[0] for r in rows]
        archetypes = [r[1] for r in rows]
        return categories, archetypes

def save_post_history(category: str, archetype: str, title: str, db_path: str = DEFAULT_DB_PATH) -> None:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO posted_history (category, archetype, title) VALUES (?, ?, ?)",
            (category, archetype, title)
        )
        conn.commit()
```

- [ ] **Step 4: Update `.gitignore`**

Append `*.db` to `.gitignore`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_db.py -v`  
Expected: PASS

---

### Task 2: Integrate SQLite Persistence into LangGraph Agent Nodes

**Files:**
- Modify: `agent/hackathon_graph.py`
- Test: `tests/test_hackathon_graph.py`

**Interfaces:**
- Consumes: `get_posted_history` and `save_post_history` from `agent/db.py`

- [ ] **Step 1: Write integration tests for `topic_curator_node` and `discord_publisher_node`**

Update/add tests in `tests/test_hackathon_graph.py` to verify DB loading and insertion.

- [ ] **Step 2: Update `topic_curator_node` and `discord_publisher_node` in `agent/hackathon_graph.py`**

In `topic_curator_node`:
- Load history from SQLite if `history_topics` is empty in initial state.

In `discord_publisher_node`:
- Upon successful `publish_to_discord(post)`, call `save_post_history(post.category, post.post_type, post.title)`.

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/`  
Expected: All tests pass.
