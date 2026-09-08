from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

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


@dataclass(frozen=True)
class JsonSchemaVerifier:
    """Validates JSON output against an explicit, safe JSON-Schema subset."""

    name: str = "json_schema"

    def verify(self, contract: TaskContract, response: str) -> tuple[Evidence, ...]:
        schema = contract.output_schema
        if schema is None:
            return ()
        candidate = _extract_json(response)
        if candidate is None:
            return (Evidence("deterministic.json_schema", "deterministic", "fail", 1.0, ("no JSON object/array found",)),)
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError as exc:
            return (Evidence("deterministic.json_schema", "deterministic", "fail", 1.0, (f"json_error:{exc.msg}",)),)
        try:
            errors = _validate_schema(value, schema, "$", root_schema=schema)
        except (TypeError, ValueError):
            errors = ("invalid schema",)
        if errors:
            return (Evidence("deterministic.json_schema", "deterministic", "fail", 1.0, tuple(errors[:8])),)
        return (Evidence("deterministic.json_schema", "deterministic", "pass", 1.0, ("schema_valid",)),)


_DEFAULT_VERIFIERS: dict[str, DeterministicVerifier] = {
    "arithmetic": ArithmeticVerifier(),
    "python_syntax": PythonSyntaxVerifier(),
    "json": JsonVerifier(),
    "json_schema": JsonSchemaVerifier(),
}


def run_deterministic_verifiers(
    contract: TaskContract,
    response: str,
    profile: EvaluationProfile,
    *,
    registry: dict[str, DeterministicVerifier] | None = None,
) -> tuple[Evidence, ...]:
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
    return "json" in format_text or contract.output_schema is not None or any(
        "json" in item.lower() for item in contract.verification_requirements
    )


def _extract_json(response: str) -> str | None:
    stripped = response.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    if stripped.startswith(("{", "[")):
        return stripped
    return None


def _validate_schema(value: Any, schema: Any, path: str, *, root_schema: dict[str, Any]) -> tuple[str, ...]:
    """Validate a deliberately bounded JSON-Schema subset without executing schema code."""
    if not isinstance(schema, dict):
        raise TypeError("schema must be an object")

    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/"):
            raise ValueError("unsupported $ref")
        target: Any = root_schema
        for part in ref[2:].split("/"):
            if not isinstance(target, dict) or part not in target:
                raise ValueError("unresolved $ref")
            target = target[part]
        return _validate_schema(value, target, path, root_schema=root_schema)

    errors: list[str] = []
    if "enum" in schema:
        enum = schema["enum"]
        if not isinstance(enum, list) or value not in enum:
            errors.append(f"{path}: value is not in enum")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value does not match const")

    if "oneOf" in schema:
        alternatives = schema["oneOf"]
        if not isinstance(alternatives, list) or not alternatives:
            raise ValueError("oneOf must be a non-empty list")
        matches = sum(not _validate_schema(value, item, path, root_schema=root_schema) for item in alternatives)
        if matches != 1:
            errors.append(f"{path}: oneOf requirement not satisfied")

    schema_type = schema.get("type")
    if schema_type is not None:
        allowed = schema_type if isinstance(schema_type, list) else [schema_type]
        if not all(isinstance(item, str) for item in allowed):
            raise ValueError("type must be a string or list of strings")
        if not any(_json_type_matches(value, item) for item in allowed):
            return tuple(errors + [f"{path}: expected type {schema_type}"])

    if isinstance(value, dict):
        required = schema.get("required", ())
        if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
            raise ValueError("required must be a list of strings")
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property '{key}'")

        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ValueError("properties must be an object")
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(_validate_schema(value[key], child_schema, f"{path}.{key}", root_schema=root_schema))

        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property '{key}'")
        elif isinstance(schema.get("additionalProperties"), dict):
            for key, item in value.items():
                if key not in properties:
                    errors.extend(_validate_schema(item, schema["additionalProperties"], f"{path}.{key}", root_schema=root_schema))

        minimum = schema.get("minProperties")
        maximum = schema.get("maxProperties")
        if minimum is not None and (not isinstance(minimum, int) or len(value) < minimum):
            errors.append(f"{path}: fewer than minProperties")
        if maximum is not None and (not isinstance(maximum, int) or len(value) > maximum):
            errors.append(f"{path}: more than maxProperties")

    if isinstance(value, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(value):
                errors.extend(_validate_schema(item, items, f"{path}[{index}]", root_schema=root_schema))
        elif items is not None:
            raise ValueError("items must be an object")
        if "minItems" in schema and (not isinstance(schema["minItems"], int) or len(value) < schema["minItems"]):
            errors.append(f"{path}: fewer than minItems")
        if "maxItems" in schema and (not isinstance(schema["maxItems"], int) or len(value) > schema["maxItems"]):
            errors.append(f"{path}: more than maxItems")
        if schema.get("uniqueItems") is True:
            if len({json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value}) != len(value):
                errors.append(f"{path}: items are not unique")

    if isinstance(value, str):
        if "minLength" in schema and (not isinstance(schema["minLength"], int) or len(value) < schema["minLength"]):
            errors.append(f"{path}: shorter than minLength")
        if "maxLength" in schema and (not isinstance(schema["maxLength"], int) or len(value) > schema["maxLength"]):
            errors.append(f"{path}: longer than maxLength")
        if "pattern" in schema:
            pattern = schema["pattern"]
            if not isinstance(pattern, str):
                raise ValueError("pattern must be a string")
            try:
                matched = re.search(pattern, value) is not None
            except re.error as exc:
                raise ValueError("invalid pattern") from exc
            if not matched:
                errors.append(f"{path}: pattern mismatch")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and (not isinstance(schema["minimum"], (int, float)) or value < schema["minimum"]):
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and (not isinstance(schema["maximum"], (int, float)) or value > schema["maximum"]):
            errors.append(f"{path}: above maximum")

    return tuple(errors)


def _json_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)
