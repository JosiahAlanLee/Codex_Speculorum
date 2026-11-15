#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from common.illum import furniture as fu

BOOK_DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gen_fields", BOOK_DIR / "clausa" / "generate_fields.py")
gen_fields = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_fields)


def render(out_pdf: Path, meta: dict, paint_ground: bool) -> None:
    lines = [
        l.strip()
        for l in (BOOK_DIR / "manuscript" / "quaestio.md").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    title = lines[0].lstrip("# ").strip()
    body = " ".join(lines[1:])

    fmap = fu.fonts()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=(fu.PW, fu.PH))

    # Page 1 (Recto): Quaestio + Digest Table
    if paint_ground:
        fu.ground(c)
    fu.ruled_frame(c, double=True)
    fu.running_head(c, "Quaestio & Tabula", "Quaestio", 1)
    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["FellTitle"], 14.5)
    y = fu.PH - 96.0
    for tline in fu.wrap(title, fmap["FellTitle"], 14.5, fu.PW - 128.0):
        c.drawString(64.0, y, tline)
        y -= 19.0

    y -= 10.0
    c.setFillColor(HexColor(fu.HEX_INK))
    c.setFont(fmap["Fell"], 10.5)
    for ln in fu.wrap(body, fmap["Fell"], 10.5, fu.PW - 128.0):
        c.drawString(64.0, y, ln)
        y -= 15.5

    y -= 22.0
    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["FellSC"], 10.0)
    c.drawString(64.0, y, "TABULA NOTAE CLAUSAE · DIGESTS")
    y -= 16.0
    c.setFillColor(HexColor(fu.HEX_MUTE))
    c.setFont(fmap["Mono"], 7.4)
    c.drawString(64.0, y, f"Field I  : {meta['field_1_sha256']}")
    y -= 13.0
    c.drawString(64.0, y, f"Combined : {meta['combined_sha256']}")
    y -= 13.0
    c.drawString(64.0, y, f"Marks    : {meta['total_marks']} total ({meta['red_marks']} rubricated, sorted y-then-x)")
    c.showPage()

    # Page 2 (Verso): Ground-sorted Nota Clausa vector plate
    gen_fields.draw_clausa_pdf_leaf(c, meta, page_no=2, paint_ground=paint_ground)
    c.showPage()
    c.save()


def main() -> None:
    meta = gen_fields.build_clausa_plate(BOOK_DIR / "build")
    render(BOOK_DIR / "out" / "07_clausa_reading.pdf", meta, paint_ground=True)
    render(BOOK_DIR / "out" / "07_clausa_illustrated.pdf", meta, paint_ground=False)
    print("[07_clausa] Built Quaestio & ground-sorted Nota Clausa SVG/PDFs.")


if __name__ == "__main__":
    main()
