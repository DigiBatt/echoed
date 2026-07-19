"""Validation of Battery Twin Envelope documents.

Two layers, matching the spec:

1. **JSON Schema** (``battwin/schemas/twin-envelope.schema.json``) — the public,
   language-neutral contract. Anyone can validate an envelope without Python.
2. **Model rules** (pydantic, :mod:`battwin.envelope`) — the reference
   implementation's stricter semantic checks (e.g. a model binding must have
   exactly one of ``source``/``inline``).

``validate_dict``/``validate_file`` run both — plus the version-declaration
rule of SPEC.md §3.1 (a document must declare a ``bte_version`` that defines
every field it uses) — and return a flat list of human-readable problem
strings (empty list = valid).
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

#: StateSnapshot fields introduced by BTE 0.1.1 (SPEC.md §3.5).
_STATE_FIELDS_0_1_1 = ("energy_throughput_kwh", "equivalent_full_cycles")


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    """Return the packaged BTE JSON Schema."""
    text = (resources.files("battwin") / "schemas" / SCHEMA_RESOURCE).read_text("utf-8")
    return json.loads(text)


@lru_cache(maxsize=1)
def load_context() -> dict[str, Any]:
    """Return the packaged BTE JSON-LD context (the value of ``@context``)."""
    text = (resources.files("battwin") / "context" / CONTEXT_RESOURCE).read_text("utf-8")
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

    problems.extend(_version_declaration_problems(plain))

    return problems


def _version_declaration_problems(plain: dict[str, Any]) -> list[str]:
    """SPEC.md §3.1: a document MUST declare a ``bte_version`` >= the earliest
    specification version that defines every field it uses."""
    if plain.get("bte_version") != "0.1.0":
        return []
    problems: list[str] = []
    if "extensions" in plain:
        problems.append(
            "version: extensions: field requires bte_version >= 0.1.1 (document declares 0.1.0)"
        )
    snapshots: list[tuple[str, Any]] = [("state", plain.get("state"))]
    history = plain.get("state_history")
    if isinstance(history, list):
        snapshots.extend((f"state_history/{i}", snap) for i, snap in enumerate(history))
    for where, snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        for field in _STATE_FIELDS_0_1_1:
            if field in snapshot:
                problems.append(
                    f"version: {where}/{field}: field requires bte_version >= 0.1.1 "
                    "(document declares 0.1.0)"
                )
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
