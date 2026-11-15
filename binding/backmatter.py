import io
import json
from pathlib import Path
from typing import Dict, List, Tuple

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from common.illum import furniture as fu

PW, PH = fu.PW, fu.PH
PAPER = fu.HEX_PAPER
INK = fu.HEX_INK
RED = fu.HEX_RED
MUTE = fu.HEX_MUTE


def load_records(repo: Path) -> List[Dict]:
    bib_path = repo / "bibliography-records.json"
    data = json.loads(bib_path.read_text(encoding="utf-8"))
    return list(data.get("records", []))


def is_project_record(rec: Dict) -> bool:
    return rec.get("section") == "Project records"


def render_backmatter_pdf(repo: Path, start_page: int, paint_ground: bool = True) -> Tuple[bytes, int]:
    """
    Renders dynamic Bibliography and Project records onto 504x720 pt pages,
    beginning on a physical recto (odd `start_page`). Returns (pdf_bytes, page_count).
    """
    assert start_page % 2 == 1, "Backmatter must open on a physical recto (odd page)."
    records = load_records(repo)
    sources = json.loads((repo / "SOURCES.json").read_text(encoding="utf-8"))
    fmap = fu.fonts()

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(PW, PH))
    page_no = start_page
    pages_emitted = 0

    def open_leaf() -> float:
        nonlocal pages_emitted
        if paint_ground:
            fu.ground(c)
        fu.ruled_frame(c, double=False)
        fu.running_head(c, "Bibliography & Project Records", "Backmatter", page_no)
        pages_emitted += 1
        return PH - 84.0

    y = open_leaf()
    c.setFillColor(HexColor(RED))
    c.setFont(fmap["FellTitle"], 16.0)
    c.drawString(64.0, y, "Bibliography")
    y -= 24.0

    bib_recs = [r for r in records if not is_project_record(r)]
    proj_recs = [r for r in records if is_project_record(r)]

    def draw_group(items: List[Dict], heading: str = "") -> None:
        nonlocal y, page_no
        if heading:
            if y < 140.0:
                c.showPage()
                page_no += 1
                y = open_leaf()
            y -= 8.0
            c.setFillColor(HexColor(RED))
            c.setFont(fmap["FellTitle"], 14.0)
            c.drawString(64.0, y, heading)
            y -= 20.0

        for rec in items:
            if y < 120.0:
                c.showPage()
                page_no += 1
                y = open_leaf()
            key_label = ", ".join(f"[{k}]" for k in rec["keys"])
            c.setFillColor(HexColor(RED))
            c.setFont(fmap["Mono"], 9.0)
            c.drawString(64.0, y, key_label)
            y -= 13.0

            c.setFillColor(HexColor(INK))
            c.setFont(fmap["Fell"], 10.0)
            for line in fu.wrap(rec["citation"], fmap["Fell"], 10.0, PW - 128.0):
                c.drawString(64.0, y, line)
                y -= 13.0

            c.setFillColor(HexColor(MUTE))
            c.setFont(fmap["FellIt"], 9.0)
            for label, field in (("Inspection:", "inspection"), ("Use:", "use")):
                val = rec.get(field, "").strip()
                if val:
                    for line in fu.wrap(f"{label} {val}", fmap["FellIt"], 9.0, PW - 136.0):
                        c.drawString(72.0, y, line)
                        y -= 12.0
            y -= 8.0

    draw_group(bib_recs)
    draw_group(proj_recs, heading="Project records")

    # Provenance summary footer from SOURCES.json
    if y < 110.0:
        c.showPage()
        page_no += 1
        y = open_leaf()
    y -= 6.0
    c.setFillColor(HexColor(MUTE))
    c.setFont(fmap["Mono"], 8.0)
    c.drawString(64.0, y, f"Provenance manifest: SOURCES.json (as_of {sources.get('as_of')}, {len(sources.get('entries', {}))} tracked modules)")

    c.showPage()
    c.save()
    return (buf.getvalue(), pages_emitted)
