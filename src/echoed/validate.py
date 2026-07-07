"""Validation of Battery Twin Envelope documents.

Two layers, matching the spec:

1. **JSON Schema** (``echoed/schemas/twin-envelope.schema.json``) — the public,
   language-neutral contract. Anyone can validate an envelope without Python.
2. **Model rules** (pydantic, :mod:`echoed.envelope`) — the reference
   implementation's stricter semantic checks (e.g. a model binding must have
   exactly one of ``source``/``inline``).

``validate_dict``/``validate_file`` run both and return a flat list of
human-readable problem strings (empty list = valid).
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema
from pydantic import ValidationError

from .envelope import _JSONLD_KEYS

SCHEMA_RESOURCE = "twin-envelope.schema.json"
CONTEXT_RESOURCE = "twin-envelope.context.jsonld"


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    """Return the packaged BTE JSON Schema."""
    text = resources.files("echoed").joinpath("schemas", SCHEMA_RESOURCE).read_text("utf-8")
    return json.loads(text)


@lru_cache(maxsize=1)
def load_context() -> dict[str, Any]:
    """Return the packaged BTE JSON-LD context (the value of ``@context``)."""
    text = resources.files("echoed").joinpath("context", CONTEXT_RESOURCE).read_text("utf-8")
    return json.loads(text)["@context"]


def validate_dict(doc: dict[str, Any]) -> list[str]:
    """Validate a parsed envelope document; returns problems (empty = valid)."""
    plain = {k: v for k, v in doc.items() if k not in _JSONLD_KEYS}
    if "id" not in plain and "@id" in doc:
        plain["id"] = doc["@id"]

    problems: list[str] = []

    validator = jsonschema.Draft202012Validator(load_schema())
    for error in sorted(validator.iter_errors(plain), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in error.absolute_path) or "<root>"
        problems.append(f"schema: {where}: {error.message}")

    from .io import from_dict  # local import to avoid a module cycle

    try:
        from_dict(doc)
    except ValidationError as exc:
        for err in exc.errors():
            where = "/".join(str(p) for p in err["loc"]) or "<root>"
            problems.append(f"model: {where}: {err['msg']}")
    except ValueError as exc:
        problems.append(f"model: <root>: {exc}")

    return problems


def validate_file(path: str | Path) -> list[str]:
    """Validate an envelope file; returns problems (empty = valid)."""
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"json: not parseable: {exc}"]
    if not isinstance(doc, dict):
        return ["json: expected a JSON object at the top level"]
    return validate_dict(doc)
