from __future__ import annotations

import math
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
    output_schema: dict[str, Any] | None = None


@dataclass(frozen=True)
class EvaluationProfile:
    dimensions: tuple[str, ...]
    hard_gates: tuple[str, ...] = ()
    deterministic_checks: tuple[str, ...] = ()
    external_verification: tuple[str, ...] = ()
    llm_evaluators: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    dimension_weights: dict[str, float] = field(default_factory=dict)
    minimum_scores: dict[str, float] = field(default_factory=dict)
    required_dimensions: tuple[str, ...] = ()
    minimum_confidence: float = 0.60
    minimum_overall_score: float = 0.75
    evaluation_effort: str = "medium"
    max_revisions: int = 1
    max_verification_steps: int = 2
    stopping_conditions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        dimension_set = set(self.dimensions)
        if not self.dimensions:
            raise ValueError("evaluation profile must configure at least one dimension")
        if len(dimension_set) != len(self.dimensions):
            raise ValueError("evaluation dimensions must be unique")
        if any(not isinstance(name, str) or not name.strip() for name in self.dimensions):
            raise ValueError("evaluation dimensions must be non-empty strings")
        if len(set(self.required_dimensions)) != len(self.required_dimensions):
            raise ValueError("required dimensions must be unique")
        if any(not isinstance(name, str) or not name.strip() for name in self.required_dimensions):
            raise ValueError("required dimensions must be non-empty strings")
        if any(name not in dimension_set for name in self.required_dimensions):
            raise ValueError("required dimensions must be present in dimensions")
        if any(name not in dimension_set for name in self.dimension_weights):
            raise ValueError("dimension weights must reference configured dimensions")
        if any(name not in dimension_set for name in self.minimum_scores):
            raise ValueError("minimum scores must reference configured dimensions")
        if any(not isinstance(weight, (int, float)) or isinstance(weight, bool) or not math.isfinite(weight) or weight < 0 for weight in self.dimension_weights.values()):
            raise ValueError("dimension weights must be finite non-negative numbers")
        for name, score in self.minimum_scores.items():
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError(f"minimum score for {name} must be a finite number between 0 and 1")
        for name in self.hard_gates + self.deterministic_checks + self.external_verification + self.llm_evaluators + self.evidence_requirements + self.stopping_conditions:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("policy selectors must be non-empty strings")
        if not isinstance(self.minimum_confidence, (int, float)) or isinstance(self.minimum_confidence, bool) or not math.isfinite(self.minimum_confidence) or not 0 <= self.minimum_confidence <= 1:
            raise ValueError("minimum confidence must be a finite number between 0 and 1")
        if not isinstance(self.minimum_overall_score, (int, float)) or isinstance(self.minimum_overall_score, bool) or not math.isfinite(self.minimum_overall_score) or not 0 <= self.minimum_overall_score <= 1:
            raise ValueError("minimum overall score must be a finite number between 0 and 1")
        if self.evaluation_effort not in {"low", "medium", "high"}:
            raise ValueError("evaluation_effort must be low, medium, or high")
        if not isinstance(self.max_revisions, int) or isinstance(self.max_revisions, bool) or self.max_revisions < 0:
            raise ValueError("max_revisions must be a non-negative integer")
        if not isinstance(self.max_verification_steps, int) or isinstance(self.max_verification_steps, bool) or self.max_verification_steps < 0:
            raise ValueError("max_verification_steps must be a non-negative integer")


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
