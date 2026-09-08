from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from urllib import error, request


@dataclass(frozen=True)
class ProviderCase:
    name: str
    provider: str
    model: str


CASES = (
    ProviderCase("Gemini 3.7 Flash", "gemini", "gemini-3.7-flash"),
    ProviderCase("Gemini 3.1 Flash-Lite", "gemini", "gemini-3.1-flash-lite"),
    ProviderCase("GPT-OSS 120B (Groq)", "groq", "openai/gpt-oss-120b"),
    ProviderCase("OpenRouter Free", "openrouter", "openrouter/free"),
)

PROMPTS = (
    "What is 17 * 24? Give the result and one short calculation.",
    "Explain what an API is to a beginner in 3 concise bullet points.",
    "Write a Python function that returns the largest number in a non-empty list.",
)


KEYS = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def run_case(case: ProviderCase, prompt: str) -> tuple[float, int, dict]:
    import os

    key_name = KEYS[case.provider]
    key = os.environ.get(key_name)
    if not key:
        raise RuntimeError(f"{key_name} is not configured")

    if case.provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{case.model}:generateContent"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"x-goog-api-key": key}
    else:
        if case.provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
        else:
            url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": case.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "User-Agent": "ReviseEngine/0.1",
        }

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", **headers},
    )

    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=60.0) as response:
            status = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc

    return time.perf_counter() - started, status, payload


def extract_text(provider: str, payload: dict) -> str:
    if provider == "gemini":
        chunks: list[str] = []
        for candidate in payload.get("candidates", []):
            content = candidate.get("content", {}) if isinstance(candidate, dict) else {}
            for part in content.get("parts", []) if isinstance(content, dict) else []:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
        return " ".join(chunks).strip()

    choices = payload.get("choices", [])
    if choices and isinstance(choices[0], dict):
        message = choices[0].get("message", {})
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"].strip()
    return ""


def main() -> int:
    print("Revise provider matrix")
    print("Primary-only smoke test; no evaluation logic is changed.")
    print()

    failures = 0
    for case in CASES:
        print(f"=== {case.name} ({case.provider}/{case.model}) ===")
        for index, prompt in enumerate(PROMPTS, 1):
            try:
                elapsed, status, payload = run_case(case, prompt)
                text = extract_text(case.provider, payload)
                preview = " ".join(text.split())[:180]
                print(f"[{index}] PASS | HTTP {status} | {elapsed:.2f}s | {preview}")
            except Exception as exc:
                failures += 1
                print(f"[{index}] FAIL | {exc}")
        print()

    print(f"Completed: {len(CASES)} providers x {len(PROMPTS)} prompts")
    print(f"Failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
