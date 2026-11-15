#!/usr/bin/env python3
"""
Paginates `books/03_liber_tertius/manuscript/reading-edition.md` onto 504x720 pt
Codex leaves with rubricated Chladni-Lutemaker dialogue speakers (`CHLADNIUS:` / `LUTIFEX:`),
inline italic span support (`*...*`), orphan-proof section heading lookahead,
native full-page `Tabula VII · Cista Resonantiae Chladniana`, and emits
`out/plates-map.json` + standalone `tabula-vii-acoustic-resonator.svg` and 96-dpi wash.
"""

import importlib.util
import json
from pathlib import Path
import sys
from typing import Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from binding import vellum
from common.illum import furniture as fu
from common.illum.styled_text import draw_styled_line, tokenize_styled_words, wrap_styled_tokens

BOOK_DIR = Path(__file__).resolve().parent

_tab_spec = importlib.util.spec_from_file_location("tabulae3_mod", BOOK_DIR / "plates" / "tabulae.py")
tabulae = importlib.util.module_from_spec(_tab_spec)
_tab_spec.loader.exec_module(tabulae)

PLATE_DISPATCH = {
    "tabula_vii": ("draw_tabula_vii_resonator_pdf_leaf", "chladni", tabulae.LIFTED_VII.upper()),
}

SPEAKERS = ("CHLADNIUS:", "LUTIFEX:")


def parse_manuscript_items(md_path: Path) -> Tuple[str, List[Tuple[str, str]]]:
    chapter_title = ""
    items: List[Tuple[str, str]] = []
    buf: List[str] = []
    buf_kind = "para"

    def flush() -> None:
        nonlocal buf
        if not buf:
            return
        items.append((buf_kind, " ".join(buf)))
        buf = []

    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if line.startswith("# "):
            flush()
            chapter_title = line[2:].strip()
        elif line.startswith("## "):
            flush()
            items.append(("section", line[3:].strip()))
        elif line.startswith("[PLATE:") and line.endswith("]"):
            flush()
            pid = line[len("[PLATE:") : -1].strip()
            items.append(("plate", pid))
        elif line.startswith(">"):
            q_txt = line[1:].strip()
            if buf and buf_kind != "quote":
                flush()
            buf_kind = "quote"
            buf.append(q_txt)
        else:
            if buf and buf_kind != "para":
                flush()
            buf_kind = "para"
            buf.append(line)
    flush()
    return chapter_title, items


def render_book(out_pdf: Path, paint_ground: bool) -> Dict[str, Dict]:
    chapter_title, items = parse_manuscript_items(BOOK_DIR / "manuscript" / "reading-edition.md")
    fmap = fu.fonts()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=(fu.PW, fu.PH))

    short_run = "Liber III · Cista Resonantiae"
    margin_x = 62.0
    max_w = fu.PW - 2.0 * margin_x
    bottom_y = 66.0

    page_no = 0
    y = 0.0
    page_open = False
    plates_meta: Dict[str, Dict] = {}

    def open_prose_page(first_page: bool = False) -> None:
        nonlocal page_no, y, page_open
        if page_open:
            c.showPage()
        page_no += 1
        page_open = True
        if paint_ground:
            fu.ground(c)
        fu.ruled_frame(c, double=first_page)
        fu.running_head(c, short_run, "Liber III", page_no)
        y = fu.PH - 88.0
        if first_page:
            c.setFillColor(HexColor(fu.HEX_RED))
            c.setFont(fmap["FellTitle"], 14.5)
            for tline in fu.wrap(chapter_title, fmap["FellTitle"], 14.5, max_w):
                c.drawString(margin_x, y, tline)
                y -= 18.5
            y -= 8.0

    open_prose_page(first_page=True)

    for idx_item, (kind, payload) in enumerate(items):
        if kind == "plate":
            if page_open:
                c.showPage()
                page_open = False
            page_no += 1
            fn_name, wash_mode, lifted_upper = PLATE_DISPATCH[payload]
            getattr(tabulae, fn_name)(c, page_no=page_no, paint_ground=paint_ground)
            c.showPage()
            plates_meta[payload] = {
                "leaf": page_no,
                "wash": wash_mode,
                "lifted": lifted_upper,
            }
            continue

        if not page_open:
            open_prose_page(first_page=False)

        if kind == "section":
            h_lines = fu.wrap(payload, fmap["FellSC"], 10.5, max_w)
            # Require enough room for BOTH the heading AND its entire following paragraph so headings never orphan!
            next_h = 85.0
            if idx_item + 1 < len(items) and items[idx_item + 1][0] == "para":
                nxt_toks = tokenize_styled_words(items[idx_item + 1][1])
                nxt_lines = wrap_styled_tokens(nxt_toks, fmap["Fell"], fmap["FellIt"], 10.1, max_w)
                next_h = len(nxt_lines) * 13.8 + 12.0
            needed = len(h_lines) * 14.5 + 8.0 + next_h
            if y - needed < bottom_y:
                open_prose_page(first_page=False)
            y -= 3.0
            c.setFillColor(HexColor(fu.HEX_RED))
            c.setFont(fmap["FellSC"], 10.5)
            for hl in h_lines:
                c.drawString(margin_x, y, hl)
                y -= 14.5
            y -= 3.5

        elif kind == "para":
            speaker_prefix = next((sp for sp in SPEAKERS if payload.startswith(sp)), None)
            if speaker_prefix:
                rest_tokens = tokenize_styled_words(payload[len(speaker_prefix) :])
                sp_w = pdfmetrics.stringWidth(speaker_prefix + " ", fmap["FellSC"], 9.5)
                lines = wrap_styled_tokens(
                    rest_tokens,
                    fmap["Fell"],
                    fmap["FellIt"],
                    10.0,
                    max_w - 14.0,
                    first_max_w=max_w - sp_w,
                )
                total_h = len(lines) * 13.8 + 5.5
                if y - total_h < bottom_y:
                    open_prose_page(first_page=False)
                c.setFillColor(HexColor(fu.HEX_RED))
                c.setFont(fmap["FellSC"], 9.5)
                c.drawString(margin_x, y, speaker_prefix)
                c.setFillColor(HexColor(fu.HEX_INK))
                draw_styled_line(c, margin_x + sp_w, y, lines[0], fmap["Fell"], fmap["FellIt"], 10.0)
                y -= 13.8
                for cl in lines[1:]:
                    draw_styled_line(c, margin_x + 14.0, y, cl, fmap["Fell"], fmap["FellIt"], 10.0)
                    y -= 13.8
                y -= 5.0
            else:
                p_tokens = tokenize_styled_words(payload)
                p_lines = wrap_styled_tokens(p_tokens, fmap["Fell"], fmap["FellIt"], 10.1, max_w)
                total_h = len(p_lines) * 13.8 + 5.5
                if y - total_h < bottom_y:
                    open_prose_page(first_page=False)
                c.setFillColor(HexColor(fu.HEX_INK))
                for pl in p_lines:
                    draw_styled_line(c, margin_x, y, pl, fmap["Fell"], fmap["FellIt"], 10.1)
                    y -= 13.8
                y -= 5.5

        elif kind == "quote":
            q_clean = payload.replace("**", "").replace("`", "").replace("*", "")
            q_words = [[(word, True)] for word in q_clean.split()]
            q_wrapped = wrap_styled_tokens(q_words, fmap["FellIt"], fmap["FellIt"], 9.5, max_w - 20.0)
            if y - (len(q_wrapped) * 12.9 + 9.0) < bottom_y:
                open_prose_page(first_page=False)
            q_top = y + 8.0
            c.setFillColor(HexColor(fu.HEX_INK))
            c.setFont(fmap["FellIt"], 9.5)
            for ql in q_wrapped:
                if y < bottom_y:
                    hnd = fu.Hand(c, amp=0.0)
                    hnd.stroke([(margin_x + 5.0, q_top), (margin_x + 5.0, y + 8.0)], weight="cip", color="red")
                    open_prose_page(first_page=False)
                    q_top = y + 8.0
                    c.setFillColor(HexColor(fu.HEX_INK))
                    c.setFont(fmap["FellIt"], 9.5)
                draw_styled_line(c, margin_x + 14.0, y, ql, fmap["FellIt"], fmap["FellIt"], 9.5)
                y -= 12.9
            hnd = fu.Hand(c, amp=0.0)
            hnd.stroke([(margin_x + 5.0, q_top), (margin_x + 5.0, y + 8.0)], weight="cip", color="red")
            y -= 6.5

    if page_open:
        c.showPage()
    c.save()
    return plates_meta


def main() -> None:
    build_dir = BOOK_DIR / "build"
    out_dir = BOOK_DIR / "out"

    tabulae.build_tabula_vii_resonator_svg(build_dir / "tabula-vii-acoustic-resonator.svg")
    vellum.export_wash_png(build_dir / "vellum-chladni-96dpi.png", wash_mode="chladni", seed=17, profile="full")

    plates_meta = render_book(out_dir / "03_liber_tertius_reading.pdf", paint_ground=True)
    render_book(out_dir / "03_liber_tertius_illustrated.pdf", paint_ground=False)
    (out_dir / "plates-map.json").write_text(json.dumps(plates_meta, indent=2) + "\n", encoding="utf-8")
    print("[03_liber_tertius] Built Tabula VII SVG, 96-dpi Chladni wash, and reading/illustrated PDFs.")


if __name__ == "__main__":
    main()
