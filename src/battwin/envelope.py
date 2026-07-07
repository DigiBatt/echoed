"""Battery Twin Envelope (BTE) document model.

A twin envelope is an immutable, serializable JSON document that *composes*
existing open artifacts into one exchangeable representation of a battery
digital twin:

- identity        -> who/what the twin mirrors (serials, passport IDs, BattINFO IRIs)
- specification   -> the cell/pack spec, by reference to a BattINFO record
- models          -> parameter sets (BPX/BattMo/...) with validity windows
- state           -> estimated states (SoC/SoH/...) with provenance
- data            -> links to time-series (BDF datasets, live feeds)
- version         -> immutable version chain (content-hash linked)

The envelope deliberately references other resources by IRI/path instead of
importing their toolchains: BattINFO records, BPX files, and BDF datasets are
linked, never embedded code dependencies. Executing models, hosting twins, and
synchronizing live state are out of scope (see SPEC.md, "Non-goals").
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

BTE_VERSION = "0.1.0"

_JSONLD_KEYS = ("@context", "@id", "@type")


class _Section(BaseModel):
    """Base for all envelope sections: strict keys, assignment validation."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Identity(_Section):
    """What physical (or virtual) battery this twin mirrors."""

    label: str = Field(description="Human-readable name of the twinned battery.")
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    battinfo_iri: Optional[str] = Field(
        default=None,
        description="IRI of the cell/cell-instance record in a BattINFO registry, "
        "e.g. https://w3id.org/battinfo/cell/<id>.",
    )
    passport_id: Optional[str] = Field(
        default=None, description="EU Digital Product Passport identifier, if any."
    )


class Specification(_Section):
    """The design-level description of the battery, by reference where possible."""

    battinfo_record: Optional[str] = Field(
        default=None,
        description="IRI or relative path of a BattINFO cell-spec record. Prefer "
        "referencing over duplicating spec fields below.",
    )
    chemistry: Optional[str] = None
    form_factor: Optional[str] = None
    nominal_capacity_ah: Optional[float] = Field(default=None, ge=0)
    nominal_voltage_volt: Optional[float] = Field(default=None, ge=0)


class ValidityWindow(_Section):
    """Operating window within which a model binding is considered valid."""

    temperature_celsius: Optional[tuple[float, float]] = None
    state_of_charge: Optional[tuple[float, float]] = None

    @model_validator(mode="after")
    def _ordered(self) -> "ValidityWindow":
        for name in ("temperature_celsius", "state_of_charge"):
            window = getattr(self, name)
            if window is not None and window[0] > window[1]:
                raise ValueError(f"{name} window must be (low, high), got {window}")
        return self


class ModelBinding(_Section):
    """A parameter set / model attached to the twin.

    Exactly one of `source` (path or IRI) or `inline` (embedded document, e.g.
    a BPX JSON object) must be provided.
    """

    kind: Literal["bpx", "battmo", "pybamm", "custom"]
    name: str
    source: Optional[str] = None
    inline: Optional[dict[str, Any]] = None
    solver_hint: Optional[str] = Field(
        default=None,
        description="Non-binding hint for implementations, e.g. 'pybamm' or 'battmo'.",
    )
    validity: Optional[ValidityWindow] = None

    @model_validator(mode="after")
    def _source_xor_inline(self) -> "ModelBinding":
        if (self.source is None) == (self.inline is None):
            raise ValueError("provide exactly one of 'source' or 'inline'")
        return self


class StateSnapshot(_Section):
    """An estimated state of the battery at a point in time."""

    as_of: datetime
    state_of_charge: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    state_of_health: Optional[float] = Field(default=None, ge=0.0, le=1.5)
    cycle_count: Optional[int] = Field(default=None, ge=0)
    internal_resistance_ohm: Optional[float] = Field(default=None, ge=0)
    method: Optional[str] = Field(
        default=None, description="How the state was estimated, e.g. 'coulomb_counting'."
    )
    source_data: Optional[str] = Field(
        default=None, description="URI of the dataset the estimate was derived from."
    )


class DataLink(_Section):
    """A link to time-series or other data belonging to the twin."""

    kind: Literal["bdf", "feed", "other"]
    uri: str = Field(description="Path, URL, or IRI of the dataset (e.g. a .bdf.csv file).")
    role: Optional[str] = Field(
        default=None, description="e.g. 'cycling', 'field', 'reference', 'characterization'."
    )
    description: Optional[str] = None


class Provenance(_Section):
    created: datetime
    created_by: Optional[str] = None
    tool: Optional[str] = None
    funding: Optional[str] = None


class VersionInfo(_Section):
    """Immutable version chain: `previous` is the content hash of the prior document."""

    number: int = Field(default=1, ge=1)
    previous: Optional[str] = Field(
        default=None, description="sha256 content hash of the previous envelope version."
    )
    changed: list[str] = Field(default_factory=list)
    timestamp: datetime


class TwinEnvelope(_Section):
    """The top-level Battery Twin Envelope document."""

    bte_version: str = BTE_VERSION
    id: str = Field(description="Stable identifier of the twin (URN or IRI).")
    identity: Identity
    specification: Optional[Specification] = None
    models: list[ModelBinding] = Field(default_factory=list)
    state: Optional[StateSnapshot] = None
    state_history: list[StateSnapshot] = Field(default_factory=list)
    data: list[DataLink] = Field(default_factory=list)
    provenance: Provenance
    version: VersionInfo

    # -- serialization ----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Plain-JSON dict with None-valued fields omitted."""
        return self.model_dump(mode="json", exclude_none=True)

    def canonical_json(self) -> str:
        """Deterministic serialization used for content hashing."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def content_hash(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def to_jsonld(self, context: str | dict[str, Any] | None = None) -> dict[str, Any]:
        """JSON-LD rendering: the plain document plus @context/@id/@type.

        By default the packaged BTE context is inlined so the document stands
        alone; pass a URL string to reference a hosted context instead.
        """
        if context is None:
            from .validate import load_context  # local import to avoid cycle

            context = load_context()
        doc: dict[str, Any] = {"@context": context, "@id": self.id, "@type": "TwinEnvelope"}
        doc.update(self.to_dict())
        return doc

    # -- versioning --------------------------------------------------------

    def next_version(self, *, timestamp: datetime | None = None, **updates: Any) -> "TwinEnvelope":
        """Return a new envelope version with `updates` applied.

        Envelopes are immutable: this copies the document, applies the given
        top-level section updates (e.g. ``state=...``, ``data=[...]``), bumps
        the version number, and links back to this version by content hash.
        If a new ``state`` is provided, the old one is appended to
        ``state_history`` automatically.
        """
        unknown = set(updates) - set(type(self).model_fields)
        if unknown:
            raise ValueError(f"unknown envelope sections: {sorted(unknown)}")
        for reserved in ("version", "bte_version", "id"):
            if reserved in updates:
                raise ValueError(f"'{reserved}' cannot be updated via next_version()")

        data = self.model_dump(exclude_none=False)
        if "state" in updates and self.state is not None:
            data["state_history"] = [*data["state_history"], data["state"]]
        for key, value in updates.items():
            data[key] = value

        data["version"] = VersionInfo(
            number=self.version.number + 1,
            previous=self.content_hash(),
            changed=sorted(updates),
            timestamp=timestamp or datetime.now(timezone.utc),
        )
        return TwinEnvelope.model_validate(data)

    def summary(self) -> str:
        """One-paragraph human summary (used by ``battwin show``)."""
        lines = [
            f"{self.identity.label} (id: {self.id})",
            f"  BTE {self.bte_version} | version {self.version.number}"
            + (f" <- {self.version.previous[:18]}..." if self.version.previous else ""),
        ]
        if self.specification:
            spec_bits = [
                b
                for b in (
                    self.specification.chemistry,
                    self.specification.form_factor,
                    f"{self.specification.nominal_capacity_ah} Ah"
                    if self.specification.nominal_capacity_ah is not None
                    else None,
                )
                if b
            ]
            if spec_bits:
                lines.append("  spec: " + ", ".join(spec_bits))
            if self.specification.battinfo_record:
                lines.append(f"  battinfo record: {self.specification.battinfo_record}")
        if self.models:
            lines.append("  models: " + ", ".join(f"{m.name} [{m.kind}]" for m in self.models))
        if self.state:
            state_bits = []
            if self.state.state_of_charge is not None:
                state_bits.append(f"SoC {self.state.state_of_charge:.0%}")
            if self.state.state_of_health is not None:
                state_bits.append(f"SoH {self.state.state_of_health:.0%}")
            if self.state.cycle_count is not None:
                state_bits.append(f"{self.state.cycle_count} cycles")
            lines.append(
                f"  state ({self.state.as_of.date().isoformat()}): " + ", ".join(state_bits)
            )
        if self.data:
            lines.append(f"  data links: {len(self.data)}")
        return "\n".join(lines)


def new_envelope(
    *,
    label: str,
    twin_id: str | None = None,
    chemistry: str | None = None,
    created_by: str | None = None,
    timestamp: datetime | None = None,
) -> TwinEnvelope:
    """Scaffold a minimal valid envelope (used by ``battwin init``)."""
    now = timestamp or datetime.now(timezone.utc)
    slug = "".join(c if c.isalnum() else "-" for c in label.lower()).strip("-")
    return TwinEnvelope(
        id=twin_id or f"urn:bte:{slug}:{date.today().isoformat()}",
        identity=Identity(label=label),
        specification=Specification(chemistry=chemistry) if chemistry else None,
        provenance=Provenance(created=now, created_by=created_by, tool=f"battwin/{_version()}"),
        version=VersionInfo(timestamp=now),
    )


def _version() -> str:
    try:
        from importlib.metadata import version

        return version("battwin")
    except Exception:  # pragma: no cover - metadata absent in odd environments
        return "0.3.0"
