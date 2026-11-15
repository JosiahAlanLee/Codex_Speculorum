#!/usr/bin/env python3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from common.illum import furniture as fu

BOOK_DIR = Path(__file__).resolve().parent


def render(out_pdf: Path, paint_ground: bool) -> None:
    md_lines = [
        l.strip()
        for l in (BOOK_DIR / "manuscript" / "prologus.md").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    title = md_lines[0].lstrip("# ").strip()
    paragraphs = [" ".join(md_lines[1:])]

    fmap = fu.fonts()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=(fu.PW, fu.PH))
    if paint_ground:
        fu.ground(c)
    fu.ruled_frame(c, double=True)
    fu.running_head(c, "De Officio Mensuratoris", "Prologus", 1)

    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["FellTitle"], 15.5)
    y = fu.PH - 96.0
    for tline in fu.wrap(title, fmap["FellTitle"], 15.5, fu.PW - 128.0):
        c.drawString(64.0, y, tline)
        y -= 20.0
    y -= 10.0
    c.setFillColor(HexColor(fu.HEX_INK))
    c.setFont(fmap["Fell"], 11.0)
    for para in paragraphs:
        for line in fu.wrap(para, fmap["Fell"], 11.0, fu.PW - 128.0):
            c.drawString(64.0, y, line)
            y -= 16.0
    c.showPage()
    c.save()


def main() -> None:
    render(BOOK_DIR / "out" / "00_prologus_reading.pdf", paint_ground=True)
    render(BOOK_DIR / "out" / "00_prologus_illustrated.pdf", paint_ground=False)
    print("[00_prologus] Built reading & illustrated component PDFs.")


if __name__ == "__main__":
    main()
