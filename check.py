import os, stat, subprocess, json, urllib.request
os.chdir("/opt/smpfx")
def line(ok, name, info=""):
    print(("PASS  " if ok else "FAIL  ") + name + (f"   ({info})" if info else ""))
r = subprocess.run(["systemctl", "is-active", "smpfx"], capture_output=True, text=True)
line(r.stdout.strip() == "active", "Backend running")
try:
    h = json.load(urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5))
    line(h.get("status") == "ok", "Backend answering")
except Exception as e:
    line(False, "Backend answering", type(e).__name__)
from app.connectors import x_connect, meta_connect, instagram_connect, threads_connect, linkedin_connect, telegram_connect
for name, m in [("X", x_connect), ("Facebook", meta_connect), ("Instagram", instagram_connect), ("Threads", threads_connect), ("LinkedIn", linkedin_connect), ("Telegram", telegram_connect)]:
    try:
        r = m.validate_connection("local_test_user") if hasattr(m, "validate_connection") else m.get_connection_status("local_test_user")
        line(r.get("status") in ("ok", "connected"), name, r.get("name") or r.get("username") or r.get("error") or r.get("status"))
    except Exception as e:
        line(False, name, type(e).__name__)
line(stat.S_IMODE(os.stat(".env").st_mode) == 0o600, "Secrets file locked")
r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
line(r.stdout.strip() == "", "All changes saved to GitHub", f"{len(r.stdout.splitlines())} unsaved" if r.stdout.strip() else "")
