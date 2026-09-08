from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any
from urllib import error, request

from .revise.models import (
    Decision,
    DimensionResult,
    EvaluationProfile,
    EvaluationResult,
    Issue,
    RevisionPlan,
    Severity,
    TaskContract,
)


class LLMPrimary:
    """Provider-neutral Primary adapter backed by a configured text callable."""

    def __init__(self, generate_text: Callable[[str], str]) -> None:
        self._generate_text = generate_text

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        return self._generate_text(_generation_prompt(contract, context))


class LLMSecondary:
    """Provider-neutral Secondary that evaluates a candidate in one structured pass."""

    def __init__(self, generate_text: Callable[[str], str]) -> None:
        self._generate_text = generate_text

    def evaluate_candidate(
        self,
        contract: TaskContract,
        response: str,
        profile: EvaluationProfile,
    ) -> EvaluationResult:
        prompt = _evaluation_prompt(contract, response, profile)
        raw = self._generate_text(prompt)
        return _parse_evaluation(raw, profile)

    def evaluators(self, contract: TaskContract, profile: EvaluationProfile):
        """Compatibility adapter for the legacy Secondary protocol."""
        cache: dict[str, EvaluationResult] = {}

        def evaluator(name: str):
            def run(current_contract: TaskContract, response: str) -> DimensionResult:
                result = cache.get(response)
                if result is None:
                    result = self.evaluate_candidate(current_contract, response, profile)
                    cache[response] = result
                return result.dimensions[name]

            return run

        return {name: evaluator(name) for name in profile.dimensions}


def build_primary(provider: str, model: str | None) -> LLMPrimary:
    """Build a Primary adapter without exposing provider details to the core engine."""
    return LLMPrimary(_text_callable(provider, model, role="primary"))


def build_secondary(provider: str, model: str | None) -> LLMSecondary:
    """Build a Secondary adapter without exposing provider details to the core engine."""
    return LLMSecondary(_text_callable(provider, model, role="secondary"))


def _text_callable(provider: str, model: str | None, *, role: str) -> Callable[[str], str]:
    provider = provider.strip().lower()
    if provider == "gemini":
        return _gemini_callable(model, role=role)
    if provider == "groq":
        return _groq_callable(model, role=role)
    if provider == "openrouter":
        return _openrouter_callable(model, role=role)
    if provider == "openai":
        return _openai_callable(model, role=role)
    if provider == "grok":
        return _xai_callable(model, role=role)
    raise ValueError(f"unsupported model provider: {provider}; available: gemini, groq, openrouter, grok, openai")


def _gemini_callable(model: str | None, *, role: str) -> Callable[[str], str]:
    key = os.environ.get("GEMINI_API_KEY")
    selected = model or os.environ.get(f"GEMINI_{role.upper()}_MODEL") or os.environ.get("GEMINI_MODEL")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is required for the Gemini provider")
    if not selected:
        raise RuntimeError(f"GEMINI_{role.upper()}_MODEL or an explicit model is required for the Gemini provider")

    def call(prompt: str) -> str:
        body = _post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{selected}:generateContent",
            {"contents": [{"parts": [{"text": prompt}]}]},
            {"x-goog-api-key": key},
            60.0,
            "Gemini",
        )
        return _extract_gemini_text(body)

    return call


def _groq_callable(model: str | None, *, role: str) -> Callable[[str], str]:
    key = os.environ.get("GROQ_API_KEY")
    selected = model or os.environ.get(f"GROQ_{role.upper()}_MODEL") or os.environ.get("GROQ_MODEL") or "openai/gpt-oss-120b"
    if not key:
        raise RuntimeError("GROQ_API_KEY is required for the Groq provider")
    return _chat_completions_callable("Groq", "https://api.groq.com/openai/v1/chat/completions", key, selected)


def _openrouter_callable(model: str | None, *, role: str) -> Callable[[str], str]:
    key = os.environ.get("OPENROUTER_API_KEY")
    selected = model or os.environ.get(f"OPENROUTER_{role.upper()}_MODEL") or os.environ.get("OPENROUTER_MODEL") or "openrouter/free"
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is required for the OpenRouter provider")
    return _chat_completions_callable("OpenRouter", "https://openrouter.ai/api/v1/chat/completions", key, selected)


def _openai_callable(model: str | None, *, role: str) -> Callable[[str], str]:
    key = os.environ.get("OPENAI_API_KEY")
    selected = model or os.environ.get(f"OPENAI_{role.upper()}_MODEL") or os.environ.get("OPENAI_MODEL")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for the OpenAI provider")
    if not selected:
        raise RuntimeError(f"OPENAI_{role.upper()}_MODEL or an explicit model is required for the OpenAI provider")
    return _responses_callable("OpenAI", "https://api.openai.com/v1/responses", key, selected)


def _xai_callable(model: str | None, *, role: str) -> Callable[[str], str]:
    key = os.environ.get("XAI_API_KEY")
    selected = model or os.environ.get(f"XAI_{role.upper()}_MODEL") or os.environ.get("XAI_MODEL")
    if not key:
        raise RuntimeError("XAI_API_KEY is required for the Grok provider")
    if not selected:
        raise RuntimeError(f"XAI_{role.upper()}_MODEL or an explicit model is required for the Grok provider")
    return _responses_callable("Grok", "https://api.x.ai/v1/responses", key, selected)


def _responses_callable(provider: str, endpoint: str, key: str, model: str) -> Callable[[str], str]:
    def call(prompt: str) -> str:
        body = _post_json(endpoint, {"model": model, "input": prompt}, {"Authorization": f"Bearer {key}"}, 60.0, provider)
        return _extract_output_text(body)

    return call


def _chat_completions_callable(provider: str, endpoint: str, key: str, model: str) -> Callable[[str], str]:
    def call(prompt: str) -> str:
        body = _post_json(
            endpoint,
            {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
            {"Authorization": f"Bearer {key}"},
            60.0,
            provider,
        )
        choices = body.get("choices", [])
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(f"{provider} response did not contain choices")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(f"{provider} response did not contain output text")
        return text.strip()

    return call


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float, provider: str) -> dict[str, Any]:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{provider} request failed ({exc.code}): {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"{provider} request failed: {exc.reason}") from exc
    if not isinstance(body, dict):
        raise RuntimeError(f"{provider} response was not a JSON object")
    return body


def _generation_prompt(contract: TaskContract, context: str | None) -> str:
    sections = [f"Task:\n{contract.goal}"]
    if contract.requirements:
        sections.append("Requirements:\n" + "\n".join(f"- {x}" for x in contract.requirements))
    if contract.constraints:
        sections.append("Constraints:\n" + "\n".join(f"- {x}" for x in contract.constraints))
    if contract.desired_format:
        sections.append(f"Format: {contract.desired_format}")
    if contract.desired_length:
        sections.append(f"Length: {contract.desired_length}")
    if contract.desired_style:
        sections.append(f"Style: {contract.desired_style}")
    if contract.known_context:
        sections.append("Context:\n" + "\n".join(contract.known_context))
    if context:
        sections.append("Revision context:\n" + context)
    return "\n\n".join(sections)


def _evaluation_prompt(contract: TaskContract, response: str, profile: EvaluationProfile) -> str:
    dimensions = "\n".join(f"- {name}" for name in profile.dimensions)
    requirements = "\n".join(f"- {x}" for x in contract.requirements) or "- none"
    constraints = "\n".join(f"- {x}" for x in contract.constraints) or "- none"
    return f"""You are the Secondary evaluator in Revise. Do not rewrite the candidate. Evaluate it against the task and return ONLY valid JSON.

Task:
{contract.goal}
Requirements:
{requirements}
Constraints:
{constraints}

Candidate response:
{response}

Dimensions to evaluate:
{dimensions}

Return exactly this JSON structure:
{{
  "dimensions": {{
    "dimension_name": {{"score": 0.0, "confidence": 0.0, "status": "pass|partial|fail", "reason": "..."}}
  }},
  "issues": [
    {{"type": "...", "severity": "critical|major|moderate|minor|informational", "description": "...", "location": null}}
  ],
  "revision": {{"strategy": "...", "instructions": ["..."]}}
}}

Cover every requested dimension. Scores and confidence are 0 to 1. Judge against the task and constraints, not personal stylistic preference."""


def _parse_evaluation(raw: str, profile: EvaluationProfile) -> EvaluationResult:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Secondary evaluator returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("dimensions"), dict):
        raise RuntimeError("Secondary evaluator response must contain a dimensions object")

    dimensions: dict[str, DimensionResult] = {}
    for name in profile.dimensions:
        item = payload["dimensions"].get(name)
        if not isinstance(item, dict):
            dimensions[name] = DimensionResult(None, 0.0, "unknown", "dimension was not evaluated")
            continue
        score = item.get("score")
        confidence = item.get("confidence", 0.0)
        status = item.get("status")
        if not isinstance(score, (int, float)) or not isinstance(confidence, (int, float)) or status not in {"pass", "partial", "fail"}:
            dimensions[name] = DimensionResult(None, 0.0, "unknown", "invalid evaluator result")
            continue
        dimensions[name] = DimensionResult(
            max(0.0, min(1.0, float(score))),
            max(0.0, min(1.0, float(confidence))),
            status,
            str(item.get("reason", "")),
        )

    issues: list[Issue] = []
    raw_issues = payload.get("issues", [])
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if not isinstance(item, dict):
                continue
            severity = item.get("severity", Severity.MINOR.value)
            try:
                severity_enum = Severity(severity)
            except ValueError:
                severity_enum = Severity.MINOR
            issues.append(
                Issue(
                    type=str(item.get("type", "evaluation")),
                    severity=severity_enum,
                    description=str(item.get("description", "")),
                    location=item.get("location") if isinstance(item.get("location"), str) else None,
                )
            )

    raw_revision = payload.get("revision", {})
    if isinstance(raw_revision, dict):
        raw_instructions = raw_revision.get("instructions", [])
        revision = RevisionPlan(
            strategy=str(raw_revision.get("strategy")) if raw_revision.get("strategy") is not None else None,
            instructions=tuple(str(x) for x in raw_instructions) if isinstance(raw_instructions, list) else (),
        )
    else:
        revision = RevisionPlan()

    known = [d for d in dimensions.values() if d.status != "unknown"]
    scores = [d.score for d in known if d.score is not None]
    confidence = sum(d.confidence for d in known) / len(known) if known else 0.0
    return EvaluationResult(
        decision=Decision.ACCEPT,
        overall_score=sum(scores) / len(scores) if scores else None,
        confidence=confidence,
        dimensions=dimensions,
        issues=tuple(issues),
        revision=revision,
    )


def _extract_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str):
        return direct.strip()
    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text" and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def _extract_gemini_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for candidate in payload.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content", {})
        if not isinstance(content, dict):
            continue
        for part in content.get("parts", []):
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
    text = "\n".join(chunks).strip()
    if not text:
        raise RuntimeError("Gemini response did not contain output text")
    return text
