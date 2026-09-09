import os
import uuid
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agent.graph import build_graph
from agent.tutorial_content import GET_TUTORIAL_CATALOG

# Helper function to extract plain text from string or list-of-dicts message content
def extract_text_content(content) -> str:
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        return "".join(text_parts)
    return str(content)

def render_mermaid(code: str, height: int = 340):
    html_code = f"""
    <div class="mermaid" style="display: flex; justify-content: center; background-color: transparent;">
    {code}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
    """
    components.html(html_code, height=height)

# Page configuration
st.set_page_config(
    page_title="LangGraph Research & AI Agent Studio",
    page_icon="🦜🔗",
    layout="wide"
)

# Custom CSS for polished aesthetic with high contrast
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #42A5F5;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #B0BEC5;
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
        background-color: #1e293b;
        color: #f1f5f9;
        border-left: 4px solid #42A5F5;
        padding: 12px;
        margin: 8px 0;
        border-radius: 6px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 0.9rem;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

load_dotenv()

# Available Gemini models
AVAILABLE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash"
]

# Initialize session state variables
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())[:8]

if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = "gemini-3.6-flash"

if "app_graph" not in st.session_state:
    st.session_state["app_graph"] = build_graph(st.session_state["selected_model"])

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
            st.session_state["app_graph"] = build_graph(st.session_state["selected_model"])
            st.rerun()

    st.divider()
    st.markdown("### 🤖 Model Selector")
    model_choice = st.selectbox(
        "Primary Model (Auto Fallbacks Enabled):",
        AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(st.session_state["selected_model"]) if st.session_state["selected_model"] in AVAILABLE_MODELS else 0
    )
    if model_choice != st.session_state["selected_model"]:
        st.session_state["selected_model"] = model_choice
        st.session_state["app_graph"] = build_graph(model_choice)
        st.success(f"Switched model to {model_choice}")

    st.divider()
    st.markdown("### 💬 Session Memory Manager")
    st.info(f"Current Thread ID: `{st.session_state['thread_id']}`")
    if st.button("🔄 New Session / Reset Memory"):
        st.session_state["thread_id"] = str(uuid.uuid4())[:8]
        st.session_state["messages_history"] = []
        st.session_state["trace_logs"] = []
        st.session_state["app_graph"] = build_graph(st.session_state["selected_model"])
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
        
        # Display existing message history with text extraction
        for msg in st.session_state["messages_history"]:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            with st.chat_message(role):
                st.markdown(extract_text_content(msg.content))
        
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
                
                try:
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
                                            content_str = extract_text_content(msg.content)
                                            st.write(f"📥 Tool Response received ({len(content_str)} chars)")
                                            trace_entry += f" -> Tool Response ({len(content_str)} chars)"
                                st.session_state["trace_logs"].append(trace_entry)
                        status_box.update(label="✅ Agent finished processing!", state="complete", expanded=False)
                    
                    # Fetch final state answer and render clean text
                    current_state = st.session_state["app_graph"].get_state(config)
                    if current_state.values and "messages" in current_state.values:
                        last_response = current_state.values["messages"][-1]
                        clean_answer = extract_text_content(last_response.content)
                        message_placeholder.markdown(clean_answer)
                        st.session_state["messages_history"].append(last_response)
                except Exception as ex:
                    err_text = str(ex)
                    if "429" in err_text or "RESOURCE_EXHAUSTED" in err_text:
                        st.error("⚠️ **API Quota Exceeded (429 Rate Limit)**: Gemini free tier request limit reached for the active model. Automatically attempting alternate models or please select another model in the sidebar.")
                    else:
                        st.error(f"⚠️ **Execution Error**: {err_text}")

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
    current_model = st.session_state.get("selected_model", "gemini-3.6-flash")
    render_mermaid(f"""
    graph TD
        START["START"] --> AgentNode["Agent Node ({current_model})"]
        AgentNode -->|"tools_condition: tool_calls present"| ToolNode["Tool Executor Node"]
        AgentNode -->|"tools_condition: final answer ready"| END["END"]
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
