# SMPF v1 — app/providers/openrouter_client.py — 2026-08-24
"""OpenRouter capability checker.

Same idea as the Groq checker: which models actually respond, and how
fast, using this key. Defaults to only testing free-tier models (the
ones with ":free" in their ID) since that's the constraint we're
building under — set free_only=False to check paid models too.

Run standalone: python -m app.providers.openrouter_client
"""
import time
from typing import List, Dict

import requests

from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL


def list_models(free_only: bool = True) -> List[str]:
    """List model IDs visible to this key. Free-tier models have ':free' in the ID."""
    resp = requests.get(f"{OPENROUTER_BASE_URL}/models", timeout=20)
    resp.raise_for_status()
    all_models = [m["id"] for m in resp.json().get("data", [])]

    if free_only:
        return [m for m in all_models if m.endswith(":free")]
    return all_models


def test_chat_model(model_id: str, prompt: str = "Reply with exactly: OK") -> Dict:
    """Send one real chat completion request. Returns pass/fail + latency + any error."""
    if not OPENROUTER_API_KEY:
        return {"model": model_id, "ok": False, "error": "OPENROUTER_API_KEY not set"}

    start = time.monotonic()
    try:
        resp = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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
        # content can be present-but-null on some models — "or ''" covers
        # both "key missing" and "key present but None"; .get()'s default
        # only covers the first case, which is what crashed here.
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


def run_full_check(free_only: bool = True) -> Dict:
    """List models (free-tier by default) and test each one. Returns a full report."""
    report = {"provider": "openrouter", "free_only": free_only, "models_visible": [], "results": []}

    try:
        report["models_visible"] = list_models(free_only=free_only)
    except Exception as exc:
        report["list_models_error"] = str(exc)
        return report

    for model_id in report["models_visible"]:
        report["results"].append(test_chat_model(model_id))

    report["working_count"] = sum(1 for r in report["results"] if r["ok"])
    report["total_count"] = len(report["results"])
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(run_full_check(), indent=2))
