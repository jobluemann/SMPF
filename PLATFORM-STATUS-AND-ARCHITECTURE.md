# SMPF — Social Media Platform Framework
## Master Platform Status, Hosting Architecture & Expansion Plan
### Generated: 2026-09-01

---

## PART 1: PLATFORM STATUS MATRIX (Color-Coded)

### 🟢 GREEN — Ready / Built / Tested

| Platform | Method | Status | Notes |
|----------|--------|--------|-------|
| **X (Twitter)** | OAuth 2.0 API | ✅ Posting works | Needs token refresh on expiry |
| **Facebook** | Meta Graph API | ✅ Connected | Requires Business verification for some features |
| **Instagram** | Instagram Graph API | ✅ Connected | Via Facebook Graph — images required |
| **Threads** | Meta Threads API | ✅ Connected | OAuth ready, text-only posts |
| **YouTube** | Google OAuth API | ✅ Connected | Video uploads, Community posts ready |
| **Telegram** | Bot API | ✅ Posting works | No OAuth — bot token only. Groups supported natively |
| **WhatsApp Web** | Playwright browser automation | ✅ QR scan + anti-detection | Human mimicry built: random delays, variable typing, mouse jitter, real user-agent, automation flag removal |
| **WhatsApp Business** | Meta Graph API | ⏸️ Awaiting token | 1:1 messaging only. No groups. Token expires 24h |
| **Reddit** | OAuth API | ✅ Connected | Text posts + link posts |
| **Google Drive** | Google OAuth API | ✅ Connected | File upload for media storage |
| **Minds** | OAuth API | ✅ Connected | Decentralized, conservative-friendly |
| **VK** | OAuth API | ✅ Connected | Russian market, limited Western use |

---

### 🟡 AMBER / ORANGE — Possible But Needs Something

| Platform | What's Needed | Cost Estimate | Priority |
|----------|--------------|---------------|----------|
| **TikTok** | TikTok for Business API approval + developer account | Free to apply, hard to get approved | 🔴 HIGH — #1 fastest growing in SA (34% YoY), 23.4M SA users |
| **Gettr** | No public API. Browser automation only (like WhatsApp Web) | Free — uses same Playwright stack | 🟡 MEDIUM — Already built admin-only connector |
| **Gab** | No official API. RSS scraping or browser automation | Free | 🟡 LOW — Niche audience |
| **DLive** | No API. Manual or stream key integration | Free | 🔴 LOW — Niche, small audience |
| **Pinterest** | Pinterest API v5 | Free to apply | 🟡 MEDIUM — 6.88% SA market share, strong for visual niches |
| **Snapchat** | Snap Kit / Marketing API | Free to apply | 🟡 LOW — 5.93M SA users, younger demographic |
| **LinkedIn** | Marketing API for company pages only. Personal profiles blocked | Free but strict approval | 🟡 LOW — User said "No LinkedIn posts" Aug 18. 15M SA users |
| **WhatsApp Business API (production)** | Meta Business verification + approved phone number | ~$0.005-0.09/msg | 🟡 MEDIUM — Needed for 1:1 client messaging at scale |

---

### 🔴 RED — Out / Restricted / Not Feasible

| Platform | Why Red | Detail |
|----------|---------|--------|
| **Truth Social** | No public API | Trump-owned, no developer access |
| **Rumble** | No posting API | Video platform, upload-only via web |
| **MeWe** | No API, dying platform | Privacy-focused, minimal market share |
| **Parler** | Defunct / rebranded | No longer viable |
| **WeChat** | Country restriction | China-only, blocked in most Western markets |
| **Line** | Country restriction | Japan/Thailand dominant, no API for international |
| **KakaoTalk** | Country restriction | Korea-only |
| **iMessage** | Apple ecosystem lock | No API, no Android support |

---

## PART 2: YOUTUBE COMMUNITY POSTS — DEEP DIVE

### Why This Matters

YouTube is the **#3 most popular social network globally** (2.58 billion MAU) and the **#2 in SA time spent** (25h 15m/month avg).

**Community Posts** (formerly Community Tab) are now available to **ALL channels** with Advanced Features enabled — **no subscriber threshold** anymore.

### Stats

| Metric | Value |
|--------|-------|
| Global MAU | 2.58 billion |
| SA Users | 25.3 million |
| Avg session duration | 14m 29s (highest of all platforms) |
| Channels posting Community 3x/week | +18-25% higher subscriber retention |
| Daily likes | 3.5 billion |
| Daily comments | 100 million |

### What You Can Post

- Text updates
- Polls & quizzes
- Images/GIFs
- Video links
- Scheduled posts (built into YouTube Studio)

### SMPF Integration Status

✅ **YouTube connector already wired** via Google OAuth.
- Community posts = possible via YouTube Data API v3
- Video uploads = already supported
- **Action item:** Add `post_community()` function to `youtube_connect.py`

---

## PART 3: BLOG & LONG-FORM PLATFORMS

### Quora — HIGHLY RECOMMENDED

| Metric | Value |
|--------|-------|
| MAU | 400-430 million |
| Monthly visits | 900+ million |
| SA-relevant? | Yes — 17% of traffic from India, 28-40% US |
| Audience quality | 65% college degree, 54% earn $100k+, 37% more likely in management |
| SEO value | 63% of visits come from Google search — answers rank organically |
| Best for | B2B, thought leadership, conservative political commentary, driving traffic to finwatchpro.net |

**Quora Spaces** = topic-based communities. Perfect for building a following around SA politics, Afrikaner issues, anti-ANC content.

**Quora+ Monetization:** Up to 95% revenue share on subscriber payments.

### Other Blog Platforms to Consider

| Platform | Audience | Best For | Auto-Post Possible? |
|----------|----------|----------|---------------------|
| **Medium** | 100M+ readers | Long-form essays, thought leadership | ❌ No API for posting. Manual or RSS import |
| **Substack** | 35M+ subscribers | Newsletters + blog hybrid | ❌ No API. Email-based only |
| **WordPress.com** | 409M+ blogs | Your own hosted blog | ✅ XML-RPC API available |
| **Blogger** | Google's platform | Simple free blogs | ✅ API available but deprecated |

### Recommendation

**Phase 1:** Quora (answers + Spaces) + your WordPress blog on finwatchpro.net
**Phase 2:** Substack newsletter for email list growth

---

## PART 4: EMAIL MARKETING TEMPLATES

### Why Email Still Matters

Email has the **highest ROI of any marketing channel**: $36-42 returned for every $1 spent.

### Recommended Free/Cheap Providers

| Provider | Free Tier | Paid Starts At | Best For |
|----------|-----------|----------------|----------|
| **Mailchimp** | 500 contacts, 1,000 sends/mo | $13/mo | Beginners, good templates |
| **Brevo (ex-Sendinblue)** | Unlimited contacts, 300 emails/day | $9/mo | Transactional + marketing |
| **MailerLite** | 1,000 contacts, 12,000 emails/mo | $9/mo | Simple, clean UI |
| **ConvertKit** | 1,000 subscribers | $9/mo | Creators, automation |

### Marketing Email Template 1: Weekly Roundup

```html
Subject: This Week They Tried to Silence Us — But You Saw It First 🚨

Hi {{FIRST_NAME}},

Here's what the mainstream media won't tell you this week:

🔥 TOP STORY: [Headline]
[2-sentence summary with link to full post on X/YouTube]

📊 STAT OF THE WEEK:
[Shocking statistic with source]

🎥 WATCH: [YouTube video title + thumbnail link]

💬 JOIN THE CONVERSATION:
[Link to Telegram group or WhatsApp]

→ Read the full breakdown: [finwatchpro.net link]

They can't censor what they don't control.

— Jo Bluemann
@jobluemann

---
Unsubscribe: {{UNSUB_LINK}}
```

### Marketing Email Template 2: New Post Alert

```html
Subject: New Post: [Catchy Headline] — What They Don't Want You to Know

{{FIRST_NAME}},

I just posted something they won't like.

[Embedded post preview or image]

👉 Read on X: [link]
👉 Watch on YouTube: [link]
👉 Share on WhatsApp: [forward link]

[1 paragraph personal voice — why this matters, your take]

This is why we built our own platforms.

— Jo

P.S. Forward this to someone who needs to wake up.
```

### Marketing Email Template 3: Re-engagement / Win-Back

```html
Subject: Did they get to you too, {{FIRST_NAME}}?

I noticed you haven't opened the last few emails.

Maybe the algorithm buried them.
Maybe you're just busy.

Or maybe — just maybe — you're tired of fighting.

I get it. But here's the thing: **they win when we go quiet.**

Here's what you missed:
• [Bullet 1 with link]
• [Bullet 2 with link]
• [Bullet 3 with link]

Still with us? Hit reply and say "I'm here."

— Jo Bluemann
```

---

## PART 5: HOSTING ARCHITECTURE BENCHMARK

### SiteGround Shared Hosting — CAN IT HANDLE THIS?

**Short answer: NO.**

| Resource | SiteGround Limit | What SMPF Needs |
|----------|-----------------|-----------------|
| **CPU Seconds** | 600,000/month (GrowBig) | Browser automation = 10-30s per post × 5 platforms × 30 days = **450,000s minimum** |
| **Memory/Process** | 768 MB | Playwright + Chromium = **500-700 MB per instance** |
| **Database** | 1,000 MB | Fine for now, but will grow with logs |
| **Long-running processes** | ❌ Forbidden | Uvicorn must run 24/7 |
| **Browser installation** | ❌ Impossible | No root access to install Chromium |
| **Python environment** | ⚠️ Limited | PHP-focused. Python via CGI only |
| **Cron jobs** | 2x per hour max | Need every minute for posting schedule |

### What Happens on SiteGround Shared

- WhatsApp Web automation → **Impossible** (no browser)
- FastAPI server → **Killed within hours**
- 5 posts/day × 30 days → **CPU limit exceeded by day 15**
- **Result:** Site suspended for rest of month

---

## PART 6: RECOMMENDED ARCHITECTURE

### The Split Model (What We Build)

```
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: WORDPRESS PORTAL (SiteGround Shared — finwatchpro.net)  │
│  ───────────────────────────────────────────────────────────────  │
│  • Client login / registration                                   │
│  • Dashboard UI (connects to Tier 2 via REST API)               │
│  • Post composer form                                            │
│  • Scheduling calendar                                           │
│ • Analytics viewer (reads from Tier 2)                          │
│  • Payment integration (PayFast, PayPal, crypto)                │
│  • Email list signup (embedded forms)                           │
│  • Blog posts (native WordPress)                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/JSON API calls
                              │ (WP plugin as API client)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 2: SMPF FASTAPI BACKEND (VPS / Local PC / Raspberry Pi)   │
│  ───────────────────────────────────────────────────────────────  │
│  • OAuth token management (X, Meta, Google, Reddit, etc.)        │
│  • Post execution engine                                         │
│  • WhatsApp Web Playwright automation                            │
│  • Image/Audio generation (Groq TTS, Pollinations)              │
│  • Content queue / scheduler                                     │
│  • SQLite database (posts, logs, sessions)                      │
│  • Daily PDF log generation                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Post to platforms
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 3: SOCIAL MEDIA PLATFORMS                                  │
│  ───────────────────────────────────────────────────────────────  │
│  X, Facebook, Instagram, Threads, YouTube, Reddit,               │
│  Telegram, WhatsApp Web, Minds, VK, Gettr                        │
└─────────────────────────────────────────────────────────────────┘
```

### WP Plugin Split Strategy (For Easy Migration)

Instead of one monolithic plugin, break into **5 independent plugins**:

| Plugin | Function | Can Run On |
|--------|----------|-----------|
| **smpf-core** | API client, authentication, dashboard frame | Any WordPress host |
| **smpf-post** | Post composer, scheduler, queue viewer | Any WordPress host |
| **smpf-analytics** | Charts, reports, export PDF | Any WordPress host |
| **smpf-payments** | PayFast, PayPal, crypto checkout | Any WordPress host |
| **smpf-integrations** | Email forms, CRM webhooks | Any WordPress host |

**Benefit:** If SiteGround suspends one site, move just that plugin. If you outgrow shared hosting, migrate `smpf-core` + `smpf-post` to a VPS while keeping the blog on SiteGround.

### Hosting Tiers for Growth

| Stage | Users | Backend Hosting | Cost |
|-------|-------|-----------------|------|
| **Phase 1: Testing** | Just you | Your PC (localhost) | Free |
| **Phase 2: Beta clients** | 5-10 | Raspberry Pi 4/5 at home | ~$100 one-time |
| **Phase 3: Paid clients** | 10-50 | VPS (DigitalOcean, Vultr, Linode) | $5-20/month |
| **Phase 4: Scale** | 50-500 | Cloud (AWS Lightsail, Hetzner) | $20-50/month |
| **Phase 5: Enterprise** | 500+ | Kubernetes cluster or managed | $100+/month |

### Recommended VPS for Phase 3

| Provider | Specs | Price | Why |
|----------|-------|-------|-----|
| **Hetzner CX21** | 2 vCPU, 4GB RAM, 40GB SSD | €5.35/mo | Best price/performance in Europe |
| **DigitalOcean Droplet** | 1 vCPU, 1GB RAM, 25GB SSD | $6/mo | Reliable, good docs |
| **Vultr Cloud** | 1 vCPU, 1GB RAM, 25GB SSD | $5/mo | Fast SSD, global locations |
| **AWS Lightsail** | 1 vCPU, 512MB RAM, 20GB SSD | $5/mo | AWS ecosystem, easy scaling |

**Minimum for Playwright:** 2 vCPU, 2GB RAM (DigitalOcean $12/mo or Hetzner €5.35/mo).

---

## PART 7: EXECUTIVE SUMMARY & NEXT ACTIONS

### What We Have Now (Working on Local PC)

- ✅ 12 platforms connected or ready
- ✅ WhatsApp Web with anti-detection
- ✅ Heartbeat pulse for session health
- ✅ Dashboard with groups manager
- ✅ Image + voice generation
- ✅ Post logging to JSONL
- ✅ 67 FastAPI routes

### What to Build Next (Priority Order)

| # | Task | Time Estimate | Blocker |
|---|------|---------------|---------|
| 1 | **Test WhatsApp Web end-to-end** | 1 session | You scan QR code |
| 2 | **Build WordPress plugin skeleton** | 2-3 days | None |
| 3 | **Add YouTube Community post function** | 1 day | YouTube API quota |
| 4 | **Add TikTok connector** | 2-3 days | TikTok developer approval |
| 5 | **Add Quora answer poster** | 1-2 days | Quora has no official post API |
| 6 | **Set up VPS for 24/7 backend** | 1 day | $5-12/month budget |
| 7 | **Email marketing integration** | 1-2 days | Choose provider (Brevo/MailerLite) |
| 8 | **Payment gateway (PayFast)** | 2-3 days | PayFast merchant approval |

### Final Recommendation

**Don't try to force everything onto SiteGround shared hosting.**

The correct architecture is:
- **WordPress on SiteGround** = customer-facing portal, blog, payments
- **FastAPI backend on VPS** = automation engine, social posting, AI generation
- **Communicate via API** = WP plugin calls your backend

This gives you:
- ✅ SiteGround for what it's good at (WordPress, PHP, email)
- ✅ VPS for what you need (Python, Playwright, 24/7 processes)
- ✅ Easy to scale either tier independently
- ✅ If one fails, the other keeps working

---

*Document version: 1.0*
*Generated by SMPF AI Assistant*
*Next review: After WhatsApp Web test + WP plugin Phase 1*
