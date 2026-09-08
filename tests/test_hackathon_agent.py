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

