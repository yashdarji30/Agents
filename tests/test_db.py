import pytest
import sqlite3
import os
import tempfile
from agent.db import init_db, get_posted_history, save_post_history, get_connection

def test_init_db_creates_table():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()
    
    try:
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posted_history'")
        table = cursor.fetchone()
        conn.close()
        assert table is not None
        assert table["name"] == "posted_history"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

def test_save_and_get_posted_history():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    try:
        init_db(db_path)
        categories, archetypes = get_posted_history(db_path)
        assert categories == []
        assert archetypes == []

        save_post_history(
            category="PostgreSQL Schema & Index Optimization",
            archetype="Technical Defense Guide",
            title="PostgreSQL Indexing",
            db_path=db_path
        )

        categories, archetypes = get_posted_history(db_path)
        assert categories == ["PostgreSQL Schema & Index Optimization"]
        assert archetypes == ["Technical Defense Guide"]

        save_post_history(
            category="Express API Architecture & Middleware Defense",
            archetype="Case Study Walkthrough",
            title="Express Rate Limiting",
            db_path=db_path
        )

        categories, archetypes = get_posted_history(db_path)
        assert len(categories) == 2
        assert categories[1] == "Express API Architecture & Middleware Defense"
        assert archetypes[1] == "Case Study Walkthrough"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
