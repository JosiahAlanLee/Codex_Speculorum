"""Inline emphasis, wrapping, and mathematical glyph fallback for the treatise pages."""

import re
from typing import List, Tuple

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from common.illum import furniture as fu

_SPAN_RE = re.compile(r"\*([^*]+)\*")

StyledWord = List[Tuple[str, bool]]


def tokenize_styled_words(text: str) -> List[StyledWord]:
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


def wrap_styled_tokens(
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


def draw_styled_line(
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
