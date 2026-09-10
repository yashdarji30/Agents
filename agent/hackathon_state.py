from typing import List, Optional, TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class ReviewerQA(BaseModel):
    question: str = Field(description="The tough technical question asked by a hackathon judge or reviewer")
    winning_answer: str = Field(description="The precise technical defense, architectural trade-off, and winning answer")

class HackathonPost(BaseModel):
    title: str = Field(description="Catchy, high-impact technical title")
    post_type: str = Field(description="Type of post: 'Technical Defense Guide', 'Case Study Walkthrough', or 'Reviewer Cheat Sheet'")
    category: str = Field(description="Target category (e.g. PostgreSQL Schema & Index Optimization, Express API Architecture & Middleware Defense, React State & Render Performance, Node.js Async Architecture, Judge Interrogation & Problem Statement Defense, Full-Stack System Design & Edge Cases)")
    judge_perspective: str = Field(description="Insights into what judges test, measure, and critique regarding this topic")
    deep_dive_content: str = Field(description="Comprehensive markdown content with real code/schema snippets in SQL, Express, React, or Node")
    reviewer_qa_pairs: List[ReviewerQA] = Field(description="2-3 tough reviewer questions paired with winning technical answers")
    actionable_checklist: List[str] = Field(description="3-5 concrete step-by-step technical execution items")

class HackathonAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    history_topics: List[str]
    history_archetypes: List[str]
    current_post: Optional[HackathonPost]
    status: str
    error: Optional[str]
