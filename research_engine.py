#!/usr/bin/env python3
"""
SMPF Research Engine — Auto Content Generation
Generates AI posts for active clients based on trending topics and client preferences.

Usage:
    python3 research_engine.py                    # Generate all pending posts
    python3 research_engine.py --topic "AI news"  # Generate for specific topic
    python3 research_engine.py --client 42        # Generate for specific client
    python3 research_engine.py --dry-run          # Preview without saving

Crontab (every 2 hours):
    0 */2 * * * cd /opt/smpfx && /opt/smpfx/venv/bin/python research_engine.py >> /var/log/smpf_research.log 2>&1
"""

import argparse
import json
import os
from dotenv import load_dotenv
load_dotenv()
import random
import requests
import sqlite3
import sys
from datetime import datetime, timedelta

# === Configuration ===
OR_API_KEY = os.getenv("OR_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
BACKEND_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "")
DATA_DIR = "/opt/smpfx/data"
DB_PATH = os.path.join(DATA_DIR, "smpf.db")

# === Simulated trending topics (replace with real APIs when integrated) ===
TRENDING_TOPICS = [
    {"topic": "OpenAI IPO and open-source AI regulation debate", "category": "technology", "source": "Business/Tech media"},
    {"topic": "South African energy crisis and load shedding updates", "category": "politics", "source": "Local news"},
    {"topic": "Bitcoin ETF approval and crypto market surge", "category": "finance", "source": "Financial media"},
    {"topic": "New AI regulation bill in US Congress", "category": "technology", "source": "Political news"},
    {"topic": "Springboks rugby World Cup preparation", "category": "sports", "source": "Sports media"},
    {"topic": "Global climate summit agreements", "category": "global", "source": "International news"},
    {"topic": "Local business startup funding rounds", "category": "business", "source": "Business news"},
    {"topic": "Faith-based community outreach programs", "category": "faith", "source": "Community news"},
]

# === Tone templates per archetype ===
ARCHETYPE_TONES = {
    "The Provocateur": "Bold, confrontational, calls out hypocrisy directly. Short punchy sentences.",
    "The Entertainer": "Witty, uses humor and memes. Relatable analogies. Light but insightful.",
    "The Analyst": "Data-driven, evidence-based, structured arguments. Facts and figures.",
    "The Leader": "Inspiring, visionary, rallying call to action. We can do this together.",
    "The Activist": "Passionate, urgent, uncompromising. Demands change now.",
    "The Diplomat": "Balanced, nuanced, sees all sides. Bridges divides with empathy.",
    "The Everyman": "Honest, relatable, down-to-earth. Like talking to a friend.",
}


def generate_post_text(topic, archetype, tone_desc, funny_serious=50, max_chars=280):
    """Generate a social media post using AI."""
    tone_info = ARCHETYPE_TONES.get(archetype, "Professional and balanced.")

    system_prompt = f"""You are a social media ghostwriter. Write in this voice:
Archetype: {archetype}
Tone: {tone_info}
Client description: {tone_desc}
Funny/serious balance: {funny_serious}% (0=serious, 100=funny)

Rules:
- Under {max_chars} characters
- Punchy, memorable, shareable
- 1-2 relevant hashtags
- No corporate buzzwords
- Write like a human, not a press release"""

    user_prompt = f"Write a post about: {topic['topic']}. Context: {topic['source']}. Category: {topic['category']}."

    # Try Groq first
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.8
            },
            timeout=30
        )
        data = resp.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    # Fallback to OpenRouter
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OR_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "meta-llama/llama-3.1-70b-instruct",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.8
            },
            timeout=30
        )
        data = resp.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return None


def generate_meme_image(topic):
    """Generate a meme image using Pollinations."""
    prompt = f"Meme about {topic['topic']}. Bold text overlay. Satirical viral style. No watermark."
    encoded = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={random.randint(1,9999)}"

    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            filename = f"/opt/smpfx/data/generated_images/research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, "wb") as f:
                f.write(resp.content)
            return filename
    except Exception:
        pass
    return None


def get_active_clients():
    """Fetch active clients from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, email, business_name, archetype, tone_description, 
               target_country, topics_json, package_slug, funny_serious_slider
        FROM clients 
        WHERE status = 'active'
    """)

    clients = []
    for row in cursor.fetchall():
        clients.append(dict(row))

    conn.close()
    return clients


def save_to_queue(client_id, post_text, image_path, platforms, topic, dry_run=False):
    """Save generated post to the approval queue."""
    if dry_run:
        print(f"  [DRY RUN] Would queue: {post_text[:80]}...")
        return True

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    approval_token = os.urandom(32).hex()
    preview_token = os.urandom(32).hex()

    cursor.execute("""
        INSERT INTO post_queue 
        (client_id, post_text, post_image_url, platforms_json, topic, status, 
         approval_token, preview_token, source, created_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, 'research', ?)
    """, (
        client_id, post_text, image_path, json.dumps(platforms), 
        topic, approval_token, preview_token, datetime.now()
    ))

    conn.commit()
    conn.close()
    return True


def post_directly(client_id, post_text, platforms):
    """Post directly to platforms (for testing or full-auto clients)."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/client/post",
            headers={"x-smpf-api-key": API_KEY, "Content-Type": "application/json"},
            json={"client_id": client_id, "text": post_text, "platforms": platforms},
            timeout=30
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="SMPF Research Engine")
    parser.add_argument("--topic", help="Specific topic to generate about")
    parser.add_argument("--client", type=int, help="Specific client ID to generate for")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument("--auto-post", action="store_true", help="Post directly (skip approval)")
    args = parser.parse_args()

    print("="*60)
    print("SMPF Research Engine")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Get clients
    clients = get_active_clients()
    if args.client:
        clients = [c for c in clients if c["id"] == args.client]

    if not clients:
        print("No active clients found.")
        return

    print(f"Found {len(clients)} active client(s)\n")

    # Select topic
    if args.topic:
        topic = {"topic": args.topic, "category": "custom", "source": "Manual"}
    else:
        topic = random.choice(TRENDING_TOPICS)

    print(f"Selected topic: {topic['topic']} ({topic['source']})\n")

    total_generated = 0
    total_posted = 0

    for client in clients:
        print(f"Client: {client['business_name']} ({client['archetype']})")

        # Generate post
        post_text = generate_post_text(
            topic, 
            client["archetype"], 
            client.get("tone_description", ""),
            client.get("funny_serious_slider", 50)
        )

        if not post_text:
            print("  ❌ Failed to generate post\n")
            continue

        print(f"  ✅ Post: {post_text[:100]}...")

        # Generate image (50% chance)
        image_path = None
        if random.random() < 0.5:
            image_path = generate_meme_image(topic)
            if image_path:
                print(f"  🖼️  Image: {image_path}")

        # Determine platforms from package
        package = client.get("package_slug", "starter")
        platforms = ["x"]  # Default, would expand based on connected tokens

        if args.auto_post:
            result = post_directly(client["id"], post_text, platforms)
            print(f"  📤 Auto-posted: {result}")
            total_posted += 1
        else:
            save_to_queue(client["id"], post_text, image_path, platforms, topic["topic"], args.dry_run)
            print(f"  📋 Queued for approval")
            total_generated += 1

        print()

    print("="*60)
    print(f"Summary: {total_generated} queued, {total_posted} auto-posted")
    print("="*60)


if __name__ == "__main__":
    main()
