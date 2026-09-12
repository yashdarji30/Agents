import os
import random
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from agent.hackathon_state import HackathonAgentState, HackathonPost
from agent.db import get_posted_history, save_post_history, DEFAULT_DB_PATH
from Discord.webhook import publish_to_discord

HACKATHON_CATEGORIES = [
    "PostgreSQL Schema & Index Optimization",
    "Express API Architecture & Middleware Defense",
    "React State & Render Performance",
    "Node.js Async Architecture & Event Loop",
    "Judge Interrogation & Problem Statement Defense",
    "Full-Stack System Design & Edge Case Handling"
]

HACKATHON_ARCHETYPES = [
    "Technical Defense Guide",
    "Case Study Walkthrough",
    "Reviewer Cheat Sheet"
]

def topic_curator_node(state: HackathonAgentState) -> Dict[str, Any]:
    topic_history = state.get("history_topics", [])
    archetype_history = state.get("history_archetypes", [])
    db_path = state.get("db_path") or DEFAULT_DB_PATH

    # Fetch existing history from SQLite database
    db_topics, db_archetypes = get_posted_history(db_path=db_path)

    combined_topics = list(set(list(topic_history) + list(db_topics)))
    combined_archetypes = list(set(list(archetype_history) + list(db_archetypes)))

    available_topics = [c for c in HACKATHON_CATEGORIES if c not in combined_topics]
    if not available_topics:
        available_topics = HACKATHON_CATEGORIES
        topic_history = []

    available_archetypes = [a for a in HACKATHON_ARCHETYPES if a not in combined_archetypes]
    if not available_archetypes:
        available_archetypes = HACKATHON_ARCHETYPES
        archetype_history = []

    selected_category = random.choice(available_topics)
    selected_archetype = random.choice(available_archetypes)

    return {
        "history_topics": list(topic_history) + [selected_category],
        "history_archetypes": list(archetype_history) + [selected_archetype],
        "status": "topic_curated"
    }

def get_api_keys() -> List[str]:
    raw_keys = os.getenv("GOOGLE_API_KEYS", "")
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    for var in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_1", "GOOGLE_API_KEY_2", "GOOGLE_API_KEY_3"]:
        val = os.getenv(var)
        if val and val.strip() and val.strip() not in keys:
            keys.append(val.strip())
    return keys if keys else [None]

def content_generator_node(state: HackathonAgentState) -> Dict[str, Any]:
    api_keys = get_api_keys()
    current_category = state["history_topics"][-1]
    current_archetype = state.get("history_archetypes", ["Technical Defense Guide"])[-1]
    print(f"[Content Generator]: Generating hackathon post for category '{current_category}' [Archetype: '{current_archetype}'] (Active API Keys: {len(api_keys)})...")
    
    candidate_models = [
        "gemini-3.6-flash"
    ]

    llm_instances = []
    for key in api_keys:
        for m in candidate_models:
            llm_instances.append(
                ChatGoogleGenerativeAI(
                    model=m,
                    google_api_key=key,
                    max_retries=2
                ).with_structured_output(HackathonPost)
            )
    
    primary_llm = llm_instances[0]
    fallbacks = llm_instances[1:]
    if fallbacks:
        structured_llm = primary_llm.with_fallbacks(fallbacks, exceptions_to_handle=(Exception,))
    else:
        structured_llm = primary_llm
    
    system_prompt = (
        "You are a Principal Hackathon Judge, Veteran Technical Director, and PERN Stack Architect (PostgreSQL, Express.js, React, Node.js). "
        "Your mission is to provide deep-dive technical guidance, system architecture patterns, and defense strategies to help hackathon teams "
        "build rock-solid MVPs and effortlessly defend their tech stack when grilled by judges."
    )
    
    prompt = f"""Generate an in-depth hackathon technical post.

Post Archetype: {current_archetype}
Category Focus: {current_category}
Target Tech Stack: PostgreSQL, Express.js, React, Node.js (PERN Stack)

Requirements for Archetype '{current_archetype}':
1. Title: High-impact, technical title.
2. Category: {current_category}.
3. Post Type: {current_archetype}.
4. Judge Perspective: Detailed breakdown of what judges test, critique, and question regarding {current_category}.
5. Deep Dive Content: Lengthy, comprehensive technical markdown guide. Include actual code/schema snippets (e.g. SQL queries, Express middleware, React custom hooks) relevant to the PERN stack.
6. Reviewer QA Pairs: 2-3 tough questions a judge will ask about this topic/stack with bulletproof, winning answers.
7. Actionable Checklist: 3-5 concrete step-by-step execution items for the team.
"""
    
    try:
        post: HackathonPost = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ])
        print(f"[Content Generator Success]: Post '{post.title}' ({post.post_type}) generated successfully.")
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
        raise RuntimeError(f"Hackathon Agent cycle failed during content generation: {error_msg}")
    
    success = publish_to_discord(post)
    if success:
        db_path = state.get("db_path") or DEFAULT_DB_PATH
        try:
            save_post_history(
                category=post.category,
                archetype=post.post_type,
                title=post.title,
                db_path=db_path
            )
            print(f"[SQLite Persistence]: Saved published post '{post.title}' ({post.category} - {post.post_type}) to SQLite database.")
        except Exception as db_err:
            print(f"[SQLite Persistence Warning]: Failed to save post history: {db_err}")
            
        return {"status": "published"}
    else:
        raise RuntimeError("Discord publish failed: DISCORD_WEBHOOK_URL may be missing or invalid in environment/secrets.")


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
