"""SMPF AI Text Generation — Groq free models with retries.
Models: openai/gpt-oss-120b, openai/gpt-oss-20b, qwen/qwen3.8-27b
"""
import os, requests, time
from dotenv import load_dotenv
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]


def generate_text(prompt: str, model: str = None, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """Generate text with retries and model rotation."""
    models_to_try = [model] if model else MODELS
    last_error = None
    
    for m in models_to_try:
        for attempt in range(3):
            try:
                resp = requests.post(GROQ_URL,
                    headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                    json={"model": m, "messages": [{"role": "user", "content": prompt}],
                          "max_tokens": max_tokens, "temperature": temperature},
                    timeout=90,
                )
                if resp.ok and resp.json().get("choices"):
                    return resp.json()["choices"][0]["message"]["content"]
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                break
            except Exception as exc:
                last_error = str(exc)
                time.sleep(2 ** attempt)
    
    raise RuntimeError(f"All models failed. Last error: {last_error}")


if __name__ == "__main__":
    result = generate_text("Write a 2-sentence post about AI. Include hashtags.", max_tokens=200)
    print(result)
