"""echoed — Battery Twin Envelope (BTE) specification and reference SDK.

A battery digital twin, expressed as an immutable, exchangeable document that
composes open artifacts by reference: BattINFO records (identity/spec), BPX
and other parameter sets (models), and BDF datasets or live feeds (data),
with estimated state and a content-hash version chain.

See SPEC.md for the specification and README.md for usage.
"""

from .envelope import (
    BTE_VERSION,
    DataLink,
    Identity,
    ModelBinding,
    Provenance,
    Specification,
    StateSnapshot,
    TwinEnvelope,
    ValidityWindow,
    VersionInfo,
    new_envelope,
)
from .io import from_dict, load, save
from .validate import load_context, load_schema, validate_dict, validate_file

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("echoed")
except Exception:  # pragma: no cover
    __version__ = "0.2.0"

__all__ = [
    "BTE_VERSION",
    "TwinEnvelope",
    "Identity",
    "Specification",
    "ModelBinding",
    "ValidityWindow",
    "StateSnapshot",
    "DataLink",
    "Provenance",
    "VersionInfo",
    "new_envelope",
    "load",
    "save",
    "from_dict",
    "validate_dict",
    "validate_file",
    "load_schema",
    "load_context",
    "__version__",
]
