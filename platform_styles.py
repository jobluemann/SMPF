"""Platform-specific post formatting rules.
Each platform has unique constraints and audience expectations.
"""

PLATFORM_CONFIG = {
    "x": {
        "name": "X (Twitter)",
        "char_limit": 280,
        "style": "Punchy, opinionated, thread-friendly. One strong hook. 2-3 hashtags max. Can be confrontational or witty.",
        "format": "Text + optional image",
        "audience": "News junkies, professionals, activists. Fast scrollers.",
        "tone_scale": {
            "funny": "Meme energy, sarcasm, hot takes",
            "serious": "Policy wonk, data-driven, breaking news style"
        },
        "example": "OpenAI wants to regulate open-source AI while prepping an $80B IPO. The playbook: fear drives legislation, legislation raises barriers, barriers protect incumbents. #OpenSource #AI",
        "hashtag_count": "2-3",
    },
    "linkedin": {
        "name": "LinkedIn",
        "char_limit": 3000,
        "style": "Professional, thought leadership, structured paragraphs. Industry insights. Avoid memes. Subtle self-promotion okay.",
        "format": "Long-form text + optional image/carousel",
        "audience": "Business professionals, decision-makers, recruiters.",
        "tone_scale": {
            "funny": "Workplace humor, relatable corporate satire",
            "serious": "Executive briefing, market analysis, policy deep-dive"
        },
        "example": "The irony is impossible to ignore.\n\nAs OpenAI prepares for its IPO, its leadership simultaneously lobbies for stricter AI regulation targeting open-source models.\n\nIf we are serious about AI safety, we need transparent standards, not regulatory moats.",
        "hashtag_count": "3-5",
    },
    "facebook": {
        "name": "Facebook",
        "char_limit": 5000,
        "style": "Conversational, community-focused, questions to drive comments. Shareable. More personal than LinkedIn.",
        "format": "Text + image/video + link preview",
        "audience": "General public, community groups, older demographics.",
        "tone_scale": {
            "funny": "Dad jokes, relatable rants, light satire",
            "serious": "Community concern, factual breakdown, local relevance"
        },
        "example": "OpenAI says open-source AI is dangerous and needs regulation. Meanwhile they are filing for an $80 billion IPO. Does anyone else see the conflict of interest here?",
        "hashtag_count": "2-4",
    },
    "instagram": {
        "name": "Instagram",
        "char_limit": 2200,
        "style": "Visual-first. Caption supports image. Short paragraphs. Heavy emoji use. Hashtag block. Storytelling vibe.",
        "format": "Image/carousel/reel + caption + hashtag block",
        "audience": "Young professionals, creatives, brand followers.",
        "tone_scale": {
            "funny": "Meme culture, reaction energy, Gen Z humor",
            "serious": "Educational carousel, infographic caption"
        },
        "example": "Swipe to see why open-source AI matters. The same company warning about AI dangers is about to IPO for $80B. #OpenSourceAI #TechPolicy #AIEthics",
        "hashtag_count": "10-30",
    },
    "threads": {
        "name": "Threads",
        "char_limit": 500,
        "style": "Casual, conversational, like texting. Sentence fragments. Soft opinions. Less polished.",
        "format": "Text + optional image",
        "audience": "Instagram crossovers, casual social users.",
        "tone_scale": {
            "funny": "Unhinged casual, irony, lowercase chaos",
            "serious": "Gentle concern, soft takes, mindful commentary"
        },
        "example": "openai: we need to regulate open-source ai because it is too dangerous. also openai: our ipo is next week at $80B valuation. make it make sense",
        "hashtag_count": "1-2",
    },
}


def get_platform_config(platform: str) -> dict:
    """Return config for a platform, defaulting to X if unknown."""
    return PLATFORM_CONFIG.get(platform.lower(), PLATFORM_CONFIG["x"])


def build_prompt(article: dict, client: dict, platform: str, tone_slider: int = None) -> str:
    """Build a platform-specific prompt for the AI."""
    cfg = get_platform_config(platform)

    # Determine tone from slider or client profile
    if tone_slider is None:
        tone_slider = client.get("funny_serious_slider", 50)

    if tone_slider < 30:
        tone_label = "funny/casual"
        tone_desc = cfg["tone_scale"]["funny"]
    elif tone_slider > 70:
        tone_label = "serious/professional"
        tone_desc = cfg["tone_scale"]["serious"]
    else:
        tone_label = "balanced"
        tone_desc = "Mix of professional insight with occasional wit or relatable hook."

    archetype = client.get("archetype", "The Analyst")
    country = client.get("target_country", "")
    industry = client.get("industry", "")
    political = client.get("political_spectrum", "")

    archetype_mods = {
        "The Provocateur": "Add a controversial edge. Challenge assumptions. Use rhetorical questions.",
        "The Entertainer": "Make it entertaining. Use analogies or pop culture. Keep it light.",
        "The Analyst": "Lead with insight. Cite implications. Logical flow.",
        "The Leader": "Inspirational. Visionary. We/us language. Call to action.",
        "The Activist": "Passionate. Justice-oriented. Clear enemy or problem.",
        "The Diplomat": "Nuanced. Multiple perspectives. Bridge-building.",
        "The Everyman": "Relatable. Conversational. Simple language.",
    }
    mod = archetype_mods.get(archetype, "")

    prompt = f"You are a ghostwriter creating a {cfg['name']} post.\n\n"
    prompt += f"ARTICLE TO BASE POST ON:\n"
    prompt += f"Title: {article['title']}\n"
    prompt += f"Source: {article['source']}\n"
    prompt += f"Summary: {article.get('summary', '')[:300]}\n\n"
    prompt += f"CLIENT PROFILE:\n"
    prompt += f"- Archetype: {archetype} ({mod})\n"
    prompt += f"- Tone slider: {tone_slider}/100 serious ({tone_desc})\n"
    prompt += f"- Industry: {industry}\n"
    prompt += f"- Country focus: {country}\n"
    prompt += f"- Political leaning: {political}\n\n"
    prompt += f"PLATFORM RULES ({cfg['name']}):\n"
    prompt += f"- Character limit: {cfg['char_limit']}\n"
    prompt += f"- Style: {cfg['style']}\n"
    prompt += f"- Audience: {cfg['audience']}\n\n"
    prompt += f"INSTRUCTIONS:\n"
    prompt += f"1. Write ONE post for {cfg['name']}.\n"
    prompt += f"2. Respect the character limit (max {cfg['char_limit']} chars).\n"
    prompt += f"3. Match the tone ({tone_label}): {tone_desc}\n"
    prompt += f"4. Apply the client's archetype voice: {mod}\n"
    prompt += f"5. Include {cfg['hashtag_count']} relevant hashtags.\n"
    prompt += f"6. End with ONE call-to-action or question.\n"
    prompt += f"7. Do NOT include meta-commentary.\n\n"
    prompt += f"Write the post now:"

    return prompt


if __name__ == "__main__":
    for p in ["x", "linkedin", "facebook", "instagram", "threads"]:
        cfg = get_platform_config(p)
        print(f"{p}: {cfg['name']} | limit={cfg['char_limit']} | hashtags={cfg['hashtag_count']}")
