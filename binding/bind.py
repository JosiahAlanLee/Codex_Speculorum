#!/usr/bin/env python3
"""
Assembles the recto-aligned omnibus Reading Edition (`binding/out/<slug>_reading.pdf`)
and emits `binding/out/binding-log.json` for structural verification.
"""

import hashlib
import io
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from binding import backmatter
from common.illum import furniture as fu

REPO = Path(__file__).resolve().parents[1]
PW, PH = fu.PW, fu.PH


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_blank_leaf(paint_ground: bool = True) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PW, PH))
    if paint_ground:
        fu.ground(c)
    c.showPage()
    c.save()
    return buf.getvalue()


def make_front_matter(vol: Dict, paint_ground: bool = True) -> bytes:
    """Creates 2-page front matter: Page 1 Title Recto, Page 2 Clavis Verso."""
    fmap = fu.fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PW, PH))

    # Page 1 (Recto): Half-title / Volume Title
    if paint_ground:
        fu.ground(c)
    fu.ruled_frame(c, double=True)
    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["FellSC"], 10.5)
    c.drawCentredString(PW / 2.0, PH - 150.0, f"{vol['series'].upper()} · VOLUME {vol['volume_number']}")
    c.setFillColor(HexColor(fu.HEX_INK))
    c.setFont(fmap["FellTitle"], 24.0)
    c.drawCentredString(PW / 2.0, PH - 205.0, vol["title"])
    c.setFillColor(HexColor(fu.HEX_MUTE))
    c.setFont(fmap["FellIt"], 12.0)
    c.drawCentredString(PW / 2.0, PH - 236.0, vol["subtitle"])
    c.setFont(fmap["Mono"], 8.5)
    c.drawCentredString(PW / 2.0, 88.0, "No one needs permission to stop using it.")
    c.showPage()

    # Page 2 (Verso): Clavis & Epistemic Tags
    if paint_ground:
        fu.ground(c)
    fu.ruled_frame(c, double=False)
    fu.running_head(c, "Clavis", "Clavis", 2)
    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["FellTitle"], 15.0)
    c.drawString(64.0, PH - 90.0, "Clavis · Key to the Tags & Marks")
    y = PH - 120.0
    tags = [
        ("[E]", "Direct empirical observation or verified deterministic computation."),
        ("[D]", "Documented primary or archival source inspected at the cited locus."),
        ("[H]", "Bounded hypothesis; states the observation that counts against it."),
        ("[V]", "Explicitly adopted value or operational commitment."),
        ("[F]", "Framed parable, worked workshop scene, or liturgical foil."),
    ]
    for code, desc in tags:
        c.setFillColor(HexColor(fu.HEX_RED))
        c.setFont(fmap["Mono"], 9.5)
        c.drawString(64.0, y, code)
        c.setFillColor(HexColor(fu.HEX_INK))
        c.setFont(fmap["Fell"], 10.5)
        c.drawString(100.0, y, desc)
        y -= 20.0
    c.showPage()
    c.save()
    return buf.getvalue()


def make_colophon(vol: Dict, edition: str, page_no: int, paint_ground: bool = True) -> bytes:
    assert page_no % 2 == 1, "Colophon must sit on a physical recto."
    fmap = fu.fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PW, PH))
    if paint_ground:
        fu.ground(c)
    fu.ruled_frame(c, double=True)
    fu.running_head(c, "Colophon", "Colophon", page_no)
    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["FellTitle"], 15.0)
    c.drawString(64.0, PH - 96.0, "Colophon & Production Record")
    c.setFillColor(HexColor(fu.HEX_INK))
    c.setFont(fmap["Fell"], 10.5)
    body = (
        f"Bound offline as the {edition} edition of {vol['title']} on 7 x 10 in "
        f"(504 x 720 pt) leaves. Procedural plates, rubricated biliteral falsifier "
        f"scales, lifted-pen vector paths, and ground-ordered Nota Clausa fields "
        f"are verified at build time; model objections and author dispositions "
        f"are preserved append-only in docs/objections/register.md."
    )
    y = PH - 124.0
    for line in fu.wrap(body, fmap["Fell"], 10.5, PW - 128.0):
        c.drawString(64.0, y, line)
        y -= 15.0
    c.showPage()
    c.save()
    return buf.getvalue()


def bind_edition(edition: str = "reading", out_pdf: Optional[Path] = None, paint_ground: bool = True) -> Tuple[Path, Path]:
    vol = json.loads((REPO / "volume.json").read_text(encoding="utf-8"))
    slug = vol["slug"]
    if out_pdf is None:
        if edition == "reading":
            out_pdf = REPO / "binding" / "out" / f"{slug}_reading.pdf"
        else:
            out_pdf = REPO / "binding" / "out" / "illustrated" / f"{slug}_illustrated.pdf"

    writer = PdfWriter()
    writer.add_metadata({"/Title": vol["title"]})
    blank_bytes = make_blank_leaf(paint_ground=paint_ground)
    blank_page_proto = PdfReader(io.BytesIO(blank_bytes)).pages[0]

    # 1. Front matter (pages 1..2)
    fm_reader = PdfReader(io.BytesIO(make_front_matter(vol, paint_ground=paint_ground)))
    for p in fm_reader.pages:
        writer.add_page(p)
    phys_page = len(writer.pages)  # 2

    book_logs: List[Dict] = []
    alignment_blanks: List[int] = []

    # 2. Recto-aligned component books
    key_field = "reading_pdf" if edition == "reading" else "illustrated_pdf"
    for b in vol["books"]:
        src_rel = b[key_field]
        src_path = REPO / src_rel
        if not src_path.is_file():
            raise FileNotFoundError(f"Missing component PDF: {src_path}")

        blank_before: List[int] = []
        if (phys_page + 1) % 2 == 0:
            phys_page += 1
            writer.add_page(blank_page_proto)
            blank_before.append(phys_page)
            alignment_blanks.append(phys_page)

        rd = PdfReader(str(src_path))
        start_page = phys_page + 1
        body_page_map: Dict[str, int] = {}
        for local_idx, page in enumerate(rd.pages, start=1):
            phys_page += 1
            writer.add_page(page)
            body_page_map[str(local_idx)] = phys_page
        end_page = phys_page

        book_logs.append({
            "id": b["id"],
            "title": b["title"],
            "source": src_rel,
            "source_sha256": sha256_file(src_path),
            "pages": len(rd.pages),
            "source_pages": len(rd.pages),
            "body_page_map": body_page_map,
            "body_blank_pages": [],
            "bibliography_source_pages": [],
            "start_page": start_page,
            "end_page": end_page,
            "blank_before": blank_before,
            "trim_mm": [round(PW / fu.MM, 2), round(PH / fu.MM, 2)],
            "scaled": False,
        })

    # 3. Colophon on physical recto
    if (phys_page + 1) % 2 == 0:
        phys_page += 1
        writer.add_page(blank_page_proto)
        alignment_blanks.append(phys_page)

    colophon_start = phys_page + 1
    col_reader = PdfReader(io.BytesIO(make_colophon(vol, edition, colophon_start, paint_ground=paint_ground)))
    for p in col_reader.pages:
        phys_page += 1
        writer.add_page(p)

    # 4. Backmatter (Bibliography & Project records) on physical recto
    if (phys_page + 1) % 2 == 0:
        phys_page += 1
        writer.add_page(blank_page_proto)
        alignment_blanks.append(phys_page)

    bib_start = phys_page + 1
    bib_bytes, _ = backmatter.render_backmatter_pdf(REPO, start_page=bib_start, paint_ground=paint_ground)
    bib_reader = PdfReader(io.BytesIO(bib_bytes))
    for p in bib_reader.pages:
        phys_page += 1
        writer.add_page(p)
    bib_end = phys_page

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with open(out_pdf, "wb") as f:
        writer.write(f)

    log_path = out_pdf.parent / "binding-log.json"
    log_data = {
        "edition": edition,
        "volume": vol["slug"],
        "trim_pt": [PW, PH],
        "total_pages": phys_page,
        "front_matter_pages": [1, 2],
        "alignment_blank_pages": alignment_blanks,
        "books": book_logs,
        "colophon_page": colophon_start,
        "bibliography": {
            "mode": "typeset",
            "start_page": bib_start,
            "end_page": bib_end,
        },
    }
    log_path.write_text(json.dumps(log_data, indent=2) + "\n", encoding="utf-8")
    return (out_pdf, log_path)


def main() -> None:
    out_pdf, log_path = bind_edition(edition="reading", paint_ground=True)
    print(f"[bind] Wrote {out_pdf.relative_to(REPO)} ({log_path.relative_to(REPO)})")


if __name__ == "__main__":
    main()
