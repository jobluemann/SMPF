# SMPF v9 — app/config.py — 2026-08-25
# Updated default callback URLs to finwatchpro.net for production.
# Local development overrides via .env (localhost:8000 already set there).
"""Config for the standalone test site.

This site is intentionally separate from smma-os. It exists to:
  1. Verify which Groq and OpenRouter models/endpoints actually work.
  2. Prove out the "connect your account" OAuth flow for social platforms,
     inside the portal, instead of pasting raw API keys.

It does NOT post to X, Instagram, or Facebook on anyone's behalf yet.
Connectors here only reach the "connected" state and stop — no publish
calls are wired in until that's explicitly turned on separately.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Base domain for callbacks ─────────────────────────────────────────────
# finwatchpro.net is the production domain. Override with localhost in .env
# for local development.
_BASE_DOMAIN = os.getenv("SMPF_BASE_DOMAIN", "https://finwatchpro.net")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# Orpheus was the original pick for the client-portal voice feature —
# fastest free-tier option identified earlier. playai-tts is the fallback
# if Orpheus's language/terms restrictions don't fit a given use case.
GROQ_TTS_MODEL = os.getenv("GROQ_TTS_MODEL", "canopylabs/orpheus-v1-english")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# X — OAuth 2.0 with PKCE, proven working via curl on 2026-08-24.
# Replaces the earlier OAuth 1.0a setup entirely.
X_CLIENT_ID = os.getenv("X_CLIENT_ID", "")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET", "")
X_CALLBACK_URL = os.getenv("X_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/x/callback")

# X — OAuth 1.0a (still required for v1.1 media/upload)
X_OAUTH1_CONSUMER_KEY = os.getenv("X_OAUTH1_CONSUMER_KEY", "")
X_OAUTH1_CONSUMER_SECRET = os.getenv("X_OAUTH1_CONSUMER_SECRET", "")
X_OAUTH1_ACCESS_TOKEN = os.getenv("X_OAUTH1_ACCESS_TOKEN", "")
X_OAUTH1_ACCESS_TOKEN_SECRET = os.getenv("X_OAUTH1_ACCESS_TOKEN_SECRET", "")
# Replaces the earlier OAuth 1.0a setup entirely.
X_CLIENT_ID = os.getenv("X_CLIENT_ID", "")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET", "")
X_CALLBACK_URL = os.getenv("X_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/x/callback")

# ─── Gettr — ADMIN ONLY, your own account, never a client's ───
# Gettr has no public API. Real username/password, browser login only.
# Deliberately named differently from every client-facing connector's
# config above, and only ever read by app/connectors/admin_only/gettr_admin.py
# — never imported into main.py, never reachable over HTTP.
GETTR_USERNAME = os.getenv("GETTR_USERNAME", "")
GETTR_PASSWORD = os.getenv("GETTR_PASSWORD", "")

# One Meta app covers both Facebook and Instagram — Instagram Business
# accounts are reached through the Facebook Graph API, not a separate
# Instagram-only OAuth app.
META_APP_ID = os.getenv("META_APP_ID", "")
META_APP_SECRET = os.getenv("META_APP_SECRET", "")
META_CALLBACK_URL = os.getenv("META_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/meta/callback")
META_GRAPH_VERSION = "v21.0"

# Instagram — DIRECT login, not routed through Facebook at all. Separate
# product ("Instagram API with Instagram Login"), separate app credential.
# Use this when the client has no Facebook presence, only Instagram.
INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID", "")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "")
INSTAGRAM_CALLBACK_URL = os.getenv("INSTAGRAM_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/instagram/callback")

# YouTube uses Google's general OAuth — same app credential pattern.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_CALLBACK_URL = os.getenv("GOOGLE_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/youtube/callback")

# Reddit — its own OAuth app, separate from everything else.
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_CALLBACK_URL = os.getenv("REDDIT_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/reddit/callback")
# Reddit requires a descriptive User-Agent on every API call or requests
# get throttled hard — this isn't optional the way it is elsewhere.
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "SMPF/0.1 (connect-only test)")

# Threads has its own app type in Meta's developer console — it is NOT
# the same app credential as the regular Facebook/Instagram one above,
# even though both are "Meta".
THREADS_APP_ID = os.getenv("THREADS_APP_ID", "")
THREADS_APP_SECRET = os.getenv("THREADS_APP_SECRET", "")
THREADS_CALLBACK_URL = os.getenv("THREADS_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/threads/callback")

# Minds — real OAuth2 API, confirmed working in the earlier prototype.
MINDS_CLIENT_ID = os.getenv("MINDS_CLIENT_ID", "")
MINDS_CLIENT_SECRET = os.getenv("MINDS_CLIENT_SECRET", "")
MINDS_CALLBACK_URL = os.getenv("MINDS_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/minds/callback")

# Pollinations — free image generation, no API key needed at all.
# See app/providers/image_gen.py's module docstring — pattern documented
# widely but NOT verified live from this sandbox (pollinations.ai isn't
# reachable from here). Confirm it actually works before relying on it.
POLLINATIONS_BASE_URL = "https://image.pollinations.ai"

# Public URL where this server is reachable from the internet.
# Used to give Instagram/Threads a public image_url they can fetch.
# On the Pi this is the Cloudflare tunnel URL, e.g.
# PUBLIC_BASE_URL=https://soccer-man-dramatically-save.trycloudflare.com
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", _BASE_DOMAIN)

# VK (VKontakte) — see the big warning at the top of vk_connect.py before
# relying on this. VK has moved much of its login flow to a newer system
# ("VK ID") with extra requirements this may not fully match.
VK_CLIENT_ID = os.getenv("VK_CLIENT_ID", "")
VK_CLIENT_SECRET = os.getenv("VK_CLIENT_SECRET", "")
VK_CALLBACK_URL = os.getenv("VK_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/vk/callback")

# Google Drive — optional dedicated callback; falls back to GOOGLE_CALLBACK_URL.
GOOGLE_DRIVE_CALLBACK_URL = os.getenv("GOOGLE_DRIVE_CALLBACK_URL", GOOGLE_CALLBACK_URL)

# WhatsApp Business API (official Meta Business Platform)
# Used for 1:1 messaging and broadcast templates. NOT for groups.
WHATSAPP_BUSINESS_PHONE_NUMBER_ID = os.getenv("WHATSAPP_BUSINESS_PHONE_NUMBER_ID", "")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
WHATSAPP_BUSINESS_TOKEN = os.getenv("WHATSAPP_BUSINESS_TOKEN", "")
WHATSAPP_BUSINESS_API_VERSION = "v21.0"

# Telegram Bot API — official, free, supports groups natively.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-locally")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_CALLBACK_URL = os.getenv("LINKEDIN_CALLBACK_URL", f"{_BASE_DOMAIN}/connectors/linkedin/callback")

LINKEDIN_ORGANIZATION_URN = os.getenv("LINKEDIN_ORGANIZATION_URN", "")
