import time
import os
import json
import argparse
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from agent.hackathon_graph import build_hackathon_graph

CONFIG_FILE_PATH = "config.json"

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Config Loader Warning]: Failed to parse '{CONFIG_FILE_PATH}': {e}")
    return {}

def get_post_interval_seconds(custom_hours: Optional[float] = None, custom_minutes: Optional[float] = None) -> float:
    # 1. CLI / explicit arguments take highest priority
    if custom_minutes is not None:
        return float(custom_minutes) * 60.0
    if custom_hours is not None:
        return float(custom_hours) * 3600.0
        
    # 2. Check .env environment variable
    env_mins = os.getenv("POST_INTERVAL_MINUTES")
    if env_mins:
        try:
            return float(env_mins) * 60.0
        except ValueError:
            pass
            
    env_hours = os.getenv("POST_INTERVAL_HOURS")
    if env_hours:
        try:
            return float(env_hours) * 3600.0
        except ValueError:
            pass

    # 3. Check config.json values
    cfg = load_config()
    cfg_mins = cfg.get("post_interval_minutes")
    if cfg_mins is not None:
        try:
            return float(cfg_mins) * 60.0
        except ValueError:
            pass
            
    cfg_hours = cfg.get("post_interval_hours")
    if cfg_hours is not None:
        try:
            return float(cfg_hours) * 3600.0
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

def start_scheduler(interval_hours: Optional[float] = None, interval_minutes: Optional[float] = None, max_runs: Optional[int] = None):
    load_dotenv()
    cfg = load_config()
    
    effective_max_runs = max_runs if max_runs is not None else cfg.get("max_runs")
    interval_seconds = get_post_interval_seconds(custom_hours=interval_hours, custom_minutes=interval_minutes)
    
    minutes = interval_seconds / 60.0
    hours = interval_seconds / 3600.0
    
    print(f"=== Hackathon Assistant Scheduler Started ===")
    if minutes < 60:
        print(f"Interval: Every {minutes:.1f} minutes ({interval_seconds:.0f} seconds)")
    else:
        print(f"Interval: Every {hours:.2f} hours ({interval_seconds:.0f} seconds)")
        
    if effective_max_runs:
        print(f"Max runs configured: {effective_max_runs} run(s) total")
        
    history_topics = []
    run_count = 0
    
    try:
        while True:
            run_count += 1
            print(f"\n--- [Run {run_count}{f' of {effective_max_runs}' if effective_max_runs else ''}] ---")
            final_state = run_hackathon_cycle(history_topics=history_topics)
            history_topics = final_state.get("history_topics", history_topics)
            
            if effective_max_runs and run_count >= effective_max_runs:
                print(f"\n[Hackathon Scheduler]: Reached target run limit ({effective_max_runs} runs). Scheduler finished!")
                break
                
            if minutes < 60:
                print(f"Waiting {minutes:.1f} minutes ({interval_seconds:.0f}s) until next cycle...")
            else:
                print(f"Waiting {hours:.2f} hours ({interval_seconds:.0f}s) until next cycle...")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n[Hackathon Scheduler]: Stopped by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hackathon Assistant Scheduler")
    parser.add_argument("--interval-hours", type=float, help="Override posting interval in hours")
    parser.add_argument("--interval-minutes", type=float, help="Override posting interval in minutes")
    parser.add_argument("--max-runs", type=int, help="Maximum number of posting cycles before stopping")
    args = parser.parse_args()
    start_scheduler(interval_hours=args.interval_hours, interval_minutes=args.interval_minutes, max_runs=args.max_runs)
