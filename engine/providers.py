from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Callable, Protocol
from urllib import error, request

from .revise.models import (
    DimensionResult,
    EvaluationProfile,
    Evidence,
    Issue,
    RevisionPlan,
    Severity,
    TaskContract,
)

DimensionEvaluator = Callable[[TaskContract, str], DimensionResult]
TextGenerator = Callable[[TaskContract, str | None], str]


class Primary(Protocol):
    """Generates a candidate response for a task."""

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        ...


class Secondary(Protocol):
    """Evaluates a candidate through task-specific dimension evaluators."""

    def evaluators(
        self,
        contract: TaskContract,
        profile: EvaluationProfile,
    ) -> Mapping[str, DimensionEvaluator]:
        ...


class Verifier(Protocol):
    """Runs deterministic or external checks and returns evidence."""

    def verify(
        self,
        contract: TaskContract,
        response: str,
        profile: EvaluationProfile,
    ) -> tuple[Evidence, ...]:
        ...


class FunctionPrimary:
    """Small adapter for a plain generation function."""

    def __init__(self, function: Callable[[TaskContract, str | None], str]) -> None:
        self._function = function

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        return self._function(contract, context)


class StructuredLLMSecondary:
    """Provider-agnostic LLM Secondary that produces structured evaluation JSON."""

    def __init__(self, generator: TextGenerator) -> None:
        self._generator = generator

    def evaluators(
        self,
        contract: TaskContract,
        profile: EvaluationProfile,
    ) -> Mapping[str, DimensionEvaluator]:
        cache: dict[str, DimensionResult] | None = None
        issues: tuple[Issue, ...] = ()
        revision = RevisionPlan()

        def evaluate_all() -> tuple[dict[str, DimensionResult], tuple[Issue, ...], RevisionPlan]:
            nonlocal cache, issues, revision
            if cache is not None:
                return cache, issues, revision
            prompt = _build_evaluation_prompt(contract, profile)
            raw = self._generator(contract, prompt)
            cache, issues, revision = _parse_evaluation(raw, profile)
            return cache, issues, revision

        def evaluator_for(name: str) -> DimensionEvaluator:
            def evaluator(_contract: TaskContract, _response: str) -> DimensionResult:
                dimensions, _, _ = evaluate_all()
                return dimensions[name]

            return evaluator

        return {name: evaluator_for(name) for name in profile.dimensions}


class OpenAIPrimary:
    """OpenAI provider adapter for the Primary role."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None, timeout: float = 60.0) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL")
        self.timeout = timeout

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI provider")
        if not self.model:
            raise RuntimeError("OPENAI_MODEL or an explicit model is required for the OpenAI provider")
        payload = {"model": self.model, "input": _build_prompt(contract, context)}
        body = _post_json(
            "https://api.openai.com/v1/responses",
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
            self.timeout,
            "OpenAI",
        )
        text = _extract_output_text(body)
        if not text:
            raise RuntimeError("OpenAI response did not contain output text")
        return text


class GeminiPrimary:
    """Gemini provider adapter for the Primary role."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None, timeout: float = 60.0) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_PRIMARY_MODEL") or os.environ.get("GEMINI_MODEL")
        self.timeout = timeout

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the Gemini provider")
        if not self.model:
            raise RuntimeError("GEMINI_PRIMARY_MODEL or an explicit model is required for the Gemini provider")
        body = _post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            {"contents": [{"parts": [{"text": _build_prompt(contract, context)}]}]},
            {"x-goog-api-key": self.api_key},
            self.timeout,
            "Gemini",
        )
        text = _extract_gemini_text(body)
        if not text:
            raise RuntimeError("Gemini response did not contain output text")
        return text


class GrokPrimary:
    """Grok/xAI provider adapter using its OpenAI-compatible API."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None, timeout: float = 60.0) -> None:
        self.api_key = api_key or os.environ.get("XAI_API_KEY")
        self.model = model or os.environ.get("XAI_MODEL")
        self.timeout = timeout

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        return _openai_compatible_generate(
            provider="Grok",
            endpoint="https://api.x.ai/v1/responses",
            api_key=self.api_key,
            model=self.model,
            contract=contract,
            context=context,
            timeout=self.timeout,
        )


class OllamaPrimary:
    """Ollama provider adapter for local models."""

    def __init__(self, *, model: str | None = None, endpoint: str | None = None, timeout: float = 120.0) -> None:
        self.model = model or os.environ.get("OLLAMA_MODEL")
        self.endpoint = (endpoint or os.environ.get("OLLAMA_ENDPOINT") or "http://localhost:11434").rstrip("/")
        self.timeout = timeout

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        if not self.model:
            raise RuntimeError("OLLAMA_MODEL or an explicit model is required for the Ollama provider")
        body = _post_json(
            f"{self.endpoint}/api/chat",
            {"model": self.model, "messages": [{"role": "user", "content": _build_prompt(contract, context)}], "stream": False},
            {},
            self.timeout,
            "Ollama",
        )
        message = body.get("message", {})
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Ollama response did not contain output text")
        return text.strip()


class GeminiSecondary(StructuredLLMSecondary):
    """Gemini-backed Secondary provider adapter."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None, timeout: float = 60.0) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        selected_model = model or os.environ.get("GEMINI_SECONDARY_MODEL")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is required for the Gemini provider")
        if not selected_model:
            raise RuntimeError("GEMINI_SECONDARY_MODEL or an explicit model is required for the Gemini provider")

        def generate(contract: TaskContract, evaluation_prompt: str | None) -> str:
            body = _post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent",
                {"contents": [{"parts": [{"text": evaluation_prompt or ""}]}]},
                {"x-goog-api-key": key},
                timeout,
                "Gemini Secondary",
            )
            return _extract_gemini_text(body)

        super().__init__(generate)


class OpenAISecondary(StructuredLLMSecondary):
    """OpenAI-backed Secondary provider adapter."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None, timeout: float = 60.0) -> None:
        key = api_key or os.environ.get("OPENAI_API_KEY")
        selected_model = model or os.environ.get("OPENAI_SECONDARY_MODEL") or os.environ.get("OPENAI_MODEL")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI provider")
        if not selected_model:
            raise RuntimeError("OPENAI_SECONDARY_MODEL or an explicit model is required for the OpenAI provider")

        def generate(contract: TaskContract, evaluation_prompt: str | None) -> str:
            body = _post_json(
                "https://api.openai.com/v1/responses",
                {"model": selected_model, "input": evaluation_prompt or ""},
                {"Authorization": f"Bearer {key}"},
                timeout,
                "OpenAI Secondary",
            )
            return _extract_output_text(body)

        super().__init__(generate)


class GrokSecondary(StructuredLLMSecondary):
    """Grok/xAI-backed Secondary provider adapter."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None, timeout: float = 60.0) -> None:
        key = api_key or os.environ.get("XAI_API_KEY")
        selected_model = model or os.environ.get("XAI_SECONDARY_MODEL") or os.environ.get("XAI_MODEL")
        if not key or not selected_model:
            raise RuntimeError("XAI_API_KEY and XAI_SECONDARY_MODEL are required for the Grok provider")

        def generate(contract: TaskContract, evaluation_prompt: str | None) -> str:
            body = _post_json(
                "https://api.x.ai/v1/responses",
                {"model": selected_model, "input": evaluation_prompt or ""},
                {"Authorization": f"Bearer {key}"},
                timeout,
                "Grok Secondary",
            )
            return _extract_output_text(body)

        super().__init__(generate)


class OllamaSecondary(StructuredLLMSecondary):
    """Ollama-backed Secondary provider adapter."""

    def __init__(self, *, model: str | None = None, endpoint: str | None = None, timeout: float = 120.0) -> None:
        selected_model = model or os.environ.get("OLLAMA_SECONDARY_MODEL") or os.environ.get("OLLAMA_MODEL")
        base = (endpoint or os.environ.get("OLLAMA_ENDPOINT") or "http://localhost:11434").rstrip("/")
        if not selected_model:
            raise RuntimeError("OLLAMA_SECONDARY_MODEL or an explicit model is required for the Ollama provider")

        def generate(contract: TaskContract, evaluation_prompt: str | None) -> str:
            body = _post_json(
                f"{base}/api/chat",
                {"model": selected_model, "messages": [{"role": "user", "content": evaluation_prompt or ""}], "stream": False, "format": "json"},
                {},
                timeout,
                "Ollama Secondary",
            )
            message = body.get("message", {})
            text = message.get("content") if isinstance(message, dict) else None
            return text.strip() if isinstance(text, str) else ""

        super().__init__(generate)


def _openai_compatible_generate(*, provider: str, endpoint: str, api_key: str | None, model: str | None, contract: TaskContract, context: str | None, timeout: float) -> str:
    if not api_key:
        raise RuntimeError(f"an API key is required for the {provider} provider")
    if not model:
        raise RuntimeError(f"a model is required for the {provider} provider")
    body = _post_json(
        endpoint,
        {"model": model, "input": _build_prompt(contract, context)},
        {"Authorization": f"Bearer {api_key}"},
        timeout,
        provider,
    )
    text = _extract_output_text(body)
    if not text:
        raise RuntimeError(f"{provider} response did not contain output text")
    return text


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: float, provider: str) -> dict:
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


def _build_prompt(contract: TaskContract, context: str | None) -> str:
    sections = [f"Task:\n{contract.goal}"]
    if contract.requirements:
        sections.append("Requirements:\n" + "\n".join(f"- {item}" for item in contract.requirements))
    if contract.constraints:
        sections.append("Constraints:\n" + "\n".join(f"- {item}" for item in contract.constraints))
    if contract.desired_format:
        sections.append(f"Format: {contract.desired_format}")
    if contract.desired_length:
        sections.append(f"Length: {contract.desired_length}")
    if contract.desired_style:
        sections.append(f"Style: {contract.desired_style}")
    if contract.known_context:
        sections.append("Context:\n" + "\n".join(contract.known_context))
    if context:
        sections.append("Previous attempt / revision context:\n" + context)
    return "\n\n".join(sections)


def _build_evaluation_prompt(contract: TaskContract, profile: EvaluationProfile) -> str:
    dimensions = "\n".join(f"- {name}" for name in profile.dimensions)
    return f"""You are the Secondary evaluator in a revision engine. Do not rewrite the answer. Evaluate the candidate against the task and return ONLY valid JSON.

Task:\n{contract.goal}
Requirements:\n{chr(10).join(f"- {x}" for x in contract.requirements) or "- none"}
Constraints:\n{chr(10).join(f"- {x}" for x in contract.constraints) or "- none"}
Candidate:\n{{RESPONSE}}

Evaluate these dimensions:\n{dimensions}

JSON shape:
{{
  "dimensions": {{"dimension_name": {{"score": 0.0, "confidence": 0.0, "status": "pass|partial|fail", "reason": "..."}}}},
  "issues": [{{"type": "...", "severity": "critical|major|moderate|minor|informational", "description": "...", "location": null}}],
  "revision": {{"strategy": "...", "instructions": ["..."]}}
}}
Scores must be between 0 and 1. Confidence must be between 0 and 1. Cover every requested dimension. Base judgments on the task, not stylistic preference.""".replace("{RESPONSE}", "the candidate response supplied by the caller")


def _parse_evaluation(raw: str, profile: EvaluationProfile) -> tuple[dict[str, DimensionResult], tuple[Issue, ...], RevisionPlan]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
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
            dimensions[name] = DimensionResult(None, 0.0, "unknown", "Secondary did not evaluate this dimension")
            continue
        score = item.get("score")
        confidence = item.get("confidence", 0.0)
        status = item.get("status")
        reason = item.get("reason", "")
        if not isinstance(score, (int, float)) or not isinstance(confidence, (int, float)) or status not in {"pass", "partial", "fail"}:
            dimensions[name] = DimensionResult(None, 0.0, "unknown", "Secondary returned an invalid dimension result")
            continue
        dimensions[name] = DimensionResult(max(0.0, min(1.0, float(score))), max(0.0, min(1.0, float(confidence))), status, str(reason))

    issues: list[Issue] = []
    raw_issues = payload.get("issues", [])
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if not isinstance(item, dict):
                continue
            severity = item.get("severity", "minor")
            if severity not in {s.value for s in Severity}:
                severity = Severity.MINOR.value
            issues.append(Issue(str(item.get("type", "evaluation")), Severity(severity), str(item.get("description", "")), item.get("location")))

    raw_revision = payload.get("revision", {})
    if isinstance(raw_revision, dict):
        instructions = raw_revision.get("instructions", [])
        revision = RevisionPlan(
            strategy=str(raw_revision.get("strategy")) if raw_revision.get("strategy") is not None else None,
            instructions=tuple(str(x) for x in instructions) if isinstance(instructions, list) else (),
        )
    else:
        revision = RevisionPlan()
    return dimensions, tuple(issues), revision


def _extract_output_text(payload: dict) -> str:
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


def _extract_gemini_text(payload: dict) -> str:
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
    return "\n".join(chunks).strip()
