from __future__ import annotations

import ast
import json
import operator
import re


def check_json(value: str) -> bool:
    try:
        json.loads(value)
        return True
    except (TypeError, json.JSONDecodeError):
        return False


def check_python_syntax(value: str) -> bool:
    try:
        ast.parse(value)
        return True
    except (SyntaxError, TypeError):
        return False


def check_arithmetic(expression: str) -> bool:
    """Validate simple arithmetic expressions without evaluating arbitrary code."""
    try:
        tree = ast.parse(expression, mode="eval")
        allowed = (ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd)
        if any(not isinstance(node, allowed) for node in ast.walk(tree)):
            return False
        value = _eval(tree.body)
        return isinstance(value, (int, float))
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        return False


def _eval(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp):
        value = _eval(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left, right = _eval(node.left), _eval(node.right)
        operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
        return operations[type(node.op)](left, right)
    raise ValueError("unsupported expression")


def check_required_strings(value: str, required: tuple[str, ...]) -> bool:
    return all(item in value for item in required)
