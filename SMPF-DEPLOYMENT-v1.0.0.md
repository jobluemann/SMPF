# SMPF — Deployment & Operations Document
## v1.0.0 — 2026-09-08

Target architecture: **Pi runs the app (24/7, home) → WireGuard tunnel → Oracle Cloud free-tier VM = permanent public gateway (Caddy TLS + fixed IP).** This replaces the churning trycloudflare.com quick tunnel.

```
Internet ──HTTPS 443──► Oracle VM 84.8.128.153 (Caddy, TLS, WG server 10.66.0.1)
                              │ WireGuard 51820/udp
                              ▼
                        Pi 10.66.0.2:8000 (FastAPI/uvicorn, ~/apps/smpfx)
```

---

## 1. Oracle VM

| Field | Value |
|-------|-------|
| Name | jobluemann |
| Shape | VM.Standard.E2.1.Micro (1 OCPU / 1 GB — **Always Free**, verify badge before any resize) |
| Image | Ubuntu 22.04 (verify with `lsb_release -a`) |
| Region | af-johannesburg-1 |
| VCN | private IP 10.0.0.211, public subnet route to IGW already added |
| Public IP | **84.8.128.153 (RESERVED — must stay attached to the primary VNIC; an unattached reserved IP bills hourly)** |
| SSH user | `ubuntu` (fallback `opc` if auth fails) |
| SSH key | `C:\Users\RudiOosthuizen\Documents\kimi\workspace\oracle-vm\oracle_smpf` (private, chmod 600) / `.pub` |

SSH from laptop:
```bash
ssh -i C:\Users\RudiOosthuizen\Documents\kimi\workspace\oracle-vm\oracle_smpf -o StrictHostKeyChecking=accept-new ubuntu@84.8.128.153
```

Attach reserved IP (Oracle console, if not yet attached):
Compute → Instances → jobluemann → Networking → Attached VNICs → Primary VNIC →
Resources: IP addresses → ⋮ on 10.0.0.211 → Edit → Reserved → POES → Update.

Also on the VM, verify the OS firewall isn't blocking:
```bash
sudo iptables -L -n | head -30
sudo ufw status
```
Ubuntu images typically have no ufw rules — the NSG is the enforcement point.

### NSG / Security List inbound rules required
| Protocol | Port | Source | Purpose |
|----------|------|--------|---------|
| TCP | 22 | 0.0.0.0/0 | SSH |
| TCP | 443 | 0.0.0.0/0 | HTTPS (Caddy) |
| UDP | 51820 | 0.0.0.0/0 | WireGuard |

Check in console: Networking → Network Security Groups (one was auto-created by the "connect subnet to internet" quick action) → ensure the above exist; add missing ones.

### Billing guardrails
- Billing → Budgets → create budget, amount **$1**, alert at 100% → email. Free tier has $300 trial credit so a small mistake won't bankrupt anything, but the alarm catches config drift.
- Never create: load balancers, NAT gateways, extra reserved IPs, non-Micro shapes, OCI Object Storage egress-heavy setups. All are billable.

---

## 2. WireGuard (VM server side)

On the VM (via SSH):
```bash
sudo apt update && sudo apt install -y wireguard
umask 077
wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key
# IP forwarding
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.d/99-wireguard.conf
sudo sysctl --system
```

Write `/etc/wireguard/wg0.conf` (Pi public key goes in `[Peer]` — generate the Pi keys on the laptop, see section 3):
```ini
[Interface]
Address = 10.66.0.1/24
ListenPort = 51820
PrivateKey = <VM_SERVER_PRIVATE_KEY>
PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o ens3 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o ens3 -j MASQUERADE

[Peer]
# Raspberry Pi
PublicKey = <PI_PUBLIC_KEY>
AllowedIPs = 10.66.0.2/32
```
(`ens3` = VM NIC name — confirm with `ip a`.)

```bash
sudo systemctl enable --now wg-quick@wg0
sudo wg show
```

---

## 3. WireGuard (Pi client side) — paste blocks

Generate Pi keys on the laptop ONCE, print both, then give him the wg0.conf:
```bash
umask 077 && wg genkey | tee pi_private.key | wg pubkey > pi_public.key
echo "PI PUBLIC: $(cat pi_public.key)"
```

Pi paste block (after Pi public key is in the VM's `[Peer]`):
```bash
sudo apt install -y wireguard
sudo tee /etc/wireguard/wg0.conf > /dev/null <<'EOF'
[Interface]
Address = 10.66.0.2/24
PrivateKey = <PI_PRIVATE_KEY>

[Peer]
PublicKey = <VM_SERVER_PUBLIC_KEY>
AllowedIPs = 10.66.0.1/32
Endpoint = 84.8.128.153:51820
PersistentKeepalive = 25
EOF
sudo systemctl enable --now wg-quick@wg0
ping -c 3 10.66.0.1
```
Expected: 3 replies. If not: check `sudo wg show` on both ends, NSG UDP 51820, and that the VM's `ens3` MASQUERADE rule exists.

**PersistentKeepalive = 25 keeps the session alive through his dynamic home IP** — the Pi initiates outbound, so IP changes are harmless.

---

## 4. Caddy (TLS reverse proxy on the VM)

```bash
sudo apt install -y caddy   # (or: apt install caddy from Caddy's official repo for latest)
sudo tee /etc/caddy/Caddyfile > /dev/null <<'EOF'
smpf.finwatchpro.net {
    reverse_proxy 10.66.0.2:8000
}
EOF
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager
```
Let's Encrypt issues automatically once DNS (step 5) resolves. Caddy renews forever with zero maintenance.

**DNS (he does, at SiteGround where finwatchpro.net is hosted):**
A record: `smpf.finwatchpro.net` → `84.8.128.153` (TTL 300).

**Tunnel redundancy:** keep cloudflared quick tunnel as an emergency fallback on the Pi — it costs nothing and requires zero config changes if the VM dies. .env would just need the URL swapped back.

---

## 5. Pi environment (final values)

On the Pi, `~/apps/smpfx/.env` — these lines change when the gateway goes live:
```ini
PUBLIC_BASE_URL=https://smpf.finwatchpro.net
META_CALLBACK_URL=https://smpf.finwatchpro.net/connectors/meta/callback
INSTAGRAM_CALLBACK_URL=https://smpf.finwatchpro.net/connectors/instagram/callback
THREADS_CALLBACK_URL=https://smpf.finwatchpro.net/connectors/threads/callback
X_CALLBACK_URL=https://smpf.finwatchpro.net/connectors/x/callback
```
After editing: `sudo fuser -k 8000/tcp ; cd ~/apps/smpfx && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000` (or whatever supervisor he settles on — recommend systemd unit `smpf.service` on the Pi so the app auto-starts on boot; TODO).

**Meta Developer apps — set the OAuth redirect (one line per app, Meta allows exactly one):**
- FB app "POES": `https://smpf.finwatchpro.net/connectors/meta/callback`
- IG app "smpf": `https://smpf.finwatchpro.net/connectors/instagram/callback`
- Threads app "POES": `https://smpf.finwatchpro.net/connectors/threads/callback`
Do this ONCE — the whole point of the fixed IP + domain is no more whitelist churn.

---

## 6. Deploy workflow

```bash
# Laptop:
cd /c/Users/RudiOosthuizen/smpf
git add -A && git commit -m '<message>' && git push origin main
# Pi:
cd ~/apps/smpfx && git pull origin main && source venv/bin/activate
pip install -r requirements.txt   # when it changed
```
Pitfall already hit: `data/x_connections.json` is tracked and causes pull conflicts when the Pi edits it. If `git pull` aborts: `git stash && git pull && git stash pop`.

---

## 7. Credentials reference (current intended state — GREP THE PI .env TO CONFIRM)

| Platform | App | App ID | Secret | Status |
|----------|-----|--------|--------|--------|
| Facebook | POES | 176960217933469 | a3788e86e9b39f6c1af73d268fb2aebb | Untested connect |
| Instagram | smpf | 911637715347553 | b3a2d2fea94b6069974e7aad7f177e44 | Untested |
| Threads | POES | 212298165323664 | 6e488c665b9c9d1c3226a0253952a133 | Connected once under old creds |

X OAuth 1.0a (WORKING — live posts verified 2026-09-07):
```
X_OAUTH1_CONSUMER_KEY=8GxzNahvGOer8twraqcZPom6A
X_OAUTH1_CONSUMER_SECRET=7vvuJpyNJyW3grBdG0S2Z711vTHLbeIDjn3PXNepeoJ1comLAc
X_OAUTH1_ACCESS_TOKEN=1183789584511049728-ARGoEkzTaJTWaYgu91XGVbYMnRd6BL
X_OAUTH1_ACCESS_TOKEN_SECRET=VURiF2jSdngjYNmzKM8u4qjSMfBgL8JmiWRZIrP0REFM0
```

Notes:
- `R@0!wyn1o1` = Meta dashboard re-auth password (NOT an API value).
- App ID = pure numbers. An `EAA...` string is an access token, never an App ID — this exact confusion cost an evening.
- All secrets stay in `.env` on the Pi / Render dashboard — never committed.
- Telegram bot token exists in the Pi .env (bot for admin approvals).
- Meta app review (screencast, advanced access) is DEFERRED — dev mode works for the app admin. Only needed when paying clients connect.

---

## 8. Operational runbook (Pi)

```bash
cd ~/apps/smpfx && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
# Port stuck: sudo fuser -k 8000/tcp
# Logs: post_log.jsonl in data/
# Health: curl http://localhost:8000/health
```
X self-test (from Pi):
```bash
cd ~/apps/smpfx && source venv/bin/activate && python3 -c \
 'from app.connectors import x_connect; print(x_connect.post_tweet("local_test_user","test"))'
```

---

*Update this document whenever infrastructure changes. Keep version in the header.*

## HANDOVER 2026-09-12 (by the northbench agent, via browser automation — read before resuming Meta work)

The following was done on the smpf Meta app (911637715347553) through the owner's logged-in browser. Do NOT redo; build on top:

- Page use case permissions ADDED/CONFIRMED: pages_manage_posts, pages_read_engagement, pages_manage_engagement, pages_show_list, read_insights, business_management (all Ready for testing)
- Long-lived page token for Page "Jo Bluemann" (id 101916918609027) stored at /opt/smpfx/.meta_page_token (chmod 600; vars: META_PAGE_ID, META_PAGE_NAME, META_PAGE_TOKEN, META_LONG_LIVED_USER_TOKEN). Page token NEVER expires while the app stays installed.
- Verified live: test post 101916918609027_1404795731859888 on the Page (safe to delete).
- Instagram publishing NOT done: needs instagram_content_publish via IG app 1567063064884198 (already linked to smpf, matches INSTAGRAM_APP_ID in .env).
- read_insights is added to the app but was not in the generated token scopes; regenerate the token when analytics are needed.
