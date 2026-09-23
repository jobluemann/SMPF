# SMPF — Milestone Status Report
**Date:** 2026-08-25
**Project:** Social Media Platform Framework (SMPF)
**Location:** `C:\Users\RudiOosthuizen\smpf`

---

## Milestone 1: Core Infrastructure

- **🟢 FastAPI server** — Running, 47 routes registered, no crashes
- **🟢 User auth (portal)** — Register/login/logout with work-email validation, password lockout, sessions
- **🟢 SQLite database** — `data/smpf.db`, users table, auto-migration on startup
- **🟢 Jinja2 templates** — Dashboard, login, register, status pages
- **🟢 Analytics API** — Chart.js dashboard with connection stats, content history, live counters

---

## Milestone 2: AI Content Generation

- **🟢 Image generator** — Pollinations.ai integration, 2 images generated
- **🟢 Voice generator (Orpheus)** — Groq TTS, 6 voices, 1 audio file generated
- **🟢 File serving** — `/generated/{filename}` and `/audio/{filename}` routes
- **🔴 Video generation** — No free API confirmed; research paused per your instruction

---

## Milestone 3: Platform Connectors (OAuth)

| Platform | Status | Details |
|----------|--------|---------|
| **X (Twitter)** | 🟢 DONE | `@jobluemann` — OAuth 2.0 with PKCE, live-tested |
| **Meta (Facebook)** | 🟢 DONE | Page: "Jo Bluemann" — OAuth live-tested |
| **Meta (Instagram)** | 🟡 IN PROGRESS | Business account ready. **Blocker:** Instagram not linked to Facebook Page. Go to [business.facebook.com](https://business.facebook.com) → link IG to Page → click Reconnect Meta |
| **Threads** | 🔴 NOT CONNECTED | Separate OAuth app. Credentials in `.env`. Needs manual connect |
| **YouTube** | 🔴 NOT CONNECTED | No `GOOGLE_CLIENT_ID` in `.env` |
| **Reddit** | 🔴 NOT CONNECTED | No `REDDIT_CLIENT_ID` in `.env` |
| **Minds** | 🔴 NOT CONNECTED | No `MINDS_CLIENT_ID` in `.env` |
| **VK** | 🔴 NOT CONNECTED | No `VK_CLIENT_ID` in `.env` |
| **Google Drive** | 🔴 NOT CONNECTED | Module built, needs OAuth connect |

### Meta Unification (NEW — Milestone 3b)
- **🟢 Meta connector v4** — One login for Facebook + Instagram. `instagram_business_basic` scope added back
- **🟢 Dashboard grouping** — Meta shown as unified card with FB Page + IG sub-status
- **🟢 Instagram direct fallback** — Still available at `/status` if Meta linking fails
- **🟡 HTTPS→HTTP auto-fix** — Instagram localhost callback now auto-corrects for dev

---

## Milestone 4: Publishing Layer

- **🔴 NOT STARTED** — No platform has publish/post code yet
- **🔴 Scheduling engine** — Not built
- **🔴 Auto-poster** — Not built

---

## Milestone 5: News Research & Meme Scraping

- **🔴 NOT STARTED** — Ground.News integration
- **🔴 NOT STARTED** — Reddit conservative meme scraper
- **🔴 NOT STARTED** — Trending topics engine

---

## Milestone 6: Client Portal & Payments

- **🔴 NOT STARTED** — WordPress plugin
- **🔴 NOT STARTED** — Payment gateway (PayFast/PayPal/crypto analysis)
- **🔴 NOT STARTED** — Multi-client profiles
- **🔴 NOT STARTED** — Subscription management

---

## Milestone 7: Additional Features

- **🔴 Email newsletter** — Provider integration not started
- **🔴 Google Drive plugin** — Module built but not connected
- **🔴 Daily PDF log** — Not built
- **🔴 Video clipping** — Research only, no implementation

---

## Credentials Status

| Service | Has Credentials |
|---------|-----------------|
| Groq API | 🟢 Yes |
| OpenRouter API | 🟢 Yes |
| X OAuth 2.0 | 🟢 Yes |
| Meta App | 🟢 Yes |
| Threads App | 🟢 Yes |
| Instagram Direct App | 🟢 Yes |
| YouTube/Google | 🔴 No |
| Reddit | 🔴 No |
| Minds | 🔴 No |
| VK | 🔴 No |

---

## Next Actions (Recommended Priority)

1. **🟡 Link Instagram to Facebook Page** — Go to Meta Business settings, link IG Business account to "Jo Bluemann" page, then click Reconnect Meta on dashboard
2. **🔴 Add missing OAuth credentials** — YouTube, Reddit, Minds, VK (get Client IDs from each platform's developer console)
3. **🔴 Build publish layer** — Code to actually post content to connected platforms
4. **🔴 News/meme research engine** — Ground.News API, Reddit scraper

---

## File Manifest

```
smpf/
├── main.py                          # v11 — 47 routes, unified Meta
├── app/
│   ├── config.py                    # v9 — finwatchpro.net defaults
│   ├── connectors/
│   │   ├── x_connect.py             # v2 — OAuth 2.0 PKCE
│   │   ├── meta_connect.py          # v4 — unified FB+IG
│   │   ├── instagram_connect.py     # v2 — direct IG fallback
│   │   ├── threads_connect.py       # v1 — separate Threads OAuth
│   │   ├── youtube_connect.py       # v1 — ready to connect
│   │   ├── reddit_connect.py        # v1 — ready to connect
│   │   ├── minds_connect.py         # v1 — ready to connect
│   │   ├── vk_connect.py            # v1 — ready to connect
│   │   └── admin_only/              # Gettr admin (not in main.py)
│   ├── integrations/
│   │   └── google_drive.py          # v1 — OAuth + upload
│   ├── providers/
│   │   ├── groq_client.py
│   │   ├── groq_tts.py              # Orpheus voice
│   │   ├── image_gen.py             # Pollinations.ai
│   │   └── openrouter_client.py
│   └── portal/
│       ├── auth.py
│       ├── database.py
│       └── models.py
├── frontend/templates/
│   ├── base.html
│   ├── dashboard.html               # v3 — unified Meta card + charts
│   ├── login.html
│   └── register.html
├── data/
│   ├── smpf.db                      # SQLite
│   ├── x_connections.json           # @jobluemann
│   ├── meta_connections.json        # Jo Bluemann page
│   ├── capability_report.json
│   ├── generated_images/            # 2 images
│   └── tts_output/                  # 1 audio
└── requirements.txt
```
