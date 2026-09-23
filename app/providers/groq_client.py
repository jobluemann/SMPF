# SMPF v2 — app/providers/groq_client.py — 2026-08-24 (fixed Orpheus default voice)
"""Groq capability checker.

Not a publisher, not a content generator — just answers one question:
"which Groq models actually respond right now, and how fast?"

Run standalone: python -m app.providers.groq_client
"""
import time
from typing import List, Dict

import requests

from app.config import GROQ_API_KEY, GROQ_BASE_URL


def list_models() -> List[str]:
    """Ask Groq which models this API key can see. Returns model IDs."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set in .env")

    resp = requests.get(
        f"{GROQ_BASE_URL}/models",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        timeout=20,
    )
    resp.raise_for_status()
    return [m["id"] for m in resp.json().get("data", [])]


def test_chat_model(model_id: str, prompt: str = "Reply with exactly: OK") -> Dict:
    """Send one real chat completion request. Returns pass/fail + latency + any error."""
    if not GROQ_API_KEY:
        return {"model": model_id, "ok": False, "error": "GROQ_API_KEY not set"}

    start = time.monotonic()
    try:
        resp = requests.post(
            f"{GROQ_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 20,
            },
            timeout=30,
        )
        elapsed_ms = round((time.monotonic() - start) * 1000)

        if resp.status_code != 200:
            return {
                "model": model_id,
                "ok": False,
                "status_code": resp.status_code,
                "error": resp.text[:300],
                "latency_ms": elapsed_ms,
            }

        data = resp.json()
        # content can be present-but-null on some models (e.g. reasoning
        # models that put output in a different field) — "or ''" covers
        # both "key missing" and "key present but None", .get()'s default
        # only covers the first case.
        reply = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        usage = data.get("usage", {})

        return {
            "model": model_id,
            "ok": True,
            "latency_ms": elapsed_ms,
            "reply": reply,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
        }
    except requests.RequestException as exc:
        return {
            "model": model_id,
            "ok": False,
            "error": str(exc),
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


# TTS models (Orpheus and similar) don't support /chat/completions at
# all — confirmed by the FAIL results the chat tester correctly
# reported. They need /audio/speech instead, a different request shape
# entirely. Route TTS-looking model IDs through this tester, not the
# chat one.
TTS_MODEL_PREFIXES = ("canopylabs/orpheus", "playai-tts")


def is_tts_model(model_id: str) -> bool:
    return any(model_id.startswith(p) for p in TTS_MODEL_PREFIXES)


def test_tts_model(model_id: str, text: str = "This is a test.", voice: str = "autumn") -> Dict:
    """Send one real text-to-speech request. Returns pass/fail + latency + audio size.

    Voice list for canopylabs/orpheus-v1-english, CONFIRMED LIVE on
    2026-08-24: autumn, diana, hannah, austin, daniel, troy. Other TTS
    models (e.g. playai-tts) have their own separate voice lists — if a
    different model fails here with a voice error, check that model's
    voices specifically rather than assuming this list applies.
    """
    if not GROQ_API_KEY:
        return {"model": model_id, "ok": False, "error": "GROQ_API_KEY not set"}

    start = time.monotonic()
    try:
        resp = requests.post(
            f"{GROQ_BASE_URL}/audio/speech",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "input": text,
                "voice": voice,
                "response_format": "wav",
            },
            timeout=30,
        )
        elapsed_ms = round((time.monotonic() - start) * 1000)

        if resp.status_code != 200:
            return {
                "model": model_id,
                "ok": False,
                "status_code": resp.status_code,
                "error": resp.text[:300],
                "latency_ms": elapsed_ms,
            }

        return {
            "model": model_id,
            "ok": True,
            "latency_ms": elapsed_ms,
            "audio_bytes": len(resp.content),
        }
    except requests.RequestException as exc:
        return {
            "model": model_id,
            "ok": False,
            "error": str(exc),
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


def run_full_check() -> Dict:
    """List every visible model and test each one with the right kind of
    request — chat models get a chat completion, TTS models get a real
    speech request. Returns a full report."""
    report = {"provider": "groq", "models_visible": [], "results": []}

    try:
        report["models_visible"] = list_models()
    except Exception as exc:
        report["list_models_error"] = str(exc)
        return report

    for model_id in report["models_visible"]:
        if is_tts_model(model_id):
            report["results"].append(test_tts_model(model_id))
        else:
            report["results"].append(test_chat_model(model_id))

    report["working_count"] = sum(1 for r in report["results"] if r["ok"])
    report["total_count"] = len(report["results"])
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(run_full_check(), indent=2))
