"""BTE 0.1.1 additions: `extensions` object, new state throughput fields,
extension-key grammar (both layers), null-value ban, empty-object omission,
and the version-declaration rule."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from battwin import (
    BTE_VERSION,
    StateSnapshot,
    TwinEnvelope,
    load,
    new_envelope,
    save,
    validate_dict,
)
from battwin.cli import main

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "cr2032.twin.json"


def _example_doc() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_bte_version_is_0_1_1() -> None:
    assert BTE_VERSION == "0.1.1"


def test_valid_namespaced_extension_keys_accepted() -> None:
    env = new_envelope(label="ext cell")
    doc = env.to_dict()
    doc["extensions"] = {
        "lab:fixture_id": "bench-07",
        "acme-tools:calibration": {"offset_mv": 1.2, "date": "2026-07-01"},
        "x2:list_value": [1, 2, 3],
        "a_b:nested:name": "colons-in-the-name-are-fine",
    }
    assert validate_dict(doc) == []
    parsed = TwinEnvelope.model_validate(doc)
    assert parsed.extensions is not None
    assert parsed.extensions["lab:fixture_id"] == "bench-07"


@pytest.mark.parametrize(
    "bad_key",
    ["fixture_id", "Lab:fixture", "1ab:fixture", "lab:", ":fixture", "", "lab fixture"],
)
def test_unnamespaced_key_rejected_by_both_layers(bad_key: str) -> None:
    doc = _example_doc()
    doc["extensions"] = {bad_key: "value"}
    # pydantic layer
    with pytest.raises(ValidationError):
        TwinEnvelope.model_validate(doc)
    # both layers via validate_dict: JSON Schema AND model must report it
    problems = validate_dict(doc)
    assert any(p.startswith("schema:") for p in problems), problems
    assert any(p.startswith("model:") for p in problems), problems


# One portable key grammar, byte-identical in both layers (SPEC §3.8):
# ^(?!(?:bte|schema|battinfo):)[a-z][a-z0-9_-]*:\S+(?![\s\S])
KEY_MATRIX = [
    ("a:b", True),
    ("a:b:c", True),
    ("a:☃", True),  # non-ASCII name: permitted (discouraged in SPEC)
    ("a:b\n", False),
    ("a:b\r", False),
    ("a:b ", False),
    ("a: ", False),
    ("a:\t", False),
    ("bte:x", False),  # reserved prefix
    ("schema:x", False),  # reserved prefix
    ("battinfo:x", False),  # reserved prefix
]


@pytest.mark.parametrize(("key", "ok"), KEY_MATRIX)
def test_key_grammar_cross_layer_agreement(key: str, ok: bool) -> None:
    """JSON Schema and pydantic must agree exactly on every key."""
    doc = _example_doc()
    doc["extensions"] = {key: "value"}
    problems = validate_dict(doc)
    schema_ok = not any(p.startswith("schema:") for p in problems)
    model_ok = not any(p.startswith("model:") for p in problems)
    assert schema_ok == ok, (key, problems)
    assert model_ok == ok, (key, problems)


def test_null_extension_value_rejected_by_both_layers() -> None:
    doc = _example_doc()
    doc["extensions"] = {"lab:note": None}
    with pytest.raises(ValidationError, match="null"):
        TwinEnvelope.model_validate(doc)
    problems = validate_dict(doc)
    assert any(p.startswith("schema:") for p in problems), problems
    assert any(p.startswith("model:") for p in problems), problems


def test_empty_extensions_omitted_and_hash_equal() -> None:
    env = new_envelope(label="empty ext")
    doc = env.to_dict()
    doc["extensions"] = {}
    with_empty = TwinEnvelope.model_validate(doc)
    assert "extensions" not in with_empty.to_dict()
    assert with_empty.content_hash() == env.content_hash()


def test_0_1_0_declaring_doc_using_0_1_1_fields_reported() -> None:
    # extensions under 0.1.0
    doc = _example_doc()
    doc["bte_version"] = "0.1.0"
    doc["state"].pop("energy_throughput_kwh", None)
    problems = validate_dict(doc)
    assert any("extensions" in p and "0.1.1" in p for p in problems), problems

    # new state field under 0.1.0 (also via state_history)
    doc = _example_doc()
    doc["bte_version"] = "0.1.0"
    doc.pop("extensions", None)
    doc["state_history"] = [dict(doc["state"])]
    problems = validate_dict(doc)
    assert any("state/energy_throughput_kwh" in p and "0.1.1" in p for p in problems), problems
    assert any("state_history/0/energy_throughput_kwh" in p for p in problems), problems


def test_0_1_1_declaring_doc_using_new_fields_is_clean() -> None:
    doc = _example_doc()  # declares 0.1.1, uses extensions + energy_throughput_kwh
    assert validate_dict(doc) == []


def test_new_state_fields_roundtrip(tmp_path: Path) -> None:
    env = new_envelope(label="throughput cell")
    env = env.next_version(
        state=StateSnapshot(
            as_of=datetime(2026, 7, 10, tzinfo=timezone.utc),
            energy_throughput_kwh=12.5,
            equivalent_full_cycles=41.7,
        )
    )
    out = tmp_path / "throughput.twin.json"
    save(env, out)
    reloaded = load(out)
    assert reloaded.state is not None
    assert reloaded.state.energy_throughput_kwh == 12.5
    assert reloaded.state.equivalent_full_cycles == 41.7
    assert validate_dict(reloaded.to_dict()) == []


def test_negative_state_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        StateSnapshot(as_of=datetime(2026, 7, 10, tzinfo=timezone.utc), energy_throughput_kwh=-1)
    with pytest.raises(ValidationError):
        StateSnapshot(as_of=datetime(2026, 7, 10, tzinfo=timezone.utc), equivalent_full_cycles=-1)


def test_hash_changes_when_extensions_change() -> None:
    base = load(EXAMPLE)
    doc = base.to_dict()
    doc["extensions"] = {"lab:fixture_id": "bench-08"}
    changed = TwinEnvelope.model_validate(doc)
    assert changed.content_hash() != base.content_hash()

    doc["extensions"] = {"lab:fixture_id": "bench-09"}
    assert TwinEnvelope.model_validate(doc).content_hash() != changed.content_hash()


def test_0_1_0_document_without_new_fields_still_validates() -> None:
    doc = _example_doc()
    doc["bte_version"] = "0.1.0"
    doc.pop("extensions", None)
    doc["state"].pop("energy_throughput_kwh", None)
    doc["state"].pop("equivalent_full_cycles", None)
    assert validate_dict(doc) == []


def test_example_file_with_extensions_validates() -> None:
    doc = _example_doc()
    assert doc["bte_version"] == "0.1.1"
    assert doc["extensions"] == {"lab:fixture_id": "bench-07"}
    assert validate_dict(doc) == []


def test_cli_validate_example_passes(capsys) -> None:
    assert main(["validate", str(EXAMPLE)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("ok") and "INVALID" not in out
