import os
import requests
from typing import Optional, Dict, Any
from agent.hackathon_state import HackathonPost

ARCHETYPE_COLORS = {
    "Technical Defense Guide": 0x2980B9,  # Cobalt Blue
    "Case Study Walkthrough": 0x27AE60,   # Emerald Green
    "Reviewer Cheat Sheet": 0x8E44AD      # Vivid Purple
}

import base64

def generate_mermaid_image_url(mermaid_code: Optional[str]) -> Optional[str]:
    if not mermaid_code or not mermaid_code.strip():
        return None
    try:
        clean_code = mermaid_code.strip()
        encoded = base64.b64encode(clean_code.encode('utf-8')).decode('utf-8')
        return f"https://mermaid.ink/img/{encoded}"
    except Exception as e:
        print(f"[Mermaid Encoder Warning]: Failed to encode diagram: {e}")
        return None

def build_discord_embed_payload(post: HackathonPost) -> Dict[str, Any]:
    color = ARCHETYPE_COLORS.get(post.post_type, 0x5865F2)
    
    description_parts = []
    description_parts.append(f"**Category:** `{post.category}`")
    description_parts.append(f"**Post Type:** `{post.post_type}`\n")
    description_parts.append(f"> **💡 Judge's Lens:**\n> {post.judge_perspective}\n")
    description_parts.append(f"### ⚡ Technical Deep Dive\n{post.deep_dive_content}")
    
    full_description = "\n".join(description_parts)
    if len(full_description) > 3900:
        full_description = full_description[:3900] + "\n\n*(Content truncated for Discord limit)*"
        
    qa_text_items = []
    for i, qa in enumerate(post.reviewer_qa_pairs, 1):
        qa_block = (
            f"**Q{i}: {qa.question}**\n"
            f"||**Winning Answer:** {qa.winning_answer}||"
        )
        qa_text_items.append(qa_block)
    qa_value = "\n\n".join(qa_text_items) if qa_text_items else "No Q&A generated."
    if len(qa_value) > 1024:
        qa_value = qa_value[:1000] + "...||"

    checklist_items = [f"- [ ] {item}" for item in post.actionable_checklist]
    checklist_value = "\n".join(checklist_items) if checklist_items else "No tasks specified."
    if len(checklist_value) > 1024:
        checklist_value = checklist_value[:1000] + "..."

    embed = {
        "title": f"🚀 [{post.post_type}] {post.title}",
        "description": full_description,
        "color": color,
        "fields": [
            {
                "name": "🎯 Reviewer Interrogation & Winning Answers",
                "value": qa_value,
                "inline": False
            },
            {
                "name": "📋 Actionable Execution Checklist",
                "value": checklist_value,
                "inline": False
            }
        ],
        "footer": {
            "text": "PERN Hackathon Mentor AI Agent • Powered by Gemini 3.6 Flash"
        }
    }

    if getattr(post, "architecture_diagram", None):
        image_url = generate_mermaid_image_url(post.architecture_diagram)
        if image_url:
            embed["image"] = {"url": image_url}
    
    return {
        "content": "@everyone 🚀 **New Hackathon Insights & Guide Posted!**",
        "embeds": [embed]
    }

def publish_to_discord(post: HackathonPost, webhook_url: Optional[str] = None) -> bool:
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        print("[Discord Webhook Error]: DISCORD_WEBHOOK_URL environment variable is missing.")
        return False
        
    payload = build_discord_embed_payload(post)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            print(f"[Discord Webhook Success]: Post '{post.title}' published successfully.")
            return True
        else:
            print(f"[Discord Webhook Error]: HTTP {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[Discord Webhook Exception]: Failed to publish to Discord: {e}")
        return False
