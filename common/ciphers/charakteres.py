import math
from typing import Dict, List, Sequence, Tuple

Point = Tuple[float, float]

# Deterministic stroke-primitive character vocabulary (unit cell [0, 1] x [0, 1])
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def glyph_strokes_for_char(ch: str, shift: int = 0) -> Tuple[List[List[Point]], List[Tuple[float, float, float, str]]]:
    """
    Returns (polylines, terminals) in unit [0..1] coordinates for a character
    under an optional twelve-mark / Caesar shift.
    Terminals are (x, y, r, kind) where kind in {'dot', 'ring'}.
    """
    ch = ch.upper()
    if ch not in ALPHABET:
        return ([], [])
    idx = (ALPHABET.index(ch) + shift) % 26
    stem_x = 0.25 + 0.5 * ((idx % 3) / 2.0)
    cross_y = 0.28 + 0.44 * (((idx // 3) % 3) / 2.0)
    diag = (idx // 9) % 3

    polylines: List[List[Point]] = [[(stem_x, 0.12), (stem_x, 0.88)]]
    if diag == 0:
        polylines.append([(0.18, cross_y), (0.82, cross_y)])
    elif diag == 1:
        polylines.append([(0.18, cross_y - 0.14), (0.82, cross_y + 0.14)])
    else:
        polylines.append([(0.18, cross_y + 0.14), (0.82, cross_y - 0.14)])

    term_kind = "ring" if (idx % 2 == 1) else "dot"
    r = 0.075 if term_kind == "ring" else 0.065
    terminals = [(stem_x, 0.12, r, term_kind)]
    if idx >= 13:
        terminals.append((0.82, cross_y, r, "ring" if term_kind == "dot" else "dot"))
    return (polylines, terminals)


def encode_glyphs(
    text: str,
    x0: float,
    y0: float,
    cell_mm: float = 3.2,
    advance_mm: float = 3.9,
    shift: int = 0,
) -> Dict[str, List]:
    """Lays out shifted stroke glyphs along a horizontal caption rail."""
    strokes: List[List[Point]] = []
    terminals: List[Tuple[float, float, float, str]] = []
    cursor = x0
    for ch in text.upper():
        if ch == " ":
            cursor += advance_mm * 0.75
            continue
        pls, tms = glyph_strokes_for_char(ch, shift=shift)
        for pl in pls:
            strokes.append([(cursor + px * cell_mm, y0 + py * cell_mm) for px, py in pl])
        for tx, ty, tr, kind in tms:
            terminals.append((cursor + tx * cell_mm, y0 + ty * cell_mm, tr * cell_mm, kind))
        cursor += advance_mm
    return {"strokes": strokes, "terminals": terminals, "shift": shift}


TWELVE_MARKS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")


def write_twelve_mark_caption(plaintext: str, shift: int = 1) -> List[str]:
    """Encodes A-Z + space into base-12 paired mark tokens shifted by `shift`."""
    vocab = " ABCDEFGHIJKLMNOPQRSTUVWXYZ."
    tokens: List[str] = []
    for ch in plaintext.upper():
        if ch not in vocab:
            continue
        val = (vocab.index(ch) + shift) % 144
        hi, lo = divmod(val, 12)
        tokens.append(f"{TWELVE_MARKS[hi]}:{TWELVE_MARKS[lo]}")
    return tokens


def decode_twelve_mark_caption(tokens: Sequence[str], shift: int = 1) -> str:
    vocab = " ABCDEFGHIJKLMNOPQRSTUVWXYZ."
    out: List[str] = []
    for tok in tokens:
        hi_s, lo_s = tok.split(":")
        val = TWELVE_MARKS.index(hi_s) * 12 + TWELVE_MARKS.index(lo_s)
        idx = (val - shift) % len(vocab)
        out.append(vocab[idx])
    return "".join(out)
