#!/usr/bin/env python3
"""
Generates native Tabulae I–IV both as standalone 2-layer A4 / 170x220mm SVGs
(with `data-channel="lifted-pen"`) and directly onto ReportLab 504x720 pt
canvases with zero clipped PDF board mounting:
  - Tabula I   : De Commate (Pythagorean Comma & 3:2 Lissajous)
  - Tabula II  : De Fibra Quaternaria (4D Hopf Fibration & Villarceau Link)
  - Tabula III : De Speculo Mobiano (Conformal Möbius Grid & 7/16 4D Vault)
  - Tabula IV  : De Calore in Limite (Strict Hot-Spots Neumann Eigenmode & Chladni)
"""

from pathlib import Path
from typing import Dict, List, Sequence, Tuple
from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from common.ciphers.charakteres import encode_glyphs
from common.ciphers.lifted_pen import encode_lifted_pen_ops, encode_lifted_pen_svg
from common.ciphers.scales import encode_falsifier_ticks
from common.illum import furniture as fu
from common.illum.platekit import Map
from common.illustrations.guilloche import lissajous_nodal, rosette, wave_ring
from common.illustrations.palette import Plate
from common.illustrations.shader_plates import (
    hopf_fibration_geometry,
    hotspots_neumann_geometry,
    mobius_conformal_geometry,
)

FALSIFIER_I = "THE CIRCLE CLOSES WITHOUT REMAINDER"
CAPTION_I = "TWELVE FIFTHS EXCEED SEVEN OCTAVES"
LIFTED_I = "The file keeps the lifts"

FALSIFIER_II = "TWO DISTINCT HOPF FIBERS UNLINK IN SPACE"
CAPTION_II = "FORTY TWO FIBERS LINK WITHOUT SEAM"
LIFTED_II = "Every circle links every other"

FALSIFIER_III = "CONFORMAL INVERSION SHEARS RIGHT ANGLES"
CAPTION_III = "SEVEN SIXTEENTHS IN THE MIRROR VAULT"
LIFTED_III = "Angles survive inversion"

FALSIFIER_IV = "FIRST NEUMANN MODE PEAKS IN THE INTERIOR"
CAPTION_IV = "EXTREMA CLEAVE TO THE OUTER BORDER"
LIFTED_IV = "No hot spot hides within"


def _centered_glyphs(caption: str, y0: float = 176.0, cell_mm: float = 2.4, advance_mm: float = 3.4, shift: int = 3) -> Dict:
    span = (len(caption) - 1) * advance_mm + cell_mm
    x0 = 85.0 - 0.5 * span
    return encode_glyphs(caption, x0=x0, y0=y0, cell_mm=cell_mm, advance_mm=advance_mm, shift=shift)


def _add_plate_furniture_svg(
    p: Plate,
    falsifier: str,
    caption: str,
    shift: int,
    header: str,
    footer: str,
    lifted_phrase: str,
) -> None:
    p.add([(12, 14), (158, 14), (158, 206), (12, 206), (12, 14)], red=False, width=0.22)
    scale = encode_falsifier_ticks(falsifier, x_mm=12.0, y_mm=14.0, w_mm=146.0, h_mm=192.0)
    for seg in scale["origin_mark"]:
        p.add(list(seg), red=True, width=0.42)
    for t in scale["ticks"]:
        p.add([t["p0"], t["p1"]], red=t["red"], width=0.24 if t["red"] else 0.16)
    for hseg in scale["group_hairlines"]:
        p.add(list(hseg), red=False, width=0.10)

    glyphs = _centered_glyphs(caption, y0=175.5, cell_mm=2.4, advance_mm=3.4, shift=shift)
    for st in glyphs["strokes"]:
        p.add(st, red=False, width=0.20, layer="text")

    p.text(85.0, 26.0, header, size_mm=3.4, red=True)
    p.text(85.0, 193.5, footer, size_mm=2.25, red=False)
    p.add_raw_svg_path(encode_lifted_pen_svg(lifted_phrase))


def _draw_plate_furniture_pdf(
    c: Canvas,
    mp: Map,
    hnd: fu.Hand,
    run_title: str,
    folio_lbl: str,
    page_no: int,
    falsifier: str,
    caption: str,
    shift: int,
    header: str,
    footer: str,
    lifted_phrase: str,
    paint_ground: bool,
) -> None:
    if paint_ground:
        fu.ground(c)
    fu.running_head(c, run_title, folio_lbl, page_no)

    frame_mm = [(12, 14), (158, 14), (158, 206), (12, 206)]
    hnd.stroke([mp.P(x, y) for x, y in frame_mm], weight="orn", color="ink", closed=True)

    scale = encode_falsifier_ticks(falsifier, x_mm=12.0, y_mm=14.0, w_mm=146.0, h_mm=192.0)
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

    glyphs = _centered_glyphs(caption, y0=175.5, cell_mm=2.4, advance_mm=3.4, shift=shift)
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
    c.setFont(fmap["FellSC"], 10.2)
    tx, ty = mp.P(85.0, 25.0)
    c.drawCentredString(tx, ty, header)
    c.setFillColor(HexColor(fu.HEX_MUTE))
    c.setFont(fmap["Mono"], 7.2)
    fx, fy = mp.P(85.0, 193.5)
    c.drawCentredString(fx, fy, footer)
    c.restoreState()

    ops = encode_lifted_pen_ops(lifted_phrase, x0=22.0, y0=201.0, span=126.0)
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


def _mm_width_to_pt(w_mm: float) -> float:
    return max(0.28, w_mm * fu.MM)


# ---------------------------------------------------------------------------
# Tabula I · De Commate
# ---------------------------------------------------------------------------

def build_tabula_i_svg(out_svg: Path) -> Plate:
    p = Plate("Tabula I · Of the Unclosed Ratio", width=170.0, height=220.0)
    _add_plate_furniture_svg(
        p,
        FALSIFIER_I,
        CAPTION_I,
        shift=3,
        header="TABULA I · DE COMMATE",
        footer="RED CORNER: BIT 0 CLOCKWISE · SHIFT +03",
        lifted_phrase=LIFTED_I,
    )
    for curve in rosette(85.0, 101.0, r_base=44.0, amp=4.2, lobes=12, passes=5):
        p.add(curve, red=False, width=0.15)
    p.add(wave_ring(85.0, 101.0, r_mid=52.0, amp=1.8, cycles=19, phase_deg=30.0), red=True, width=0.20)
    p.add(lissajous_nodal(85.0, 101.0, rx=22.0, ry=22.0, p_freq=3, q_freq=2, delta_deg=90.0), red=False, width=0.20)

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(p.svg(opaque_ground=True), encoding="utf-8")
    return p


def draw_tabula_i_pdf_leaf(c: Canvas, page_no: int, paint_ground: bool) -> None:
    mp = Map(width_mm=170.0, height_mm=220.0)
    hnd = fu.Hand(c, amp=0.0)
    _draw_plate_furniture_pdf(
        c, mp, hnd,
        "Liber I · Tabula I", "Tabula I", page_no,
        FALSIFIER_I, CAPTION_I, shift=3,
        header="TABULA I · DE COMMATE",
        footer="RED CORNER: BIT 0 CLOCKWISE · SHIFT +03",
        lifted_phrase=LIFTED_I,
        paint_ground=paint_ground,
    )
    for curve in rosette(85.0, 101.0, r_base=44.0, amp=4.2, lobes=12, passes=5):
        hnd.stroke([mp.P(x, y) for x, y in curve], weight="hair", color="ink")
    hnd.stroke([mp.P(x, y) for x, y in wave_ring(85.0, 101.0, r_mid=52.0, amp=1.8, cycles=19, phase_deg=30.0)], weight="cip", color="red")
    hnd.stroke([mp.P(x, y) for x, y in lissajous_nodal(85.0, 101.0, rx=22.0, ry=22.0, p_freq=3, q_freq=2, delta_deg=90.0)], weight="orn", color="ink")


# ---------------------------------------------------------------------------
# Tabula II · De Fibra Quaternaria (4D Hopf Fibration)
# ---------------------------------------------------------------------------

def build_tabula_ii_hopf_svg(out_svg: Path) -> Plate:
    p = Plate("Tabula II · De Fibra Quaternaria", width=170.0, height=220.0)
    _add_plate_furniture_svg(
        p,
        FALSIFIER_II,
        CAPTION_II,
        shift=5,
        header="TABULA II · DE FIBRA QUATERNARIA",
        footer="S3 TO R3 HOPF PROJECTION · LINKING INVARIANT +1 · SHIFT +05",
        lifted_phrase=LIFTED_II,
    )
    geom = hopf_fibration_geometry(cx=85.0, cy=101.0, r_horizon=56.5)
    for pts, w_mm in geom["ink_strokes"]:
        p.add(pts, red=False, width=w_mm)
    for pts, w_mm in geom["red_strokes"]:
        p.add(pts, red=True, width=w_mm)
    for sx, sy in geom["triad_seals"]:
        p.ring(sx, sy, r=1.25, red=True, width=0.22, steps=36)

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(p.svg(opaque_ground=True), encoding="utf-8")
    return p


def draw_tabula_ii_hopf_pdf_leaf(c: Canvas, page_no: int, paint_ground: bool) -> None:
    mp = Map(width_mm=170.0, height_mm=220.0)
    hnd = fu.Hand(c, amp=0.0)
    _draw_plate_furniture_pdf(
        c, mp, hnd,
        "Liber I · Tabula II", "Tabula II", page_no,
        FALSIFIER_II, CAPTION_II, shift=5,
        header="TABULA II · DE FIBRA QUATERNARIA",
        footer="S3 TO R3 HOPF PROJECTION · LINKING INVARIANT +1 · SHIFT +05",
        lifted_phrase=LIFTED_II,
        paint_ground=paint_ground,
    )
    geom = hopf_fibration_geometry(cx=85.0, cy=101.0, r_horizon=56.5)
    for pts, w_mm in geom["ink_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="ink")
    for pts, w_mm in geom["red_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="red")
    for sx, sy in geom["triad_seals"]:
        px, py = mp.P(sx, sy)
        hnd.ring(px, py, r=mp.mm(1.25), weight="cip", color="red")


# ---------------------------------------------------------------------------
# Tabula III · De Speculo Mobiano (Conformal Möbius Chamber & 4D Hyper-Vault)
# ---------------------------------------------------------------------------

def build_tabula_iii_mobius_svg(out_svg: Path) -> Plate:
    p = Plate("Tabula III · De Speculo Mobiano", width=170.0, height=220.0)
    _add_plate_furniture_svg(
        p,
        FALSIFIER_III,
        CAPTION_III,
        shift=7,
        header="TABULA III · DE SPECULO MOBIANO",
        footer="ISOTHERMAL CONFORMAL GRID · 7:16 HYPER-VAULT · SHIFT +07",
        lifted_phrase=LIFTED_III,
    )
    geom = mobius_conformal_geometry(cx=85.0, cy=101.0, r_ap=55.5)
    for pts, w_mm in geom["ink_strokes"]:
        p.add(pts, red=False, width=w_mm)
    for pts, w_mm in geom["red_strokes"]:
        p.add(pts, red=True, width=w_mm)
    for fx, fy in geom["foci"]:
        p.ring(fx, fy, r=1.8, red=True, width=0.26, steps=40)
        p.ring(fx, fy, r=0.7, red=True, width=0.22, steps=24)
    for vx, vy in geom["vault"]["verts_2d"]:
        p.ring(vx, vy, r=0.65, red=False, width=0.16, steps=20)

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(p.svg(opaque_ground=True), encoding="utf-8")
    return p


def draw_tabula_iii_mobius_pdf_leaf(c: Canvas, page_no: int, paint_ground: bool) -> None:
    mp = Map(width_mm=170.0, height_mm=220.0)
    hnd = fu.Hand(c, amp=0.0)
    _draw_plate_furniture_pdf(
        c, mp, hnd,
        "Liber I · Tabula III", "Tabula III", page_no,
        FALSIFIER_III, CAPTION_III, shift=7,
        header="TABULA III · DE SPECULO MOBIANO",
        footer="ISOTHERMAL CONFORMAL GRID · 7:16 HYPER-VAULT · SHIFT +07",
        lifted_phrase=LIFTED_III,
        paint_ground=paint_ground,
    )
    geom = mobius_conformal_geometry(cx=85.0, cy=101.0, r_ap=55.5)
    for pts, w_mm in geom["ink_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="ink")
    for pts, w_mm in geom["red_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="red")
    for fx, fy in geom["foci"]:
        px, py = mp.P(fx, fy)
        hnd.ring(px, py, r=mp.mm(1.8), weight="cip", color="red")
        hnd.dot(px, py, r=mp.mm(0.65), color="red")
    for vx, vy in geom["vault"]["verts_2d"]:
        px, py = mp.P(vx, vy)
        hnd.ring(px, py, r=mp.mm(0.65), weight="hair", color="ink")


# ---------------------------------------------------------------------------
# Tabula IV · De Calore in Limite (Strict Hot-Spots Neumann & Chladni Modes)
# ---------------------------------------------------------------------------

def build_tabula_iv_hotspots_svg(out_svg: Path) -> Plate:
    p = Plate("Tabula IV · De Calore in Limite", width=170.0, height=220.0)
    _add_plate_furniture_svg(
        p,
        FALSIFIER_IV,
        CAPTION_IV,
        shift=9,
        header="TABULA IV · DE CALORE IN LIMITE",
        footer="STRICT HOT-SPOTS NEUMANN MODE · EXTREMA ON BOUNDARY · SHIFT +09",
        lifted_phrase=LIFTED_IV,
    )
    geom = hotspots_neumann_geometry(cx=85.0, cy=101.0)
    for pts, w_mm in geom["ink_strokes"]:
        p.add(pts, red=False, width=w_mm)
    for pts, w_mm in geom["red_strokes"]:
        p.add(pts, red=True, width=w_mm)

    for px_m, py_m in (geom["hot_pole"], geom["cold_pole"]):
        p.ring(px_m, py_m, r=2.3, red=True, width=0.28, steps=40)
        p.ring(px_m, py_m, r=0.9, red=True, width=0.24, steps=24)

    p.text(geom["hot_pole"][0], geom["hot_pole"][1] - 3.6, "MAX +", size_mm=2.2, red=True)
    p.text(geom["cold_pole"][0], geom["cold_pole"][1] + 5.2, "MIN -", size_mm=2.2, red=True)
    for mx, my, r_lbl in geom["medallion_labels"]:
        p.text(mx, my, r_lbl, size_mm=2.1, red=False)

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(p.svg(opaque_ground=True), encoding="utf-8")
    return p


def draw_tabula_iv_hotspots_pdf_leaf(c: Canvas, page_no: int, paint_ground: bool) -> None:
    mp = Map(width_mm=170.0, height_mm=220.0)
    hnd = fu.Hand(c, amp=0.0)
    _draw_plate_furniture_pdf(
        c, mp, hnd,
        "Liber I · Tabula IV", "Tabula IV", page_no,
        FALSIFIER_IV, CAPTION_IV, shift=9,
        header="TABULA IV · DE CALORE IN LIMITE",
        footer="STRICT HOT-SPOTS NEUMANN MODE · EXTREMA ON BOUNDARY · SHIFT +09",
        lifted_phrase=LIFTED_IV,
        paint_ground=paint_ground,
    )
    geom = hotspots_neumann_geometry(cx=85.0, cy=101.0)
    for pts, w_mm in geom["ink_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="ink")
    for pts, w_mm in geom["red_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="red")

    for px_m, py_m in (geom["hot_pole"], geom["cold_pole"]):
        px, py = mp.P(px_m, py_m)
        hnd.ring(px, py, r=mp.mm(2.3), weight="cip", color="red")
        hnd.dot(px, py, r=mp.mm(0.85), color="red")

    fmap = fu.fonts()
    c.saveState()
    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["Mono"], 6.8)
    hx, hy = mp.P(geom["hot_pole"][0], geom["hot_pole"][1] - 3.8)
    cx_p, cy_p = mp.P(geom["cold_pole"][0], geom["cold_pole"][1] + 5.0)
    c.drawCentredString(hx, hy, "MAX +")
    c.drawCentredString(cx_p, cy_p, "MIN -")
    c.setFillColor(HexColor(fu.HEX_MUTE))
    for mx, my, r_lbl in geom["medallion_labels"]:
        lx, ly = mp.P(mx, my)
        c.drawCentredString(lx, ly, r_lbl)
    c.restoreState()


# ---------------------------------------------------------------------------
# Tabula V · Canon Cancrizans Koopmanianus (Raag Bhairav Crab Canon)
# ---------------------------------------------------------------------------

FALSIFIER_V = "BHAIRAV DEPARTS FROM ITSELF UNDER OCTAVE INVERSION"
CAPTION_V = "WHAT ASCENDS BY FOURTH RETURNS BY FIFTH"
LIFTED_V = "Read backward from the octave"


def _load_canon_score():
    import importlib.util as _ilu
    canon_py = Path(__file__).resolve().parents[1] / "canon" / "play_koopman_canon.py"
    sp = _ilu.spec_from_file_location("canon_mod", canon_py)
    mod = _ilu.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod.build_canon_score()


def build_tabula_v_canon_svg(out_svg: Path) -> Plate:
    from common.illustrations.shader_plates import canon_koopman_geometry

    p = Plate("Tabula V · Canon Cancrizans Koopmanianus", width=170.0, height=220.0)
    _add_plate_furniture_svg(
        p,
        FALSIFIER_V,
        CAPTION_V,
        shift=11,
        header="TABULA V · CANON CANCRIZANS BHAIRAV",
        footer="R_RECTA(K) * R_CANCRI(31-K) = 2:1 · KOOPMAN MODES · SHIFT +11",
        lifted_phrase=LIFTED_V,
    )
    geom = canon_koopman_geometry(_load_canon_score(), cx=85.0)
    for pts, w_mm in geom["ink_strokes"]:
        p.add(pts, red=False, width=w_mm)
    for pts, w_mm in geom["red_strokes"]:
        p.add(pts, red=True, width=w_mm)
    for nx_p, ny_p in geom["recta_notes"]:
        p.ring(nx_p, ny_p, r=0.82, red=False, width=0.22, steps=20)
    wcx, wcy = geom["wheel_center"]
    p.ring(wcx, wcy, r=1.9, red=True, width=0.26, steps=32)
    for lx, ly, txt, is_red, sz in geom["labels"]:
        p.text(lx, ly, txt, size_mm=sz, red=is_red)

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(p.svg(opaque_ground=True), encoding="utf-8")
    return p


def draw_tabula_v_canon_pdf_leaf(c: Canvas, page_no: int, paint_ground: bool) -> None:
    from common.illustrations.shader_plates import canon_koopman_geometry

    mp = Map(width_mm=170.0, height_mm=220.0)
    hnd = fu.Hand(c, amp=0.0)
    _draw_plate_furniture_pdf(
        c, mp, hnd,
        "Liber I · Tabula V", "Tabula V", page_no,
        FALSIFIER_V, CAPTION_V, shift=11,
        header="TABULA V · CANON CANCRIZANS BHAIRAV",
        footer="R_RECTA(K) * R_CANCRI(31-K) = 2:1 · KOOPMAN MODES · SHIFT +11",
        lifted_phrase=LIFTED_V,
        paint_ground=paint_ground,
    )
    geom = canon_koopman_geometry(_load_canon_score(), cx=85.0)
    for pts, w_mm in geom["ink_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="ink")
    for pts, w_mm in geom["red_strokes"]:
        hnd.stroke([mp.P(x, y) for x, y in pts], weight=_mm_width_to_pt(w_mm), color="red")
    for nx_p, ny_p in geom["recta_notes"]:
        px, py = mp.P(nx_p, ny_p)
        hnd.dot(px, py, r=mp.mm(0.78), color="ink")
    wcx, wcy = geom["wheel_center"]
    px_c, py_c = mp.P(wcx, wcy)
    hnd.ring(px_c, py_c, r=mp.mm(1.9), weight="cip", color="red")
    hnd.dot(px_c, py_c, r=mp.mm(0.65), color="red")

    fmap = fu.fonts()
    c.saveState()
    for lx, ly, txt, is_red, sz in geom["labels"]:
        c.setFillColor(HexColor(fu.HEX_RED if is_red else fu.HEX_MUTE))
        c.setFont(fmap["Mono"], max(5.6, sz * 2.85))
        tx, ty = mp.P(lx, ly)
        c.drawCentredString(tx, ty, txt)
    c.restoreState()
