# SMPF v1 — test_capabilities.py — 2026-08-24
"""Run this to check what actually works right now.

    python test_capabilities.py

Tests every visible Groq model and every free-tier OpenRouter model
with a real chat completion call. Prints a plain summary, then saves
the full JSON report to data/capability_report.json for later reference.

Requires GROQ_API_KEY and/or OPENROUTER_API_KEY set in .env — missing
keys just skip that provider with a clear message, not a crash.
"""
import json
import os
from datetime import datetime, timezone

from app.config import GROQ_API_KEY, OPENROUTER_API_KEY, DATA_DIR
from app.providers import groq_client, openrouter_client


def print_report(report: dict):
    provider = report["provider"]
    if "list_models_error" in report:
        print(f"\n{provider.upper()}: could not list models — {report['list_models_error']}")
        return

    print(f"\n{provider.upper()} — {report.get('working_count', 0)}/{report.get('total_count', 0)} models working")
    for r in report["results"]:
        if r["ok"]:
            extra = f"{r['audio_bytes']} bytes audio" if "audio_bytes" in r else ""
            print(f"  OK    {r['model']:<45} {r['latency_ms']:>5}ms  {extra}")
        else:
            err = r.get("error", "unknown error")[:80]
            print(f"  FAIL  {r['model']:<45} {err}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    full_report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "groq": None,
        "openrouter": None,
    }

    if GROQ_API_KEY:
        groq_report = groq_client.run_full_check()
        full_report["groq"] = groq_report
        print_report(groq_report)
    else:
        print("\nGROQ: skipped — GROQ_API_KEY not set in .env")

    if OPENROUTER_API_KEY:
        or_report = openrouter_client.run_full_check(free_only=True)
        full_report["openrouter"] = or_report
        print_report(or_report)
    else:
        print("\nOPENROUTER: skipped — OPENROUTER_API_KEY not set in .env")

    out_path = os.path.join(DATA_DIR, "capability_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
    print(f"\nFull report saved to {out_path}")


if __name__ == "__main__":
    main()
