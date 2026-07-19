# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [Unreleased]

### Added

- BTE spec revision **0.1.1** (backward compatible): `state.energy_throughput_kwh`
  and `state.equivalent_full_cycles` (SPEC §3.5); a top-level `extensions` object
  for vendor/tool-specific facts (SPEC §3.8) with a single portable key grammar
  (`^(?!(?:bte|schema|battinfo):)[a-z][a-z0-9_-]*:\S+(?![\s\S])`) enforced
  identically by the JSON Schema and the pydantic model, reserved
  `bte:`/`schema:`/`battinfo:` prefixes, no null values, and empty-object
  omission from the canonical form; and the version-declaration rule
  (SPEC §3.1), reported by `validate_dict` when a `0.1.0` document uses
  `0.1.1` fields.
- Canonical datetime form (SPEC §4): all datetimes serialize as RFC 3339 UTC
  with `Z`, offsets normalized, fractional seconds without trailing zeros —
  `load(save(env))` is a content-hash fixed point.
- JSON-LD context terms `bte:energyThroughputKilowattHour`,
  `bte:equivalentFullCycles`, `bte:extensions` (`@json`).

### Changed

- Envelope and all section models are now frozen (immutable after
  construction), matching the spec's immutability language; `next_version()`
  documents wholesale section replacement (no merging).

## [0.3.0] - 2026-07-08

Renamed from `echoed` to **battwin**. The **Battery Twin Envelope (BTE)**
format name is unchanged, as is its namespace `https://w3id.org/battinfo/twin#`
(BattINFO remains the IRI authority), the `bte:` JSON-LD prefix, the `urn:bte:`
id scheme, and the `.twin.json` suffix — a package name is not a format name
(cf. `batterydf` ≠ BDF). Renaming also unblocks PyPI publication: `echoed` was
squatted by an unrelated project, whereas `battwin` is free.

> Note: the `gleaned` collector package referenced in the older entries below
> is today's **battfeed** (renamed in the same round).

### Changed (breaking)

- Import package, console script, and PyPI distribution are now `battwin`
  (`import echoed` no longer exists). The packaged JSON Schema / JSON-LD context
  resource paths move from `echoed/…` to `battwin/…` accordingly.

### Removed

- Legacy pre-BTE harvester outputs `assets/data/battery_data.{csv,json,parquet}`
  (2024-era artifacts a spec package should not ship).

## [0.2.0] - 2026-07-07 (as echoed)

Complete refocus: echoed is now the **Battery Twin Envelope (BTE)**
specification and reference SDK. The earlier framework skeleton
(`DigitalTwin` orchestration class, harvester wiring, placeholder metamodel /
workflow / visualization modules) has been removed; the source/harvester
protocol design lives on in the `gleaned` collector package.

### Added

- `SPEC.md` — BTE v0.1.0 draft specification.
- Envelope document model (`echoed.envelope`): identity, specification, model
  bindings (BPX/BattMo/PyBaMM/custom), state snapshots, BDF data links,
  provenance, and a content-hash version chain (`next_version()`).
- Packaged JSON Schema (2020-12) and JSON-LD context.
- Two-layer validation (`echoed.validate`): JSON Schema + model rules.
- `echoed` CLI: `init`, `validate`, `show`, `hash`, `diff`.
- Worked example: `examples/cr2032.twin.json`.

### Changed

- License: BSD-3-Clause → Apache-2.0 (with NOTICE).
- Dependencies reduced to `pydantic` + `jsonschema` (previously declared
  rdflib/EMMOntoPy/owlrl/jinja2/requests were never used and are dropped).

### Removed

- `DigitalTwin`, harvester protocols (moved to `gleaned`), BDF ingestion
  helper (superseded by `batterydf`), and all placeholder subpackages.

## [Unreleased]

### Added

- Baseline repository governance files (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`).
- CI workflow for linting, type-checking, and tests.
