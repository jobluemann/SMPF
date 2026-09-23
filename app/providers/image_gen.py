# SMPF v1 — app/providers/image_gen.py — 2026-08-24
"""Image generation — for memes and social post visuals.

Uses Pollinations.ai — genuinely free image generation, and unlike
every other provider in this project, NO API KEY at all. No signup,
nothing to leak, nothing to rotate. It's a simple GET request that
returns raw image bytes directly (Stable Diffusion / Flux under the
hood, per Pollinations' own docs).

*** NOT VERIFIED LIVE *** — this sandbox can't reach pollinations.ai
(not on the allowed network list), so the URL pattern below is built
from Pollinations' documented usage pattern, not a live-confirmed
request the way Orpheus TTS was. Run this once locally and confirm it
actually returns a real image before relying on it for production.
"""
import os
import time
import urllib.parse

import requests

from app.config import POLLINATIONS_BASE_URL, DATA_DIR

IMAGE_OUTPUT_DIR = os.path.join(DATA_DIR, "generated_images")


def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    seed: int = None,
    nologo: bool = True,
) -> dict:
    """Generate an image from a text prompt. Saves it and returns the path + timing.

    No API key required — this is the whole point of using Pollinations
    for this feature. `seed` fixes randomness if you want a reproducible
    result for the same prompt; leave it None for a fresh image each time.
    """
    if not prompt or not prompt.strip():
        return {"ok": False, "error": "prompt cannot be empty"}

    encoded_prompt = urllib.parse.quote(prompt.strip())
    url = f"{POLLINATIONS_BASE_URL}/prompt/{encoded_prompt}"

    params = {"width": width, "height": height}
    if seed is not None:
        params["seed"] = seed
    if nologo:
        params["nologo"] = "true"

    start = time.monotonic()
    try:
        resp = requests.get(url, params=params, timeout=60)
        elapsed_ms = round((time.monotonic() - start) * 1000)

        if resp.status_code != 200:
            return {
                "ok": False,
                "status_code": resp.status_code,
                "error": resp.text[:300],
                "latency_ms": elapsed_ms,
            }

        content_type = resp.headers.get("content-type", "")
        if "image" not in content_type:
            # Got a 200 but not actually an image — likely an error page
            # or rate-limit message disguised as a 200. Worth knowing
            # rather than silently saving a broken "image" file.
            return {
                "ok": False,
                "error": f"response wasn't an image (content-type: {content_type})",
                "latency_ms": elapsed_ms,
            }

        os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
        ext = "jpg" if "jpeg" in content_type else "png"
        filename = f"img_{int(time.time() * 1000)}.{ext}"
        output_path = os.path.join(IMAGE_OUTPUT_DIR, filename)

        with open(output_path, "wb") as f:
            f.write(resp.content)

        return {
            "ok": True,
            "output_path": output_path,
            "image_bytes": len(resp.content),
            "latency_ms": elapsed_ms,
            "prompt": prompt,
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": str(exc),
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


if __name__ == "__main__":
    import json
    result = generate_image("a conservative meme about government spending, cartoon style")
    print(json.dumps(result, indent=2))
