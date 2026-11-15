#!/usr/bin/env python3
"""
Generates native Tabula VIII (`Speculum Diophantinum & Diagonalis Gödeliana`)
for `04_liber_quartus` both as a standalone 2-layer 170x220mm plotter SVG
(`tabula-viii-godel-diophantine.svg`) and directly onto a 504x720 pt ReportLab canvas.
"""

from pathlib import Path
from typing import Dict
from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from common.ciphers.charakteres import encode_glyphs
from common.ciphers.lifted_pen import encode_lifted_pen_ops, encode_lifted_pen_svg
from common.ciphers.scales import encode_falsifier_ticks
from common.illum import furniture as fu
from common.illum.platekit import Map
from common.illustrations.palette import Plate
from common.illustrations.shader_plates import godel_diophantine_geometry

FALSIFIER_VIII = "SOME ENUMERABLE SET LACKS A SINGLE FOLD POLYNOMIAL"
CAPTION_VIII = "THIS CAPTION HAS NO SECOND WITNESS"
LIFTED_VIII = "One witness suffices yet truth outruns proof"


def _centered_glyphs(caption: str, y0: float = 176.5, cell_mm: float = 2.3, advance_mm: float = 3.40, shift: int = 19) -> Dict:
    span = (len(caption) - 1) * advance_mm + cell_mm
    x0 = 85.0 - 0.5 * span
    return encode_glyphs(caption, x0=x0, y0=y0, cell_mm=cell_mm, advance_mm=advance_mm, shift=shift)


def _mm_width_to_pt(w_mm: float) -> float:
    return max(0.24, w_mm * fu.MM)


def build_tabula_viii_godel_svg(out_svg: Path) -> Plate:
    p = Plate("Tabula VIII · Speculum Diophantinum", width=170.0, height=220.0)

    p.add([(12, 14), (158, 14), (158, 206), (12, 206), (12, 14)], red=False, width=0.22)
    scale = encode_falsifier_ticks(FALSIFIER_VIII, x_mm=12.0, y_mm=14.0, w_mm=146.0, h_mm=192.0)
    for seg in scale["origin_mark"]:
        p.add(list(seg), red=True, width=0.42)
    for t in scale["ticks"]:
        p.add([t["p0"], t["p1"]], red=t["red"], width=0.24 if t["red"] else 0.16)
    for hseg in scale["group_hairlines"]:
        p.add(list(hseg), red=False, width=0.10)

    geom = godel_diophantine_geometry(cx=85.0, cy=96.5)
    for pts, w_mm in geom["ink_strokes"]:
        p.add(pts, red=False, width=w_mm)
    for pts, w_mm in geom["red_strokes"]:
        p.add(pts, red=True, width=w_mm)

    glyphs = _centered_glyphs(CAPTION_VIII, y0=176.5, shift=19)
    for st in glyphs["strokes"]:
        p.add(st, red=False, width=0.20, layer="text")

    p.text(85.0, 26.0, "TABULA VIII · SPECULUM DIOPHANTINUM", size_mm=3.3, red=True)
    for lx, ly, txt, is_red, sz in geom["labels"]:
        p.text(lx, ly, txt, size_mm=sz, red=is_red)
    p.text(85.0, 193.5, "SINGLE-FOLD DIOPHANTINE · AUT(D)=ID · SHIFT +19", size_mm=2.2, red=False)
    p.add_raw_svg_path(encode_lifted_pen_svg(LIFTED_VIII))

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(p.svg(opaque_ground=True), encoding="utf-8")
    return p


def draw_tabula_viii_godel_pdf_leaf(c: Canvas, page_no: int, paint_ground: bool) -> None:
    if paint_ground:
        fu.ground(c)
    fu.running_head(c, "Liber IV · Tabula VIII", "Tabula VIII", page_no)

    mp = Map(width_mm=170.0, height_mm=220.0)
    hnd = fu.Hand(c, amp=0.0)

    frame_mm = [(12, 14), (158, 14), (158, 206), (12, 206)]
    hnd.stroke([mp.P(x, y) for x, y in frame_mm], weight="orn", color="ink", closed=True)

    scale = encode_falsifier_ticks(FALSIFIER_VIII, x_mm=12.0, y_mm=14.0, w_mm=146.0, h_mm=192.0)
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

    geom = godel_diophantine_geometry(cx=85.0, cy=96.5)
    for pts, w_mm in geom["ink_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="ink")
    for pts, w_mm in geom["red_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="red")

    glyphs = _centered_glyphs(CAPTION_VIII, y0=176.5, shift=19)
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
    c.drawCentredString(tx, ty, "TABULA VIII · SPECULUM DIOPHANTINUM")
    for lx, ly, txt, is_red, sz in geom["labels"]:
        c.setFillColor(HexColor(fu.HEX_RED if is_red else fu.HEX_MUTE))
        c.setFont(fmap["Mono"], max(4.9, sz * 2.85))
        px_l, py_l = mp.P(lx, ly)
        c.drawCentredString(px_l, py_l, txt)
    c.setFillColor(HexColor(fu.HEX_MUTE))
    c.setFont(fmap["Mono"], 7.0)
    fx, fy = mp.P(85.0, 193.5)
    c.drawCentredString(fx, fy, "SINGLE-FOLD DIOPHANTINE · AUT(D)=ID · SHIFT +19")
    c.restoreState()

    ops = encode_lifted_pen_ops(LIFTED_VIII, x0=22.0, y0=201.0, span=126.0)
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
