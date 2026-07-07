"""``battwin`` command-line interface.

Small by design: validate, show, init, diff, hash. Anything that *runs* a
twin (simulation, sync, hosting) is intentionally out of scope — see SPEC.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .envelope import new_envelope
from .io import load, save
from .validate import validate_file


def _cmd_validate(args: argparse.Namespace) -> int:
    failed = 0
    for path in args.files:
        problems = validate_file(path)
        if problems:
            failed += 1
            print(f"INVALID  {path}")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"ok       {path}")
    return 1 if failed else 0


def _cmd_show(args: argparse.Namespace) -> int:
    envelope = load(args.file)
    print(envelope.summary())
    return 0


def _cmd_hash(args: argparse.Namespace) -> int:
    print(load(args.file).content_hash())
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    envelope = new_envelope(
        label=args.label,
        twin_id=args.id,
        chemistry=args.chemistry,
        created_by=args.created_by,
    )
    out = Path(args.out)
    save(envelope, out, jsonld=args.jsonld)
    print(f"wrote {out}")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    a, b = load(args.a), load(args.b)
    if a.id != b.id:
        print(f"different twins: {a.id} vs {b.id}")
        return 1
    a_doc, b_doc = a.to_dict(), b.to_dict()
    changed = sorted(
        key
        for key in set(a_doc) | set(b_doc)
        if key != "version" and a_doc.get(key) != b_doc.get(key)
    )
    print(f"versions: {a.version.number} -> {b.version.number}")
    print("changed sections: " + (", ".join(changed) if changed else "none"))
    if b.version.previous == a.content_hash():
        print("version chain: intact (b.previous == hash(a))")
        return 0
    print("version chain: BROKEN (b.previous != hash(a))")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="battwin",
        description="Battery Twin Envelope (BTE): validate, inspect, and scaffold twin documents.",
    )
    parser.add_argument("--version", action="version", version=f"battwin {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate envelope files against the BTE spec")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=_cmd_validate)

    p = sub.add_parser("show", help="print a human summary of an envelope")
    p.add_argument("file")
    p.set_defaults(func=_cmd_show)

    p = sub.add_parser("hash", help="print the content hash of an envelope")
    p.add_argument("file")
    p.set_defaults(func=_cmd_hash)

    p = sub.add_parser("init", help="scaffold a minimal valid envelope")
    p.add_argument("--label", required=True, help="human-readable name of the twinned battery")
    p.add_argument("--chemistry", default=None)
    p.add_argument("--id", default=None, help="twin identifier (URN/IRI); generated if omitted")
    p.add_argument("--created-by", default=None)
    p.add_argument(
        "--jsonld", action="store_true", help="write JSON-LD (with @context) instead of plain JSON"
    )
    p.add_argument("-o", "--out", required=True)
    p.set_defaults(func=_cmd_init)

    p = sub.add_parser("diff", help="compare two versions of a twin and check the version chain")
    p.add_argument("a")
    p.add_argument("b")
    p.set_defaults(func=_cmd_diff)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
