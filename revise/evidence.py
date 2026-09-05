from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Evidence


_SOURCE_PRIORITY = {
    "deterministic": 4,
    "external": 3,
    "specialized_llm": 2,
    "llm": 1,
}


@dataclass(frozen=True)
class FusedEvidence:
    evidence: tuple[Evidence, ...]
    confidence: float


def fuse_evidence(items: Iterable[Evidence]) -> FusedEvidence:
    """Normalize evidence without pretending conflicting judges are consensus.

    Higher-reliability evidence is preferred when methods conflict. Confidence is
    capped by the strongest available source and reduced when high-priority
    sources materially disagree.
    """
    evidence = tuple(items)
    if not evidence:
        return FusedEvidence((), 0.0)

    ordered = tuple(sorted(evidence, key=lambda e: _SOURCE_PRIORITY.get(e.source, 0), reverse=True))
    top_priority = _SOURCE_PRIORITY.get(ordered[0].source, 0)
    top = tuple(e for e in ordered if _SOURCE_PRIORITY.get(e.source, 0) == top_priority)

    confidence = max(e.confidence for e in top)
    results = {e.result.strip().lower() for e in top}
    if len(results) > 1:
        confidence *= 0.6

    return FusedEvidence(ordered, max(0.0, min(1.0, confidence)))
