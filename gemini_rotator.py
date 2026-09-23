"""Gemini Image/Text Generation with Gmail account rotation.

Reads keys from /opt/smpfx/data/gemini_config.json.
To add more Gmail accounts:
  1. Go to https://aistudio.google.com/app/apikey (switch Gmail account)
  2. Create API key
  3. Edit /opt/smpfx/data/gemini_config.json, add ["label", "key"] to keys array
  4. Restart backend
"""
import os, requests, json, base64, time
from datetime import datetime, timezone

DATA_DIR = "/opt/smpfx/data"
CONFIG_FILE = os.path.join(DATA_DIR, "gemini_config.json")
QUOTA_FILE = os.path.join(DATA_DIR, "gemini_quota.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"keys": [], "image_models": [], "text_models": []}


def load_quota():
    if os.path.exists(QUOTA_FILE):
        try:
            with open(QUOTA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_quota(q):
    with open(QUOTA_FILE, "w") as f:
        json.dump(q, f, indent=2)


def is_key_exhausted(label, quota, hours=24):
    """Check if key was marked exhausted within last N hours."""
    last_fail = quota.get(label, {}).get("last_fail")
    if not last_fail:
        return False
    try:
        dt = datetime.fromisoformat(last_fail)
        return (datetime.now(timezone.utc) - dt).total_seconds() < (hours * 3600)
    except:
        return False


def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> str:
    """Generate image, rotating through Gmail accounts. Returns file path or None."""
    config = load_config()
    quota = load_quota()
    keys = config.get("keys", [])
    models = config.get("image_models", ["gemini-2.5-flash-image"])

    if not keys:
        print("[Gemini] No keys configured. Add to gemini_config.json")
        return None

    saved_path = None

    for label, key in keys:
        if is_key_exhausted(label, quota):
            print(f"[Gemini] Skipping {label} — exhausted within last 24h")
            continue

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["Text", "Image"]}
            }

            try:
                print(f"[Gemini] Trying {label} / {model}...")
                resp = requests.post(url, headers={"Content-Type": "application/json"},
                    json=payload, timeout=90)

                if resp.status_code == 429:
                    err = resp.json().get("error", {}).get("message", "")
                    print(f"[Gemini] {label}/{model}: Quota exceeded (429)")
                    quota[label] = {"last_fail": datetime.now(timezone.utc).isoformat(), "reason": "quota"}
                    save_quota(quota)
                    break  # Don't try other models for this key

                if not resp.ok:
                    print(f"[Gemini] {label}/{model}: HTTP {resp.status_code}")
                    continue

                data = resp.json()
                for candidate in data.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            img_data = base64.b64decode(part["inlineData"]["data"])
                            mime = part["inlineData"].get("mimeType", "image/png")
                            ext = "png" if "png" in mime else "jpg"

                            gen_dir = os.path.join(DATA_DIR, "generated_images")
                            os.makedirs(gen_dir, exist_ok=True)
                            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                            filename = f"gemini_{label}_{ts}.{ext}"
                            filepath = os.path.join(gen_dir, filename)

                            with open(filepath, "wb") as f:
                                f.write(img_data)

                            quota[label] = {"last_success": datetime.now(timezone.utc).isoformat()}
                            save_quota(quota)
                            print(f"[Gemini] SUCCESS — {filepath} ({len(img_data)} bytes)")
                            return filepath

            except Exception as exc:
                print(f"[Gemini] {label}/{model}: Exception {exc}")
                continue

    print("[Gemini] All keys exhausted. Use Pollinations fallback.")
    return None


def generate_text(prompt: str, max_tokens: int = 500) -> str:
    """Generate text, rotating through Gmail accounts."""
    config = load_config()
    quota = load_quota()
    keys = config.get("keys", [])
    models = config.get("text_models", ["gemini-2.5-flash"])

    if not keys:
        return None

    for label, key in keys:
        if is_key_exhausted(label, quota, hours=1):
            continue

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}

            try:
                resp = requests.post(url, headers={"Content-Type": "application/json"},
                    json=payload, timeout=60)

                if resp.status_code == 429:
                    quota[label] = {"last_fail": datetime.now(timezone.utc).isoformat()}
                    save_quota(quota)
                    break

                if resp.ok:
                    data = resp.json()
                    if "candidates" in data and data["candidates"]:
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return text

            except Exception:
                pass

    return None


if __name__ == "__main__":
    print("Gemini Rotator Status:")
    config = load_config()
    print(f"  Keys configured: {len(config.get('keys', []))}")
    for label, key in config.get("keys", []):
        masked = key[:10] + "..." + key[-4:]
        print(f"    {label}: {masked}")
    print(f"  Image models: {config.get('image_models', [])}")
    print(f"  Text models: {config.get('text_models', [])}")
    print()
    print("To add more keys, edit:", CONFIG_FILE)
    print("Then run: sudo systemctl restart smpfx")
