"""Revise engine package."""

import os
from pathlib import Path


def _load_project_env() -> None:
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_project_env()

from .engine import Engine, EngineResult
from .execution import ExecutionTrace, TraceEvent, console_trace_sink
from .llm import LLMPrimary, LLMSecondary, build_primary, build_secondary
from .model import ModelRouter, ModelSelection, SecondaryRouter
from .providers import FunctionPrimary, Primary, Secondary, Verifier
from .service import EngineRequest, EngineResponse, EngineService, create_default_service

__all__ = [
    "Engine", "EngineResult", "EngineRequest", "EngineResponse", "EngineService",
    "ExecutionTrace", "TraceEvent", "console_trace_sink",
    "FunctionPrimary", "LLMPrimary", "LLMSecondary", "ModelRouter", "ModelSelection",
    "Primary", "Secondary", "SecondaryRouter", "Verifier", "build_primary", "build_secondary",
    "create_default_service",
]
