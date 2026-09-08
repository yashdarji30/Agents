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



