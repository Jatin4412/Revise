from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from typing import Protocol

from .models import Evidence, EvaluationProfile, TaskContract


class DeterministicVerifier(Protocol):
    """A verifier that checks a property without asking an LLM to judge it."""

    name: str

    def verify(self, contract: TaskContract, response: str) -> tuple[Evidence, ...]:
        ...


_ARITHMETIC_EXPRESSION_RE = re.compile(r"\d+(?:\s*(?:[+\-*/×÷])\s*\d+)+")
_NUMERIC_ANSWER_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*$")


@dataclass(frozen=True)
class ArithmeticVerifier:
    """Checks simple arithmetic equalities and direct numeric answers."""

    name: str = "arithmetic"

    def verify(self, contract: TaskContract, response: str) -> tuple[Evidence, ...]:
        evidence: list[Evidence] = []

        # First check explicit arithmetic equalities in the generated response.
        equality_pattern = re.compile(
            r"(?P<expr>\d+(?:\s*[+\-*/×÷]\s*\d+)+)\s*=\s*(?P<value>-?\d+(?:\.\d+)?)"
        )
        for match in equality_pattern.finditer(response):
            expression = match.group("expr")
            expected = float(match.group("value"))
            try:
                actual = _safe_arithmetic(expression)
            except (ArithmeticError, ValueError, SyntaxError):
                continue
            passed = abs(actual - expected) <= 1e-9
            evidence.append(
                Evidence(
                    "deterministic.arithmetic",
                    "deterministic",
                    "pass" if passed else "fail",
                    1.0,
                    (f"{expression} = {match.group('value')}",),
                )
            )

        # If the task contains a direct arithmetic expression, compare it with
        # a response that is itself a single numeric answer. This catches cases
        # such as: prompt "What is 25 × 17?" -> response "425".
        task_expressions = _ARITHMETIC_EXPRESSION_RE.findall(contract.goal)
        if len(task_expressions) == 1:
            expression = task_expressions[0]
            answer = _NUMERIC_ANSWER_RE.fullmatch(response)
            if answer is not None:
                try:
                    expected = _safe_arithmetic(expression)
                    actual = float(answer.group(1))
                except (ArithmeticError, ValueError, SyntaxError):
                    expected = actual = None
                if expected is not None and actual is not None:
                    passed = abs(expected - actual) <= 1e-9
                    evidence.append(
                        Evidence(
                            "deterministic.arithmetic",
                            "deterministic",
                            "pass" if passed else "fail",
                            1.0,
                            (f"task_expression:{expression}", f"numeric_answer:{answer.group(1)}"),
                        )
                    )

        return tuple(evidence)


@dataclass(frozen=True)
class PythonSyntaxVerifier:
    """Compiles Python snippets to AST without executing user code."""

    name: str = "python_syntax"

    def verify(self, contract: TaskContract, response: str) -> tuple[Evidence, ...]:
        del contract
        snippets = re.findall(r"```(?:python|py)\s*\n(.*?)```", response, flags=re.IGNORECASE | re.DOTALL)
        evidence: list[Evidence] = []
        for index, snippet in enumerate(snippets, start=1):
            try:
                ast.parse(snippet)
                result = "pass"
                provenance = (f"python_block_{index}",)
            except SyntaxError as exc:
                result = "fail"
                provenance = (f"python_block_{index}", f"syntax_error:{exc.msg}")
            evidence.append(Evidence("deterministic.python_syntax", "deterministic", result, 1.0, provenance))
        return tuple(evidence)


@dataclass(frozen=True)
class JsonVerifier:
    """Checks that a JSON-formatted response is syntactically valid."""

    name: str = "json"

    def verify(self, contract: TaskContract, response: str) -> tuple[Evidence, ...]:
        if not _expects_json(contract):
            return ()
        candidate = _extract_json(response)
        if candidate is None:
            return (Evidence("deterministic.json", "deterministic", "fail", 1.0, ("no JSON object/array found",)),)
        try:
            json.loads(candidate)
        except json.JSONDecodeError as exc:
            return (Evidence("deterministic.json", "deterministic", "fail", 1.0, (f"json_error:{exc.msg}",)),)
        return (Evidence("deterministic.json", "deterministic", "pass", 1.0, ("valid JSON",)),)


_DEFAULT_VERIFIERS: dict[str, DeterministicVerifier] = {
    "arithmetic": ArithmeticVerifier(),
    "python_syntax": PythonSyntaxVerifier(),
    "json": JsonVerifier(),
}


def run_deterministic_verifiers(contract: TaskContract, response: str, profile: EvaluationProfile, *, registry: dict[str, DeterministicVerifier] | None = None) -> tuple[Evidence, ...]:
    """Run only the deterministic checks selected by the evaluation profile."""
    selected = registry or _DEFAULT_VERIFIERS
    evidence: list[Evidence] = []
    for name in profile.deterministic_checks:
        verifier = selected.get(name)
        if verifier is not None:
            evidence.extend(verifier.verify(contract, response))
    return tuple(evidence)


def _safe_arithmetic(expression: str) -> float:
    normalized = expression.replace("×", "*").replace("÷", "/")
    tree = ast.parse(normalized, mode="eval")

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right == 0:
                raise ZeroDivisionError("division by zero")
            return left / right
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        raise ValueError("unsupported arithmetic expression")

    return visit(tree)


def _expects_json(contract: TaskContract) -> bool:
    format_text = (contract.desired_format or "").lower()
    return "json" in format_text or any("json" in item.lower() for item in contract.verification_requirements)


def _extract_json(response: str) -> str | None:
    stripped = response.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    if stripped.startswith(("{", "[")):
        return stripped
    return None
