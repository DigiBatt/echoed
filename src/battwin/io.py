"""Load and save Battery Twin Envelope documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .envelope import _JSONLD_KEYS, TwinEnvelope


def from_dict(doc: dict[str, Any]) -> TwinEnvelope:
    """Build an envelope from a parsed JSON document.

    Accepts both plain-JSON and JSON-LD renderings: ``@context`` and ``@type``
    are dropped, and ``@id`` is used as ``id`` when the plain key is absent.
    """
    data = {k: v for k, v in doc.items() if k not in _JSONLD_KEYS}
    if "id" not in data and "@id" in doc:
        data["id"] = doc["@id"]
    return TwinEnvelope.model_validate(data)


def load(path: str | Path) -> TwinEnvelope:
    """Load an envelope from a ``.twin.json`` / ``.json`` / ``.jsonld`` file."""
    raw = Path(path).read_text(encoding="utf-8")
    doc = json.loads(raw)
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: expected a JSON object at the top level")
    return from_dict(doc)


def save(
    envelope: TwinEnvelope,
    path: str | Path,
    *,
    jsonld: bool = False,
    indent: int = 2,
) -> Path:
    """Write an envelope to disk; returns the path written.

    With ``jsonld=True`` the document carries ``@context``/``@id``/``@type``
    (self-contained JSON-LD); otherwise plain JSON is written.
    """
    target = Path(path)
    doc = envelope.to_jsonld() if jsonld else envelope.to_dict()
    target.write_text(json.dumps(doc, indent=indent) + "\n", encoding="utf-8")
    return target
