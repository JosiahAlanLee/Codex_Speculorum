#!/usr/bin/env python3
import hashlib
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from common.ciphers.clausa_base import ClausaConfig, ClausaEngine
from common.illum import furniture as fu
from common.illum.platekit import Map
from common.illustrations.palette import Plate

SPECIMEN_KEY = "MERSENNE KEPLER KIRCHER"
SPECIMEN_PLAINTEXT = (
    "SEALED SPECIMEN I: EVERY TEMPERAMENT CHOOSES WHERE THE ERROR LIVES. "
    "THE MARKS OF THIS FIELD ARE WRITTEN IN GROUND ORDER SO ELEMENT SEQUENCE REVEALS NOTHING."
)


def build_clausa_plate(out_dir: Path) -> dict:
    cfg = ClausaConfig(grid_diameter=89, cell_mm=1.35, origin_x_mm=24.9, origin_y_mm=54.0, char_capacity=240)
    eng = ClausaEngine(cfg)
    sealed = eng.seal_field(SPECIMEN_KEY, 1, SPECIMEN_PLAINTEXT)

    # Verify roundtrip immediately
    recovered = eng.unseal_field(SPECIMEN_KEY, 1, sealed["marks"])
    assert recovered == SPECIMEN_PLAINTEXT, "Nota Clausa round-trip mismatch!"

    p = Plate("Nota Clausa · I", width=170.0, height=220.0)
    cx_mm = cfg.origin_x_mm + (cfg.grid_diameter * cfg.cell_mm) / 2.0
    cy_mm = cfg.origin_y_mm + (cfg.grid_diameter * cfg.cell_mm) / 2.0
    r_mm = (cfg.grid_diameter * cfg.cell_mm) / 2.0 + 3.0
    p.ring(cx_mm, cy_mm, r_mm, red=True, width=0.22)
    p.ring(cx_mm, cy_mm, r_mm + 1.6, red=False, width=0.16)
    p.text(85.0, 32.0, "NOTA CLAUSA · I", size_mm=3.6, red=True)

    half_len = 0.42
    for m in sealed["marks"]:
        mx = cfg.origin_x_mm + (m["gx"] + 0.5) * cfg.cell_mm
        my = cfg.origin_y_mm + (m["gy"] + 0.5) * cfg.cell_mm
        ang = (m["heading"] / 16.0) * math.pi
        dx, dy = half_len * math.cos(ang), half_len * math.sin(ang)
        p.add([(mx - dx, my - dy), (mx + dx, my + dy)], red=(m["bit"] == 1), width=0.22)

    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / "nota-clausa-1.svg"
    svg_path.write_text(p.svg(opaque_ground=True), encoding="utf-8")

    meta = {
        "field_1_sha256": sealed["sha256"],
        "combined_sha256": hashlib.sha256(sealed["sha256"].encode("utf-8")).hexdigest(),
        "red_marks": sealed["red_count"],
        "total_marks": len(sealed["marks"]),
        "cfg": cfg,
        "marks": sealed["marks"],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps({k: v for k, v in meta.items() if k not in ("cfg", "marks")}, indent=2) + "\n",
        encoding="utf-8",
    )
    return meta


def draw_clausa_pdf_leaf(c: Canvas, meta: dict, page_no: int, paint_ground: bool) -> None:
    if paint_ground:
        fu.ground(c)
    fu.running_head(c, "Nota Clausa", "Nota Clausa I", page_no)

    cfg: ClausaConfig = meta["cfg"]
    mp = Map(width_mm=170.0, height_mm=220.0)
    hnd = fu.Hand(c, amp=0.0)

    cx_mm = cfg.origin_x_mm + (cfg.grid_diameter * cfg.cell_mm) / 2.0
    cy_mm = cfg.origin_y_mm + (cfg.grid_diameter * cfg.cell_mm) / 2.0
    r_mm = (cfg.grid_diameter * cfg.cell_mm) / 2.0 + 3.0
    ccx, ccy = mp.P(cx_mm, cy_mm)
    hnd.ring(ccx, ccy, r=mp.mm(r_mm), weight="cip", color="red")
    hnd.ring(ccx, ccy, r=mp.mm(r_mm + 1.6), weight="hair", color="ink")

    fmap = fu.fonts()
    c.saveState()
    c.setFillColor(HexColor(fu.HEX_RED))
    c.setFont(fmap["FellSC"], 10.5)
    tx, ty = mp.P(85.0, 32.0)
    c.drawCentredString(tx, ty, "NOTA CLAUSA · I")
    c.restoreState()

    # Emit 1,440 two-point strokes strictly in ground (gy, gx) order
    half_len = 0.42
    for m in meta["marks"]:
        mx = cfg.origin_x_mm + (m["gx"] + 0.5) * cfg.cell_mm
        my = cfg.origin_y_mm + (m["gy"] + 0.5) * cfg.cell_mm
        ang = (m["heading"] / 16.0) * math.pi
        dx, dy = half_len * math.cos(ang), half_len * math.sin(ang)
        p0 = mp.P(mx - dx, my - dy)
        p1 = mp.P(mx + dx, my + dy)
        c.saveState()
        c.setStrokeColor(fu.rgb(fu.RED if m["bit"] == 1 else fu.INK))
        c.setLineWidth(0.55)
        p = c.beginPath()
        p.moveTo(*p0)
        p.lineTo(*p1)
        c.drawPath(p, stroke=1, fill=0)
        c.restoreState()
