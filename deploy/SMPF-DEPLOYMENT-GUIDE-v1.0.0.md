# SMPF Deployment Guide — v1.0.0

**Project:** Social Media Platform Framework (SMPF)  
**Client Portal:** finwatchpro.net (WordPress on SiteGround)  
**Backend API:** Hetzner CX21 VPS (€5.35/mo)  
**Prepared:** 2026-09-04

---

## What's in the Deploy Package

| File | Size | Purpose |
|------|------|---------|
| `smpf-core.zip` | 7.2 KB | Required by ALL other plugins. API client + admin dashboard |
| `smpf-post.zip` | 3.4 KB | Post composer, scheduler, content creation |
| `smpf-analytics.zip` | 2.1 KB | Platform stats, engagement graphs, connection health |
| `smpf-payments.zip` | 9.9 KB | Donation bar, Ko-fi/BMC widgets, package tiers |
| `smpf-integrations.zip` | 2.4 KB | Social media connector management UI |
| `smpf-portal-theme.zip` | 4.9 KB | SMPF Portal theme (neutral white, no sidebars) |
| `smpf-backend-v1.zip` | 268.6 KB | FastAPI backend + connectors + portal auth |

---

## Part 1: WordPress Deployment (SiteGround)

### Step 1 — Install Plugins (IN THIS ORDER)

1. Log into your WordPress admin at `https://finwatchpro.net/wp-admin`
2. Go to **Plugins → Add New → Upload Plugin**
3. Install **smpf-core.zip** first (required by all others)
4. Activate it
5. Install the remaining 4 plugins in any order:
   - `smpf-post.zip`
   - `smpf-analytics.zip`
   - `smpf-payments.zip`
   - `smpf-integrations.zip`
6. Activate each after upload

### Step 2 — Install Theme

1. Go to **Appearance → Themes → Add New → Upload Theme**
2. Upload `smpf-portal-theme.zip`
3. Activate **SMPF Portal**

### Step 3 — Configure SMPF Core

1. Go to **SMPF → Settings** (left sidebar)
2. Set **Backend URL** to your Hetzner VPS IP or domain (e.g. `https://api.finwatchpro.net`)
3. Set **API Key** (you'll generate this on the backend — see Part 2)
4. Save

### Step 4 — Configure Payments Plugin

1. Go to **SMPF → Packages**
2. Fill in your payment links:
   - **PayPal:** `https://paypal.me/jobluemann` (or your link)
   - **Ko-fi:** `https://ko-fi.com/jobluemann`
   - **Buy Me a Coffee:** `https://buymeacoffee.com/jobluemann`
   - **BTC Address:** your wallet address
   - **ETH Address:** your wallet address
3. Enable **Donation Bar**
4. Set **Interval** (1–10 minutes, default 5)
5. Upload your **QR Code** (the `bmc-qr-code.png` you already have)
6. Save

### Step 5 — Configure Ko-fi Widget

1. In **SMPF → Packages**, scroll to **Ko-fi Widget**
2. Enable widget
3. Set **Username:** `jobluemann`
4. Set **Type:** `floating-chat` (the blue chat bubble you wanted)
5. Save

---

## Part 2: Backend Deployment (Hetzner VPS)

### Step 1 — Provision Server

1. Sign up at [hetzner.com](https://www.hetzner.com/cloud)
2. Create a **CX21** server:
   - **OS:** Ubuntu 22.04 LTS
   - **Location:** EU (Falkenstein or Nuremberg)
   - **Price:** €5.35/month
3. Add your SSH key or set a root password
4. Note the **IPv4 address** (e.g. `78.46.xxx.xxx`)

### Step 2 — Upload Backend Code

```bash
# On your local machine, extract and upload
scp -r smpf-backend-v1.zip root@YOUR_SERVER_IP:/root/
ssh root@YOUR_SERVER_IP
apt update && apt install -y python3-pip python3-venv nginx
unzip smpf-backend-v1.zip -d /opt/smpf/
cd /opt/smpf
```

### Step 3 — Create Environment File

```bash
cd /opt/smpf
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `/opt/smpf/.env`:

```env
# SMPF Backend Configuration
SECRET_KEY=change-this-to-a-random-32-char-string
DATA_DIR=/opt/smpf/data

# X (Twitter) OAuth 2.0
X_CLIENT_ID=V2NhRFpHSGlGQTI4RExJOThDU1Y6MTpjaQ
X_CLIENT_SECRET=your-client-secret

# Meta (Facebook/Instagram)
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret

# Groq AI (Free tier — image gen + TTS)
GROQ_API_KEY=gsk_your-groq-key-here

# OpenRouter (Free tier backup)
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key

# Telegram Bot
TELEGRAM_BOT_TOKEN=8801125744:AAGYHq6Uv3I7BuC7YPkpwas6D9MygpYWDMM

# WhatsApp Business API (optional)
WHATSAPP_BUSINESS_TOKEN=your-token
WHATSAPP_BUSINESS_PHONE_ID=your-phone-id
```

### Step 4 — Run with Uvicorn

```bash
cd /opt/smpf
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

For production, use a systemd service or PM2.

### Step 5 — Nginx Reverse Proxy (SSL)

Create `/etc/nginx/sites-available/smpf`:

```nginx
server {
    listen 80;
    server_name api.finwatchpro.net;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:
```bash
ln -s /etc/nginx/sites-available/smpf /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

Then get SSL with Certbot:
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d api.finwatchpro.net
```

---

## Part 3: Social Media API Setup

### X (Twitter) — ✅ WORKING
- OAuth 2.0 app already created
- Client ID: `V2NhRFpHSGlGQTI4RExJOThDU1Y6MTpjaQ`
- Add callback URL in X Developer Portal: `https://api.finwatchpro.net/connectors/x/callback`

### Facebook — ✅ WORKING
- Connected via Meta Graph API
- Your personal Facebook account works

### Instagram — ⚠️ REQUIRES ACTION
**You MUST convert your Instagram to a Business or Creator account:**
1. Open Instagram app → Settings → Account → Switch to Professional Account
2. Choose **Creator** (recommended for influencers)
3. Connect to your Facebook Page
4. Add `https://api.finwatchpro.net/connectors/instagram-graph/callback` to Meta app Valid OAuth Redirect URIs
5. Submit app for review (Meta requires a verification video)

### Threads — ❌ BLOCKED
- Requires Instagram Business connection first
- Same Meta app as Instagram

### WhatsApp Web — ✅ AVAILABLE
- QR code scan from dashboard
- Session persists until phone disconnects
- Heartbeat pulse checks every 5 minutes

### WhatsApp Business API — 💰 OPTIONAL
- Requires Meta Business verification
- Pay-as-you-go (~$0.005/message)

### Telegram — ✅ WORKING
- Bot token already configured
- Use `/api/telegram/updates` to discover chat IDs

---

## Part 4: Post-Deploy Checklist

- [ ] WordPress plugins installed and activated
- [ ] SMPF Portal theme active
- [ ] Backend URL configured in SMPF Core settings
- [ ] Hetzner VPS provisioned and running
- [ ] Nginx + SSL configured
- [ ] `.env` file populated with all API keys
- [ ] X OAuth callback URL whitelisted
- [ ] Instagram account converted to Creator/Business
- [ ] Meta app redirect URIs whitelisted
- [ ] Donation bar configured with your links
- [ ] Ko-fi floating chat widget enabled
- [ ] Test post sent to at least one platform

---

## Quick Reference: File Locations

| Component | Local Path |
|-----------|-----------|
| All deploy ZIPs | `C:\Users\RudiOosthuizen\smpf\deploy\` |
| Full website preview | `C:\Users\RudiOosthuizen\smpf\preview\full-website-preview.html` |
| Master architecture doc | `C:\Users\RudiOosthuizen\smpf\SMPF-MASTER-DOCUMENT-v1.0.0.md` |
| Backend source | `C:\Users\RudiOosthuizen\smpf\main.py` + `app/` |
| WordPress plugins source | `C:\Users\RudiOosthuizen\smpf\wordpress-plugins\` |
| WordPress theme source | `C:\Users\RudiOosthuizen\smpf\wordpress-theme\` |

---

## Support & Next Steps

**Immediate next milestone:** Get Instagram connected (requires account conversion).  
**After that:** Content automation pipeline — news research → AI post generation → scheduled publishing.  
**Long term:** Client onboarding portal with package selection, payment, and consultant assignment.

*Built for Jo Bluemann — SMPF v1.0.0*
