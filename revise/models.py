from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Mode(str, Enum):
    LITE = "lite"
    BASIC = "basic"
    PRO = "pro"
    AUTO = "auto"


class Decision(str, Enum):
    ACCEPT = "accept"
    REVISE = "revise"
    ASK = "ask"


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    INFORMATIONAL = "informational"


@dataclass(frozen=True)
class TaskContract:
    goal: str
    requirements: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    desired_format: str | None = None
    desired_length: str | None = None
    desired_style: str | None = None
    mode: Mode = Mode.BASIC
    known_context: tuple[str, ...] = ()
    missing_context: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    verification_requirements: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationProfile:
    dimensions: tuple[str, ...]
    hard_gates: tuple[str, ...] = ()
    deterministic_checks: tuple[str, ...] = ()
    external_verification: tuple[str, ...] = ()
    llm_evaluators: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    evaluation_effort: str = "medium"
    max_revisions: int = 1
    max_verification_steps: int = 2
    stopping_conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class DimensionResult:
    score: float | None
    confidence: float
    status: str
    reason: str = ""


@dataclass(frozen=True)
class Evidence:
    source: str
    method: str
    result: str
    confidence: float
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class Issue:
    type: str
    severity: Severity
    description: str
    location: str | None = None
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class RevisionPlan:
    strategy: str | None = None
    instructions: tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationPlan:
    required: bool = False
    method: str | None = None


@dataclass(frozen=True)
class EvaluationResult:
    decision: Decision
    overall_score: float | None
    confidence: float
    dimensions: dict[str, DimensionResult] = field(default_factory=dict)
    issues: tuple[Issue, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    revision: RevisionPlan = field(default_factory=RevisionPlan)
    verification: VerificationPlan = field(default_factory=VerificationPlan)


@dataclass(frozen=True)
class Version:
    id: str
    response: str
    evaluation: EvaluationResult | None = None
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
