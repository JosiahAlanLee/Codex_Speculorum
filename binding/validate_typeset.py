"""
Typeset, vector-carrier, ground-order cipher, and post-vellum contrast QA.
Works seamlessly with `pypdf` + `pypdfium2` (and uses `fitz`/PyMuPDF if present).
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from pypdf import PdfReader
from pypdf.generic import ContentStream
import pypdfium2 as pdfium

from binding import vellum
from common.ciphers.lifted_pen import decode_lifted_pen_ops


def _extract_pdf_vector_ops(reader: PdfReader, page_index: int) -> List[Tuple]:
    page = reader.pages[page_index]
    cs = ContentStream(page.get_contents(), reader)
    return list(cs.operations)


def verify_lifted_pen_survives(reader: PdfReader, page_index: int, expected_phrase: str) -> None:
    """Confirms the M/L/Q lifted-pen vector subpath survives inside the bound PDF stream."""
    ops = _extract_pdf_vector_ops(reader, page_index)
    cur_subpath: List[Tuple] = []

    for operands, op in ops:
        if op == b"m":
            cur_subpath.append(("M", float(operands[0]), float(operands[1])))
        elif op == b"l":
            cur_subpath.append(("L", float(operands[0]), float(operands[1])))
        elif op in (b"c", b"v", b"y"):
            cur_subpath.append(("C", float(operands[-2]), float(operands[-1])))
        elif op in (b"S", b"s", b"B", b"b"):
            if sum(1 for item in cur_subpath if item[0] == "C") >= 5:
                decoded = decode_lifted_pen_ops(cur_subpath)
                if decoded == expected_phrase.upper():
                    return
            cur_subpath = []
        elif op == b"n":
            cur_subpath = []

    raise AssertionError(f"Lifted-pen phrase {expected_phrase!r} not found in bound PDF page {page_index + 1} vector stream.")


def verify_ground_ordered_clausa(reader: PdfReader, page_index: int, min_marks: int = 1000) -> None:
    ops = _extract_pdf_vector_ops(reader, page_index)
    stroke_rgb = (0.0, 0.0, 0.0)
    pending_move = None
    mark_centers: List[Tuple[float, float]] = []

    def is_mark_ink(rgb_t: Tuple[float, float, float]) -> bool:
        is_black = abs(rgb_t[0] - 22 / 255) < 0.03 and abs(rgb_t[1] - 25 / 255) < 0.03
        is_red = abs(rgb_t[0] - 163 / 255) < 0.03 and abs(rgb_t[1] - 43 / 255) < 0.03
        return is_black or is_red

    for operands, op in ops:
        if op == b"RG" and len(operands) == 3:
            stroke_rgb = (float(operands[0]), float(operands[1]), float(operands[2]))
        elif op == b"m" and len(operands) == 2:
            pending_move = (float(operands[0]), float(operands[1]))
        elif op == b"l" and len(operands) == 2 and pending_move is not None:
            x0, y0 = pending_move
            x1, y1 = float(operands[0]), float(operands[1])
            seg_len = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            if is_mark_ink(stroke_rgb) and 0.4 <= seg_len <= 6.0:
                cx = round(0.5 * (x0 + x1), 2)
                cy = round(0.5 * (y0 + y1), 2)
                mark_centers.append((cx, cy))
            pending_move = None
        elif op not in (b"S", b"q", b"Q", b"w", b"J", b"j"):
            pending_move = None

    if len(mark_centers) < min_marks:
        raise AssertionError(f"Expected >={min_marks} Nota Clausa marks on page {page_index + 1}, found {len(mark_centers)}.")

    keys = [(-round(cy, 1), round(cx, 1)) for (cx, cy) in mark_centers]
    if keys != sorted(keys):
        raise AssertionError(f"Nota Clausa marks on page {page_index + 1} violate (y, x) ground ordering!")


def verify_rendered_contrast_and_red_ink(pdf_path: Path, plate_page_index: int) -> None:
    doc = pdfium.PdfDocument(str(pdf_path))
    try:
        page = doc[plate_page_index]
        bmp = page.render(scale=2.0)
        arr = bmp.to_numpy()[:, :, :3]
    finally:
        doc.close()

    lum = arr.mean(axis=2)
    p95 = float(np.percentile(lum, 95))
    p01 = float(np.percentile(lum, 0.5))
    if p95 < 175.0 or p01 > 75.0:
        raise AssertionError(f"Rendered contrast degraded on page {plate_page_index + 1}: p95={p95:.1f}, p0.5={p01:.1f}")

    c_max = arr.max(axis=2).astype(np.int16)
    c_min = arr.min(axis=2).astype(np.int16)
    chromatic_pixels = int(np.sum((c_max - c_min) >= 65))
    if chromatic_pixels < 40:
        raise AssertionError(f"Rubric #a32b24 pixels missing or washed out on page {plate_page_index + 1} ({chromatic_pixels} px).")


def validate(pdf_path: Path, repo: Path, log: Dict) -> None:
    rd = PdfReader(str(pdf_path))

    if log.get("edition") == "illustrated":
        subj = str((rd.metadata or {}).get("/Subject", ""))
        if vellum.STAMP not in subj:
            raise AssertionError(f"Illustrated PDF missing vellum metadata stamp ({vellum.STAMP}).")

    bib_records = json.loads((repo / "bibliography-records.json").read_text(encoding="utf-8"))["records"]
    bib_s = log["bibliography"]["start_page"] - 1
    bib_e = log["bibliography"]["end_page"]
    full_bib_text = "\n".join(rd.pages[i].extract_text() for i in range(bib_s, bib_e))
    for rec in bib_records:
        for k in rec["keys"]:
            if f"[{k}]" not in full_bib_text:
                raise AssertionError(f"Citation key [{k}] missing from bound backmatter.")

    # Dynamically verify lifted-pen vector survival + post-vellum red contrast across all book plates
    for b in log["books"]:
        bid = b["id"]
        plates_manifest = repo / "books" / bid / "out" / "plates-map.json"
        if plates_manifest.is_file():
            pmap = b["body_page_map"]
            pmeta = json.loads(plates_manifest.read_text(encoding="utf-8"))
            for info in pmeta.values():
                leaf_key = str(info["leaf"])
                phys_idx = int(pmap[leaf_key]) - 1
                verify_lifted_pen_survives(rd, phys_idx, info["lifted"])
                verify_rendered_contrast_and_red_ink(pdf_path, phys_idx)

    books_by_id = {b["id"]: b for b in log["books"]}
    if "07_clausa" in books_by_id:
        b7 = books_by_id["07_clausa"]
        clausa_phys_idx = b7["end_page"] - 1
        verify_ground_ordered_clausa(rd, clausa_phys_idx, min_marks=1400)
