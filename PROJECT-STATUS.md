# SMPF Project Status — 2026-08-27

## Platform: Social Media Posting Framework
**User:** Jo Bluemann (@jobluemann)  
**Workspace:** `C:\Users\RudiOosthuizen\smpf`

---

## 🟢 COMPLETED

| # | Item | Notes |
|---|------|-------|
| 1 | Server core (FastAPI + SQLite auth) | Login, register, dashboard, logout working |
| 2 | Neutral white theme | Landing page, auth forms, dashboard styled |
| 3 | Static file serving | `/static/style.css` serving correctly |
| 4 | X (Twitter) connector | ✅ CONNECTED — OAuth 2.0 with PKCE |
| 5 | Facebook connector | ✅ CONNECTED — Pages + posting works |
| 6 | Instagram Graph connector | ✅ CONNECTED via Facebook API fallback |
| 7 | Disconnect → redirect to dashboard | All platforms now redirect properly |
| 8 | Meta app scope fix | Removed blocked `instagram_business_basic` from Facebook |
| 9 | Free AI integrations | Groq (text + TTS Orpheus), OpenRouter, Pollinations (images) |
| 10 | Analytics dashboard | Charts.js: connections donut, content bar, recent content |
| 11 | Content generation UI | Meme generator + voice generator in dashboard |
| 12 | **WhatsApp Web connector** | ✅ NEW — Playwright-based, personal number, group posting |
| 13 | **Posting API (`/api/post`)** | ✅ NEW — Unified endpoint for X, Facebook, Instagram, WhatsApp |
| 14 | **X posting (`post_tweet`)** | ✅ NEW — OAuth 2.0 tweet.write scope added |
| 15 | **Facebook posting (`post_to_facebook_page`)** | ✅ NEW — Uses page access token |
| 16 | **Dashboard post tester** | ✅ NEW — UI to test posts to all platforms |
| 17 | **Post logging (`/api/post-log`)** | ✅ NEW — JSONL daily log of all posts |

---

## 🟡 IN PROGRESS

| # | Item | Status |
|---|------|--------|
| 18 | **Threads connector** | App set up, needs redirect URI whitelisted in Meta Console |
| 19 | **Instagram live posting test** | Code ready (`post_to_instagram`), needs live image URL + token test |
| 20 | **YouTube** | OAuth routes ready, not tested |
| 21 | **Reddit** | OAuth routes ready, not tested |
| 22 | **Minds** | OAuth routes ready, not tested |
| 23 | **VK** | OAuth routes ready, not tested |
| 24 | **Google Drive** | OAuth routes ready, upload API working |

---

## 🔴 NOT STARTED

| # | Item | Status |
|---|------|--------|
| 25 | Hashtag generator | Requested |
| 26 | Group/tag generator | Requested |
| 27 | Onboarding questionnaire | Requested |
| 28 | Client opt-in workflow | Requested — approval → payment → calendar |
| 29 | Team allocation system | Requested — assign clients to consultants |
| 30 | Subscription/payment system | Requested |
| 31 | **Siteground deployment** | Needs plan → see Deployment Strategy below |
| 32 | **WordPress plugin** | Frontend for client portal on Siteground |
| 33 | News/meme research engine | Ground.News API, Reddit scraper |
| 34 | Scheduling engine | Auto-post at optimal times |
| 35 | Email newsletter | Provider integration not started |
| 36 | Daily PDF log | Not built |
| 37 | Video clipping | Research only, no implementation |

---

## 🔧 Known Issues

- **Threads:** Needs `https://localhost:8000/connectors/threads/callback` added to Valid OAuth Redirect URIs in Meta Developer Console
- **Instagram:** Uses fallback mapping (not live API discovery) due to Meta permission blocks. `post_to_instagram()` is code-complete but **untested live**
- **X posting:** `tweet.write` scope was just added to `x_connect.py`. User must **disconnect and reconnect X** to get a token with posting permission
- **Server:** Must restart after code changes; runs on `localhost:8000` (AD blocks 127.0.0.1)
- **WhatsApp:** QR code expires ~40 seconds. Session persisted via Playwright storage_state. Phone must stay online

---

## 📋 Next Actions (Your Choice)

1. **Test posting pipeline** — Use dashboard "Test post" UI to try X, Facebook, Instagram, WhatsApp
2. **Fix Threads** — whitelist redirect URI in Meta Console
3. **Plan Siteground deployment** — see strategy below
4. **Build hashtag + group generators**
5. **Design onboarding questionnaire + opt-in workflow**

---

## 🚀 Siteground Deployment Strategy

### Problem
Siteground **shared hosting** runs PHP only. FastAPI (Python) cannot run natively on shared plans. You have two real options:

### Option A: Render Free Tier Bridge + WP Plugin (RECOMMENDED)

**Architecture:**
```
┌─────────────────┐      API calls (HTTPS)      ┌─────────────────────┐
│  Siteground     │  ────────────────────────►  │  Render.com (free)  │
│  WordPress      │                             │  FastAPI backend    │
│  + SMPF Plugin  │  ◄────────────────────────  │  Python + SQLite    │
└─────────────────┘      JSON responses         └─────────────────────┘
```

**How it works:**
1. Host the FastAPI app on **Render.com free tier** (keeps running 24/7, spins down after 15min idle)
2. Build a **WordPress plugin** (`smpf-wp-bridge`) that lives on Siteground
3. The WP plugin provides:
   - Client login/registration (delegates to FastAPI auth API)
   - Dashboard UI showing connection status (fetches from `/api/analytics/connections`)
   - Post creation form (sends to `/api/post`)
   - OAuth callback relay — WP plugin forwards auth codes to Render backend
4. All OAuth app callbacks point to the Render domain (e.g., `https://smpf.onrender.com/connectors/x/callback`)
5. The WP plugin stores only the Render API base URL and auth tokens locally

**Pros:**
- FastAPI runs natively on a proper Python host
- Free tier on Render is genuinely free
- WordPress plugin is lightweight PHP — easy to install/update on Siteground
- Can scale: paid Render tier when you have many clients

**Cons:**
- Two separate deployments to manage
- Render free tier spins down after 15min idle (cold start ~30s)
- Need to configure CORS on FastAPI for the WP domain

**Render setup steps:**
1. Push SMPF code to a private GitHub repo
2. Connect repo to Render.com → New Web Service
3. Set environment variables (all API keys, secrets, callback URLs)
4. Change all callback URLs from `localhost:8000` to `smpf.onrender.com`
5. Verify OAuth flows work against Render domain

---

### Option B: Direct Python on Siteground (NOT RECOMMENDED)

Siteground shared hosting does **not** support:
- Persistent Python processes (uvicorn)
- pip install of compiled packages (Playwright, SQLAlchemy C extensions)
- Long-running background jobs

You would need to upgrade to Siteground **Cloud VPS** (~$100/month) to run Python. Not viable for MVP.

---

### Option C: All-PHP Rewrite on Siteground (NOT RECOMMENDED)

Rewrite the entire backend in PHP to run directly on Siteground. This loses:
- All the AI integrations (Groq, OpenRouter, TTS)
- Playwright-based connectors (WhatsApp, Gettr)
- Python async concurrency
- 2+ weeks of dev work

**Verdict: Do not do this.**

---

## 🏗️ Recommended Architecture

```
                    ┌─────────────────────────────────────┐
                    │         CLIENT BROWSER              │
                    └─────────────┬───────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
    ┌───────────────┐    ┌───────────────┐    ┌─────────────────┐
    │  Siteground   │    │  Siteground   │    │   Render.com    │
    │  WordPress    │    │  WP Plugin    │    │  FastAPI App    │
    │  (finwatchpro)│◄──►│  (smpf-bridge)│◄──►│  (smpf-backend) │
    │  Landing,     │    │  Dashboard,   │    │  OAuth, AI,     │
    │  Pricing,     │    │  Connect,     │    │  Posting,       │
    │  Blog         │    │  Post UI      │    │  Scheduling     │
    └───────────────┘    └───────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
                        ┌──────────┐           ┌──────────┐
                        │  MySQL   │           │  SQLite  │
                        │  (WP)    │           │  (SMPF)  │
                        └──────────┘           └──────────┘
```

**WP Plugin responsibilities:**
- Shortcodes for client dashboard (`[smpf_dashboard]`)
- Admin settings page for Render API base URL
- Proxy OAuth callbacks to Render (avoids CORS issues)
- Webhook receiver for post notifications from Render

**Render backend responsibilities:**
- All OAuth flows (X, Meta, Threads, etc.)
- AI content generation (Groq, OpenRouter, Pollinations)
- WhatsApp automation (Playwright)
- Post scheduling and queue
- Analytics aggregation

---

## 📁 Files Changed Today

| File | Change |
|------|--------|
| `app/connectors/whatsapp_connect.py` | **NEW** — WhatsApp Web automation connector |
| `app/connectors/x_connect.py` | Added `tweet.write` scope + `post_tweet()` function |
| `app/connectors/meta_connect.py` | Added `post_to_facebook_page()` function |
| `main.py` | Added WhatsApp routes, `/api/post`, `/api/post-log`, `/api/whatsapp/send` |
| `frontend/templates/dashboard.html` | Added "Test post" UI card |
| `frontend/templates/whatsapp_qr.html` | **NEW** — QR scan page with auto-polling |
| `PROJECT-STATUS.md` | This file |

---

## 🧪 How to Test Posting Right Now

1. **Restart the server:**
   ```bash
   cd C:\Users\RudiOosthuizen\smpf
   python -m uvicorn main:app --host localhost --port 8000 --reload
   ```

2. **Open dashboard:** `https://localhost:8000/dashboard`

3. **If X posting fails with 403:** Disconnect X → reconnect X (to get new `tweet.write` token)

4. **Test Facebook:** Should work immediately with current connected page

5. **Test Instagram:** Needs a **publicly accessible image URL** (Instagram Graph API cannot read local files). Use an image hosted online or generate one via `/api/images/generate` and serve it via `/generated/{filename}`

6. **Test WhatsApp:** Click Connect → scan QR with phone → wait for "Connected" → enter group name exactly as shown in WhatsApp → post

7. **Check post log:** `GET https://localhost:8000/api/post-log`
