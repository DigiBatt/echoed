# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

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
