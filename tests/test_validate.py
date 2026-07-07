"""Two-layer validation: JSON Schema (public contract) + model rules."""

import json
from pathlib import Path

from echoed import load, load_context, load_schema, validate_dict, validate_file

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "cr2032.twin.json"


def _example_doc() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_is_valid() -> None:
    assert validate_file(EXAMPLE) == []


def test_schema_and_context_are_packaged() -> None:
    schema = load_schema()
    assert schema["title"] == "Battery Twin Envelope"
    context = load_context()
    assert context["bte"].startswith("https://")


def test_missing_identity_reported() -> None:
    doc = _example_doc()
    del doc["identity"]
    problems = validate_dict(doc)
    assert any("identity" in p for p in problems)


def test_bad_kind_reported() -> None:
    doc = _example_doc()
    doc["data"][0]["kind"] = "spreadsheet"
    problems = validate_dict(doc)
    assert any("data/0" in p and "kind" in p for p in problems)


def test_soc_out_of_range_reported() -> None:
    doc = _example_doc()
    doc["state"]["state_of_charge"] = 1.4
    problems = validate_dict(doc)
    assert any("state_of_charge" in p for p in problems)


def test_extra_top_level_field_reported() -> None:
    doc = _example_doc()
    doc["surprise"] = 1
    problems = validate_dict(doc)
    assert problems, "additionalProperties must be rejected"


def test_model_binding_with_both_source_and_inline_reported() -> None:
    doc = _example_doc()
    doc["models"][0]["source"] = "also-a-path.json"
    problems = validate_dict(doc)
    assert problems


def test_jsonld_document_validates() -> None:
    env = load(EXAMPLE)
    assert validate_dict(env.to_jsonld()) == []


def test_unparseable_file_reported(tmp_path: Path) -> None:
    bad = tmp_path / "bad.twin.json"
    bad.write_text("{not json", encoding="utf-8")
    problems = validate_file(bad)
    assert problems and problems[0].startswith("json:")
