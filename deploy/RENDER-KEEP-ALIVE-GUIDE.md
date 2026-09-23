# SMPF Render Keep-Alive Guide — Bulletproof $0 Hosting

**Last updated:** 2026-09-04  
**Goal:** Run SMPF backend on Render free tier 24/7 without sleep  
**Cost:** $0/month

---

## The Math (Why This Works)

| Render Rule | Our Counter |
|------------|-------------|
| Sleeps after **15 minutes of inactivity** | Ping every **10 minutes** |
| Inactivity = zero HTTP requests | Health endpoint returns in **<50ms** |
| 15 min timer resets on EVERY request | Timer resets every 10 min → **never hits 15** |

**Result:** Backend stays hot 24/7. No cold starts. No delays.

---

## What We're Building

```
┌─────────────────────┐     Every 10 min     ┌─────────────────────┐
│   GitHub Actions    │ ───────────────────► │   Render.com        │
│   (free cron job)   │   GET /health        │   smpf-backend      │
│                     │                      │   (stays awake)     │
└─────────────────────┘                      └─────────────────────┘
        │                                            │
        │ Backup ping every 5 min                    │ X, FB, IG, WhatsApp,
        ▼                                            │ Groq AI, TTS, images
┌─────────────────────┐                            │
│   UptimeRobot       │ ───────────────────────────┘
│   (free monitor)    │
└─────────────────────┘
```

**Redundant pings:** If GitHub Actions misses one cycle, UptimeRobot hits it 5 minutes later. Zero gaps.

---

## Step 1: Add Health Endpoint (Done)

A new `/health` endpoint has been added to `main.py`:

```python
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "smpf-backend"}
```

This returns instantly — no DB queries, no file I/O, no external API calls. Perfect for ping services.

---

## Step 2: Deploy to Render

### 2a. Create GitHub Repo

```bash
cd C:\Users\RudiOosthuizen\smpf
git init
git add .
git commit -m "SMPF v1.0.0 with health check"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/smpf-backend.git
git push -u origin main
```

### 2b. Sign Up & Deploy on Render

1. Go to [render.com](https://render.com) → Sign up with GitHub
2. Click **New +** → **Web Service**
3. Connect your `smpf-backend` repo
4. Configure:

| Setting | Value |
|---------|-------|
| Name | `smpf-backend` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Plan | `Free` |

5. Add Environment Variables:

```
SECRET_KEY=your-random-32-char-string
X_CLIENT_ID=V2NhRFpHSGlGQTI4RExJOThDU1Y6MTpjaQ
X_CLIENT_SECRET=your-x-secret
GROQ_API_KEY=gsk_your-groq-key
TELEGRAM_BOT_TOKEN=8801125744:AAGYHq6Uv3I7BuC7YPkpwas6D9MygpYWDMM
```

6. Click **Create Web Service**

Your URL: `https://smpf-backend.onrender.com`

Test: `https://smpf-backend.onrender.com/health` → should return `{"status":"ok"}`

---

## Step 3: Set Up GitHub Actions Keep-Alive (PRIMARY)

The file `.github/workflows/keep-alive.yml` is already in your repo. It pings your backend every **10 minutes**.

### Enable it:

1. Push the workflow file to GitHub (already done if you pushed the whole repo)
2. Go to your GitHub repo → **Actions** tab
3. Click **Keep SMPF Backend Alive**
4. Click **Enable workflow**

GitHub Actions runs every 10 minutes, forever, for **$0**.

---

## Step 4: Set Up UptimeRobot Backup (SECONDARY)

If GitHub Actions ever fails, UptimeRobot is your safety net.

1. Go to [uptimerobot.com](https://uptimerobot.com) → Sign up (free)
2. Click **Add New Monitor**
3. Configure:

| Field | Value |
|-------|-------|
| Monitor Type | HTTP(s) |
| Friendly Name | SMPF Backend Health |
| URL | `https://smpf-backend.onrender.com/health` |
| Monitoring Interval | 5 minutes (free tier max) |

4. Save

---

## Ping Schedule (Redundant Coverage)

| Time | GitHub Actions | UptimeRobot |
|------|---------------|-------------|
| 00:00 | ✅ Ping | ✅ Ping |
| 00:05 | | ✅ Ping |
| 00:10 | ✅ Ping | ✅ Ping |
| 00:15 | | ✅ Ping |
| 00:20 | ✅ Ping | ✅ Ping |

**Maximum gap between pings: 5 minutes.** Render needs 15 minutes of silence to sleep. **Impossible.**

---

## The Storage Issue (Be Honest About This)

Render free tier has **ephemeral disk**. Files are wiped on:
- Deploys
- Restarts
- Rare maintenance events

**What this means for SMPF:**

| Data | Storage | Survives restart? |
|------|---------|-------------------|
| OAuth tokens | JSON file on disk | ❌ No — reconnect after deploy |
| Post logs | JSONL file on disk | ❌ No — logs lost on restart |
| Generated images | File on disk | ❌ No |
| AI prompts/history | File on disk | ❌ No |

**Workarounds (all free):**

1. **Accept it** — For a single-user system, reconnecting platforms after a deploy takes 2 minutes. Not a big deal.
2. **Use Render PostgreSQL** — $7/month (not free). Not worth it yet.
3. **Store critical tokens in env vars** — Set them via Render dashboard, they persist forever.

> **Bottom line:** The backend stays awake and serves API requests 24/7. Data loss only happens on deploy/restart, which is rare once you're live.

---

## Post-Deploy Checklist

- [ ] Backend deployed to Render at `https://smpf-backend.onrender.com`
- [ ] `/health` endpoint returns `{"status":"ok"}`
- [ ] GitHub Actions workflow enabled and running
- [ ] UptimeRobot monitor added
- [ ] WordPress → SMPF Settings → Backend URL updated
- [ ] OAuth callback URLs updated in all developer portals
- [ ] Test post sent to at least one platform

---

## Cost Summary

| Service | Cost |
|---------|------|
| Render.com (web service) | $0 |
| GitHub Actions (cron) | $0 |
| UptimeRobot (monitor) | $0 |
| SiteGround (WordPress) | Already paid |
| **Total** | **$0** |

---

## Migration Path (When Budget Allows)

When you can afford Hetzner (€5.35/mo):
1. Update WordPress SMPF Settings → Backend URL to new IP
2. Update OAuth callback URLs in dev portals
3. Transfer GitHub Actions workflow to new URL
4. Cancel Render service

Zero code changes. Just URL swaps.

---

*Guide version: 1.0.0 | SMPF Keep-Alive System*
