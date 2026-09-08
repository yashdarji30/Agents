import os
import requests
from typing import Optional, Dict, Any
from agent.hackathon_state import HackathonPost

def build_discord_embed_payload(post: HackathonPost) -> Dict[str, Any]:
    checklist_text = "\n".join([f"• {item}" for item in post.actionable_checklist])
    
    mcq_blocks = []
    for idx, q in enumerate(post.mcqs, 1):
        opts = "\n".join([f"**{opt.label}.** {opt.text}" for opt in q.options])
        spoiler_ans = f"||**Answer:** {q.correct_option} - {q.explanation}||"
        mcq_blocks.append(f"**Q{idx}: {q.question}**\n{opts}\n{spoiler_ans}")
    
    mcq_text = "\n\n".join(mcq_blocks)
    
    embed = {
        "title": f"🚀 Hackathon Prep: {post.title}",
        "description": f"**Category:** `{post.category}`",
        "color": 0x5865F2,  # Blurple color banner
        "fields": [
            {
                "name": "💡 Strategy Tip",
                "value": f"> {post.strategy_tip}",
                "inline": False
            },
            {
                "name": "📋 Actionable Checklist",
                "value": checklist_text,
                "inline": False
            },
            {
                "name": "❓ Quiz Time!",
                "value": mcq_text,
                "inline": False
            }
        ],
        "footer": {
            "text": "Hackathon Assistant AI Agent • Powered by LangGraph & Gemini"
        }
    }
    
    return {"embeds": [embed]}

def publish_to_discord(post: HackathonPost, webhook_url: Optional[str] = None) -> bool:
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        print("[Discord Publisher Error]: DISCORD_WEBHOOK_URL not configured.")
        return False
    
    payload = build_discord_embed_payload(post)
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"[Discord Publisher Success]: Published '{post.title}' to Discord.")
        return True
    except Exception as e:
        print(f"[Discord Publisher Error]: Failed to post to Discord: {e}")
        return False
