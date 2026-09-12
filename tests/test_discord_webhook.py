import base64
import pytest
from Discord.webhook import generate_mermaid_image_url, build_discord_embed_payload
from agent.hackathon_state import HackathonPost, ReviewerQA

def test_generate_mermaid_image_url():
    assert generate_mermaid_image_url(None) is None
    assert generate_mermaid_image_url("") is None
    assert generate_mermaid_image_url("   ") is None
    
    diagram = "flowchart TD\n  A --> B"
    url = generate_mermaid_image_url(diagram)
    assert url is not None
    assert url.startswith("https://mermaid.ink/img/")
    
    # Verify base64 content
    encoded_part = url.replace("https://mermaid.ink/img/", "")
    decoded = base64.b64encode(diagram.encode('utf-8')).decode('utf-8')
    assert encoded_part == decoded

def test_build_discord_embed_payload_with_image():
    qa = ReviewerQA(question="Q", winning_answer="A")
    post_with_diagram = HackathonPost(
        title="System Design",
        post_type="Technical Defense Guide",
        category="Full-Stack System Design & Edge Case Handling",
        judge_perspective="Perspective",
        deep_dive_content="Content",
        reviewer_qa_pairs=[qa],
        actionable_checklist=["Task 1"],
        architecture_diagram="flowchart TD\n  React --> Express"
    )
    
    payload = build_discord_embed_payload(post_with_diagram)
    embed = payload["embeds"][0]
    assert "image" in embed
    assert embed["image"]["url"].startswith("https://mermaid.ink/img/")

def test_build_discord_embed_payload_without_image():
    qa = ReviewerQA(question="Q", winning_answer="A")
    post_no_diagram = HackathonPost(
        title="System Design",
        post_type="Technical Defense Guide",
        category="Full-Stack System Design & Edge Case Handling",
        judge_perspective="Perspective",
        deep_dive_content="Content",
        reviewer_qa_pairs=[qa],
        actionable_checklist=["Task 1"],
        architecture_diagram=None
    )
    
    payload = build_discord_embed_payload(post_no_diagram)
    embed = payload["embeds"][0]
    assert "image" not in embed
