# Battery Twin Envelope (BTE) Specification

**Version:** 0.1.0 (draft)
**Status:** Draft for community review
**Editor:** Simon Clark
**License:** Apache-2.0 (specification text and reference implementation)

## 1. Motivation

Battery digital twins are being built by labs, OEMs, service platforms, and
regulators — but there is no shared answer to the question *"what is a battery
digital twin, as a data artifact?"* Parameter sets have BPX, time-series data
has BDF, semantic records have BattINFO, and regulatory data has the EU
Battery Passport, yet the **composition** — one exchangeable object that says
*this battery, this specification, these models, this state, this data* — is
reinvented privately by every platform.

The Battery Twin Envelope (BTE) is that composition layer: a small, versioned
document format for **expressing and encapsulating** a battery digital twin so
it can be exchanged between tools, registries, and platforms.

BTE deliberately specifies **documents, not engines**. How a twin is hosted,
simulated, or synchronized is an implementation concern (commercial or
otherwise); how it is *expressed* is a community concern.

## 2. Relationship to existing standards

A BTE envelope composes by **reference**, not duplication:

| Concern | Referenced standard | Envelope section |
|---|---|---|
| Semantic identity and cell records | [BattINFO](https://github.com/BIG-MAP/BattINFO) IRIs / records | `identity`, `specification` |
| Physics/empirical parameter sets | [BPX](https://github.com/FaradayInstitution/BPX), BattMo parameter sets | `models` |
| Time-series measurement data | [BDF](https://github.com/battery-data-alliance/battery-data-format) datasets, live feeds | `data` |
| Regulatory identity | EU Digital Product Passport identifiers | `identity.passport_id` |
| Ontology grounding | EMMO domain-battery, via the JSON-LD context | all sections |

Implementations MAY resolve these references with the corresponding
toolchains (battinfo, batterydf, bpx, …); the envelope itself requires none of
them.

## 3. Document model

An envelope is a JSON object (media type suggestion:
`application/battery-twin+json`; conventional filename suffix `.twin.json`).
JSON-LD rendering is defined in §6.

### 3.1 Top level

| Field | Type | Req. | Meaning |
|---|---|---|---|
| `bte_version` | string | MUST | Spec version this document conforms to (`0.1.x`). |
| `id` | string | MUST | Stable identifier of the *twin* (URN or IRI). Identical across versions of the same twin. |
| `identity` | object | MUST | What the twin mirrors (§3.2). |
| `specification` | object | MAY | Design-level description (§3.3). |
| `models` | array | MAY | Model/parameter-set bindings (§3.4). |
| `state` | object | MAY | Latest estimated state (§3.5). |
| `state_history` | array | MAY | Prior state snapshots, oldest first. |
| `data` | array | MAY | Links to datasets and feeds (§3.6). |
| `provenance` | object | MUST | Creation metadata (§3.7). |
| `version` | object | MUST | Version-chain record (§4). |

Unknown top-level fields are invalid in v0.1 (forward compatibility is
handled by `bte_version`).

### 3.2 `identity`

`label` (MUST); `manufacturer`, `model`, `serial_number`, `battinfo_iri`
(IRI of a BattINFO cell/cell-instance record), `passport_id` (all MAY).

### 3.3 `specification`

Prefer referencing a BattINFO record via `battinfo_record` (IRI or relative
path) over duplicating fields. Convenience fields for standalone use:
`chemistry`, `form_factor`, `nominal_capacity_ah`, `nominal_voltage_volt`.
Numeric field names carry unit suffixes following the BDF naming convention
(`{quantity}_{unit}`, snake_case).

### 3.4 `models[]`

Each binding: `kind` (`bpx` | `battmo` | `pybamm` | `custom`, MUST), `name`
(MUST), and **exactly one** of `source` (path/IRI) or `inline` (embedded
document, e.g. a BPX JSON object). Optional `solver_hint` (non-binding) and
`validity` (operating window: `temperature_celsius: [low, high]`,
`state_of_charge: [low, high]`).

Envelopes describe *which* models apply and *when they are valid* — never how
to execute them.

### 3.5 `state` / `state_history[]`

A snapshot: `as_of` (ISO 8601, MUST); `state_of_charge` (0–1),
`state_of_health` (0–1.5), `cycle_count`, `internal_resistance_ohm`, `method`
(estimation method), `source_data` (URI of the dataset the estimate derives
from) — all MAY. When a new snapshot replaces `state`, the old one SHOULD be
appended to `state_history`.

### 3.6 `data[]`

Each link: `kind` (`bdf` | `feed` | `other`, MUST), `uri` (MUST), `role`
(e.g. `cycling`, `field`, `characterization`), `description`. `bdf` links
SHOULD point at conforming BDF datasets (e.g. `*.bdf.csv`).

### 3.7 `provenance`

`created` (ISO 8601, MUST); `created_by`, `tool`, `funding` (MAY).

## 4. Versioning and immutability

Envelope documents are **immutable**. Updating a twin means issuing a new
document with:

1. the same `id`;
2. `version.number` incremented by 1;
3. `version.previous` set to the **content hash** of the prior document;
4. `version.changed` listing the updated top-level sections;
5. a new `version.timestamp`.

The content hash is `"sha256:" + hex(sha256(canonical_json))`, where
`canonical_json` is the document serialized with sorted keys, separators
`(",", ":")`, UTF-8, and all null-valued fields omitted. This yields a
verifiable hash chain: any consumer can check that a claimed successor really
derives from its predecessor. (Implementations proved this pattern in
production twin platforms; BTE standardizes the *shape*, not the platform.)

## 5. Validation and conformance

A document conforms to BTE v0.1 if it validates against the JSON Schema
published with this spec (`echoed/schemas/twin-envelope.schema.json`) **and**
satisfies the semantic rules above (one-of `source`/`inline`; ordered
windows; version-chain rules when a predecessor is available).

The reference SDK (`pip install echoed`) implements both layers:
`echoed validate <file>`.

## 6. JSON-LD rendering

Adding `"@context"` (the context published with this spec), `"@id"` (= `id`)
and `"@type": "TwinEnvelope"` to a conforming document yields JSON-LD, mapping
identity fields to schema.org and domain terms to the `bte:` namespace, with
BattINFO IRIs as first-class references. The `bte:` namespace IRI
(`https://w3id.org/battery-twin-envelope#`) is **pending registration**;
until registered, treat term IRIs as provisional. Deeper EMMO alignment
(quantities, units) is planned for v0.2 in coordination with BattINFO.

## 7. Non-goals

BTE v0.1 intentionally does **not** specify:

- executing simulations (that is the job of PyBaMM, BattMo, and platforms);
- hosting, APIs, or synchronization protocols for live twins;
- fleet/tenant management;
- acquisition of measurement data (see the `gleaned` collector toolkit and
  the BDF ecosystem);
- replacing BattINFO records, BPX files, or BDF datasets — it links them.

## 8. Example

See [`examples/cr2032.twin.json`](examples/cr2032.twin.json) for a complete
envelope: a CR2032 cell with a BattINFO spec reference, an inline custom
model stub, one state snapshot, and a BDF data link.

## 9. Acknowledgements

Developed in continuity with the DigiBatt project, funded by the European
Union under grant agreement 101103997.
