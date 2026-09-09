# LangGraph Research & AI Agent Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dual-purpose LangGraph research agent application with web search capabilities and an interactive Streamlit multi-tab studio dashboard.

**Architecture:** LangGraph graph engine (`AgentState`, `web_search`/`fetch_web_page`/`evaluate_python_code` tools, `agent_node` with Gemini model binding, `ToolNode`, `tools_condition`, and `MemorySaver`) exposed via CLI (`main.py`) and multi-tab Streamlit dashboard (`app.py`).

**Tech Stack:** Python 3.10+, LangGraph (`langgraph`, `langgraph-checkpoint`), LangChain Google GenAI (`langchain-google-genai`), DuckDuckGo Search (`duckduckgo-search`), BeautifulSoup4 (`bs4`), Streamlit (`streamlit`), python-dotenv.

## Global Constraints
- Target Gemini model: `gemini-2.5-flash` (with fallback handling for model config).
- Directory structure strictly matching design spec: `agent/` package (`state.py`, `tools.py`, `graph.py`, `tutorial_content.py`), `app.py`, `main.py`, `requirements.txt`.
- Code must adhere to TDD where applicable, exact file paths, zero vague placeholders.

---

### Task 1: Environment & Dependency Setup

**Files:**
- Create: `requirements.txt`
- Modify: `.env`
- Create: `tests/test_env.py`

**Interfaces:**
- Consumes: `GOOGLE_API_KEY` from `.env`
- Produces: Installed virtual environment packages, verified Gemini connection

- [ ] **Step 1: Create `requirements.txt`**

```text
langchain>=0.3.0
langchain-core>=0.3.0
langchain-google-genai>=2.0.0
langgraph>=0.2.0
langgraph-checkpoint>=2.0.0
streamlit>=1.35.0
duckduckgo-search>=6.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Install dependencies into virtual environment**

Run: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
Expected: Successfully installed packages without conflicts.

- [ ] **Step 3: Create `tests/test_env.py` to verify API key and model import**

```python
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def test_api_key_and_model():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    assert api_key is not None and len(api_key) > 0, "GOOGLE_API_KEY not found in environment"
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    assert llm.model == "gemini-2.5-flash"
```

- [ ] **Step 4: Run environment test**

Run: `.\.venv\Scripts\pytest.exe tests/test_env.py -v`
Expected: PASS

- [ ] **Step 5: Commit task changes**

```bash
git add requirements.txt tests/test_env.py
git commit -m "chore: set up requirements and environment verification test"
```

---

### Task 2: Agent State Definition (`agent/state.py`)

**Files:**
- Create: `agent/__init__.py`
- Create: `agent/state.py`
- Create: `tests/test_state.py`

**Interfaces:**
- Consumes: `langchain_core.messages.AnyMessage`, `langgraph.graph.message.add_messages`
- Produces: `AgentState` TypedDict definition with `messages`, `research_topic`, `status`

- [ ] **Step 1: Write failing test `tests/test_state.py`**

```python
from langchain_core.messages import HumanMessage, AIMessage
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
```

- [ ] **Step 2: Run test to verify failure**

Run: `.\.venv\Scripts\pytest.exe tests/test_state.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agent'`

- [ ] **Step 3: Create `agent/__init__.py` and `agent/state.py`**

Create `agent/__init__.py`:
```python
# agent package initializer
```

Create `agent/state.py`:
```python
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    research_topic: str
    status: str
```

- [ ] **Step 4: Run test to verify pass**

Run: `.\.venv\Scripts\pytest.exe tests/test_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit state definition**

```bash
git add agent/__init__.py agent/state.py tests/test_state.py
git commit -m "feat: implement AgentState definition using TypedDict and add_messages reducer"
```

---

### Task 3: Research Tools Suite (`agent/tools.py`)

**Files:**
- Create: `agent/tools.py`
- Create: `tests/test_tools.py`

**Interfaces:**
- Consumes: `duckduckgo_search`, `requests`, `bs4`, `ast`
- Produces: `@tool web_search(query: str) -> str`, `@tool fetch_web_page(url: str) -> str`, `@tool evaluate_python_code(code: str) -> str`

- [ ] **Step 1: Write failing unit tests in `tests/test_tools.py`**

```python
from agent.tools import web_search, fetch_web_page, evaluate_python_code

def test_evaluate_python_code_valid():
    valid_code = "x = 10\ny = 20\nresult = x + y\nprint(result)"
    res = evaluate_python_code.invoke({"code": valid_code})
    assert "Syntax OK" in res

def test_evaluate_python_code_invalid():
    invalid_code = "def foo(:"
    res = evaluate_python_code.invoke({"code": invalid_code})
    assert "Syntax Error" in res or "Error" in res

def test_web_search_tool():
    res = web_search.invoke({"query": "LangGraph Python"})
    assert isinstance(res, str)
    assert len(res) > 0
```

- [ ] **Step 2: Run test to verify failure**

Run: `.\.venv\Scripts\pytest.exe tests/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agent.tools'`

- [ ] **Step 3: Implement `agent/tools.py`**

```python
import ast
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from duckduckgo_search import DDGS

@tool
def web_search(query: str) -> str:
    """Searches the web using DuckDuckGo to find documentation, guides, and technical information.
    
    Args:
        query: Search topic or keywords.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return f"No web search results found for query: '{query}'"
            formatted = []
            for idx, r in enumerate(results, 1):
                title = r.get("title", "No Title")
                body = r.get("body", "No Description")
                href = r.get("href", "#")
                formatted.append(f"[{idx}] {title}\nURL: {href}\nSnippet: {body}\n")
            return "\n---\n".join(formatted)
    except Exception as e:
        return f"Error executing web search: {str(e)}"

@tool
def fetch_web_page(url: str) -> str:
    """Fetches and extracts clean text content from a web page URL.
    
    Args:
        url: The web URL to inspect.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove script, style, and navigation tags
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
            
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)
        return cleaned_text[:3000] if len(cleaned_text) > 3000 else cleaned_text
    except Exception as e:
        return f"Error fetching web page at '{url}': {str(e)}"

@tool
def evaluate_python_code(code: str) -> str:
    """Parses and checks the syntax validity of a Python code snippet.
    
    Args:
        code: Python source code string.
    """
    try:
        ast.parse(code)
        return "Syntax OK: Code compiled and validated successfully."
    except SyntaxError as se:
        return f"Syntax Error on line {se.lineno}: {se.msg}"
    except Exception as e:
        return f"Validation Error: {str(e)}"
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.\.venv\Scripts\pytest.exe tests/test_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit tools module**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: implement web_search, fetch_web_page, and evaluate_python_code tools"
```

---

### Task 4: LangGraph Engine & Memory Checkpointer (`agent/graph.py`)

**Files:**
- Create: `agent/graph.py`
- Create: `tests/test_graph.py`

**Interfaces:**
- Consumes: `AgentState`, `web_search`, `fetch_web_page`, `evaluate_python_code`
- Produces: `build_graph()` returning a compiled `CompiledStateGraph` with `MemorySaver` checkpointer.

- [ ] **Step 1: Write failing unit test in `tests/test_graph.py`**

```python
import os
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
        return
    app = build_graph()
    config = {"configurable": {"thread_id": "test_thread_1"}}
    inputs = {
        "messages": [HumanMessage(content="What is LangGraph?")],
        "research_topic": "LangGraph overview",
        "status": "started"
    }
    output = app.invoke(inputs, config=config)
    assert len(output["messages"]) > 1
```

- [ ] **Step 2: Run test to verify failure**

Run: `.\.venv\Scripts\pytest.exe tests/test_graph.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agent.graph'`

- [ ] **Step 3: Implement `agent/graph.py`**

```python
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

def build_graph(model_name: str = "gemini-2.5-flash"):
    api_key = os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.2,
        streaming=True
    )
    tools = [web_search, fetch_web_page, evaluate_python_code]
    llm_with_tools = llm.bind_tools(tools)
    
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
```

- [ ] **Step 4: Run graph tests**

Run: `.\.venv\Scripts\pytest.exe tests/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit graph module**

```bash
git add agent/graph.py tests/test_graph.py
git commit -m "feat: implement LangGraph state graph with ToolNode, tools_condition, and MemorySaver"
```

---

### Task 5: Masterclass & Tutorial Content Catalog (`agent/tutorial_content.py`)

**Files:**
- Create: `agent/tutorial_content.py`
- Create: `tests/test_tutorial_content.py`

**Interfaces:**
- Consumes: Hardcoded masterclass guides and code snippets
- Produces: Dictionary catalog of tutorials for UI rendering in Streamlit Tab 3.

- [ ] **Step 1: Write failing unit test `tests/test_tutorial_content.py`**

```python
from agent.tutorial_content import GET_TUTORIAL_CATALOG

def test_tutorial_catalog_integrity():
    catalog = GET_TUTORIAL_CATALOG()
    assert "State & Schema" in catalog
    assert "Nodes & Edges" in catalog
    assert "Tool Integration" in catalog
    assert "Checkpointer Memory" in catalog
    for title, module in catalog.items():
        assert "description" in module
        assert "code" in module
```

- [ ] **Step 2: Run test to verify failure**

Run: `.\.venv\Scripts\pytest.exe tests/test_tutorial_content.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `agent/tutorial_content.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.\.venv\Scripts\pytest.exe tests/test_tutorial_content.py -v`
Expected: PASS

- [ ] **Step 5: Commit tutorial content module**

```bash
git add agent/tutorial_content.py tests/test_tutorial_content.py
git commit -m "feat: implement LangGraph masterclass content catalog"
```

---

### Task 6: CLI Runner & Verification Script (`main.py`)

**Files:**
- Modify: `main.py`
- Test: `.\.venv\Scripts\python.exe main.py`

**Interfaces:**
- Consumes: `agent.graph.build_graph()`
- Produces: Terminal execution trace and research response

- [ ] **Step 1: Update `main.py`**

```python
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent.graph import build_graph

def run_cli_research(prompt: str):
    load_dotenv()
    print(f"🚀 Initializing LangGraph Research Agent...")
    print(f"🔍 Research Topic: {prompt}\n")
    
    app = build_graph()
    config = {"configurable": {"thread_id": "cli_session_1"}}
    
    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "research_topic": prompt,
        "status": "started"
    }
    
    print("--- Graph Execution Trace ---")
    for event in app.stream(initial_state, config=config, stream_mode="updates"):
        for node_name, node_output in event.items():
            print(f"📌 Executed Node: [{node_name}]")
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"   🛠️ Tool Call Requested: {tc['name']} with args {tc['args']}")
                    elif msg.type == "tool":
                        print(f"   📥 Tool Execution Result snippet: {str(msg.content)[:150]}...")
    
    final_state = app.get_state(config)
    last_msg = final_state.values["messages"][-1]
    print("\n================ FINAL REPORT ================")
    print(last_msg.content)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Explain LangGraph StateGraph, MemorySaver checkpointers, and ToolNode with an example."
    run_cli_research(query)
```

- [ ] **Step 2: Run `main.py` verification**

Run: `.\.venv\Scripts\python.exe main.py "Briefly explain LangGraph"`
Expected: Output showing executed nodes `[agent]` and final response printed cleanly.

- [ ] **Step 3: Commit `main.py`**

```bash
git add main.py
git commit -m "feat: upgrade main.py to stream LangGraph execution trace and display research reports"
```

---

### Task 7: Streamlit Interactive Multi-Tab Dashboard (`app.py`)

**Files:**
- Create: `app.py`
- Test: `streamlit run app.py`

**Interfaces:**
- Consumes: `agent.graph.build_graph()`, `agent.tutorial_content.GET_TUTORIAL_CATALOG()`
- Produces: Interactive Web Interface with 3 Tabs & Sidebar Controls

- [ ] **Step 1: Implement `app.py`**

```python
import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agent.graph import build_graph
from agent.tutorial_content import GET_TUTORIAL_CATALOG

# Page configuration
st.set_page_config(
    page_title="LangGraph Research & AI Agent Studio",
    page_icon="🦜🔗",
    layout="wide"
)

# Custom CSS for polished aesthetic
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 1.1rem;
    }
    .trace-box {
        background-color: #f8f9fa;
        border-left: 4px solid #1E88E5;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

load_dotenv()

# Initialize session state variables
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())[:8]

if "app_graph" not in st.session_state:
    st.session_state["app_graph"] = build_graph()

if "messages_history" not in st.session_state:
    st.session_state["messages_history"] = []

if "trace_logs" not in st.session_state:
    st.session_state["trace_logs"] = []

# Sidebar Controls
with st.sidebar:
    st.image("https://img.icons8.com/color/96/network-graph.png", width=64)
    st.title("Studio Controls")
    
    # API Key check
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        st.success("✅ GOOGLE_API_KEY Configured")
    else:
        st.error("⚠️ GOOGLE_API_KEY missing in .env")
        user_key = st.text_input("Enter Gemini API Key:", type="password")
        if user_key:
            os.environ["GOOGLE_API_KEY"] = user_key
            st.session_state["app_graph"] = build_graph()
            st.rerun()

    st.divider()
    st.markdown("### 💬 Session Memory Manager")
    st.info(f"Current Thread ID: `{st.session_state['thread_id']}`")
    if st.button("🔄 New Session / Reset Memory"):
        st.session_state["thread_id"] = str(uuid.uuid4())[:8]
        st.session_state["messages_history"] = []
        st.session_state["trace_logs"] = []
        st.session_state["app_graph"] = build_graph()
        st.rerun()

    st.divider()
    st.markdown("### 🚀 Quick Research Prompts")
    quick_prompts = [
        "Explain LangGraph Checkpointers with examples",
        "Compare LangGraph vs AutoGen vs CrewAI",
        "Show a Runnable ToolNode Python code snippet",
        "How do subgraphs work in LangGraph?"
    ]
    selected_prompt = None
    for p in quick_prompts:
        if st.button(p, use_container_width=True):
            selected_prompt = p

# Main App Header
st.markdown("<div class='main-title'>🦜🔗 LangGraph Research & AI Agent Studio</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Autonomous research assistant & interactive graph architecture blueprint</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "💬 Research & Coding Assistant",
    "🔍 Graph Inspector & Trace",
    "📚 LangGraph Masterclass Guide"
])

# ----------------------------------------------------
# TAB 1: Chat Assistant & Live Trace
# ----------------------------------------------------
with tab1:
    col_chat, col_trace = st.columns([3, 2])
    
    with col_chat:
        st.markdown("#### Chat Conversation")
        
        # Display existing message history
        for msg in st.session_state["messages_history"]:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            with st.chat_message(role):
                st.markdown(msg.content)
        
        # Process input
        input_prompt = st.chat_input("Ask a research question or request a LangGraph code tutorial...")
        if selected_prompt:
            input_prompt = selected_prompt

        if input_prompt:
            human_msg = HumanMessage(content=input_prompt)
            st.session_state["messages_history"].append(human_msg)
            with st.chat_message("user"):
                st.markdown(input_prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                status_placeholder = st.empty()
                
                config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
                input_state = {
                    "messages": [human_msg],
                    "research_topic": input_prompt,
                    "status": "processing"
                }
                
                with status_placeholder.status("🤖 Agent thinking & invoking tools...", expanded=True) as status_box:
                    for event in st.session_state["app_graph"].stream(input_state, config=config, stream_mode="updates"):
                        for node_name, node_output in event.items():
                            trace_entry = f"Node executed: [{node_name}]"
                            st.write(f"⚙️ Executed **{node_name}** node")
                            
                            if "messages" in node_output:
                                for msg in node_output["messages"]:
                                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                                        for tc in msg.tool_calls:
                                            st.write(f"🛠️ Tool Call: `{tc['name']}`")
                                            trace_entry += f" -> Tool Call: {tc['name']}"
                                    elif msg.type == "tool":
                                        st.write(f"📥 Tool Response received ({len(msg.content)} chars)")
                                        trace_entry += f" -> Tool Response received"
                            st.session_state["trace_logs"].append(trace_entry)
                    status_box.update(label="✅ Agent finished processing!", state="complete", expanded=False)
                
                # Fetch final state answer
                current_state = st.session_state["app_graph"].get_state(config)
                last_response = current_state.values["messages"][-1]
                message_placeholder.markdown(last_response.content)
                st.session_state["messages_history"].append(last_response)

    with col_trace:
        st.markdown("#### Live Node Trace Logs")
        if not st.session_state["trace_logs"]:
            st.info("No trace events recorded yet. Run a prompt to see node execution flow.")
        else:
            for idx, log in enumerate(st.session_state["trace_logs"], 1):
                st.markdown(f"<div class='trace-box'><b>Step {idx}:</b> {log}</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 2: Graph Inspector & State Viewer
# ----------------------------------------------------
with tab2:
    st.markdown("### LangGraph Architecture Diagram")
    st.mermaid("""
    graph TD
        START([START]) --> AgentNode[Agent Node / Gemini 2.5 Flash]
        AgentNode -->|tools_condition: tool_calls present| ToolNode[Tool Executor Node]
        AgentNode -->|tools_condition: final answer ready| END([END])
        ToolNode --> AgentNode
    """)
    
    st.divider()
    st.markdown("### Live State & Checkpointer Inspector")
    config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
    state_snapshot = st.session_state["app_graph"].get_state(config)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Current State Values")
        if state_snapshot.values:
            st.json({
                "research_topic": state_snapshot.values.get("research_topic", ""),
                "status": state_snapshot.values.get("status", ""),
                "message_count": len(state_snapshot.values.get("messages", []))
            })
        else:
            st.info("State is currently uninitialized for this thread ID.")

    with col2:
        st.markdown("#### Next Pending Nodes")
        st.write(state_snapshot.next if state_snapshot.next else "None (Graph completed)")

# ----------------------------------------------------
# TAB 3: LangGraph Masterclass Guide
# ----------------------------------------------------
with tab3:
    st.markdown("### 📚 LangGraph Masterclass Interactive Tutorials")
    catalog = GET_TUTORIAL_CATALOG()
    
    for key, item in catalog.items():
        with st.expander(f"📘 {item['title']}", expanded=(key == "State & Schema")):
            st.markdown(item["description"])
            st.code(item["code"], language="python")
```

- [ ] **Step 2: Verify app syntax and imports**

Run: `.\.venv\Scripts\python.exe -m py_compile app.py`
Expected: Return status 0 (no syntax errors).

- [ ] **Step 3: Commit `app.py`**

```bash
git add app.py
git commit -m "feat: implement Streamlit multi-tab studio dashboard with live node trace and masterclass"
```

---

### Task 8: End-to-End Verification & Walkthrough

**Files:**
- Test all python files & tests in `tests/`
- Run Streamlit app check

- [ ] **Step 1: Execute full test suite**

Run: `.\.venv\Scripts\pytest.exe -v`
Expected: All tests pass.

- [ ] **Step 2: Run CLI verification**

Run: `.\.venv\Scripts\python.exe main.py "Explain LangGraph tools_condition"`
Expected: Complete trace and research output printed.

- [ ] **Step 3: Launch Streamlit server in non-blocking test mode**

Run: `.\.venv\Scripts\streamlit.exe run app.py --server.headless true`
Expected: Server starts cleanly without errors.
