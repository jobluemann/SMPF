# SMPF — Social Media Platform Framework
## Master Requirements & Architecture Document — v2.1

| Field | Value |
|-------|-------|
| **Project** | SMPF — Social Media Platform Framework |
| **Version** | 2.1 |
| **Date** | 2026-09-08 |
| **Owner** | Jo Bluemann (jobluemann) |
| **Repository** | github.com/jobluemann/smpf-backend (private) |
| **App Runtime** | Raspberry Pi 4, 24/7, home (~/apps/smpfx) |
| **Public Gateway** | Oracle Cloud free-tier VM (WireGuard + Caddy) → smpf.finwatchpro.net |
| **License** | Proprietary — all rights reserved |

---

# 1. SCOPE & REQUIREMENTS

## 1.1 Vision

SMPF is an automated social media management platform that:

1. **Researches** trending topics and top news stories (America, South Africa, Global)
2. **Vets** stories for bias/factuality using sources like Ground News (left/center/right rankings)
3. **Generates** content in the client's voice using free-tier AI (Groq, OpenRouter, Pollinations)
4. **Posts** automatically to connected social platforms at optimal peak times
5. **Monitors** engagement (views, likes, reposts, replies by country/region)
6. **Manages** conversations — responds to comments in the client's voice

## 1.2 Business Model

Digital marketing company specializing in social media growth, engagement, advertising, website design, and automation.

**Target customers:**
- Clients who want full managed service (we post for them)
- Self-service customers who buy a package and use the portal themselves

**Product packages (subscription tiers) — platforms sellable individually AND bundled:**

| Package | Platforms | Description |
|---------|-----------|-------------|
| **Facebook Only** | Facebook | Entry tier |
| **FB + IG Bundle** | Facebook + Instagram | Core Meta package |
| **Full Meta** | FB + IG + Threads | Complete Meta presence |
| **Everything** | All connected platforms + X | Full service |

**Payment methods (tip/support first, subscriptions later):**
PayPal, Ko-fi, BuyMeACoffee, BTC wallet, ETH wallet

**Future:** PayFast (SA), Stripe (global) — pending account approval

## 1.3 Client Onboarding Flow

```
Register (work email only, 12+ char password)
  → Login to portal
  → Connect social platforms (OAuth per platform)
  → Opt-in to managed service
  → Questionnaire (topics, audience, posting preferences)
  → Package selection → Payment
  → Telegram notification + calendar entry to admin
  → Admin assigns consultant (company email)
```

**Registration rules:**
- Work domain email required (Gmail/Outlook gets a security warning, not blocked)
- Minimum 12-character password
- Recovery email also must be work domain
- Account lockout after failed login attempts
- Email verification link + activation key controlled by monthly payments
- Payment reminder emails on the 25th and last day of month

## 1.4 Content Strategy

**Persona: Jo Bluemann** (reference client) — full profile: `perspective-profile.md`
- Conservative, Christian values (personal relationship with God, doesn't attend church)
- Anti-ANC, anti-taxation ("taxation is legalized theft"), pro-death-penalty, anti-abortion
- South African Afrikaner, proud of nationality
- Big on history, politics, statistics
- Style: controversial, provocative, mirror-flip rhetoric, "shoe on the other foot"
- AI fixes spelling/grammar, keeps voice

**Posting cadence:**
- Peak periods per platform, per region (SA, USA, international)
- Vary posting times with jitter so it doesn't look like a bot
- 5 posts per platform per day max
- Story morning + afternoon; memes any time
- Polls added ~1 month after engagement rebuilds (NOT on every post)

**Topic coverage per platform:** platform-specific audience targeting (e.g., GETTR skews American conservative).

## 1.5 Functional Requirements

| # | Requirement | Status |
|---|-------------|--------|
| R1 | Multi-platform posting (text + image) | 🟡 X proven live; FB/IG/Threads code done, connect pending |
| R2 | AI content generation (Groq/OpenRouter) | ✅ Built |
| R3 | AI image generation (Pollinations, free) | ✅ Built |
| R4 | Text-to-speech voice posts (Groq Orpheus) | ✅ Built |
| R5 | News research + bias vetting | 🔴 Future |
| R6 | Social media watcher bot (story-break alerts) | 🔴 Future |
| R7 | Scheduled posting (cron, varied times, regional peak windows) | 🔴 Future |
| R8 | Hashtag generator + group @mentions | 🔴 Future |
| R9 | Engagement analytics (views/likes/reposts by region) | 🟡 Basic counts |
| R10 | Conversation management (auto-reply in client voice) | 🔴 Future |
| R11 | Daily activity log PDF | 🔴 Future |
| R12 | Client portal (register/login/packages/billing) | 🟡 Auth built |
| R13 | Newsletter function (client's own SMTP provider) | 🔴 Future |
| R14 | Google Drive storage integration | ✅ Built |
| R15 | Platform connection keep-alive pulse | 🟡 WhatsApp pulse built; generic version future |
| R16 | Permanent public URL (fixed IP + domain + TLS) | 🟡 Oracle VM + WireGuard + Caddy — deploy in progress |

## 1.6 Non-Functional Requirements

- **Cost:** All AI and hosting on free tiers. Zero monthly infrastructure cost. (Exception: Meta WhatsApp Business API pay-as-you-go per conversation — user-approved.)
- **Availability:** 24/7 on Raspberry Pi. No sleep mode (Render free-tier problem avoided by Pi).
- **Network:** Home dynamic IP is fine — Pi initiates outbound WireGuard with PersistentKeepalive; VM has fixed reserved IP 84.8.128.153.
- **Scale path:** Split into WordPress plugins deployable across multiple SiteGround shared servers; load balancer optional third server.
- **Security:** Secrets in .env only, never in code. No social-media OAuth to enter the portal itself.
- **Deployment:** GitHub → git pull on Pi. Manual deploy for shared hosting.

---

# 2. ARCHITECTURE & DESIGN

## 2.1 System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     CLIENT BROWSERS                               │
│         (Dashboard, Portal, Mobile)                               │
└──────────────────────┬───────────────────────────────────────────┘
                       │ HTTPS  smpf.finwatchpro.net
        ┌──────────────┴──────────────┐
        │   Oracle Cloud VM (gateway)  │  Caddy auto-TLS, fixed IP
        │   84.8.128.153  Ubuntu 22.04 │  WireGuard server 10.66.0.1
        └──────────────┬──────────────┘
                       │ WireGuard UDP 51820 (Pi initiates, keepalive 25s)
        ┌──────────────┴──────────────┐
        │   Raspberry Pi 4 — 24/7      │  10.66.0.2
        │                              │
        │   FastAPI (main.py) :8000    │
        │   ├── Connectors (12)        │
        │   ├── Providers (AI)         │
        │   ├── Portal (auth/users)    │
        │   └── Integrations (Drive)   │
        │                              │
        │   SQLite (portal users)      │
        │   data/ (connections, logs,  │
        │         generated media)     │
        └─────────────────────────────┘
```

**Fallback:** Cloudflare quick tunnel (`cloudflared tunnel --url http://localhost:8000`) — emergency only; URL churns on restart.

## 2.2 Technology Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Backend | Python 3.13 + FastAPI + uvicorn | Free |
| Frontend | Jinja2 templates + vanilla HTML/CSS | Free |
| Database | SQLite (SQLAlchemy ORM) | Free |
| Auth | Session middleware + salted password hash | Free |
| App host | Raspberry Pi (home) | Free |
| Gateway | Oracle Cloud VM.Standard.E2.1.Micro (Always Free) | Free |
| VPN | WireGuard (VM↔Pi) | Free |
| TLS/Proxy | Caddy (auto Let's Encrypt) | Free |
| AI Text | Groq API (free tier, failover: OpenRouter) | Free |
| AI Voice | Groq Orpheus TTS (~95ms latency) | Free |
| AI Image | Pollinations.ai (no key) | Free |
| Repo | GitHub (private) | Free |
| DNS | SiteGround (finwatchpro.net) | Existing |

**Retired hosting paths:** Render (free tier sleeps after 15 min — rejected despite keep-alive hacks). Cloudflare quick tunnel as PRIMARY (URL churn — demoted to fallback). Hetzner €5.35/mo (deferred — zero-cost requirement). IPsec Pi→SiteGround (replaced by WireGuard to Oracle).

## 2.3 Connector Architecture

Every connector follows the same contract:

```
get_authorize_url(state)      → OAuth start URL
complete_connect_flow(...)    → token exchange + identity + persist
get_connection_status(user)   → {status, identity}
disconnect(user)              → remove stored connection
post_*(user, content)         → platform publish (where implemented)
```

**Storage:** One JSON file per connector in `data/`:
`x_connections.json`, `meta_connections.json`, `instagram_connections.json`, `threads_connections.json`, etc.

**Design rule:** Connectors originally stopped at CONNECTED. Posting is now enabled per-platform; X proved the pattern.

## 2.4 Meta Platform Strategy

**Three separate connectors, three separate dashboard entries, three separate product unlocks:**

| Connector | Credentials | API Base | Image Posting |
|-----------|-------------|----------|---------------|
| `meta_connect` (Facebook) | META_APP_ID/SECRET (app "POES") | graph.facebook.com | Multipart upload (no public URL needed) |
| `instagram_connect` (Instagram direct) | INSTAGRAM_APP_ID/SECRET (app "smpf") | graph.instagram.com | **Public image_url required** |
| `threads_connect` (Threads) | THREADS_APP_ID/SECRET (app "POES") | graph.threads.net | **Public image_url required** |

**Key insight:** Meta supports one app with multiple products, but we deliberately run FB, IG, Threads as separately-credentialed apps so each platform is individually sellable and its OAuth redirect/whitelist is independent (Meta allows only ONE redirect URI per app — the fixed domain smpf.finwatchpro.net makes this sustainable).

**Instagram image constraint:** Instagram/Threads fetch the image server-side from a public URL. Local Pi images are exposed via `{PUBLIC_BASE_URL}/generated/{filename}` (now the fixed domain instead of the churning tunnel URL).

**`instagram_graph_connect.py`** retained as the FB-linked Instagram path (FB+IG bundle where the client's IG is linked to their FB Page). Not the primary path.

**App Review note:** All advanced scopes work immediately in dev mode for the app admin. Meta App Review (screencast etc.) is deferred until paying clients need to connect — NOT needed for current testing.

## 2.5 X (Twitter) Architecture — Lessons Locked In

| Decision | Detail |
|----------|--------|
| Posting auth | **OAuth 1.0a** — permanent, never expires |
| Posting endpoint | **v2** `/2/tweets` (v1.1 `statuses/update.json` returns **404** — dead) |
| Media upload | v1.1 `media/upload.json` (OAuth 1.0a required for upload) |
| Connect flow | OAuth 2.0 + PKCE (for dashboard identity) |
| Token expiry | OAuth 2.0 access tokens die every 2h — auto-refresh implemented; OAuth 1.0a bypasses the problem entirely |

**Critical debugging lesson (2026-09-07):** X accepts OAuth 1.0a auth on the v2 tweets endpoint — text AND media_ids. The empty-error 404 from v1.1 cost hours; the v2 + OAuth1 combination is the documented solution. Live text + image posts verified.

## 2.6 Directory Structure

```
smpf/
├── main.py                  # FastAPI app, routes, /api/post orchestrator
├── requirements.txt
├── .env                     # ALL secrets (never committed)
├── app/
│   ├── config.py            # Env loader, constants, PUBLIC_BASE_URL
│   ├── connectors/
│   │   ├── x_connect.py           # X posting ✅
│   │   ├── meta_connect.py        # Facebook standalone ✅
│   │   ├── instagram_connect.py   # Instagram direct ✅
│   │   ├── instagram_graph_connect.py  # IG via FB (bundle path)
│   │   ├── threads_connect.py     # Threads ✅
│   │   ├── youtube_connect.py
│   │   ├── reddit_connect.py
│   │   ├── minds_connect.py
│   │   ├── vk_connect.py
│   │   ├── whatsapp_connect.py        # WhatsApp Web (QR session)
│   │   ├── whatsapp_business_connect.py
│   │   ├── telegram_connect.py
│   │   └── admin_only/gettr_admin.py  # GETTR creds, browser-only
│   ├── providers/
│   │   ├── groq_client.py       # Chat/reasoning
│   │   ├── groq_tts.py          # Orpheus voice
│   │   ├── openrouter_client.py # Failover models
│   │   └── image_gen.py         # Pollinations images
│   ├── integrations/google_drive.py
│   └── portal/
│       ├── auth.py              # Password rules, lockout, work-email check
│       ├── database.py
│       └── models.py            # User
├── frontend/
│   └── templates/               # landing, login, register, dashboard, whatsapp_qr
└── data/                        # Runtime JSON + generated media (gitignored)
    ├── generated_images/
    ├── tts_output/
    ├── post_log.jsonl
    └── *_connections.json
```

---

# 3. TECHNICAL / IMPLEMENTATION

## 3.1 Core Endpoints

### Health & Status
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Uptime-monitor ping (keep-alive) |
| GET | `/dashboard` | Connector status board (auth required) |
| GET | `/api/analytics/overview` | Platform/content counts |
| GET | `/api/analytics/connections` | Per-platform status for charts |
| GET | `/api/analytics/content-history` | Recent generated media |

### Portal Auth
| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/register` | Work-email validation, 12+ char password, salted hash |
| GET/POST | `/login` | Session auth + lockout after failed attempts |
| GET | `/logout` | Clear session |

### Unified Posting
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/post` | Multi-platform post: `{platforms[], content{text, image_url}, whatsapp{group_names[]}, telegram{chat_id}}` |
| GET | `/api/post-log` | Recent posting activity (JSONL) |

Platform dispatch in `/api/post`:
- `x` → download image → `upload_media` (v1.1 OAuth1) → `post_tweet` (v2 OAuth1)
- `facebook` → `post_text` OR `post_image` (multipart page token)
- `instagram` → `_make_public_image_url` → `post_image` (container → publish)
- `threads` → `post_text` OR `post_image` (container → publish)
- `telegram` → `send_message`
- `whatsapp` → `send_message_to_group` per group

Helpers: `_resolve_image_local()` (remote→temp file), `_make_public_image_url()` (local→public URL), `_log_post()` (JSONL audit log).

### Content Generation
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/images/generate` | Pollinations image from prompt → PNG |
| POST | `/api/tts/generate` | Groq Orpheus TTS → WAV |

### Media Serving
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/generated/{filename}` | Public image URL source (IG/Threads fetch target) |
| GET | `/audio/{filename}` | TTS output |

## 3.2 Connector Implementation Details

### x_connect.py
- `post_tweet(user, text, media_ids)` — OAuth 1.0a first (env creds) → v2 tweets; falls back to OAuth 2.0 bearer + auto-refresh on 401
- `upload_media(user, path)` — `_prepare_image_for_x()` resizes to ≤1200px, JPEG q85, ≤5MB → v1.1 upload (OAuth1)
- SCOPES: `tweet.read users.read offline.access tweet.write`

### meta_connect.py (Facebook, standalone)
- SCOPES: `pages_show_list pages_manage_posts business_management`
- Flow: code → long-lived user token → `me/accounts` (page tokens) → store pages
- `post_text` → `/{page-id}/feed`
- `post_image` → `/{page-id}/photos` multipart + caption
- Uses **Page Access Token**, never user token

### instagram_connect.py (direct, standalone)
- Product: "Instagram API with Instagram Login" (separate from FB)
- SCOPES: `instagram_business_basic instagram_business_content_publish`
- Account MUST be Business/Creator
- Flow: code → short token → long-lived → `graph.instagram.com/me`
- `post_image(user, image_url, caption)` → `/{ig-id}/media` → `/{ig-id}/media_publish`

### threads_connect.py
- SCOPES: `threads_basic threads_content_publish`
- Flow: code → short → long-lived (`th_exchange_token`) → `graph.threads.net/v1.0/me`
- `post_text` → container (`media_type=TEXT`) → `threads_publish`
- `post_image` → container (`media_type=IMAGE` + public `image_url`) → `threads_publish`

### whatsapp_connect.py (WhatsApp Web)
- QR-code pairing flow (session-based, unofficial)
- Group list management (add/remove groups, multi-group broadcast)
- `/api/whatsapp/health` — session heartbeat pulse (detect auto-logout)
- **Limitation:** WhatsApp Web sessions drop; pulse + re-pair needed. Official Business API (separate connector) is the reliable path — pay-as-you-go Meta pricing.

## 3.3 Configuration (.env)

```ini
# Public internet base (fixed domain via Oracle gateway) — REQUIRED for IG/Threads images
PUBLIC_BASE_URL=https://smpf.finwatchpro.net

# X — OAuth 2.0 connect flow
X_CLIENT_ID / X_CLIENT_SECRET / X_CALLBACK_URL

# X — OAuth 1.0a PERMANENT posting (v2 API)
X_OAUTH1_CONSUMER_KEY / X_OAUTH1_CONSUMER_SECRET
X_OAUTH1_ACCESS_TOKEN / X_OAUTH1_ACCESS_TOKEN_SECRET

# Meta (separate apps per platform — see 2.4)
META_APP_ID / META_APP_SECRET / META_CALLBACK_URL
INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET / INSTAGRAM_CALLBACK_URL
THREADS_APP_ID / THREADS_APP_SECRET / THREADS_CALLBACK_URL

# AI (free tiers)
GROQ_API_KEY / OPENROUTER_API_KEY
GROQ_TTS_MODEL=canopylabs/orpheus-v1-english

# Messaging
TELEGRAM_BOT_TOKEN
WHATSAPP_BUSINESS_PHONE_NUMBER_ID / WHATSAPP_BUSINESS_TOKEN

GETTR_USERNAME / GETTR_PASSWORD   # admin_only, browser-based, no API exists
SECRET_KEY / DEBUG
```

**Security notes:** `R@0!wyn1o1`-style passwords are Meta dashboard unlock passwords, never API values. Access tokens (`EAA...`) are NOT App IDs. App ID = pure numbers. All secrets stay in `.env` on the Pi.

## 3.4 Deployment Runbook

Full infrastructure runbook (Oracle VM, WireGuard, Caddy, DNS, Pi blocks, credentials): **SMPF-DEPLOYMENT-v1.0.0.md** (keep next to this document).

Quick reference:
```bash
# Pi:
cd ~/apps/smpfx && git pull origin main && source venv/bin/activate
pip install -r requirements.txt   # when requirements change
uvicorn main:app --host 0.0.0.0 --port 8000
# Port conflict: sudo fuser -k 8000/tcp
# Pull conflict on data/x_connections.json: git stash && git pull && git stash pop
```

## 3.5 Known Issues & Resolutions Log

| Date | Issue | Resolution |
|------|-------|------------|
| 2026-09-05 | X OAuth 2.0 token dies every 2h | Migrated posting to OAuth 1.0a (permanent) |
| 2026-09-06 | X OAuth 1.0a 401 "Could not authenticate you" (code 32) on media upload | Old v1.1 endpoints partially shut down; posting moved to v2 `/2/tweets` with OAuth1 — text AND media work |
| 2026-09-07 | X v1.1 `statuses/update.json` → 404 empty error | Post via **v2 `/2/tweets` with OAuth 1.0a** — works for text + media |
| 2026-09-07 | "Invalid App ID" on FB connect | EAA access token had been pasted into META_APP_ID; real App ID is numeric |
| 2026-09-07 | Meta "Insecure login blocked" (err 1349187) | Callback URLs were `http://192.168.x.x` — Meta requires HTTPS; fixed domain solves permanently |
| 2026-09-07 | FB "App not active" | Old "smpf" FB app flagged — replaced with "POES" app (untested at v2.1 time) |
| 2026-09-07 | Threads URI-not-whitelisted (err 1349168) | Meta allows ONE redirect URI per app; separate Threads app with its own whitelist |
| 2026-09-08 | trycloudflare quick tunnel URL churns on restart | Oracle VM + WireGuard + Caddy + smpf.finwatchpro.net (deploy in progress) |
| 2026-09-08 | Oracle reserved IP 84.8.128.153 created unattached | Must attach to primary VNIC — unattached reserved IPs bill hourly |
| Ongoing | Pi SSH not available to AI assistant | All Pi work = paste blocks; laptop Bash + Oracle VM SSH are assistant-accessible |

## 3.6 Environment / Platform Matrix

| Platform | Connect | Post Text | Post Image | Blockers |
|----------|---------|-----------|------------|----------|
| **X** | ✅ | ✅ live | ✅ live | None — production ready |
| **Facebook** | 🟡 | ✅ code | ✅ code | POES app connect untested; redirect whitelist → fixed domain |
| **Instagram (direct)** | 🟡 | n/a | ✅ code | Business account required; connect untested; public image URL (fixed domain solves) |
| **Threads** | ✅ (old creds) | ✅ code | ✅ code | Reconnect under POES app creds; scope toggle |
| Telegram | ✅ | ✅ | — | None |
| WhatsApp Web | 🟡 | ✅ | — | Session drop risk; pulse monitor in place |
| WhatsApp Business | ✅ config | ✅ | — | Meta pay-as-you-go costs per conversation |
| YouTube | ✅ connect | — | — | Posting not built |
| Reddit | ✅ connect | — | — | Posting not built |
| Minds | ✅ connect | — | — | Posting not built |
| VK | ✅ connect | — | — | Posting not built |
| GETTR | 🔴 admin only | — | — | No public API; browser automation only |
| Google Drive | ✅ | — | — | Storage working |
| LinkedIn | 🔴 | — | — | Not built (user deprioritized — no LinkedIn posts) |
| Quora | 🔴 | — | — | Evaluated — blog-style; revisit in Phase 2 |

Legend: ✅ working · 🟡 code done, config/connect pending · 🔴 not viable/built

---

# 4. FUNCTION REFERENCE

## 4.1 Posting Functions (production)

```python
# X — app/connectors/x_connect.py
post_tweet(local_user_id, text, media_ids=None) -> {status, tweet_id, text_preview}
upload_media(local_user_id, media_path) -> {status, media_id}
    └── _prepare_image_for_x(path)  # auto-resize ≤1200px, JPEG q85, ≤5MB

# Facebook — app/connectors/meta_connect.py
post_text(local_user_id, message) -> {status, post_id, page_name}
post_image(local_user_id, image_path, caption="") -> {status, post_id, page_name}
    └── _get_first_page(user)  # resolves page_id + page_access_token

# Instagram — app/connectors/instagram_connect.py
post_image(local_user_id, image_url, caption="") -> {status, media_id, username}
    # image_url MUST be public HTTPS; two-step container→publish

# Threads — app/connectors/threads_connect.py
post_text(local_user_id, text) -> {status, thread_id, username}
post_image(local_user_id, image_url, text="") -> {status, thread_id, username}
    # two-step container→publish; image_url MUST be public HTTPS

# Telegram — app/connectors/telegram_connect.py
send_message(chat_id, text) -> {status: sent}

# WhatsApp Web — app/connectors/whatsapp_connect.py
send_message_to_group(group_name, text) -> {status}
add_group(user, name) / remove_group(user, group_id) / list_groups(user)
check_session_health(user)  # auto-logout pulse
```

## 4.2 Connect-Flow Functions (all connectors)

```python
get_authorize_url(state) -> url            # build OAuth URL
complete_connect_flow(user, code, ...) -> {status, identity}
get_connection_status(user) -> {status, identity/profile}
disconnect(user) -> {status: disconnected}
```

## 4.3 AI Provider Functions

```python
# app/providers/groq_client.py — chat/reasoning via Groq free tier
# app/providers/openrouter_client.py — model failover
# app/providers/groq_tts.py
generate_speech(text, voice="autumn") -> {ok, output_path}   # Orpheus, ~95ms
# app/providers/image_gen.py
generate_image(prompt) -> {ok, output_path}                  # Pollinations, free
```

## 4.4 Portal Functions

```python
# app/portal/auth.py
validate_work_email(email) -> (bool, msg)        # blocks free-mail w/ warning
validate_password_strength(pw) -> (bool, msg)    # 12+ chars
hash_password(pw) -> (hash, salt)
verify_password(pw, hash, salt) -> bool
is_locked_out(user) -> bool                       # failed-attempt lockout
record_failed_login(user, db) / reset_failed_logins(user, db)
```

## 4.5 Orchestration Helpers (main.py)

```python
_resolve_image_local(image_url) -> local_path | None      # remote→temp download
_make_public_image_url(image_ref) -> public_url | None    # local→public URL
_log_post(results, text)                                   # append post_log.jsonl
_oauth_start(module, key) / _oauth_callback(...)           # generic OAuth routes
```

---

# 5. ROADMAP

## Phase 1 — Posting Core (IN PROGRESS)
- [x] X text+image, permanent auth ← **production ready**
- [ ] **Oracle gateway live:** reserved IP attached → WireGuard → Caddy → DNS → Pi .env → Meta whitelists
- [ ] Facebook connect+post (POES app, fixed-domain callback)
- [ ] Instagram direct connect+post (Business acct + fixed-domain callback)
- [ ] Threads reconnect+post (POES app creds)
- [ ] Pi systemd unit (auto-start on boot)
- [ ] $1 budget alarm in Oracle Billing

## Phase 2 — Automation
- [ ] Cron scheduler on Pi (peak-time windows SA/USA/international, varied jitter, 5/day/platform cap)
- [ ] News research + Ground News bias vetting (so-what/who/why/where/when filter applied to stories)
- [ ] Watcher bot (story-break early posting)
- [ ] Daily PDF activity log
- [ ] Hashtag + group mention generator
- [ ] Engagement analytics pull per platform
- [ ] Conservative meme sourcing pipeline (Reddit/forums curation for repost)

## Phase 3 — Business
- [ ] Package/subscription engine (FB-only / FB+IG / Full Meta / Everything + X)
- [ ] Payment: PayPal, Ko-fi, BuyMeACoffee, BTC, ETH (tip-first model)
- [ ] Onboarding questionnaire → Telegram approval → calendar
- [ ] Consultant assignment + company-email allocation
- [ ] Newsletter module (client-brings-own-SMTP)
- [ ] Meta App Review submissions (when first paying client needs it)

## Phase 4 — Scale
- [ ] WordPress-plugin packaging per module (SiteGround shared-hosting deploy)
- [ ] Multi-server split + optional load balancer
- [ ] Platform watchlist refresh (deep-dive: GETTR, Gab, DLive APIs)

## Phase 5 — Media (exploratory)
- [ ] Video/reel generation with stock images + Orpheus voiceover
- [ ] Clipping/editing tooling (OpenRouter-powered, admin level)
- [ ] Client-portal TTS answers (Orpheus reads replies to client questions)

---

# 6. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-08-17 | Project inception — social media manager concept |
| v1.5 | 2026-08-25 | Portal auth, connector framework, Render deploy |
| v1.8 | 2026-09-04 | GitHub established; Pi chosen as 24/7 host; X image pipeline |
| v1.9 | 2026-09-05 | X OAuth 1.0a media upload; auto-refresh on 401 |
| v2.0 | 2026-09-07 | X permanent posting solved (v2+OAuth1); Meta split into 3 standalone connectors with full posting; master document created |
| v2.1 | 2026-09-08 | Oracle Cloud free-tier gateway architecture (WireGuard + Caddy + smpf.finwatchpro.net) replacing quick tunnel; Meta POES/smpf app credential set finalized; deployment doc split out; X OAuth1 401 root-cause added to issue log |

---

*Document: SMPF-Master-Document.md in the repo root — commit with code changes. Update the version table on every milestone. Companion: SMPF-DEPLOYMENT-v1.0.0.md.*
