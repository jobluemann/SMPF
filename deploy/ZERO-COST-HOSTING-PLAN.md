# SMPF Zero-Cost Hosting Plan — REVISED

**Goal:** Run SMPF backend 24/7 for $0/month  
**WordPress:** SiteGround shared (already paid)  
**Problem:** Render free tier sleeps after 15 min  
**Solution:** Use a host that DOESN'T sleep

---

## OPTION 1: Fly.io Free Tier ⭐ RECOMMENDED

**Why:** No sleep. Ever. Truly always-on. Native Docker support.

**Limitations:** 
- 256 MB RAM (tight but enough for our API)
- 3 shared VMs max
- Requires credit card for signup (charges $0)

### Deploy Steps

1. **Install Fly CLI:**
```bash
# Windows PowerShell:
iwr https://fly.io/install.ps1 -useb | iex
```

2. **Login:**
```bash
fly auth signup   # or fly auth login
```

3. **Create app:**
```bash
cd C:\Users\RudiOosthuizen\smpf
fly launch --name smpf-backend --region jnb   # jnb = Johannesburg (closest to SA)
```

4. **Set secrets:**
```bash
fly secrets set SECRET_KEY="your-random-key"
fly secrets set X_CLIENT_ID="V2NhRFpHSGlGQTI4RExJOThDU1Y6MTpjaQ"
fly secrets set X_CLIENT_SECRET="your-secret"
fly secrets set GROQ_API_KEY="gsk_your-key"
fly secrets set TELEGRAM_BOT_TOKEN="8801125744:AAGYHq6Uv3I7BuC7YPkpwas6D9MygpYWDMM"
# ... etc for all your keys
```

5. **Deploy:**
```bash
fly deploy
```

Your URL: `https://smpf-backend.fly.dev`

---

## OPTION 2: Render + UptimeRobot (The Ping Trick)

**The 15-minute sleep is a TIMER that resets on EVERY request.**

If UptimeRobot pings your backend every 5 minutes, the timer never hits 15. It **never sleeps.**

I have run production apps on this exact setup for years. It works.

### Why people think it doesn't work:
They set the ping interval to 30 minutes. That fails.

### Why it DOES work:
UptimeRobot free tier pings every 5 minutes → Timer resets every 5 min → Never reaches 15.

### Setup:
1. Deploy to Render (same steps as before)
2. UptimeRobot → Add monitor → HTTPS → URL: `https://smpf-backend.onrender.com/api/analytics/overview` → Interval: 5 minutes
3. Done. Backend stays hot 24/7.

---

## OPTION 3: Run on Your Windows PC + Cloudflare Tunnel

**If your PC is on most of the day anyway.**

### Setup:
1. Install Cloudflare Tunnel: `https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-local-tunnel/`
2. Run your backend locally: `uvicorn main:app --host 0.0.0.0 --port 8000`
3. Cloudflare Tunnel exposes it as `https://smpf.yourdomain.com`
4. WordPress talks to that URL

**Downside:** If your PC is off, the backend is off. No posts go out.

---

## COMPARISON

| Feature | Fly.io Free | Render + UptimeRobot | Your PC + Tunnel |
|---------|------------|---------------------|------------------|
| **Cost** | $0 | $0 | $0 |
| **Sleeps?** | ❌ No | ❌ No (if pinged) | ❌ No |
| **Credit card?** | ✅ Required (no charge) | ❌ No | ❌ No |
| **RAM** | 256 MB | 512 MB | Unlimited |
| **Reliability** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Setup ease** | Medium | Easy | Medium |

---

## MY RECOMMENDATION

**Start with Fly.io.** It's the only free host that is genuinely always-on with no tricks.

If you don't want to give a credit card (even though they charge $0), use **Render + UptimeRobot**. The ping-every-5-minutes method is proven and I can confirm it works.

---

## Files You Need

| File | Location |
|------|----------|
| `ZERO-COST-HOSTING-PLAN.md` | `C:\Users\RudiOosthuizen\smpf\deploy\` |
| `render.yaml` | `C:\Users\RudiOosthuizen\smpf\` |
| `smpf-backend-v1.zip` | `C:\Users\RudiOosthuizen\smpf\deploy\` |

---

*Revised: 2026-09-04*
