from __future__ import annotations

import ast
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .models import Evidence


@dataclass(frozen=True)
class CheckResult:
    passed: bool | None
    evidence: Evidence


def check_json(response: str) -> CheckResult:
    try:
        json.loads(response)
    except json.JSONDecodeError as exc:
        return CheckResult(False, Evidence("deterministic", "schema_validation", f"invalid JSON: {exc.msg}", 0.99))
    return CheckResult(True, Evidence("deterministic", "schema_validation", "valid JSON", 0.99))


def check_python_syntax(response: str) -> CheckResult:
    source = response.strip()
    if source.startswith("```"):
        source = re.sub(r"^```(?:python)?\\s*|\\s*```$", "", source, flags=re.IGNORECASE)
    try:
        ast.parse(source)
    except SyntaxError as exc:
        return CheckResult(False, Evidence("deterministic", "compile_or_tests", f"Python syntax error: {exc.msg}", 0.99))
    return CheckResult(True, Evidence("deterministic", "compile_or_tests", "Python syntax is valid", 0.99))


def check_arithmetic(expected: float, actual: float, tolerance: float = 1e-9) -> CheckResult:
    passed = math.isclose(expected, actual, rel_tol=tolerance, abs_tol=tolerance)
    result = f"expected={expected}, actual={actual}"
    return CheckResult(passed, Evidence("deterministic", "calculator", result, 0.999))


def check_required_strings(response: str, required: list[str]) -> CheckResult:
    missing = [item for item in required if item not in response]
    passed = not missing
    result = "all required strings present" if passed else f"missing: {missing}"
    return CheckResult(passed, Evidence("deterministic", "required_content", result, 0.98))
