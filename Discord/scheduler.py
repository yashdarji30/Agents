import time
import os
import argparse
from typing import List, Optional
from dotenv import load_dotenv
from agent.hackathon_graph import build_hackathon_graph

def get_post_interval_seconds(custom_hours: Optional[float] = None) -> float:
    if custom_hours is not None:
        return float(custom_hours) * 3600.0
    env_val = os.getenv("POST_INTERVAL_HOURS")
    if env_val:
        try:
            return float(env_val) * 3600.0
        except ValueError:
            pass
    return 18000.0  # Default: 5 hours (18000 seconds)

def run_hackathon_cycle(history_topics: Optional[List[str]] = None) -> dict:
    load_dotenv()
    print("\n[Hackathon Scheduler]: Starting execution cycle...")
    app = build_hackathon_graph()
    
    initial_state = {
        "messages": [],
        "history_topics": history_topics or [],
        "current_post": None,
        "status": "started",
        "error": None
    }
    
    final_state = app.invoke(initial_state)
    print(f"[Hackathon Scheduler]: Cycle complete. Status: {final_state.get('status')}")
    return final_state

def start_scheduler(interval_hours: Optional[float] = None):
    load_dotenv()
    interval_seconds = get_post_interval_seconds(interval_hours)
    hours = interval_seconds / 3600.0
    print(f"=== Hackathon Assistant Scheduler Started ===")
    print(f"Interval: Every {hours:.2f} hours ({interval_seconds:.0f} seconds)")
    history_topics = []
    
    try:
        while True:
            final_state = run_hackathon_cycle(history_topics=history_topics)
            history_topics = final_state.get("history_topics", history_topics)
            print(f"Waiting {hours:.2f} hours ({interval_seconds:.0f}s) until next cycle...\n")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n[Hackathon Scheduler]: Stopped by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hackathon Assistant Scheduler")
    parser.add_argument("--interval-hours", type=float, help="Override posting interval in hours")
    args = parser.parse_args()
    start_scheduler(interval_hours=args.interval_hours)
