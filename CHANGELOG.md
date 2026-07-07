# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [0.2.0] - 2026-07-07

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
