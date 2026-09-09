import os
import pytest
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent.graph import build_graph

def test_graph_initialization():
    load_dotenv()
    app = build_graph()
    assert app is not None

def test_graph_invocation():
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not configured")
    app = build_graph()
    config = {"configurable": {"thread_id": "test_thread_1"}}
    inputs = {
        "messages": [HumanMessage(content="What is LangGraph?")],
        "research_topic": "LangGraph overview",
        "status": "started"
    }
    try:
        output = app.invoke(inputs, config=config)
        assert len(output["messages"]) > 1
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            pytest.skip(f"Skipping test due to API rate limit: {e}")
        else:
            raise e
