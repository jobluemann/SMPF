# SMPF WordPress Plugins — Deployment Guide

## What Was Built

Five independent WordPress plugins that form the client-facing portal on SiteGround. Each can be activated/deactivated separately.

```
wordpress-plugins/
├── smpf-core/              ← ACTIVATE FIRST (required by all others)
│   ├── smpf-core.php
│   ├── includes/
│   │   ├── class-smpf-api-client.php
│   │   └── class-smpf-admin.php
│   ├── assets/
│   │   ├── css/smpf-admin.css
│   │   └── js/smpf-admin.js
│   └── templates/
│       ├── dashboard.php
│       └── settings.php
│
├── smpf-post/
│   ├── smpf-post.php
│   └── templates/
│       ├── post-composer.php
│       └── post-schedule.php
│
├── smpf-analytics/
│   ├── smpf-analytics.php
│   └── templates/
│       └── analytics.php
│
├── smpf-payments/
│   ├── smpf-payments.php
│   └── templates/
│       └── packages.php
│
└── smpf-integrations/
    ├── smpf-integrations.php
    └── templates/
        └── integrations.php
```

---

## Plugin Descriptions

| Plugin | Function | Depends On |
|--------|----------|-----------|
| **smpf-core** | Admin menu, REST API client to FastAPI backend, settings page, dashboard status | Nothing |
| **smpf-post** | Post composer form, platform checkboxes, live posting to backend | smpf-core |
| **smpf-analytics** | Post history table, content overview, generated media gallery | smpf-core |
| **smpf-payments** | PayFast/PayPal/crypto settings, package tier display | smpf-core |
| **smpf-integrations** | Email provider config, Telegram notifications, email signup shortcode | smpf-core |

---

## How to Deploy to SiteGround

### Step 1: Zip each plugin folder separately

```bash
cd C:/Users/RudiOosthuizen/smpf/wordpress-plugins
zip -r smpf-core.zip smpf-core/
zip -r smpf-post.zip smpf-post/
zip -r smpf-analytics.zip smpf-analytics/
zip -r smpf-payments.zip smpf-payments/
zip -r smpf-integrations.zip smpf-integrations/
```

### Step 2: Upload via WordPress Admin

1. Log in to `https://finwatchpro.net/wp-admin`
2. Go to **Plugins → Add New → Upload Plugin**
3. Upload `smpf-core.zip` first, then activate it
4. Go to **SMPF → Settings** and enter your backend URL:
   - Local dev: `http://127.0.0.1:8000`
   - Production VPS: `https://your-vps-ip:8000`
5. Click **Test Connection** — should show green "Backend connected"
6. Upload and activate the other 4 plugins in any order

### Step 3: Verify

- **SMPF → Dashboard** — shows platform connection status from backend
- **SMPF → Create Post** — compose and send posts
- **SMPF → Analytics** — view post history
- **SMPF → Packages** — configure payment gateways
- **SMPF → Integrations** — set up email provider

---

## Architecture

```
┌─────────────────────────────────────────┐
│  WordPress on SiteGround (PHP/MySQL)    │
│  ─────────────────────────────────────  │
│  • SMPF plugins (admin dashboard)       │
│  • Blog posts (native WordPress)        │
│  • Payment pages (WooCommerce or custom)│
│  • Email signup forms (shortcode)       │
└─────────────────────────────────────────┘
                   │
                   │ wp_remote_request()
                   │ (HTTPS/JSON)
                   ▼
┌─────────────────────────────────────────┐
│  FastAPI Backend (Python)               │
│  ─────────────────────────────────────  │
│  • OAuth token storage                  │
│  • Post execution engine                │
│  • WhatsApp Web automation              │
│  • AI generation (images, voice)        │
│  • Scheduling queue                     │
└─────────────────────────────────────────┘
```

---

## Security Notes

- API calls use `wp_remote_request()` with nonce verification
- Capability check: `manage_options` on all admin endpoints
- `sslverify: false` is set for local development — **change to true in production**
- API key header `X-API-Key` is supported but optional (add in Settings)

---

## What's NOT in These Plugins (yet)

| Feature | Why Not | Future Plan |
|---------|---------|-------------|
| Client frontend (customer login) | Needs user registration system | Phase 2: WooCommerce integration or custom roles |
| Real-time scheduling | Needs cron job or background worker | Phase 2: WP Cron calls backend schedule API |
| Payment processing | Needs gateway APIs (PayFast SDK) | Phase 2: Add PayFast IPN handler |
| Email API sync | Needs provider-specific SDKs | Phase 2: MailerLite/Brevo REST calls |
| Client analytics dashboard | Needs role-based access | Phase 2: Custom `smpf_client` role |

---

## File Locations

- **Source:** `C:/Users/RudiOosthuizen/smpf/wordpress-plugins/`
- **Deploy to:** `wp-content/plugins/` on SiteGround

---

*Version 1.0.0 — Built for SMPF*
