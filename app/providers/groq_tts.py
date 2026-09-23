# SMPF v1 — app/providers/groq_tts.py — 2026-08-24
"""Text-to-speech for the client portal.

This is the actual feature — not the capability tester. Given a piece
of text (e.g. an answer to a client's question), returns real audio
using Groq's Orpheus model.

Uses the /audio/speech endpoint, confirmed correct after the earlier
capability test wrongly hit /chat/completions and reported Orpheus as
"failing" — it wasn't failing, it was just being asked the wrong way.
"""
import os
import time
from typing import Optional

import requests

from app.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_TTS_MODEL, DATA_DIR

AUDIO_OUTPUT_DIR = os.path.join(DATA_DIR, "tts_output")


def generate_speech(
    text: str,
    voice: str = "autumn",
    model: str = GROQ_TTS_MODEL,
    response_format: str = "wav",
) -> dict:
    """Convert text to speech. Saves the audio file and returns its path + timing.

    Voice list for canopylabs/orpheus-v1-english, CONFIRMED LIVE against
    a real error response on 2026-08-24: autumn, diana, hannah, austin,
    daniel, troy. (The earlier default of "Aaliyah-PlayAI" was a guess
    borrowed from playai-tts's naming convention and was wrong for
    Orpheus specifically — Orpheus has its own separate voice list.)

    If `model` is changed to something other than Orpheus, this list
    does not necessarily apply — check that model's own voice list.
    """
    if not GROQ_API_KEY:
        return {"ok": False, "error": "GROQ_API_KEY not set in .env"}

    if not text or not text.strip():
        return {"ok": False, "error": "text cannot be empty"}

    start = time.monotonic()
    try:
        resp = requests.post(
            f"{GROQ_BASE_URL}/audio/speech",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "input": text.strip(),
                "voice": voice,
                "response_format": response_format,
            },
            timeout=30,
        )
        elapsed_ms = round((time.monotonic() - start) * 1000)

        if resp.status_code != 200:
            return {
                "ok": False,
                "status_code": resp.status_code,
                "error": resp.text[:300],
                "latency_ms": elapsed_ms,
            }

        os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
        filename = f"tts_{int(time.time() * 1000)}.{response_format}"
        output_path = os.path.join(AUDIO_OUTPUT_DIR, filename)

        with open(output_path, "wb") as f:
            f.write(resp.content)

        return {
            "ok": True,
            "output_path": output_path,
            "audio_bytes": len(resp.content),
            "latency_ms": elapsed_ms,
            "model": model,
            "voice": voice,
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": str(exc),
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


if __name__ == "__main__":
    import json
    result = generate_speech("This is a test of the client portal voice feature.", voice="autumn")
    print(json.dumps(result, indent=2))
