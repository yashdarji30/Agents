from typing import List, Optional, TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class MCQOption(BaseModel):
    label: str = Field(description="Option label (e.g., A, B, C, D)")
    text: str = Field(description="Option description")

class MCQuestion(BaseModel):
    question: str = Field(description="The multiple-choice question prompt")
    options: List[MCQOption] = Field(description="List of 4 options (A, B, C, D)")
    correct_option: str = Field(description="The correct option label (e.g., A, B, C, or D)")
    explanation: str = Field(description="Detailed explanation of why this option is correct")

class HackathonPost(BaseModel):
    title: str = Field(description="Catchy topic title for the hackathon post")
    category: str = Field(description="Category (e.g., Ideation & Scoping, MVP Architecture, Team Synergy & Git, Presentation & Pitching, Managing Sprint Time, API & Third-Party Integration)")
    strategy_tip: str = Field(description="Actionable strategic advice for hackathon success")
    actionable_checklist: List[str] = Field(description="3-4 step-by-step concrete tasks")
    mcqs: List[MCQuestion] = Field(description="1-2 interactive multiple-choice questions")

class HackathonAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    history_topics: List[str]
    current_post: Optional[HackathonPost]
    status: str
    error: Optional[str]
