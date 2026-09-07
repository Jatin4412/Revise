from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Callable, Protocol
from urllib import error, request

from .revise.models import DimensionResult, EvaluationProfile, Evidence, TaskContract

DimensionEvaluator = Callable[[TaskContract, str], DimensionResult]


class Primary(Protocol):
    """Generates a candidate response for a task."""

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        ...


class Secondary(Protocol):
    """Provides task-specific evaluator functions for a candidate response."""

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


class OpenAIPrimary:
    """Minimal OpenAI Responses API adapter for server-side engine use."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
        endpoint: str = "https://api.openai.com/v1/responses",
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")
        self.timeout = timeout
        self.endpoint = endpoint

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAIPrimary")

        payload = json.dumps({"model": self.model, "input": _build_prompt(contract, context)}).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed ({exc.code}): {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc.reason}") from exc

        text = _extract_output_text(body)
        if not text:
            raise RuntimeError("OpenAI response did not contain output text")
        return text


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


def _extract_output_text(payload: dict) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str):
        return direct.strip()

    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str):
                    chunks.append(text)
    return "\n".join(chunks).strip()
