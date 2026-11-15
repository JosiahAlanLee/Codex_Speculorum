#!/usr/bin/env python3
"""
Validates bound PDF trim geometry (504 x 720 pt), recto book-opening parity,
SHA-256 component provenance, blank alignment leaves, and delegates typeset,
cipher, and vellum checks to `binding/validate_typeset.py`.
"""

import hashlib
import json
from pathlib import Path
import sys

from pypdf import PdfReader

from binding import validate_typeset
from common.illum.furniture import PH, PW

REPO = Path(__file__).resolve().parents[1]


def validate_pdf(pdf_path: Path, repo: Path = REPO) -> None:
    log_path = pdf_path.parent / "binding-log.json"
    if not log_path.is_file():
        raise FileNotFoundError(f"Missing binding log: {log_path}")
    log = json.loads(log_path.read_text(encoding="utf-8"))

    rd = PdfReader(str(pdf_path))
    volume = json.loads((repo / "volume.json").read_text(encoding="utf-8"))
    if (rd.metadata or {}).get("/Title") != volume["title"]:
        raise AssertionError(f"Unexpected PDF title for {pdf_path.name}.")
    if volume["title"] not in rd.pages[0].extract_text():
        raise AssertionError(f"Volume title missing from the cover of {pdf_path.name}.")
    if len(rd.pages) != log["total_pages"]:
        raise AssertionError(f"Page count mismatch: PDF has {len(rd.pages)}, log records {log['total_pages']}.")

    # 1. Every leaf must match 504 x 720 pt trim
    for idx, p in enumerate(rd.pages, start=1):
        w = float(p.mediabox.width)
        h = float(p.mediabox.height)
        if abs(w - PW) > 0.5 or abs(h - PH) > 0.5:
            raise AssertionError(f"Page {idx} trim {w}x{h} != {PW}x{PH}.")

    # 2. Alignment blanks must carry zero text
    for b_pno in log.get("alignment_blank_pages", []):
        txt = rd.pages[b_pno - 1].extract_text().strip()
        if txt:
            raise AssertionError(f"Alignment blank leaf {b_pno} contains unexpected text: {txt!r}")

    # 3. Component book recto parity, SHA-256, and leaf parity
    for book in log["books"]:
        if book["start_page"] % 2 != 1:
            raise AssertionError(f"Book {book['id']} starts on verso page {book['start_page']}; must be recto (odd).")
        src_file = repo / book["source"]
        actual_sha = hashlib.sha256(src_file.read_bytes()).hexdigest()
        if actual_sha != book["source_sha256"]:
            raise AssertionError(f"Source SHA-256 drift for {book['source']}.")
        for local_s, phys in book["body_page_map"].items():
            local_i = int(local_s)
            if (local_i % 2) != (phys % 2):
                raise AssertionError(f"Recto/verso parity broken in {book['id']} local {local_i} -> physical {phys}.")

    # 4. Colophon & Backmatter recto starts
    if log["colophon_page"] % 2 != 1:
        raise AssertionError("Colophon does not open on a physical recto.")
    if log["bibliography"]["start_page"] % 2 != 1:
        raise AssertionError("Bibliography does not open on a physical recto.")
    bib_text = rd.pages[log["bibliography"]["start_page"] - 1].extract_text()
    if "Bibliography" not in bib_text:
        raise AssertionError("Backmatter opening recto missing 'Bibliography' heading.")

    if log["bibliography"].get("mode") == "typeset":
        validate_typeset.validate(pdf_path, repo, log)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python binding/validate.py <bound.pdf>", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).resolve()
    validate_pdf(target, REPO)
    print(f"[validate] OK: {target.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
