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

ENGINE_URL = "http://127.0.0.1:8000/v1/engine"
SECONDARY = {"provider": "gemini", "model": "gemini-3.1-flash-lite"}


def run_case(case: ProviderCase, prompt: str) -> tuple[float, dict]:
    payload = {
        "prompt": prompt,
        "mode": "basic",
        "primary_model": {"provider": case.provider, "model": case.model},
        "secondary_model": SECONDARY,
    }
    req = request.Request(
        ENGINE_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=120.0) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:300]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc
    return time.perf_counter() - started, body


def main() -> int:
    print("Revise full pipeline matrix")
    print("Primary -> Secondary -> evaluation -> decision -> final selection")
    print(f"Secondary fixed for comparison: {SECONDARY['provider']}/{SECONDARY['model']}")
    print()

    failures = 0
    for case in CASES:
        print(f"=== {case.name} ({case.provider}/{case.model}) ===")
        for index, prompt in enumerate(PROMPTS, 1):
            try:
                elapsed, body = run_case(case, prompt)
                text = body.get("text", "")
                decision = body.get("decision", "unknown")
                version = body.get("version_id")
                if not isinstance(text, str) or not text.strip():
                    raise RuntimeError("engine returned empty text")
                if decision not in {"accept", "revise", "ask"}:
                    raise RuntimeError(f"unexpected decision: {decision}")
                preview = " ".join(text.split())[:180]
                print(f"[{index}] PASS | {elapsed:.2f}s | decision={decision} | version={version} | {preview}")
            except Exception as exc:
                failures += 1
                print(f"[{index}] FAIL | {exc}")
        print()

    print(f"Completed: {len(CASES)} providers x {len(PROMPTS)} prompts")
    print(f"Failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
