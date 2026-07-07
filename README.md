# echoed

**The Battery Twin Envelope (BTE): an open specification — plus reference SDK — for expressing and exchanging battery digital twins.**

A battery digital twin is, as a *data artifact*, a composition: an identity, a
specification, one or more models, an estimated state, and links to
measurement data. Today every platform encapsulates that composition
privately. `echoed` defines it openly, as a small immutable JSON document —
the **twin envelope** — that references existing open standards instead of
reinventing them:

```
BattINFO records ─────┐  (identity & specification, by IRI)
BPX / BattMo params ──┼──▶  Battery Twin Envelope (.twin.json)  ──▶ registries,
BDF datasets & feeds ─┘  (models & data, by reference)               platforms,
                                                                     archives
```

Envelopes are **documents, not engines**: how a twin is hosted, simulated, or
synchronized is an implementation concern; how it is expressed is a community
concern. The full format is defined in [SPEC.md](SPEC.md).

## Installation

```bash
pip install echoed
```

Dependencies: `pydantic` and `jsonschema` — nothing else.

## Quickstart

```python
from echoed import new_envelope, save, validate_file

twin = new_envelope(label="Bench cell 001", chemistry="LFP")
save(twin, "bench-cell-001.twin.json")
assert validate_file("bench-cell-001.twin.json") == []
```

Updating a twin creates a new, hash-chained version — envelopes are immutable:

```python
from datetime import datetime, timezone
from echoed import StateSnapshot, load, save

v1 = load("bench-cell-001.twin.json")
v2 = v1.next_version(
    state=StateSnapshot(
        as_of=datetime.now(timezone.utc),
        state_of_charge=0.8,
        method="coulomb_counting",
        source_data="data/SINTEF__001__20260707_001.bdf.csv",
    )
)
assert v2.version.previous == v1.content_hash()  # verifiable lineage
save(v2, "bench-cell-001.v2.twin.json")
```

And from the command line:

```bash
echoed init --label "Bench cell 001" --chemistry LFP -o cell.twin.json
echoed validate cell.twin.json
echoed show cell.twin.json
echoed diff cell.twin.json cell.v2.twin.json   # checks the version chain
```

## What's in an envelope

```jsonc
{
  "bte_version": "0.1.0",
  "id": "urn:bte:energizer-cr2032:demo-001",
  "identity":      { "label": "...", "serial_number": "...", "battinfo_iri": "...", "passport_id": "..." },
  "specification": { "battinfo_record": "https://w3id.org/battinfo/cell-spec/...", "chemistry": "Li/MnO2" },
  "models":        [ { "kind": "bpx", "name": "...", "source": "params.bpx.json", "validity": { "...": "..." } } ],
  "state":         { "as_of": "2026-07-07T12:00:00Z", "state_of_charge": 0.82, "method": "coulomb_counting" },
  "data":          [ { "kind": "bdf", "uri": "data/SINTEF__DEMO-001__20260707_001.bdf.csv", "role": "cycling" } ],
  "provenance":    { "created": "...", "created_by": "...", "tool": "echoed/0.2.0" },
  "version":       { "number": 2, "previous": "sha256:...", "changed": ["state"], "timestamp": "..." }
}
```

A complete example lives at [examples/cr2032.twin.json](examples/cr2032.twin.json).
Envelopes also render as JSON-LD (`save(..., jsonld=True)`) using the packaged
context, so they slot into linked-data pipelines alongside BattINFO.

## Non-goals

`echoed` deliberately does **not**:

- run simulations (that's PyBaMM, BattMo, and the platforms built on them);
- host twins or define sync/REST protocols;
- manage fleets or tenants;
- acquire measurement data (see [gleaned](https://github.com/DigiBatt/gleaned)
  for source→BDF collection, and the BDF toolchain for files at rest);
- replace BattINFO, BPX, or BDF — it composes them by reference.

## Related projects

| Project | Role relative to echoed |
|---|---|
| [BattINFO](https://github.com/BIG-MAP/BattINFO) | semantic records the envelope references for identity/spec |
| [BDF / batterydf](https://github.com/battery-data-alliance/battery-data-format) | time-series datasets the envelope links in `data[]` |
| [BPX](https://github.com/FaradayInstitution/BPX) | parameter sets bound in `models[]` |
| [gleaned](https://github.com/DigiBatt/gleaned) | collects live source data into the BDF files a twin links |

## Python support

Python 3.10 – 3.12.

## Acknowledgements

<img src="docs/assets/img/Flag_of_Europe.png" alt="EU flag" width="100">

This project has received support from European Union research and innovation
programs under grant agreement
[101103997 – DigiBatt](https://digibattproject.eu/).

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
