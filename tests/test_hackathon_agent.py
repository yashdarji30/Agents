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
