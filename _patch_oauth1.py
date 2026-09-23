import re

path = r"C:/Users/RudiOosthuizen/smpf/app/connectors/x_connect.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add OAuth1 import after the requests import
old_import = "import requests\nfrom PIL import Image"
new_import = "import requests\nfrom requests_oauthlib import OAuth1\nfrom PIL import Image"
content = content.replace(old_import, new_import)

# Add OAuth 1.0a config imports
old_config = "from app.config import X_CLIENT_ID, X_CLIENT_SECRET, X_CALLBACK_URL, DATA_DIR"
new_config = """from app.config import (
    X_CLIENT_ID, X_CLIENT_SECRET, X_CALLBACK_URL, DATA_DIR,
    X_OAUTH1_CONSUMER_KEY, X_OAUTH1_CONSUMER_SECRET,
    X_OAUTH1_ACCESS_TOKEN, X_OAUTH1_ACCESS_TOKEN_SECRET,
)"""
content = content.replace(old_config, new_config)

# Replace upload_media function
old_upload = '''def upload_media(local_user_id: str, media_path: str) -> dict:
    """Upload an image or video to X via v1.1 media/upload.

    Returns {"status": "ok", "media_id": ...} on success.
    """
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "error", "error": "X not connected."}

    access_token = conn.get("access_token")
    if not access_token:
        return {"status": "error", "error": "No access token. Reconnect X."}

    prepared_path = _prepare_image_for_x(media_path)

    try:
        with open(prepared_path, "rb") as f:
            resp = requests.post(
                UPLOAD_MEDIA_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                files={"media": f},
                timeout=30,
            )
        if resp.status_code == 401:
            if _refresh_access_token(local_user_id):
                access_token = _load_connections()[local_user_id]["access_token"]
                f.seek(0)
                resp = requests.post(
                    UPLOAD_MEDIA_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    files={"media": f},
                    timeout=30,
                )
        if resp.status_code == 403:
            return {
                "status": "error",
                "error": "Forbidden — your X token lacks tweet.write scope. Disconnect and reconnect X to grant posting permission.",
            }
        resp.raise_for_status()
        data = resp.json()
        return {"status": "ok", "media_id": data.get("media_id_string")}
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"X media upload error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Media upload failed: {type(exc).__name__}: {exc}"}
    finally:
        # Clean up our temp resize file if we created one
        if prepared_path != media_path and os.path.exists(prepared_path):
            try:
                os.remove(prepared_path)
            except Exception:
                pass'''

new_upload = '''def upload_media(local_user_id: str, media_path: str) -> dict:
    """Upload an image or video to X via v1.1 media/upload.

    Uses OAuth 1.0a if configured (required for media upload),
    otherwise falls back to OAuth 2.0 bearer token.

    Returns {"status": "ok", "media_id": ...} on success.
    """
    prepared_path = _prepare_image_for_x(media_path)

    try:
        with open(prepared_path, "rb") as f:
            # v1.1 media/upload requires OAuth 1.0a
            if X_OAUTH1_CONSUMER_KEY and X_OAUTH1_ACCESS_TOKEN:
                auth = OAuth1(
                    X_OAUTH1_CONSUMER_KEY,
                    X_OAUTH1_CONSUMER_SECRET,
                    X_OAUTH1_ACCESS_TOKEN,
                    X_OAUTH1_ACCESS_TOKEN_SECRET,
                )
                resp = requests.post(
                    UPLOAD_MEDIA_URL,
                    auth=auth,
                    files={"media": f},
                    timeout=30,
                )
            else:
                # Fallback to OAuth 2.0 (usually fails for media upload)
                connections = _load_connections()
                conn = connections.get(local_user_id)
                if not conn:
                    return {"status": "error", "error": "X not connected."}
                access_token = conn.get("access_token")
                if not access_token:
                    return {"status": "error", "error": "No access token. Reconnect X."}
                resp = requests.post(
                    UPLOAD_MEDIA_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    files={"media": f},
                    timeout=30,
                )
        resp.raise_for_status()
        data = resp.json()
        return {"status": "ok", "media_id": data.get("media_id_string")}
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"X media upload error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Media upload failed: {type(exc).__name__}: {exc}"}
    finally:
        # Clean up our temp resize file if we created one
        if prepared_path != media_path and os.path.exists(prepared_path):
            try:
                os.remove(prepared_path)
            except Exception:
                pass'''

content = content.replace(old_upload, new_upload)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("OK")
