from langchain_core.messages import HumanMessage
from agent.state import AgentState

def test_agent_state_structure():
    state: AgentState = {
        "messages": [HumanMessage(content="Hello")],
        "research_topic": "LangGraph tutorial",
        "status": "idle"
    }
    assert state["research_topic"] == "LangGraph tutorial"
    assert state["status"] == "idle"
    assert len(state["messages"]) == 1
    assert state["messages"][0].content == "Hello"
