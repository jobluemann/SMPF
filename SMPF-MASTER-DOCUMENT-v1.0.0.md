# Social Media Platform Framework (SMPF)

**Project Master Document**  
**Version:** 1.0.0  
**Date:** 2026-09-02  
**Author:** Jo Bluemann (Digital Marketing / Social Media Growth)  
**Maintainer:** AI Development Partner  
**Repository:** Private GitHub (oostech / finwatchpro)

---

## 1. Executive Summary

**SMPF** is a hybrid social-media automation platform built on a **Python FastAPI backend** and a **WordPress frontend/client portal**. It is designed to operate entirely on free-tier infrastructure — free AI model APIs, free hosting where possible, and open-source components — while delivering professional-grade social media management, content creation, scheduling, and analytics.

The platform targets:
- **Individual content creators** (initially Jo Bluemann's personal brand)
- **Digital marketing agency clients** who purchase posting packages
- **Future SaaS subscribers** who self-serve via the WordPress portal

**Core Philosophy:** Conservative, logic-driven commentary on politics, history, and culture; pro-free-speech; anti-big-government; Christian-values foundation; unapologetically South African (Afrikaner) and proud. All AI-generated content reflects this worldview.

---

## 2. System Architecture

### 2.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER / VISITOR                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  WordPress Site │    │  FastAPI Backend     │    │  External APIs  │
│  (SiteGround)   │◄──►│  (VPS - Hetzner)     │◄──►│  Social Media   │
│                 │    │                      │    │  AI Models      │
│  - Client Portal│    │  - Scheduling        │    │  News Sources   │
│  - Dashboard    │    │  - Post Engine       │    │  Analytics      │
│  - Settings     │    │  - AI Content Gen    │    │                 │
│  - Donation Bar │    │  - Browser Automation│    │  X / Twitter    │
│                 │    │  - Analytics DB      │    │  Meta / FB      │
└─────────────────┘    └──────────────────────┘    │  Instagram      │
                                                   │  Threads        │
                                                   │  WhatsApp       │
                                                   │  Groq / OpenRouter
                                                   │  News APIs      │
                                                   └─────────────────┘
```

### 2.2 Backend (FastAPI)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI (Python) | REST API, async endpoints |
| **Scheduler** | APScheduler / Celery | Timed post execution |
| **Browser Automation** | Playwright + Chromium | Headless posting to platforms |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Posts, analytics, configs |
| **AI Content** | Groq API, OpenRouter free tiers | Text generation, meme ideas |
| **TTS** | Groq Orpheus | Voiceover for video content |
| **Image Gen** | Groq/OpenRouter + Plugin APIs | Memes, ad images, thumbnails |
| **Hosting** | Hetzner CX21 VPS (€5.35/mo) | 24/7 backend server |

### 2.3 Frontend (WordPress)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **CMS** | WordPress (SiteGround shared) | Client portal, landing pages |
| **Theme** | SMPF Portal (custom) | Neutral white, card-based UI |
| **Auth** | WP native + custom plugin | Client registration, login |
| **Payments** | PayPal, Ko-fi, BMC, Crypto | Tip-based + package billing |
| **API Bridge** | smpf-core plugin | Connects WP to FastAPI backend |

### 2.4 WordPress Plugin Architecture

All plugins are **modular, independent, and API-driven**.

| Plugin | Status | Purpose |
|--------|--------|---------|
| **smpf-core** | ✅ Built | API client, admin menu, dashboard, settings |
| **smpf-post** | ✅ Built | Post composer, scheduler UI, topic selector |
| **smpf-analytics** | ✅ Built | Charts, connection status, reports viewer |
| **smpf-payments** | ✅ Built | Donation bar, package tiers, payment links |
| **smpf-integrations** | ✅ Built | Email signup, CRM webhooks, Telegram alerts |

---

## 3. Design System

### 3.1 Visual Identity

| Element | Specification |
|---------|--------------|
| **Primary Background** | `#f6f7f7` (light grey) |
| **Card Background** | `#ffffff` (white) |
| **Primary Text** | `#1d2327` (near-black) |
| **Secondary Text** | `#646970` (grey) |
| **Accent / Links** | `#2271b1` (WordPress blue) |
| **Success** | `#00a32a` (green) |
| **Danger** | `#d63638` (red) |
| **Warning** | `#dba617` (amber) |
| **Donation Bar** | Gradient `#1a1a2e → #16213e` |
| **Banner Pulse** | Gradient `#f59e0b → #d97706` |

### 3.2 Typography
- **System font stack**: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif`
- **Base size**: 16px
- **Headings**: Bold, tight letter-spacing

### 3.3 Layout Principles
- **Container max-width**: 1200px
- **Card padding**: 20px
- **Border radius**: 4px (admin cards), 12px (donation bar)
- **Shadow**: `0 1px 1px rgba(0,0,0,0.04)` (subtle, flat)
- **Responsive breakpoint**: 768px

### 3.4 Component Patterns
- **Buttons**: Pill or rounded rectangle, solid colour
- **Forms**: Full-width inputs, 500px max, focus ring in accent blue
- **Tables**: Striped, hover highlight, uppercase headers
- **Alerts**: Left-border accent, light background

---

## 4. Platform Integration Matrix

| Platform | API Type | Auth Method | Status | Notes |
|----------|----------|-------------|--------|-------|
| **X (Twitter)** | REST API v2 | OAuth 2.0 + OAuth 1.0a | ✅ Connected | Tweet, media, polls |
| **Facebook** | Graph API | OAuth 2.0 | ✅ Connected | Pages + Groups |
| **Instagram** | Graph API | OAuth 2.0 (via FB) | 🟡 In Progress | Business/Creator account required |
| **Threads** | Graph API | OAuth 2.0 (via FB) | 🟡 In Progress | Requires FB app verification |
| **WhatsApp** | Business API | Meta Business | 🔴 Planned | WA Business account needed |
| **LinkedIn** | REST API | OAuth 2.0 | 🔴 Planned | Lower priority |
| **Gettr** | No official API | N/A | 🔴 Blocked | No API available |
| **Gab** | No official API | N/A | 🔴 Blocked | No API available |
| **Minds** | Limited API | OAuth | 🟡 Research | Under investigation |
| **DLive** | No API | N/A | 🔴 Blocked | No API available |
| **TikTok** | Research API | OAuth 2.0 | 🟡 Research | Limited access |
| **Telegram** | Bot API | Bot Token | ✅ Ready | `8801125744:AAGYHq6Uv3I7BuC7YPkpwas6D9MygpYWDMM` |
| **YouTube** | Data API v3 | OAuth 2.0 | 🟡 Planned | Community posts |
| **Quora** | No API | N/A | 🔴 Blocked | Manual/blog cross-post only |

---

## 5. AI Model Strategy

All content generation uses **free-tier APIs** to keep operational costs at zero.

| Provider | Models | Use Case | Status |
|----------|--------|----------|--------|
| **Groq** | Llama 3.1, Mixtral, Gemma | Primary text generation | ✅ Active |
| **OpenRouter** | Multiple free endpoints | Fallback / variety | ✅ Active |
| **Groq TTS** | Orpheus | Voiceover generation | ✅ Recommended |
| **Google Cloud TTS** | Standard voices | Backup voice option | 🟡 Backup |
| **Image Gen** | Built-in plugins / DALL-E free | Memes, thumbnails | 🟡 Limited |

---

## 6. Client Portal Specifications

### 6.1 User Flow

```
Landing Page → Register → Verify Email → Login → Dashboard
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
              Connect Social                    View Analytics                 Manage Subscription
              Media Accounts                    (posts, engagement)            (upgrade/downgrade)
                    │
                    ▼
              Opt-In to AI
              Management
                    │
                    ▼
              Questionnaire
              (topics, tone, goals)
                    │
                    ▼
              Choose Package
              → Pay
                    │
                    ▼
              Telegram Alert
              → Admin Approval
                    │
                    ▼
              Calendar Booking
              → Consultant Assignment
```

### 6.2 Package Tiers (Planned)

| Tier | Platforms | Posts/Day | Price | WhatsApp |
|------|-----------|-----------|-------|----------|
| **Starter** | X + 1 Meta | 3 | R299 / $17 | ❌ |
| **Growth** | X + All Meta + Telegram | 5 | R499 / $29 | ❌ |
| **Pro** | All + WhatsApp Groups | 10 | R799 / $47 | ✅ |
| **Enterprise** | Everything + AI Voice | Unlimited | Custom | ✅ |

### 6.3 Authentication Requirements
- Minimum 12-character password
- No free email providers (Gmail, Yahoo, etc.) — work domain required
- Warning disclaimer if free email used
- Two-factor recovery via secondary work email
- No social-login (security requirement)

### 6.4 Payment Methods
- **Tips/Donations**: PayPal, Ko-fi, Buy Me a Coffee, BTC, ETH (floating banner)
- **Subscriptions**: PayFast (SA), PayPal, Payoneer, Crypto (ETH/BTC wallets)
- **Billing**: Invoice on 25th, due last day of month, email notification
- **Access Control**: Payment status gates platform access

---

## 7. Content Strategy & AI Persona

### 7.1 Voice & Tone
- **Conservative**, unapologetic, logic-first
- **Anti-establishment**: hates big government, high taxes, globalist agendas
- **Pro-Christian values**: personal faith as foundation, not church-going performative
- **South African patriot**: Afrikaner identity, proud heritage
- **Anti-censorship**: welcomes labels (racist, xenophobe, antisemite, etc.) as badges
- **Statistics-driven**: always counters emotion with data and "shoe on the other foot" logic
- **Men's advocacy**: traditional gender roles, anti-feminist, pro-masculinity
- **Age/Experience**: 49-year-old BA (Hons) Business Management, IT-certified, dyslexic/ADHD/bipolar but sharp

### 7.2 Content Types
1. **News Commentary** — Top stories from Ground News (bias-ranked), re-framed through conservative lens
2. **Memes** — Sourced from Reddit, Facebook conservative groups; edited for brand alignment
3. **Original Posts** — AI-generated based on trending topics, scheduled for peak hours
4. **Video Scripts** — TTS voiceover + stock imagery/clips for Reels/TikTok/YouTube Shorts
5. **Blog Cross-Posts** — Quora, Medium, LinkedIn articles (long-form)

### 7.3 Posting Schedule
- **South Africa**: Morning story (~8-9 AM), afternoon story (~4-5 PM), meme (varies)
- **USA**: Aligned to EST/EDT peak hours
- **International**: Global trending topics, timezone-agnostic
- **Maximum**: 5 posts per platform per day (3 scheduled + 2 breaking news)
- **Randomization**: Post times vary by ±15 minutes to avoid bot detection

---

## 8. Hosting & Infrastructure

| Layer | Provider | Specs | Cost | Notes |
|-------|----------|-------|------|-------|
| **WordPress** | SiteGround (shared) | Standard | ~$15/mo | Domain: finwatchpro.net |
| **Backend VPS** | Hetzner CX21 | 2 vCPU / 4 GB RAM | €5.35/mo | Ubuntu 22.04, Docker optional |
| **Alternative VPS** | Hostinger VPS 2 | 2 vCPU / 8 GB RAM | ~$9/mo | If local LLM needed |
| **Alternative VPS** | DigitalOcean | 2 vCPU / 4 GB RAM | $12/mo | Droplet |
| **Domain** | SiteGround / Afrihost | finwatchpro.net / oostech.co.za | Included | DNS managed at registrar |

**Rationale:** SiteGround Cloud VPS ($80-100/mo) is 15× more expensive than Hetzner for the same RAM. Split architecture keeps costs minimal.

---

## 9. Security & Compliance

- **API Keys**: Stored in WordPress options table + backend `.env` file; never committed to Git
- **OAuth Tokens**: Encrypted at rest; refresh token rotation
- **HTTPS**: Required for all OAuth callbacks (localhost/loopback blocked by AD policy; use HTTPS)
- **Client Data**: GDPR-aligned opt-in; no data sold; client owns their social accounts
- **WhatsApp**: Business API only; no spam; opt-in groups only

---

## 10. Version Control & Development

| Component | Repository | Visibility | CI/CD |
|-----------|-----------|------------|-------|
| **Backend** | `smpf-backend` | Private GitHub | Manual deploy to VPS |
| **WP Plugins** | `smpf-wordpress-plugins` | Private GitHub | ZIP upload / FTP |
| **WP Theme** | `smpf-portal-theme` | Private GitHub | ZIP upload / FTP |
| **Docs** | `smpf-docs` | Private GitHub | Markdown only |

### 10.1 Versioning Scheme
- **Semantic Versioning**: `MAJOR.MINOR.PATCH`
- **Current**: `1.0.0`
- **Backend API version**: `/api/v1/...`

### 10.2 Deployment Workflow
1. Develop locally
2. Commit to private GitHub
3. Backend: `git pull` on VPS + `systemctl restart smpf`
4. WordPress: ZIP plugin/theme → Upload → Activate
5. Database migrations: Manual SQL or WP-CLI scripts

---

## 11. Roadmap & Milestones

### Phase 1 — Foundation ✅ (Current)
- [x] FastAPI backend scaffold
- [x] X/Twitter OAuth + posting
- [x] Facebook OAuth + posting
- [x] WordPress plugin suite (5 plugins)
- [x] SMPF Portal theme
- [x] Donation bar (tips)
- [x] Telegram bot integration

### Phase 2 — Meta Completion 🟡 (Next)
- [ ] Instagram Business API connection
- [ ] Threads posting via Meta Graph API
- [ ] Meta app verification (video submission)
- [ ] WhatsApp Business API connector
- [ ] Client registration + email verification

### Phase 3 — Expansion 🔴 (Future)
- [ ] LinkedIn auto-post
- [ ] TikTok Research API integration
- [ ] YouTube Community posts
- [ ] Gettr/Gab/Minds/DLive (if APIs become available)
- [ ] AI video generation pipeline
- [ ] Voice cloning (optional, low priority)
- [ ] Real-time social media watcher / breaking news bot

### Phase 4 — Monetization 🔴 (Future)
- [ ] Client self-service portal (packages, checkout)
- [ ] Subscription billing automation
- [ ] Payment gateway integration (PayFast, PayPal, Crypto)
- [ ] Consultant assignment workflow
- [ ] White-label option for resellers

---

## 12. Key Credentials & Configuration

> **WARNING:** This section contains sensitive references. Store actual secrets in `.env` files or WP options — never in version control.

### 12.1 X (Twitter) API
- OAuth 1.0a: Consumer Key + Secret
- OAuth 2.0: Client ID + Secret + Access Token + Refresh Token
- Bearer Token for read operations

### 12.2 Meta (Facebook/Instagram/Threads)
- App ID: `1274102852459915`
- App Secret: (redacted)
- Business Account: Required for Instagram/Threads
- Redirect URI: Must be HTTPS, whitelisted in app settings

### 12.3 Telegram
- Bot Token: `8801125744:AAGYHq6Uv3I7BuC7YPkpwas6D9MygpYWDMM`

### 12.4 Groq API
- Key: `gsk_...` (stored in backend `.env`)
- Endpoint: `https://api.groq.com/openai/v1/`

### 12.5 OpenRouter
- Key: (stored in backend `.env`)
- Endpoint: `https://openrouter.ai/api/v1/`

---

## 13. Daily Operations

### 13.1 Automated Workflow
1. **Morning**: Scrape top news (Ground News, RSS feeds, APIs)
2. **Bias Check**: Rank stories left/center/right; select balanced or counter-narrative angle
3. **Content Generation**: AI writes post in Jo's voice; includes hashtags, mentions
4. **Media Creation**: Generate meme/image or select from pool
5. **Queue**: Add to scheduler with randomized timestamp
6. **Post**: Execute via Playwright/API at scheduled time
7. **Log**: Record to daily PDF + analytics DB
8. **Monitor**: Track engagement, replies, shares

### 13.2 Daily Log (PDF)
- Platform, post time, content summary, media type
- Success/failure status, error messages
- Engagement metrics (likes, shares, replies, reach)
- Geographic breakdown (if available)

---

## 14. File Structure

```
smpf/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   ├── .env
│   ├── requirements.txt
│   └── Dockerfile
├── wordpress-plugins/
│   ├── smpf-core/
│   ├── smpf-post/
│   ├── smpf-analytics/
│   ├── smpf-payments/
│   └── smpf-integrations/
├── wordpress-theme/
│   ├── style.css
│   ├── functions.php
│   ├── header.php
│   ├── footer.php
│   ├── index.php
│   └── page.php
├── preview/
│   └── donation-bar-preview.html
└── docs/
    └── SMPF-MASTER-DOCUMENT-v1.0.0.md   <-- This file
```

---

## 15. Support & Maintenance

| Task | Frequency | Owner |
|------|-----------|-------|
| API token refresh | As needed (OAuth 2.0) | Automated |
| Content review | Daily | Jo Bluemann |
| Plugin updates | Monthly | Developer |
| Security audit | Quarterly | Developer |
| Backup (WP + DB) | Weekly | SiteGround auto |
| Backup (VPS) | Weekly | Manual / Cron |

---

## 16. Glossary

| Term | Definition |
|------|------------|
| **SMPF** | Social Media Platform Framework |
| **APScheduler** | Python job scheduler for timed tasks |
| **Playwright** | Headless browser automation library |
| **OAuth 2.0** | Authorization framework for API access |
| **TTS** | Text-to-Speech |
| **VPS** | Virtual Private Server |
| **WP** | WordPress |

---

*Document Version: 1.0.0*  
*Last Updated: 2026-09-02*  
*Next Review: Upon completion of Phase 2 (Meta platforms)*
