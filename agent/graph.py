import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.tools import web_search, fetch_web_page, evaluate_python_code

SYSTEM_PROMPT = """You are an expert AI Research Assistant and Senior LangGraph Architect.
Your mission is to research topics thoroughly, consult documentation via web search when necessary, validate code snippets using python evaluation tools, and generate comprehensive, clear, and runnable tutorials.

Guidelines:
1. When asked about complex topics or technical documentation, use `web_search` and `fetch_web_page` to obtain factual, up-to-date details.
2. Before presenting Python code examples to the user, validate their syntax using `evaluate_python_code`.
3. Provide clear markdown formatting with title headers, bullet points, and code blocks.
"""

def create_agent_node(llm_with_tools):
    def agent_node(state: AgentState) -> Dict[str, Any]:
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = llm_with_tools.invoke(messages)
        return {
            "messages": [response],
            "status": "processing"
        }
    return agent_node

def build_graph(model_name: str = "gemini-3.6-flash"):
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY_1") or os.getenv("GOOGLE_API_KEY_2") or os.getenv("GOOGLE_API_KEY_3")
    tools = [web_search, fetch_web_page, evaluate_python_code]
    
    # Candidate Gemini models for automatic fallback resilience when 429 rate limits occur
    candidate_models = [
        "gemini-3.6-flash"
    ]
    
    # Put requested model first in order
    if model_name in candidate_models:
        candidate_models.remove(model_name)
    ordered_models = [model_name] + candidate_models
    
    bound_llms = []
    for m in ordered_models:
        bound_llms.append(
            ChatGoogleGenerativeAI(
                model=m,
                google_api_key=api_key,
                max_retries=1,
                streaming=True
            ).bind_tools(tools)
        )
    
    primary_llm = bound_llms[0]
    fallbacks = bound_llms[1:]
    
    # Smart fallback chain: automatically switch models if primary model hits rate limits or errors
    llm_with_tools = primary_llm.with_fallbacks(fallbacks, exceptions_to_handle=(Exception,))
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", create_agent_node(llm_with_tools))
    workflow.add_node("tools", ToolNode(tools))
    
    # Edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition, ["tools", END])
    workflow.add_edge("tools", "agent")
    
    # Checkpointer for conversation state memory
    memory = MemorySaver()
    compiled_app = workflow.compile(checkpointer=memory)
    return compiled_app
