"""REST API routes for client-facing operations.

These routes are called by the SiteGround PHP frontend.
All routes require authentication via X-SMPF-API-Key header.
"""
import os, json
from fastapi import APIRouter, HTTPException, Header, Depends, Request, Form
from pydantic import BaseModel
from typing import List, Optional

from app.api.client_wrapper import (
    get_connection_status, disconnect_platform, post_to_platforms,
    upload_media, start_oauth, complete_oauth,
    load_client_connections, save_client_connections,
)

router = APIRouter(prefix="/api/client", tags=["client"])

API_KEY = os.environ.get("SMPF_API_KEY", "dev-key-change-in-production")

def verify_api_key(x_smpf_api_key: str = Header(...)):
    if x_smpf_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


# ─── Models ──────────────────────────────────────────────────────────────

class PostRequest(BaseModel):
    client_id: str
    text: str
    platforms: List[str]
    image_url: Optional[str] = None

class OAuthStart(BaseModel):
    client_id: str
    platform: str

class OAuthComplete(BaseModel):
    state: str
    code: str

class TokenStore(BaseModel):
    client_id: str
    platform: str
    token_data: dict


# ─── Routes ────────────────────────────────────────────────────────────────

@router.get("/health")
def client_health():
    return {"status": "ok", "service": "smpf-client-api"}


@router.get("/status/{client_id}")
def client_platform_status(client_id: str, _=Depends(verify_api_key)):
    """Return connection status for all platforms for a client."""
    platforms = ["x", "facebook", "instagram", "threads", "linkedin", 
                 "youtube", "reddit", "minds", "vk", "telegram", "whatsapp"]
    results = {}
    for p in platforms:
        results[p] = get_connection_status(client_id, p)
    return {"client_id": client_id, "platforms": results}


@router.post("/post")
def client_post(req: PostRequest, _=Depends(verify_api_key)):
    """Post content on behalf of a client."""
    results = post_to_platforms(req.client_id, req.text, req.platforms, req.image_url)
    return {"client_id": req.client_id, "results": results}


@router.post("/oauth/start")
def client_oauth_start(req: OAuthStart, _=Depends(verify_api_key)):
    """Start OAuth flow for a client. Returns URL to redirect to."""
    result = start_oauth(req.client_id, req.platform)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/oauth/complete")
def client_oauth_complete(req: OAuthComplete, _=Depends(verify_api_key)):
    """Complete OAuth callback."""
    result = complete_oauth(req.state, req.code)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/token/store")
def client_store_token(req: TokenStore, _=Depends(verify_api_key)):
    """Store a token for a client (used when SiteGround already has the token)."""
    save_client_connections(req.client_id, req.platform, req.token_data)
    return {"status": "stored", "client_id": req.client_id, "platform": req.platform}


@router.get("/token/{client_id}/{platform}")
def client_get_token(client_id: str, platform: str, _=Depends(verify_api_key)):
    """Retrieve a client's token data."""
    data = load_client_connections(client_id, platform)
    return {"client_id": client_id, "platform": platform, "data": data}


@router.post("/disconnect")
def client_disconnect(client_id: str = Form(...), platform: str = Form(...), _=Depends(verify_api_key)):
    """Disconnect a platform for a client."""
    result = disconnect_platform(client_id, platform)
    return result

@router.get("/health/platforms")
def client_platforms_health(_=Depends(verify_api_key)):
    """Validate all platform tokens by calling their APIs. Returns live status."""
    from app.connectors import (
        x_connect, meta_connect, instagram_connect,
        threads_connect, linkedin_connect, telegram_connect,
        youtube_connect, reddit_connect, minds_connect, vk_connect,
    )
    validators = {
        "x": x_connect,
        "facebook": meta_connect,
        "instagram": instagram_connect,
        "threads": threads_connect,
        "linkedin": linkedin_connect,
        "youtube": youtube_connect,
        "reddit": reddit_connect,
        "minds": minds_connect,
        "vk": vk_connect,
        "telegram": telegram_connect,
    }
    results = {}
    for name, module in validators.items():
        try:
            if hasattr(module, "validate_connection"):
                results[name] = module.validate_connection("local_test_user")
            else:
                results[name] = {"status": "unknown", "platform": name, "reason": "no validator"}
        except Exception as exc:
            results[name] = {"status": "error", "platform": name, "error": str(exc)}
    return {"checked_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "platforms": results}


