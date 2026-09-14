from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .models import Evidence

_PRIORITY = {"deterministic": 4, "external": 3, "specialized_llm": 2, "llm": 1}
_ALLOWED_RESULTS = {"pass", "fail", "unknown", "partial"}


@dataclass(frozen=True)
class FusedEvidence:
    evidence: tuple[Evidence, ...]
    confidence: float


def validate_evidence(evidence: Iterable[Evidence]) -> tuple[Evidence, ...]:
    """Validate evidence at the fusion boundary so malformed evidence cannot pass policy."""
    validated: list[Evidence] = []
    for index, item in enumerate(evidence):
        if not isinstance(item, Evidence):
            raise ValueError(f"evidence[{index}] must be an Evidence instance")
        if not isinstance(item.source, str) or not item.source.strip():
            raise ValueError(f"evidence[{index}] source must be a non-empty string")
        if not isinstance(item.method, str) or not item.method.strip():
            raise ValueError(f"evidence[{index}] method must be a non-empty string")
        if item.result not in _ALLOWED_RESULTS:
            raise ValueError(f"evidence[{index}] result is invalid")
        if isinstance(item.confidence, bool) or not isinstance(item.confidence, (int, float)) or not math.isfinite(item.confidence) or not 0 <= item.confidence <= 1:
            raise ValueError(f"evidence[{index}] confidence must be a finite number between 0 and 1")
        if any(not isinstance(value, str) or not value.strip() for value in item.provenance):
            raise ValueError(f"evidence[{index}] provenance entries must be non-empty strings")
        validated.append(item)
    return tuple(validated)


def fuse_evidence(evidence: Iterable[Evidence]) -> FusedEvidence:
    items = sorted(validate_evidence(evidence), key=lambda e: _PRIORITY.get(e.method, 0), reverse=True)
    if not items:
        return FusedEvidence((), 0.0)

    confidence = sum(e.confidence for e in items) / len(items)
    for index, current in enumerate(items):
        for other in items[index + 1 :]:
            if _PRIORITY.get(current.method, 0) == _PRIORITY.get(other.method, 0) and current.result != other.result:
                confidence *= 0.75
    return FusedEvidence(tuple(items), confidence)
