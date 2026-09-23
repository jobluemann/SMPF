#!/usr/bin/env python3
"""
SMPF Research Engine v2  Client-Personalized Content Generation with Ground.News-style Bias Analysis

No hardcoded topics. Every client gets:
- Live news from RSS feeds matched to their interests/location
- Ground.News-style bias spectrum analysis (left/center/right coverage)
- Factuality scoring
- Personalized framing based on client's political leaning + archetype

Uses free AI only (OpenRouter free tier, Pollinations fallback)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, "/opt/smpfx")

from datetime import datetime, timezone
from research_sources import research_for_client, RSS_REGISTRY
from bias_analyzer import (
    load_bias_map, group_articles_by_topic, analyze_topic_group,
    generate_framing_prompt, filter_by_client_preference
)
from ai_generate import generate_text

DATA_DIR = "/opt/smpfx/data"
DB_PATH = os.path.join(DATA_DIR, "smpf.db")


def load_client_profile(client_id: int) -> dict:
    """Load client profile from DB or fallback."""
    if os.path.exists(DB_PATH):
        import sqlite3
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM smpf_clients WHERE id = ?", (client_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                return dict(row)
        except sqlite3.OperationalError:
            pass
    return None


def load_all_active_clients() -> list:
    if os.path.exists(DB_PATH):
        import sqlite3
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM smpf_clients WHERE status = 'active'")
            rows = cur.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            return []
    return []


def save_to_queue(client_id: int, post_text: str, article: dict, topic_analysis: dict, image_path: str = None, dry_run: bool = False):
    if dry_run:
        print(f"  [DRY RUN] Would queue for client {client_id}")
        return
    queue_file = os.path.join(DATA_DIR, "post_queue.jsonl")
    entry = {
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "client_id": client_id,
        "post_text": post_text,
        "source_article": article,
        "topic_analysis": topic_analysis,
        "image_path": image_path,
        "status": "pending_approval",
    }
    with open(queue_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  \u2705 Queued for approval")


def main():
    parser = argparse.ArgumentParser(description="SMPF Research Engine v2")
    parser.add_argument("--client", type=int, help="Generate for specific client ID")
    parser.add_argument("--topic", type=str, help="Override with manual topic keyword")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument("--sources", action="store_true", help="List available RSS sources")
    args = parser.parse_args()
    
    if args.sources:
        print("Available RSS sources:")
        for slug, url in RSS_REGISTRY.items():
            print(f"  {slug}: {url}")
        return
    
    print("=" * 70)
    print("SMPF Research Engine v2  Personalized + Ground.News-style Bias")
    print("=" * 70)
    
    # Load bias map
    bias_map = load_bias_map()
    print(f"\n\ud83d\udcca Loaded bias ratings for {len(bias_map)} sources")
    
    # Load clients
    if args.client:
        clients = [load_client_profile(args.client)]
    else:
        clients = load_all_active_clients()
    
    if not clients or not clients[0]:
        # Demo client = YOU (Rudi)
        clients = [{
            "id": 0,
            "business_name": "Rudi Oosthuizen (Demo)",
            "archetype": "The Analyst",
            "personality_json": json.dumps({"openness": 80, "conscientiousness": 70}),
            "topics_json": json.dumps(["Technology", "AI", "Business", "South Africa", "Politics"]),
            "target_country": "South Africa",
            "tone": "professional",
            "funny_serious_slider": 30,
            "political_spectrum": "centre-right",
            "industry": "Technology",
        }]
        print("No active clients in DB  using YOUR demo profile\n")
    
    total = 0
    for client in clients:
        if not client:
            continue
        print(f"\n\ud83d\udc64 Client: {client.get('business_name', 'Unknown')}")
        print(f"    Archetype: {client.get('archetype', 'Unknown')}")
        print(f"    Topics: {client.get('topics_json', '[]')}")
        print(f"    Country: {client.get('target_country', 'Global')}")
        print(f"    Political: {client.get('political_spectrum', 'Unknown')}")
        print(f"    Tone: {client.get('tone', 'neutral')} ({client.get('funny_serious_slider', 50)}/100 serious)")
        print()
        
        # 1. Fetch live articles
        print("\ud83d\udd0d Fetching live articles...")
        articles = research_for_client(client, max_items=20)
        print(f"    Found {len(articles)} raw articles")
        
        if not articles:
            print("    \u274c No articles found\n")
            continue
        
        # 2. Filter by client preference (bias boosting)
        print("\u2696\ufe0f  Filtering by client political preference + factuality...")
        filtered = filter_by_client_preference(articles, client, bias_map)
        print(f"    Top article scores: {[a['_bias_score'] for a in filtered[:3]]}")
        
        # 3. Group by topic for Ground.News-style analysis
        print("\ud83d\udcca Grouping by topic for bias analysis...")
        groups = group_articles_by_topic(filtered, min_overlap=2)
        print(f"    Formed {len(groups)} topic clusters")
        
        if not groups:
            # Fallback: use top single article
            best = filtered[0]
            groups = [{"headline": best["title"], "articles": [best], "topic_keywords": []}]
        
        # Pick the best group (most sources, best coverage)
        best_group = max(groups, key=lambda g: len(g["articles"]))
        
        # 4. Analyze bias spectrum
        analysis = analyze_topic_group(best_group["articles"], bias_map)
        print(f"\n    \ud83d\udcc8 BIAS ANALYSIS:")
        print(f"       Headline: {best_group['headline'][:70]}...")
        print(f"       Sources covering this: {analysis.get('total_sources', 0)}")
        print(f"       Spectrum: Left={analysis['spectrum'].get('left',0)+analysis['spectrum'].get('far-left',0)+analysis['spectrum'].get('centre-left',0)}, Centre={analysis['spectrum'].get('centre',0)}, Right={analysis['spectrum'].get('right',0)+analysis['spectrum'].get('far-right',0)+analysis['spectrum'].get('centre-right',0)}")
        print(f"       Overall lean: {analysis.get('overall_lean', 'unknown')}")
        print(f"       Factuality: {analysis.get('factuality', 0)}/10")
        print(f"       Coverage: {analysis.get('coverage', 'unknown')}")
        print(f"       Bias spread: {analysis.get('bias_spread', 0)}")
        print(f"       Source names: {', '.join(analysis.get('sources', [])[:5])}")
        
        # Pick the article that best matches client preference
        best_article = best_group["articles"][0]
        for a in best_group["articles"]:
            if a.get("_bias_score", 0) > best_article.get("_bias_score", 0):
                best_article = a
        
        print(f"\n    \u2705 Selected article: [{best_article.get('origin','')}] {best_article['title'][:60]}...")
        print(f"       Source: {best_article['source']} (bias score: {best_article.get('_bias_score',0)})")
        
        # 5. Generate framing prompt with Ground.News-style instructions
        prompt = generate_framing_prompt(client, analysis, best_article)
        
        # 6. Generate post with free AI
        print(f"\n    \u270d\ufe0f Generating post with free AI...")
        try:
            post_text = generate_text(prompt, max_tokens=500, temperature=0.7)
        except Exception as exc:
            print(f"    \u274c AI failed: {exc}")
            post_text = f"{best_article['title']}\n\nRead more: {best_article['url']}\n#news"
        
        print(f"\n    \ud83d\udcdd GENERATED POST:\n")
        for line in post_text.split("\n"):
            print(f"       {line}")
        print()
        
        # 7. Save to queue
        save_to_queue(client["id"], post_text, best_article, analysis, dry_run=args.dry_run)
        total += 1
        print()
    
    print("=" * 70)
    print(f"Summary: {total} post(s) generated")
    if args.dry_run:
        print("(DRY RUN \u2014 nothing saved)")
    print("=" * 70)


if __name__ == "__main__":
    main()
