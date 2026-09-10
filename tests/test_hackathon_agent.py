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

def test_topic_curator_node_tracks_categories_and_archetypes():
    from agent.hackathon_graph import topic_curator_node, HACKATHON_CATEGORIES, HACKATHON_ARCHETYPES
    state = {"history_topics": [], "history_archetypes": []}
    res = topic_curator_node(state)
    
    assert "history_topics" in res
    assert "history_archetypes" in res
    assert len(res["history_topics"]) == 1
    assert len(res["history_archetypes"]) == 1
    assert res["history_topics"][0] in HACKATHON_CATEGORIES
    assert res["history_archetypes"][0] in HACKATHON_ARCHETYPES

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

def test_hackathon_interval_config():
    import os
    from unittest.mock import patch
    from Discord.scheduler import get_post_interval_seconds
    
    with patch.dict(os.environ, {"POST_INTERVAL_HOURS": "2.5"}):
        assert get_post_interval_seconds() == 9000.0
    
    with patch.dict(os.environ, {}, clear=True):
        assert get_post_interval_seconds() == 18000.0

def test_hackathon_scheduler_cycle():
    from unittest.mock import patch, MagicMock
    from Discord.scheduler import run_hackathon_cycle
    
    with patch("Discord.scheduler.build_hackathon_graph") as mock_build:
        mock_app = MagicMock()
        mock_app.invoke.return_value = {
            "status": "published",
            "history_topics": ["MVP Architecture"]
        }
        mock_build.return_value = mock_app
        
        result = run_hackathon_cycle(history_topics=[])
        assert result["status"] == "published"
        assert mock_app.invoke.called



