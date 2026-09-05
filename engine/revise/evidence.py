from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Evidence

_PRIORITY = {"deterministic": 4, "external": 3, "specialized_llm": 2, "llm": 1}


@dataclass(frozen=True)
class FusedEvidence:
    evidence: tuple[Evidence, ...]
    confidence: float


def fuse_evidence(evidence: Iterable[Evidence]) -> FusedEvidence:
    items = sorted(evidence, key=lambda e: _PRIORITY.get(e.method, 0), reverse=True)
    if not items:
        return FusedEvidence((), 0.0)

    confidence = sum(e.confidence for e in items) / len(items)
    for index, current in enumerate(items):
        for other in items[index + 1 :]:
            if _PRIORITY.get(current.method, 0) == _PRIORITY.get(other.method, 0) and current.result != other.result:
                confidence *= 0.75
    return FusedEvidence(tuple(items), confidence)
