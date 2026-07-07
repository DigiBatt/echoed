"""Envelope model behavior: construction, hashing, version chain."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from echoed import (
    ModelBinding,
    StateSnapshot,
    TwinEnvelope,
    ValidityWindow,
    load,
    new_envelope,
    save,
    validate_dict,
)

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "cr2032.twin.json"


def test_new_envelope_is_valid() -> None:
    env = new_envelope(label="Test cell", chemistry="LFP")
    assert validate_dict(env.to_dict()) == []
    assert env.version.number == 1
    assert env.identity.label == "Test cell"


def test_example_roundtrips(tmp_path: Path) -> None:
    env = load(EXAMPLE)
    out = tmp_path / "copy.twin.json"
    save(env, out)
    assert load(out).to_dict() == env.to_dict()


def test_jsonld_rendering_roundtrips(tmp_path: Path) -> None:
    env = load(EXAMPLE)
    out = tmp_path / "copy.twin.jsonld"
    save(env, out, jsonld=True)
    reloaded = load(out)
    assert reloaded.to_dict() == env.to_dict()
    assert reloaded.id == env.id


def test_content_hash_is_stable_and_sensitive() -> None:
    env = load(EXAMPLE)
    assert env.content_hash() == load(EXAMPLE).content_hash()
    bumped = env.next_version(
        state=StateSnapshot(as_of=datetime(2026, 7, 8, tzinfo=timezone.utc), state_of_charge=0.5)
    )
    assert bumped.content_hash() != env.content_hash()


def test_next_version_builds_chain_and_archives_state() -> None:
    env = load(EXAMPLE)
    new_state = StateSnapshot(
        as_of=datetime(2026, 7, 8, tzinfo=timezone.utc),
        state_of_charge=0.5,
        method="coulomb_counting",
    )
    v2 = env.next_version(state=new_state)
    assert v2.version.number == env.version.number + 1
    assert v2.version.previous == env.content_hash()
    assert v2.version.changed == ["state"]
    assert v2.id == env.id
    # prior state snapshot is archived
    assert env.state is not None
    assert v2.state_history[-1].as_of == env.state.as_of
    assert v2.state is not None and v2.state.state_of_charge == 0.5


def test_next_version_rejects_reserved_and_unknown_sections() -> None:
    env = new_envelope(label="x")
    with pytest.raises(ValueError, match="version"):
        env.next_version(version=None)
    with pytest.raises(ValueError, match="unknown"):
        env.next_version(nonsense=1)


def test_model_binding_requires_exactly_one_of_source_inline() -> None:
    ModelBinding(kind="bpx", name="ok-source", source="params.bpx.json")
    ModelBinding(kind="custom", name="ok-inline", inline={"a": 1})
    with pytest.raises(ValidationError):
        ModelBinding(kind="bpx", name="both", source="x", inline={"a": 1})
    with pytest.raises(ValidationError):
        ModelBinding(kind="bpx", name="neither")


def test_validity_window_must_be_ordered() -> None:
    with pytest.raises(ValidationError):
        ValidityWindow(temperature_celsius=(40.0, 10.0))


def test_unknown_top_level_field_rejected() -> None:
    doc = load(EXAMPLE).to_dict()
    doc["surprise"] = True
    with pytest.raises(ValidationError):
        TwinEnvelope.model_validate(doc)
