"""SMPF Research Sources  Live news aggregation per client preferences.
No hardcoded topics. Everything is driven by client config.
"""
import json
import os
import re
import feedparser
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

DATA_DIR = "/opt/smpfx/data"
CACHE_DIR = os.path.join(DATA_DIR, "research_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


#  RSS Feed Registry (client can subscribe to any of these) 
RSS_REGISTRY = {
    # South Africa
    "news24_sa": "https://www.news24.com/rss",
    "mailguardian": "https://mg.co.za/rss",
    "dailymaverick": "https://www.dailymaverick.co.za/rss",
    "mybroadband": "https://mybroadband.co.za/news/feed",
    "businessday": "https://www.businesslive.co.za/bd/rss",
    "sowetan": "https://www.sowetanlive.co.za/rss",
    # Global Tech
    "techcrunch": "https://techcrunch.com/feed/",
    "theverge": "https://www.theverge.com/rss/index.xml",
    "arstechnica": "http://feeds.arstechnica.com/arstechnica/index",
    "hackernews": "https://hnrss.org/newest",
    # Global News
    "reuters": "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
    "bbc_world": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "ap_world": "https://rsshub.app/apnews/topics/apf-topnews",
    # Reddit (via RSS bridge)
    "reddit_tech": "https://rsshub.app/reddit/r/technology",
    "reddit_worldnews": "https://rsshub.app/reddit/r/worldnews",
    "reddit_sa": "https://rsshub.app/reddit/r/southafrica",
    "reddit_business": "https://rsshub.app/reddit/r/business",
    "reddit_memes": "https://rsshub.app/reddit/r/memes",
    "reddit_conservative": "https://rsshub.app/reddit/r/Conservative",
    "reddit_liberal": "https://rsshub.app/reddit/r/Liberal",
}


#  NewsAPI (free tier: 100 req/day) 
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")


def fetch_newsapi(query: str, country: str = None, category: str = None, page_size: int = 10) -> List[Dict]:
    """Fetch headlines from NewsAPI."""
    if not NEWSAPI_KEY:
        return []
    url = "https://newsapi.org/v2/top-headlines" if not query else "https://newsapi.org/v2/everything"
    params = {"apiKey": NEWSAPI_KEY, "pageSize": page_size}
    if query:
        params["q"] = query
        params["sortBy"] = "relevancy"
        params["language"] = "en"
    if country:
        params["country"] = country
    if category:
        params["category"] = category
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if data.get("status") == "ok":
            return [
                {
                    "title": a["title"],
                    "url": a["url"],
                    "source": a["source"]["name"],
                    "published": a["publishedAt"],
                    "summary": a.get("description", ""),
                    "origin": "newsapi",
                }
                for a in data.get("articles", [])
            ]
    except Exception:
        pass
    return []


#  RSS Fetcher 
def fetch_rss(feed_url: str, max_items: int = 10) -> List[Dict]:
    """Fetch and parse an RSS feed."""
    try:
        fp = feedparser.parse(feed_url)
        items = []
        for entry in fp.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "source": fp.feed.get("title", feed_url),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:300],
                "origin": "rss",
            })
        return items
    except Exception:
        return []


def fetch_rss_by_slug(slug: str, max_items: int = 10) -> List[Dict]:
    """Fetch RSS by registry slug."""
    url = RSS_REGISTRY.get(slug)
    if not url:
        return []
    return fetch_rss(url, max_items)


#  Reddit (direct API, no auth needed for public subreddits) 
def fetch_reddit_hot(subreddit: str, limit: int = 10) -> List[Dict]:
    """Fetch hot posts from a subreddit."""
    try:
        resp = requests.get(
            f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}",
            headers={"User-Agent": "SMPF/1.0"},
            timeout=15,
        )
        data = resp.json()
        posts = []
        for child in data.get("data", {}).get("children", []):
            p = child["data"]
            posts.append({
                "title": p["title"],
                "url": f"https://reddit.com{p['permalink']}",
                "source": f"r/{subreddit}",
                "published": datetime.fromtimestamp(p["created_utc"], tz=timezone.utc).isoformat(),
                "summary": p.get("selftext", "")[:300],
                "origin": "reddit",
                "score": p.get("score", 0),
            })
        return posts
    except Exception:
        return []


#  HackerNews Top Stories 
def fetch_hackernews(limit: int = 10) -> List[Dict]:
    """Fetch top stories from HN."""
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:limit]
        stories = []
        for sid in top_ids:
            story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10).json()
            if story and story.get("title"):
                stories.append({
                    "title": story["title"],
                    "url": story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                    "source": "HackerNews",
                    "published": datetime.fromtimestamp(story.get("time", 0), tz=timezone.utc).isoformat(),
                    "summary": story.get("text", "")[:300],
                    "origin": "hackernews",
                    "score": story.get("score", 0),
                })
        return stories
    except Exception:
        return []


#  Client Research Config 
def get_client_sources(client_profile: Dict) -> List[str]:
    """Determine which RSS/news sources to use based on client profile."""
    sources = []
    
    # Geography
    country = client_profile.get("target_country", "").lower()
    if "south africa" in country or country == "za":
        sources.extend(["news24_sa", "dailymaverick", "mailguardian", "mybroadband", "sowetan", "reddit_sa"])
    if "usa" in country or country == "us" or "america" in country:
        sources.extend(["reddit_worldnews", "ap_world"])
    
    # Global defaults always included
    sources.extend(["hackernews", "reddit_tech", "reddit_business", "reddit_memes"])
    
    # Political leaning
    political = client_profile.get("political_spectrum", "").lower()
    if "conservative" in political:
        sources.append("reddit_conservative")
    if "liberal" in political or "progressive" in political:
        sources.append("reddit_liberal")
    
    # Industry/topics
    topics = client_profile.get("topics_json", "[]")
    try:
        topics = json.loads(topics) if isinstance(topics, str) else topics
    except:
        topics = []
    topic_map = {
        "technology": ["techcrunch", "theverge", "arstechnica", "reddit_tech"],
        "politics": ["reddit_worldnews", "reddit_conservative", "reddit_liberal"],
        "business": ["businessday", "reddit_business"],
        "sports": [],  # Add sports feeds
        "entertainment": [],  # Add entertainment feeds
        "finance": ["businessday", "reddit_business"],
    }
    for topic in topics:
        t = topic.lower()
        for key, feeds in topic_map.items():
            if key in t:
                sources.extend(feeds)
    
    return list(dict.fromkeys(sources))  # dedup while preserving order


def build_newsapi_query(client_profile: Dict) -> Optional[str]:
    """Build a NewsAPI search query from client interests."""
    topics = client_profile.get("topics_json", "[]")
    try:
        topics = json.loads(topics) if isinstance(topics, str) else topics
    except:
        topics = []
    
    # Build OR query from topics
    if topics:
        query = " OR ".join([f'"{t}"' for t in topics[:5]])
        return query
    
    # Fallback based on industry
    industry = client_profile.get("industry", "").lower()
    if industry:
        return industry
    return None


#  Main Research Function 
def research_for_client(client_profile: Dict, max_items: int = 20) -> List[Dict]:
    """Fetch trending topics for a specific client based on their profile."""
    all_items = []
    
    # 1. RSS feeds based on client profile
    sources = get_client_sources(client_profile)
    for slug in sources:
        items = fetch_rss_by_slug(slug, max_items=5)
        for item in items:
            item["_client_relevance"] = "geography" if any(s in slug for s in ["sa", "southafrica", "za"]) else "interest"
        all_items.extend(items)
    
    # 2. NewsAPI query
    query = build_newsapi_query(client_profile)
    if query:
        country_code = None
        country = client_profile.get("target_country", "").lower()
        if "south africa" in country or country == "za":
            country_code = "za"
        if "usa" in country or country == "us" or "america" in country:
            country_code = "us"
        items = fetch_newsapi(query, country=country_code, page_size=10)
        for item in items:
            item["_client_relevance"] = "newsapi"
        all_items.extend(items)
    
    # 3. Reddit hot from relevant subreddits
    subreddits = []
    topics = client_profile.get("topics_json", "[]")
    try:
        topics = json.loads(topics) if isinstance(topics, str) else topics
    except:
        topics = []
    subreddit_map = {
        "technology": "technology",
        "politics": "worldnews",
        "business": "business",
        "memes": "memes",
        "sports": "sports",
        "finance": "wallstreetbets",
    }
    for topic in topics:
        t = topic.lower()
        for key, sub in subreddit_map.items():
            if key in t and sub not in subreddits:
                subreddits.append(sub)
    
    # Always include some general ones
    for sub in ["technology", "worldnews", "memes", "business"]:
        if sub not in subreddits:
            subreddits.append(sub)
    
    for sub in subreddits[:3]:
        items = fetch_reddit_hot(sub, limit=5)
        for item in items:
            item["_client_relevance"] = "reddit"
        all_items.extend(items)
    
    # 4. HackerNews (always good for tech/business)
    if any(t in str(topics).lower() for t in ["tech", "business", "startup", "ai"]):
        items = fetch_hackernews(limit=5)
        for item in items:
            item["_client_relevance"] = "hackernews"
        all_items.extend(items)
    
    # Deduplicate by URL
    seen = set()
    deduped = []
    for item in all_items:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            deduped.append(item)
    
    return deduped[:max_items]


if __name__ == "__main__":
    # Test with a sample client profile
    test_profile = {
        "target_country": "South Africa",
        "topics_json": json.dumps(["Technology", "Politics", "AI", "Business"]),
        "political_spectrum": "centre",
        "industry": "Technology",
    }
    items = research_for_client(test_profile, max_items=15)
    print(f"Found {len(items)} items for test client:\n")
    for i, item in enumerate(items, 1):
        print(f"{i}. [{item['origin']}] {item['title'][:80]}")
        print(f"   Source: {item['source']} | {item.get('published', 'N/A')[:10]}")
        print(f"   URL: {item['url'][:80]}")
        print()
