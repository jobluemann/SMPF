"""SMPF Bias Analyzer  Ground.News-style coverage analysis, completely free.

Groups articles by topic, calculates:
- Coverage spectrum (how many Left/Center/Right sources covered it)
- Factuality score (weighted by source reputation)
- Bias spread (range from most-left to most-right source)
- Framing recommendations (how to write for a centre-right vs centre-left client)
"""
import json
import os
import re
from collections import defaultdict
from typing import List, Dict, Tuple
from datetime import datetime

DATA_DIR = "/opt/smpfx/data"
BIAS_MAP_PATH = os.path.join(DATA_DIR, "source_bias_map.json")


def load_bias_map() -> Dict:
    """Load source bias ratings."""
    if os.path.exists(BIAS_MAP_PATH):
        with open(BIAS_MAP_PATH, "r") as f:
            return json.load(f)
    return {}


def normalize_bias_score(bias: float) -> str:
    """Convert -2 to +2 score into label."""
    if bias <= -1.5: return "far-left"
    if bias <= -0.5: return "left"
    if bias <= 0.5: return "centre"
    if bias <= 1.5: return "right"
    return "far-right"


def extract_topic_keywords(title: str) -> set:
    """Extract topic keywords from a headline for grouping."""
    # Remove common stop words
    stop = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "shall", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their", "and", "but", "or", "nor", "so", "yet", "if", "because", "although", "though", "while", "where", "when", "after", "before", "until", "since", "than", "as", "from", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once", "here", "there", "all", "each", "few", "more", "most", "other", "some", "such", "no", "not", "only", "own", "same", "so", "than", "too", "very", "just", "now"}
    words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
    return set(w for w in words if w not in stop)


def group_articles_by_topic(articles: List[Dict], min_overlap: int = 2) -> List[Dict]:
    """Group articles that appear to be about the same topic."""
    groups = []
    used = set()
    
    for i, article in enumerate(articles):
        if i in used:
            continue
        title = article.get("title", "")
        keywords = extract_topic_keywords(title)
        if not keywords:
            continue
        
        group = [article]
        used.add(i)
        
        for j, other in enumerate(articles[i+1:], i+1):
            if j in used:
                continue
            other_keywords = extract_topic_keywords(other.get("title", ""))
            overlap = len(keywords & other_keywords)
            if overlap >= min_overlap:
                group.append(other)
                used.add(j)
        
        if len(group) >= 1:
            groups.append({
                "topic_keywords": list(keywords)[:5],
                "articles": group,
                "headline": article["title"],
            })
    
    return groups


def analyze_topic_group(group: List[Dict], bias_map: Dict) -> Dict:
    """Analyze a group of articles about the same topic."""
    if not group:
        return {}
    
    lean_counts = {"left": 0, "centre-left": 0, "centre": 0, "centre-right": 0, "right": 0, "far-left": 0, "far-right": 0, "unknown": 0}
    factuality_scores = []
    bias_scores = []
    sources = []
    
    for article in group:
        origin = article.get("origin", "")
        source_slug = None
        # Try to match article source to bias map
        source_name = article.get("source", "").lower()
        for slug, info in bias_map.items():
            if slug.startswith("_"):
                continue
            if info.get("name", "").lower() in source_name:
                source_slug = slug
                break
        
        if not source_slug:
            # Fallback: match by origin
            for slug, info in bias_map.items():
                if slug.startswith("_"):
                    continue
                if slug == origin or origin.startswith(slug):
                    source_slug = slug
                    break
        
        if source_slug and source_slug in bias_map:
            info = bias_map[source_slug]
            lean = info.get("lean", "unknown")
            lean_counts[lean] = lean_counts.get(lean, 0) + 1
            factuality_scores.append(info.get("factuality", 5))
            bias_scores.append(info.get("bias", 0))
            sources.append(info.get("name", source_slug))
        else:
            lean_counts["unknown"] = lean_counts.get("unknown", 0) + 1
    
    # Calculate spectrum
    total_known = sum(v for k, v in lean_counts.items() if k != "unknown")
    
    # Weighted factuality
    factuality = round(sum(factuality_scores) / len(factuality_scores), 1) if factuality_scores else 5.0
    
    # Bias spread
    bias_min = min(bias_scores) if bias_scores else 0
    bias_max = max(bias_scores) if bias_scores else 0
    bias_spread = round(bias_max - bias_min, 1)
    
    # Overall lean (weighted average)
    if bias_scores:
        avg_bias = round(sum(bias_scores) / len(bias_scores), 1)
        overall_lean = normalize_bias_score(avg_bias)
    else:
        overall_lean = "unknown"
    
    # Coverage rating (how many sides covered it)
    sides = 0
    if lean_counts.get("left", 0) + lean_counts.get("far-left", 0) + lean_counts.get("centre-left", 0) > 0:
        sides += 1
    if lean_counts.get("centre", 0) > 0:
        sides += 1
    if lean_counts.get("right", 0) + lean_counts.get("far-right", 0) + lean_counts.get("centre-right", 0) > 0:
        sides += 1
    
    coverage = "narrow"
    if sides >= 2:
        coverage = "balanced"
    if sides >= 3:
        coverage = "full-spectrum"
    if total_known <= 1:
        coverage = "single-source"
    
    return {
        "total_sources": total_known,
        "spectrum": lean_counts,
        "factuality": factuality,
        "bias_spread": bias_spread,
        "overall_lean": overall_lean,
        "coverage": coverage,
        "sides_covered": sides,
        "sources": list(set(sources)),
    }


def generate_framing_prompt(client_profile: Dict, topic_analysis: Dict, article: Dict) -> str:
    """Generate an AI prompt that instructs the model to frame the post according to:
    - Client's political leaning
    - The topic's actual bias spectrum (so we can acknowledge or counter it)
    - Client's archetype voice
    """
    archetype = client_profile.get("archetype", "The Analyst")
    client_lean = client_profile.get("political_spectrum", "centre").lower()
    tone = client_profile.get("tone", "professional")
    slider = client_profile.get("funny_serious_slider", 50)
    country = client_profile.get("target_country", "")
    
    # Archetype voices
    archetype_voices = {
        "The Provocateur": "Bold, contrarian, challenges conventional wisdom.",
        "The Entertainer": "Witty, humorous, uses pop culture references.",
        "The Analyst": "Data-driven, logical, cites facts and trends.",
        "The Leader": "Inspirational, visionary, uses 'we' language.",
        "The Activist": "Passionate, calls to action, highlights injustice or opportunity.",
        "The Diplomat": "Balanced, nuanced, presents multiple sides.",
        "The Everyman": "Relatable, conversational, simple language.",
    }
    voice = archetype_voices.get(archetype, archetype_voices["The Analyst"])
    
    # Framing instruction based on topic analysis + client preference
    topic_lean = topic_analysis.get("overall_lean", "centre")
    topic_spread = topic_analysis.get("bias_spread", 0)
    factuality = topic_analysis.get("factuality", 5)
    coverage = topic_analysis.get("coverage", "narrow")
    
    framing = f"""GROUND.NEWS-STYLE CONTENT FRAMING INSTRUCTIONS:

CLIENT PROFILE:
- Voice: {voice}
- Tone: {tone} (seriousness: {slider}/100)
- Client's political leaning: {client_lean}
- Target country: {country or "Global"}

TOPIC ANALYSIS (from our free bias analyzer):
- Overall media lean on this topic: {topic_lean}
- Bias spread across sources: {topic_spread} (0=same angle, 3+={topic_spread > 3 and 'widely different angles' or 'some variation'})
- Factuality of sources: {factuality}/10 ({factuality >= 7 and 'highly factual' or factuality >= 5 and 'mixed' or 'low factuality'})
- Coverage spectrum: {coverage} ({topic_analysis.get('sides_covered', 0)} of 3 sides: left/centre/right)
- Sources covering this: {', '.join(topic_analysis.get('sources', [])[:5])}

FRAMING RULES:
1. Write from a {client_lean} perspective, but DO NOT misrepresent facts.
2. If the topic has a strong lean opposite to the client, acknowledge the other side briefly then pivot to the client's view.
3. If factuality is low ({factuality < 6}), be cautious  use "reportedly," "claims suggest," or question framing.
4. If coverage is narrow (only one side covered it), the post should either:
   - Highlight that mainstream media is ignoring this angle, OR
   - Add nuance that readers won't get elsewhere
5. Match the client's voice exactly. {voice}
6. Max 280 chars for X, 500 for others.
7. Include 2-4 relevant hashtags.

ARTICLE TO BASE POST ON:
Title: {article['title']}
Source: {article['source']}
Summary: {article.get('summary', '')[:400]}

Write the post:"""
    
    return framing


def filter_by_client_preference(articles: List[Dict], client_profile: Dict, bias_map: Dict) -> List[Dict]:
    """Filter articles to match client's political preference + boost factuality."""
    client_lean = client_profile.get("political_spectrum", "").lower()
    
    # Bias preference mapping
    preference_boost = {
        "far-left": {"far-left": 3, "left": 2, "centre-left": 1, "centre": 0, "centre-right": -1, "right": -2, "far-right": -3},
        "left": {"far-left": 2, "left": 3, "centre-left": 2, "centre": 1, "centre-right": 0, "right": -1, "far-right": -2},
        "centre-left": {"far-left": 1, "left": 2, "centre-left": 3, "centre": 2, "centre-right": 1, "right": 0, "far-right": -1},
        "centre": {"far-left": 0, "left": 1, "centre-left": 2, "centre": 3, "centre-right": 2, "right": 1, "far-right": 0},
        "centre-right": {"far-left": -1, "left": 0, "centre-left": 1, "centre": 2, "centre-right": 3, "right": 2, "far-right": 1},
        "right": {"far-left": -2, "left": -1, "centre-left": 0, "centre": 1, "centre-right": 2, "right": 3, "far-right": 2},
        "far-right": {"far-left": -3, "left": -2, "centre-left": -1, "centre": 0, "centre-right": 1, "right": 2, "far-right": 3},
    }
    
    boost_map = preference_boost.get(client_lean, preference_boost["centre"])
    
    scored = []
    for article in articles:
        origin = article.get("origin", "")
        source_name = article.get("source", "").lower()
        
        # Match to bias map
        lean = "unknown"
        fact = 5
        for slug, info in bias_map.items():
            if slug.startswith("_"):
                continue
            if info.get("name", "").lower() in source_name or slug == origin:
                lean = info.get("lean", "unknown")
                fact = info.get("factuality", 5)
                break
        
        score = boost_map.get(lean, 0)
        # Boost high-factuality sources
        score += (fact - 5) * 0.3
        
        scored.append((score, article, lean, fact))
    
    # Sort by score descending
    scored.sort(key=lambda x: -x[0])
    
    # Return top articles with their bias metadata
    result = []
    for score, article, lean, fact in scored:
        article["_bias_score"] = round(score, 1)
        article["_source_lean"] = lean
        article["_source_factuality"] = fact
        result.append(article)
    
    return result


if __name__ == "__main__":
    # Test
    bias_map = load_bias_map()
    print(f"Loaded {len(bias_map)} source bias ratings")
    
    # Test grouping
    sample_articles = [
        {"title": "OpenAI IPO sparks debate over AI regulation", "source": "TechCrunch", "origin": "rss"},
        {"title": "OpenAI prepares for IPO while lobbying for stricter AI rules", "source": "MyBroadband", "origin": "rss"},
        {"title": "OpenAI's IPO and the irony of anti-open-source lobbying", "source": "Hacker News", "origin": "rss"},
        {"title": "Springboks win against All Blacks in thriller", "source": "Sowetan", "origin": "rss"},
    ]
    
    groups = group_articles_by_topic(sample_articles)
    print(f"\nFound {len(groups)} topic groups")
    
    for group in groups:
        analysis = analyze_topic_group(group["articles"], bias_map)
        print(f"\nTopic: {group['headline'][:60]}...")
        print(f"  Sources: {analysis.get('total_sources', 0)}")
        print(f"  Lean: {analysis.get('overall_lean', 'unknown')}")
        print(f"  Factuality: {analysis.get('factuality', 0)}/10")
        print(f"  Coverage: {analysis.get('coverage', 'unknown')}")
        print(f"  Spread: {analysis.get('bias_spread', 0)}")
