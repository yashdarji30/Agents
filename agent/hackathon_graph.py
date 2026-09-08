import os
import random
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from agent.hackathon_state import HackathonAgentState, HackathonPost
from Discord.webhook import publish_to_discord

HACKATHON_CATEGORIES = [
    "Ideation & Scoping",
    "MVP Architecture",
    "Team Synergy & Git",
    "Presentation & Pitching",
    "Managing Sprint Time",
    "API & Third-Party Integration"
]

def topic_curator_node(state: HackathonAgentState) -> Dict[str, Any]:
    history = state.get("history_topics", [])
    available = [c for c in HACKATHON_CATEGORIES if c not in history]
    if not available:
        available = HACKATHON_CATEGORIES
        history = []
    
    selected_category = random.choice(available)
    updated_history = list(history) + [selected_category]
    
    return {
        "history_topics": updated_history,
        "status": "topic_curated"
    }

def content_generator_node(state: HackathonAgentState) -> Dict[str, Any]:
    api_key = os.getenv("GOOGLE_API_KEY")
    current_category = state["history_topics"][-1]
    print(f"[Content Generator]: Generating hackathon post for category '{current_category}'...")
    
    candidate_models = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.7-flash"
    ]


    
    llm_instances = [
        ChatGoogleGenerativeAI(
            model=m,
            google_api_key=api_key,
            max_retries=2
        ).with_structured_output(HackathonPost)
        for m in candidate_models
    ]
    
    primary_llm = llm_instances[0]
    fallbacks = llm_instances[1:]
    structured_llm = primary_llm.with_fallbacks(fallbacks, exceptions_to_handle=(Exception,))
    
    prompt = f"""You are a top hackathon mentor. Generate a high-value, practical hackathon preparation post for participants.
Category focus: {current_category}

Include:
1. A clear, catchy title.
2. The category ({current_category}).
3. A detailed, actionable strategy tip.
4. An actionable checklist of 3-4 steps.
5. 1-2 interactive multiple-choice questions with 4 options (A, B, C, D), correct answer, and explanation.
"""
    
    try:
        post: HackathonPost = structured_llm.invoke([
            SystemMessage(content="You generate structured hackathon advice."),
            HumanMessage(content=prompt)
        ])
        print(f"[Content Generator Success]: Post '{post.title}' generated successfully.")
        return {
            "current_post": post,
            "status": "content_generated"
        }
    except Exception as e:
        print(f"[Content Generator Error]: Failed to generate content: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def discord_publisher_node(state: HackathonAgentState) -> Dict[str, Any]:
    post = state.get("current_post")
    if not post:
        error_msg = state.get("error", "No current post generated")
        print(f"[Discord Publisher Skipped]: Skipping publish because no post is available. Cause: {error_msg}")
        return {"status": "publish_skipped", "error": error_msg}
    
    success = publish_to_discord(post)
    if success:
        return {"status": "published"}
    else:
        return {"status": "publish_failed", "error": "Discord publish call returned False"}


def build_hackathon_graph():
    workflow = StateGraph(HackathonAgentState)
    
    workflow.add_node("topic_curator", topic_curator_node)
    workflow.add_node("content_generator", content_generator_node)
    workflow.add_node("discord_publisher", discord_publisher_node)
    
    workflow.add_edge(START, "topic_curator")
    workflow.add_edge("topic_curator", "content_generator")
    workflow.add_edge("content_generator", "discord_publisher")
    workflow.add_edge("discord_publisher", END)
    
    return workflow.compile()
