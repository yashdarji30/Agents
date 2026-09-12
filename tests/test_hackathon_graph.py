import inspect
import pytest
from agent import hackathon_graph

def test_prompt_contains_architecture_diagram_requirement():
    source = inspect.getsource(hackathon_graph.content_generator_node)
    assert "8. Architecture Diagram (Optional)" in source
    assert "1. Title: High-impact, technical title." in source
    assert "7. Actionable Checklist: 3-5 concrete step-by-step execution items for the team." in source
