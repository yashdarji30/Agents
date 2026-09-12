import sqlite3
import os
from typing import List, Tuple
from contextlib import closing

DEFAULT_DB_PATH = "hackathon_history.db"

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Connect to SQLite database and return connection object."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize the posted_history table in SQLite if it does not exist."""
    with closing(get_connection(db_path)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posted_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    archetype TEXT NOT NULL,
                    title TEXT NOT NULL,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

def get_posted_history(db_path: str = DEFAULT_DB_PATH) -> Tuple[List[str], List[str]]:
    """
    Fetch lists of previously posted categories and archetypes.
    Returns:
        (categories, archetypes)
    """
    if db_path != ":memory:" and not os.path.exists(db_path):
        init_db(db_path)

    try:
        with closing(get_connection(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, archetype FROM posted_history ORDER BY id ASC")
            rows = cursor.fetchall()
            
            categories = [row["category"] for row in rows]
            archetypes = [row["archetype"] for row in rows]
            return categories, archetypes
    except sqlite3.OperationalError:
        init_db(db_path)
        return [], []

def save_post_history(category: str, archetype: str, title: str, db_path: str = DEFAULT_DB_PATH) -> None:
    """Record a successfully posted topic and archetype into SQLite."""
    if db_path != ":memory:" and not os.path.exists(db_path):
        init_db(db_path)

    with closing(get_connection(db_path)) as conn:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO posted_history (category, archetype, title) VALUES (?, ?, ?)",
                (category, archetype, title)
            )
