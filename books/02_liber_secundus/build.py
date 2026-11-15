#!/usr/bin/env python3
"""
Paginates `books/02_liber_secundus/manuscript/reading-edition.md` onto 504x720 pt
Codex leaves with rubricated Escher-Borges dialogue speakers (`SCULPTOR:` / `CUSTOS:`),
inline italic span support (`*...*`), native full-page `Tabula VI · Fornix Sine Periodo`,
and emits `out/plates-map.json` + standalone `tabula-vi-aperiodic-vault.svg` and 96-dpi wash.
"""

import importlib.util
import json
from pathlib import Path
import re
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

BOOK_DIR = Path(__file__).resolve().parent

_tab_spec = importlib.util.spec_from_file_location("tabulae2_mod", BOOK_DIR / "plates" / "tabulae.py")
tabulae = importlib.util.module_from_spec(_tab_spec)
_tab_spec.loader.exec_module(tabulae)

PLATE_DISPATCH = {
    "tabula_vi": ("draw_tabula_vi_vault_pdf_leaf", "aperiodic", tabulae.LIFTED_VI.upper()),
}

SPEAKERS = ("SCULPTOR:", "CUSTOS:")
_SPAN_RE = re.compile(r"\*([^*]+)\*")

StyledWord = List[Tuple[str, bool]]


def _tokenize_styled_words(text: str) -> List[StyledWord]:
    """
    Splits whitespace-delimited words into intra-word `(sub_segment, is_italic)` runs
    so punctuation directly adjacent to `*italic*` spans (`(*Fornix Sine Periodo*)`,
    `*three*,`) never acquires artificial spaces.
    """
    cleaned = text.replace("**", "").replace("`", "")
    # Replace spaces inside `*...*` with a sentinel so we can split on outer whitespace cleanly
    SENT = "\x00"
    marked = _SPAN_RE.sub(lambda m: "*" + m.group(1).replace(" ", SENT) + "*", cleaned)
    words_out: List[StyledWord] = []
    for raw_tok in marked.split():
        # Expand sentinel spaces back into separate styled words while keeping attached punctuation tight
        parts = raw_tok.split(SENT)
        in_it = False
        for part in parts:
            segs: StyledWord = []
            buf: List[str] = []
            for ch in part:
                if ch == "*":
                    if buf:
                        segs.append(("".join(buf), in_it))
                        buf = []
                    in_it = not in_it
                else:
                    buf.append(ch)
            if buf:
                segs.append(("".join(buf), in_it))
            if segs:
                words_out.append(segs)
    return words_out


def _segment_font(text: str, preferred: str) -> str:
    glyphs = getattr(pdfmetrics.getFont(preferred).face, "charToGlyph", {})
    if all(ord(char) in glyphs for char in text):
        return preferred
    return fu.fonts()["Math"]


def _word_width(word: StyledWord, rom_font: str, it_font: str, size: float) -> float:
    return sum(
        pdfmetrics.stringWidth(seg, _segment_font(seg, it_font if is_it else rom_font), size)
        for seg, is_it in word
    )


def _wrap_styled_tokens(
    words: List[StyledWord],
    rom_font: str,
    it_font: str,
    size: float,
    max_w: float,
    first_max_w: float | None = None,
) -> List[List[StyledWord]]:
    lines: List[List[StyledWord]] = []
    cur: List[StyledWord] = []
    cur_w = 0.0
    space_w = pdfmetrics.stringWidth(" ", rom_font, size)

    for word in words:
        ww = _word_width(word, rom_font, it_font, size)
        limit = first_max_w if (not lines and first_max_w is not None) else max_w
        needed = ww if not cur else (space_w + ww)
        if cur and (cur_w + needed > limit):
            lines.append(cur)
            cur = [word]
            cur_w = ww
        else:
            cur.append(word)
            cur_w += needed
    if cur:
        lines.append(cur)
    return lines


def _draw_styled_line(
    c: canvas.Canvas,
    x: float,
    y: float,
    line_words: List[StyledWord],
    rom_font: str,
    it_font: str,
    size: float,
) -> None:
    cx = x
    space_w = pdfmetrics.stringWidth(" ", rom_font, size)
    for idx, word in enumerate(line_words):
        if idx > 0:
            cx += space_w
        for seg, is_it in word:
            fnt = _segment_font(seg, it_font if is_it else rom_font)
            c.setFont(fnt, size)
            c.drawString(cx, y, seg)
            cx += pdfmetrics.stringWidth(seg, fnt, size)


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

    short_run = "Liber II · Bibliotheca Sine Periodo"
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
        fu.running_head(c, short_run, "Liber II", page_no)
        y = fu.PH - 88.0
        if first_page:
            c.setFillColor(HexColor(fu.HEX_RED))
            c.setFont(fmap["FellTitle"], 14.5)
            for tline in fu.wrap(chapter_title, fmap["FellTitle"], 14.5, max_w):
                c.drawString(margin_x, y, tline)
                y -= 18.5
            y -= 8.0

    open_prose_page(first_page=True)

    for kind, payload in items:
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
            needed = len(h_lines) * 14.5 + 34.0
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
                rest_tokens = _tokenize_styled_words(payload[len(speaker_prefix) :])
                sp_w = pdfmetrics.stringWidth(speaker_prefix + " ", fmap["FellSC"], 9.5)
                lines = _wrap_styled_tokens(
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
                _draw_styled_line(c, margin_x + sp_w, y, lines[0], fmap["Fell"], fmap["FellIt"], 10.0)
                y -= 13.8
                for cl in lines[1:]:
                    _draw_styled_line(c, margin_x + 14.0, y, cl, fmap["Fell"], fmap["FellIt"], 10.0)
                    y -= 13.8
                y -= 5.0
            else:
                p_tokens = _tokenize_styled_words(payload)
                p_lines = _wrap_styled_tokens(p_tokens, fmap["Fell"], fmap["FellIt"], 10.1, max_w)
                total_h = len(p_lines) * 13.8 + 5.5
                if y - total_h < bottom_y:
                    open_prose_page(first_page=False)
                c.setFillColor(HexColor(fu.HEX_INK))
                for pl in p_lines:
                    _draw_styled_line(c, margin_x, y, pl, fmap["Fell"], fmap["FellIt"], 10.1)
                    y -= 13.8
                y -= 5.5

        elif kind == "quote":
            q_clean = payload.replace("**", "").replace("`", "").replace("*", "")
            q_words = [[(word, True)] for word in q_clean.split()]
            q_wrapped = _wrap_styled_tokens(q_words, fmap["FellIt"], fmap["FellIt"], 9.5, max_w - 20.0)
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
                _draw_styled_line(c, margin_x + 14.0, y, ql, fmap["FellIt"], fmap["FellIt"], 9.5)
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

    tabulae.build_tabula_vi_vault_svg(build_dir / "tabula-vi-aperiodic-vault.svg")
    vellum.export_wash_png(build_dir / "vellum-aperiodic-96dpi.png", wash_mode="aperiodic", seed=17, profile="full")

    plates_meta = render_book(out_dir / "02_liber_secundus_reading.pdf", paint_ground=True)
    render_book(out_dir / "02_liber_secundus_illustrated.pdf", paint_ground=False)
    (out_dir / "plates-map.json").write_text(json.dumps(plates_meta, indent=2) + "\n", encoding="utf-8")
    print("[02_liber_secundus] Built Tabula VI SVG, 96-dpi aperiodic wash, and reading/illustrated PDFs.")


if __name__ == "__main__":
    main()
