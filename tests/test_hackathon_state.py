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
