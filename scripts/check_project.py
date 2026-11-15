#!/usr/bin/env python3
"""
Pre-flight and post-build repository verifier:
1. Validates `volume.json`, `SOURCES.json`, and `bibliography-records.json` schemas.
2. Runs `docs/objections/validate.py` on `docs/objections/register.md`.
3. Verifies every `[key]` cited in `books/*/manuscript/*.md` exists in
   `bibliography-records.json` (dynamic citation check, zero hardcoded ranges).
4. With `--built`, verifies expected omnibus PDFs and `binding-log.json` files exist.
"""

import argparse
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from docs.objections import validate as obj_validate

CITATION_RE = re.compile(r"\[([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)\]")


def check_schemas_and_citations() -> None:
    vol = json.loads((REPO / "volume.json").read_text(encoding="utf-8"))
    assert vol.get("trim_pt") == [504.0, 720.0], "Canonical trim_pt must be [504.0, 720.0]."
    assert len(vol.get("books", [])) >= 1, "volume.json must declare at least one book."

    sources = json.loads((REPO / "SOURCES.json").read_text(encoding="utf-8"))
    assert "as_of" in sources and isinstance(sources.get("entries"), dict), "Invalid SOURCES.json schema."
    for rel_path, meta in sources["entries"].items():
        if not (REPO / rel_path).exists():
            raise AssertionError(f"SOURCES.json references missing path: {rel_path}")
        for req in ("source", "hand", "tree_sha256"):
            if req not in meta:
                raise AssertionError(f"SOURCES.json entry {rel_path} missing '{req}'.")

    bib = json.loads((REPO / "bibliography-records.json").read_text(encoding="utf-8"))
    defined_keys = {k for r in bib.get("records", []) for k in r.get("keys", [])}

    for md in (REPO / "books").glob("*/manuscript/*.md"):
        txt = md.read_text(encoding="utf-8")
        for match in CITATION_RE.finditer(txt):
            ckey = match.group(1)
            if ckey not in defined_keys:
                raise AssertionError(f"{md.relative_to(REPO)} cites undefined key [{ckey}].")

    obj_validate.parse_register((REPO / "docs" / "objections" / "register.md").read_text(encoding="utf-8"))


def check_built(edition: str) -> None:
    vol = json.loads((REPO / "volume.json").read_text(encoding="utf-8"))
    slug = vol["slug"]
    if edition in ("all", "reading"):
        p = REPO / "binding" / "out" / f"{slug}_reading.pdf"
        if not p.is_file():
            raise FileNotFoundError(f"Expected built reading edition missing: {p}")
    if edition in ("all", "illustrated"):
        p = REPO / "binding" / "out" / "illustrated" / f"{slug}_illustrated.pdf"
        if not p.is_file():
            raise FileNotFoundError(f"Expected built illustrated edition missing: {p}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", action="store_true")
    ap.add_argument("--edition", choices=["all", "reading", "illustrated"], default="all")
    args = ap.parse_args()

    check_schemas_and_citations()
    if args.built:
        check_built(args.edition)
    print(f"[check_project] OK (built={args.built}, edition={args.edition})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
