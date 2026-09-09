from typing import Dict, Any

def GET_TUTORIAL_CATALOG() -> Dict[str, Dict[str, Any]]:
    return {
        "State & Schema": {
            "title": "1. Understanding AgentState & Reducers",
            "description": "State in LangGraph defines the shared data structure passed between nodes. Utilizing TypedDict and Annotated[list, add_messages] ensures messages append smoothly rather than overwrite.",
            "code": """from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # add_messages is a reducer function that appends new messages to history
    messages: Annotated[list[AnyMessage], add_messages]
    research_topic: str
    status: str
"""
        },
        "Nodes & Edges": {
            "title": "2. Defining Graph Nodes & Control Flow Edges",
            "description": "Nodes are Python functions that receive current state and return state updates. Edges dictate transition routes (normal edges or conditional routing functions).",
            "code": """from langgraph.graph import StateGraph, START, END

def chatbot_node(state: AgentState):
    # Process state and call LLM
    return {"messages": [response]}

workflow = StateGraph(AgentState)
workflow.add_node("chatbot", chatbot_node)
workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", END)
app = workflow.compile()
"""
        },
        "Tool Integration": {
            "title": "3. Binding Tools & ToolNode Execution",
            "description": "LangGraph prebuilt ToolNode automatically executes tool calls requested by an LLM, returning ToolMessage objects back into state.",
            "code": """from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition

@tool
def calculate_square(n: int) -> int:
    return n * n

tools = [calculate_square]
llm_with_tools = llm.bind_tools(tools)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")
"""
        },
        "Checkpointer Memory": {
            "title": "4. Persistence & Conversation Memory",
            "description": "MemorySaver enables session threads and checkpointing state history across interactive turns.",
            "code": """from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Invoke with thread configuration
config = {"configurable": {"thread_id": "session_abc123"}}
response = app.invoke({"messages": [HumanMessage(content="My name is Yash")]}, config=config)
"""
        }
    }
