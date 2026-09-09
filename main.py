import sys
import argparse
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent.graph import build_graph
from Discord.scheduler import run_hackathon_cycle, start_scheduler

# Configure stdout for UTF-8 on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_cli_research(prompt: str):
    load_dotenv()
    print(f"=== Initializing LangGraph Research Agent ===")
    print(f"Research Topic: {prompt}\n")
    
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
            print(f"[Node Executed]: [{node_name}]")
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"  -> Tool Call Requested: {tc['name']} with args {tc['args']}")
                    elif msg.type == "tool":
                        print(f"  <- Tool Result received ({len(str(msg.content))} chars)")
    
    final_state = app.get_state(config)
    last_msg = final_state.values["messages"][-1]
    print("\n================ FINAL REPORT ================")
    print(last_msg.content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LangGraph AI Assistant & Hackathon Auto-Poster")
    parser.add_argument("--hackathon-now", action="store_true", help="Trigger single hackathon generation and Discord post immediately")
    parser.add_argument("--hackathon-schedule", action="store_true", help="Run background continuous scheduler")
    parser.add_argument("--interval-hours", type=float, default=None, help="Post interval in hours when running scheduler")
    parser.add_argument("--interval-minutes", type=float, default=None, help="Post interval in minutes when running scheduler")
    parser.add_argument("--max-runs", type=int, default=None, help="Maximum number of posting runs before stopping")
    parser.add_argument("query", nargs="?", default=None, help="Research prompt for default agent")
    
    args, unknown = parser.parse_known_args()
    
    if args.hackathon_now:
        print("=== Triggering Immediate Hackathon Agent Post ===")
        run_hackathon_cycle()
    elif args.hackathon_schedule:
        start_scheduler(
            interval_hours=args.interval_hours,
            interval_minutes=args.interval_minutes,
            max_runs=args.max_runs
        )
    else:
        query_text = args.query or "Explain LangGraph StateGraph, MemorySaver checkpointers, and ToolNode with an example."
        run_cli_research(query_text)