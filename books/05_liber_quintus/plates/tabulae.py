#!/usr/bin/env python3
"""
Generates native Tabula IX (`Colophon Sine Auctore`) for `05_liber_quintus` both as
a standalone 2-layer 170x220mm plotter SVG (`tabula-ix-colophon-sine-auctore.svg`)
and directly onto a 504x720 pt ReportLab canvas.

The plate draws three bands:
  1. Charta / Sententia / Probatio with the Comparator bracket and the rubricated
     *Hiatus* interval between paper and statement.
  2. The empty byline cartouche approached by three strokes that stop short:
     Somnium (wave), Machina (staircase), Institutio (dashed rule).
  3. The register tally, read live from `docs/objections/register.md` at build time:
     one upright per entry, rubricated when the entry carries a dated disposition.
"""

import math
from pathlib import Path
import sys
from typing import Dict, List, Tuple

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from common.ciphers.charakteres import encode_glyphs
from common.ciphers.lifted_pen import encode_lifted_pen_ops, encode_lifted_pen_svg
from common.ciphers.scales import encode_falsifier_ticks
from common.illum import furniture as fu
from common.illum.platekit import Map
from common.illustrations.palette import Plate
from docs.objections import validate as obj_validate

FALSIFIER_IX = "A CHECKER THAT READS THE CLAIM NOT ONLY THE PROOF"
CAPTION_IX = "NO HAND SIGNED THIS CAPTION"
LIFTED_IX = "The gift was checked and nobody signed it"
SHIFT_IX = 23  # ninth prime, continuing +13 / +17 / +19 of Libri II-IV

Point = Tuple[float, float]


def register_tally() -> List[bool]:
    """Returns one flag per register entry: True when the entry carries an Author/Objector disposition."""
    text = (REPO / "docs" / "objections" / "register.md").read_text(encoding="utf-8")
    entries = obj_validate.parse_register(text)
    return [obj_validate.status(e) != "open" for e in entries]


def _rect(x: float, y: float, w: float, h: float) -> List[Point]:
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]


def _ellipse(cx: float, cy: float, rx: float, ry: float, steps: int = 96) -> List[Point]:
    pts = []
    for k in range(steps + 1):
        t = 2.0 * math.pi * k / steps
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    return pts


def _dashes(p0: Point, p1: Point, dash_mm: float = 1.6, gap_mm: float = 1.1) -> List[List[Point]]:
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    segs: List[List[Point]] = []
    s = 0.0
    while s < L:
        e = min(L, s + dash_mm)
        segs.append([(x0 + ux * s, y0 + uy * s), (x0 + ux * e, y0 + uy * e)])
        s = e + gap_mm
    return segs


def colophon_geometry(cx: float = 85.0, tally: List[bool] = None) -> Dict:
    """
    Builds the stroke lists (mm, top-left origin on the 170x220 plate) and labels
    for Tabula IX. `tally` is the register state; it defaults to the live register.
    """
    if tally is None:
        tally = register_tally()

    ink: List[Tuple[List[Point], float]] = []
    red: List[Tuple[List[Point], float]] = []
    labels: List[Tuple[float, float, str, bool, float]] = []

    # --- Band 1: Charta · Sententia · Probatio -------------------------------
    y_box, h_box, w_box = 44.0, 18.0, 30.0
    xs_box = [cx - 62.0, cx - 15.0, cx + 32.0]
    names = ["CHARTA", "SENTENTIA", "PROBATIO"]
    for x0, name in zip(xs_box, names):
        ink.append((_rect(x0, y_box, w_box, h_box), 0.26))
        # ruled "text" lines inside each leaf
        for k in range(4):
            yy = y_box + 4.0 + k * 3.4
            ink.append(([(x0 + 3.5, yy), (x0 + w_box - 3.5 - (2.0 if k == 3 else 0.0), yy)], 0.12))
        labels.append((x0 + 0.5 * w_box, y_box + h_box + 4.6, name, False, 2.1))

    # Comparator bracket joining Sententia and Probatio
    xb0, xb1 = xs_box[1] + 0.5 * w_box, xs_box[2] + 0.5 * w_box
    yb = y_box + h_box + 8.0
    ink.append(([(xb0, yb), (xb0, yb + 3.2), (xb1, yb + 3.2), (xb1, yb)], 0.26))
    xm = 0.5 * (xb0 + xb1)
    ink.append(([(xm, yb + 3.2), (xm, yb + 6.4)], 0.26))
    # a small "equals" below the bracket stem
    ink.append(([(xm - 2.2, yb + 8.0), (xm + 2.2, yb + 8.0)], 0.26))
    ink.append(([(xm - 2.2, yb + 9.6), (xm + 2.2, yb + 9.6)], 0.26))
    labels.append((xm, yb + 13.6, "COMPARATOR", False, 2.0))

    # Hiatus: rubricated dashed interval between Charta and Sententia
    xh0, xh1 = xs_box[0] + w_box, xs_box[1]
    yh = y_box + 0.5 * h_box
    for seg in _dashes((xh0 + 1.0, yh), (xh1 - 1.0, yh), dash_mm=1.2, gap_mm=1.0):
        red.append((seg, 0.30))
    labels.append((0.5 * (xh0 + xh1), yh - 3.0, "HIATUS", True, 2.0))

    # --- Band 2: the empty byline ---------------------------------------------
    cy = 112.0
    rx, ry = 29.0, 10.5
    ink.append((_ellipse(cx, cy, rx, ry), 0.30))
    ink.append(([(cx - 21.0, cy + 3.2), (cx + 21.0, cy + 3.2)], 0.14))  # the unsigned line

    stop = 4.0  # every hand stops this far short of the cartouche

    # Somnium: a wave arriving from the left
    wave: List[Point] = []
    x_start, x_end = 24.0, cx - rx - stop
    n = 48
    for k in range(n + 1):
        t = k / n
        x = x_start + (x_end - x_start) * t
        y = cy - 1.5 + 2.6 * math.sin(2.0 * math.pi * 3.0 * t) * (0.35 + 0.65 * (1.0 - t))
        wave.append((x, y))
    ink.append((wave, 0.26))
    labels.append((x_start + 6.0, cy - 7.5, "SOMNIUM", False, 2.0))

    # Machina: a staircase arriving from the right
    stair: List[Point] = []
    x_s, x_e = 146.0, cx + rx + stop
    y_s, y_e = cy - 9.0, cy - 1.5
    steps = 6
    for k in range(steps + 1):
        t = k / steps
        x = x_s + (x_e - x_s) * t
        y = y_s + (y_e - y_s) * (k / steps)
        if k > 0:
            stair.append((x, stair[-1][1]))
        stair.append((x, y))
    ink.append((stair, 0.26))
    labels.append((x_s - 6.0, cy - 12.0, "MACHINA", False, 2.0))

    # Institutio: a dashed rule arriving from below
    for seg in _dashes((cx, 139.0), (cx, cy + ry + stop), dash_mm=1.8, gap_mm=1.2):
        ink.append((seg, 0.26))
    labels.append((cx, 143.0, "INSTITUTIO", False, 2.0))

    # --- Band 3: the register tally --------------------------------------------
    n_tally = max(1, len(tally))
    pitch = 3.6
    span = (n_tally - 1) * pitch
    x0 = cx - 0.5 * span
    y_t0, y_t1 = 152.0, 160.0
    ink.append(([(x0 - 6.0, y_t1 + 1.6), (x0 + span + 6.0, y_t1 + 1.6)], 0.14))
    for k, disposed in enumerate(tally):
        x = x0 + k * pitch
        seg = [(x, y_t0), (x, y_t1)]
        if disposed:
            red.append((seg, 0.34))
        else:
            ink.append((seg, 0.26))
    labels.append((cx, y_t1 + 5.4, f"REGISTRUM · O-001 … O-{n_tally:03d}", False, 2.0))

    return {"ink_strokes": ink, "red_strokes": red, "labels": labels, "n_tally": n_tally}


def _centered_glyphs(caption: str, y0: float = 176.5, cell_mm: float = 2.3, advance_mm: float = 3.40, shift: int = SHIFT_IX) -> Dict:
    span = (len(caption) - 1) * advance_mm + cell_mm
    x0 = 85.0 - 0.5 * span
    return encode_glyphs(caption, x0=x0, y0=y0, cell_mm=cell_mm, advance_mm=advance_mm, shift=shift)


def _mm_width_to_pt(w_mm: float) -> float:
    return max(0.24, w_mm * fu.MM)


def _footer(n_tally: int) -> str:
    return f"COLOPHON SINE AUCTORE · REGISTRUM N={n_tally} · SHIFT +{SHIFT_IX}"


def build_tabula_ix_colophon_svg(out_svg: Path) -> Plate:
    p = Plate("Tabula IX · Colophon Sine Auctore", width=170.0, height=220.0)

    p.add([(12, 14), (158, 14), (158, 206), (12, 206), (12, 14)], red=False, width=0.22)
    scale = encode_falsifier_ticks(FALSIFIER_IX, x_mm=12.0, y_mm=14.0, w_mm=146.0, h_mm=192.0)
    for seg in scale["origin_mark"]:
        p.add(list(seg), red=True, width=0.42)
    for t in scale["ticks"]:
        p.add([t["p0"], t["p1"]], red=t["red"], width=0.24 if t["red"] else 0.16)
    for hseg in scale["group_hairlines"]:
        p.add(list(hseg), red=False, width=0.10)

    geom = colophon_geometry(cx=85.0)
    for pts, w_mm in geom["ink_strokes"]:
        p.add(pts, red=False, width=w_mm)
    for pts, w_mm in geom["red_strokes"]:
        p.add(pts, red=True, width=w_mm)

    glyphs = _centered_glyphs(CAPTION_IX, y0=176.5)
    for st in glyphs["strokes"]:
        p.add(st, red=False, width=0.20, layer="text")

    p.text(85.0, 26.0, "TABULA IX · COLOPHON SINE AUCTORE", size_mm=3.3, red=True)
    for lx, ly, txt, is_red, sz in geom["labels"]:
        p.text(lx, ly, txt, size_mm=sz, red=is_red)
    p.text(85.0, 193.5, _footer(geom["n_tally"]), size_mm=2.2, red=False)
    p.add_raw_svg_path(encode_lifted_pen_svg(LIFTED_IX))

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(p.svg(opaque_ground=True), encoding="utf-8")
    return p


def draw_tabula_ix_colophon_pdf_leaf(c: Canvas, page_no: int, paint_ground: bool) -> None:
    if paint_ground:
        fu.ground(c)
    fu.running_head(c, "Liber V · Tabula IX", "Tabula IX", page_no)

    mp = Map(width_mm=170.0, height_mm=220.0)
    hnd = fu.Hand(c, amp=0.0)

    frame_mm = [(12, 14), (158, 14), (158, 206), (12, 206)]
    hnd.stroke([mp.P(x, y) for x, y in frame_mm], weight="orn", color="ink", closed=True)

    scale = encode_falsifier_ticks(FALSIFIER_IX, x_mm=12.0, y_mm=14.0, w_mm=146.0, h_mm=192.0)
    for p0, p1 in scale["origin_mark"]:
        hnd.stroke([mp.P(*p0), mp.P(*p1)], weight="heavy", color="red")
    for t in scale["ticks"]:
        hnd.stroke(
            [mp.P(*t["p0"]), mp.P(*t["p1"])],
            weight="cip" if t["red"] else "hair",
            color="red" if t["red"] else "ink",
        )
    for p0, p1 in scale["group_hairlines"]:
        hnd.stroke([mp.P(*p0), mp.P(*p1)], weight="hair", color="sepia")

    geom = colophon_geometry(cx=85.0)
    for pts, w_mm in geom["ink_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="ink")
    for pts, w_mm in geom["red_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="red")

    glyphs = _centered_glyphs(CAPTION_IX, y0=176.5)
    for st in glyphs["strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in st], weight="cip", color="ink")
    for tx, ty, tr, kind in glyphs["terminals"]:
        px, py = mp.P(tx, ty)
        if kind == "dot":
            hnd.dot(px, py, r=mp.mm(tr), color="red")
        else:
            hnd.ring(px, py, r=mp.mm(tr), weight="hair", color="ink")

    fmap = fu.fonts()
    c.saveState()
    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["FellSC"], 10.0)
    tx, ty = mp.P(85.0, 25.0)
    c.drawCentredString(tx, ty, "TABULA IX · COLOPHON SINE AUCTORE")
    for lx, ly, txt, is_red, sz in geom["labels"]:
        c.setFillColor(HexColor(fu.HEX_RED if is_red else fu.HEX_MUTE))
        c.setFont(fmap["Mono"], max(4.9, sz * 2.85))
        px_l, py_l = mp.P(lx, ly)
        c.drawCentredString(px_l, py_l, txt)
    c.setFillColor(HexColor(fu.HEX_MUTE))
    c.setFont(fmap["Mono"], 7.0)
    fx, fy = mp.P(85.0, 193.5)
    c.drawCentredString(fx, fy, _footer(geom["n_tally"]))
    c.restoreState()

    ops = encode_lifted_pen_ops(LIFTED_IX, x0=22.0, y0=201.0, span=126.0)
    c.saveState()
    c.setStrokeColor(fu.rgb(fu.INK))
    c.setLineWidth(0.35)
    path = c.beginPath()
    for op in ops:
        if op[0] == "M":
            path.moveTo(*mp.P(op[1], op[2]))
        elif op[0] == "L":
            path.lineTo(*mp.P(op[1], op[2]))
        elif op[0] == "Q":
            ctrl = mp.P(op[1], op[2])
            end = mp.P(op[3], op[4])
            path.curveTo(ctrl[0], ctrl[1], ctrl[0], ctrl[1], end[0], end[1])
    c.drawPath(path, stroke=1, fill=0)
    c.restoreState()
