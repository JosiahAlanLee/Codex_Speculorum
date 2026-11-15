#!/usr/bin/env python3
"""
Deterministic 96-dpi vellum finishing (`light` and `full` profiles) + Volume II
mathematical shader washes (`hopf`, `mobius`, `hotspots`, `canon`, `aperiodic`).
Generates warm vellum fields with feathered text/cipher/plate protection zones
and merges each vellum sheet *underneath* the pure vector foreground page so
strokes, glyphs, lifted-pen paths, and ground-ordered Nota Clausa marks remain
crisp vectors in the finished illustrated PDF.
"""

import argparse
import hashlib
import io
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from scipy.ndimage import gaussian_filter

from common.illum.furniture import PAPER, PH, PW
from common.illustrations.shader_plates import (
    aperiodic_vellum_field,
    canon_vellum_field,
    hopf_vellum_field,
    hotspots_vellum_field,
    mobius_vellum_field,
)

VERSION = "vellum-1"
STAMP = "CodexIntervallorum:vellum-1"
DPI = 96
SCALE = DPI / 72.0
PADDING_PT = 3.0
GRAIN_PADDING_PT = 1.0
PIGMENT = (104, 72, 39)
RUBRIC_WASH = (152, 68, 46)
SLATE_WASH = (70, 84, 92)
PROFILES = ("light", "full")
WASH_MODES = ("none", "hopf", "mobius", "hotspots", "canon", "aperiodic")


def seed_for(base_seed: int, page_index: int) -> int:
    h = hashlib.sha256(f"{VERSION}:{base_seed}:{page_index}".encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


def make_texture(
    page_index: int,
    seed: int = 17,
    profile: str = "light",
    protected_boxes_pt: Sequence[Tuple[float, float, float, float]] = (),
    wash_mode: str = "none",
) -> Image.Image:
    if profile not in PROFILES:
        raise ValueError(f"Unknown vellum profile: {profile}")
    if wash_mode not in WASH_MODES:
        raise ValueError(f"Unknown shader wash_mode: {wash_mode}")

    w_px = int(round(PW * SCALE))
    h_px = int(round(PH * SCALE))
    rng = np.random.default_rng(seed_for(seed, page_index))

    yy, xx = np.mgrid[0:h_px, 0:w_px].astype(np.float32)
    nx = xx / max(1.0, w_px - 1)
    ny = yy / max(1.0, h_px - 1)

    p1 = float(rng.uniform(0, 6.283))
    p2 = float(rng.uniform(0, 6.283))
    wave = (
        0.50 * np.sin(2.3 * np.pi * nx + p1) * np.cos(1.9 * np.pi * ny + p2)
        + 0.30 * np.cos(4.1 * np.pi * (nx + 0.6 * ny) - p1)
        + 0.20 * np.sin(5.7 * np.pi * (ny - 0.4 * nx) + p2)
    )
    edge_dist = np.minimum(np.minimum(nx, 1.0 - nx), np.minimum(ny, 1.0 - ny))
    vignette = np.clip((0.16 - edge_dist) / 0.16, 0.0, 1.0) ** 1.6

    if profile == "light":
        strength = 0.032 * (0.5 + 0.5 * wave) + 0.048 * vignette
    else:
        grain = rng.normal(0.0, 0.016, size=(h_px, w_px)).astype(np.float32)
        strength = np.clip(0.064 * (0.5 + 0.5 * wave) + 0.095 * vignette + grain, 0.0, 0.22)

    if protected_boxes_pt:
        mask = np.ones((h_px, w_px), dtype=np.float32)
        for (x0, y0, x1, y1) in protected_boxes_pt:
            px0 = max(0, int((x0 - PADDING_PT) * SCALE))
            px1 = min(w_px, int((x1 + PADDING_PT) * SCALE))
            py0 = max(0, int((PH - y1 - PADDING_PT) * SCALE))
            py1 = min(h_px, int((PH - y0 + PADDING_PT) * SCALE))
            mask[py0:py1, px0:px1] = 0.26
        mask = gaussian_filter(mask, sigma=22.0)
        strength = strength * mask

    warm_sh = np.zeros((h_px, w_px), dtype=np.float32)
    cool_sh = np.zeros((h_px, w_px), dtype=np.float32)
    if wash_mode != "none":
        gain = 0.095 if profile == "light" else 0.135
        if wash_mode == "hopf":
            w_raw, c_raw = hopf_vellum_field(nx, ny)
        elif wash_mode == "mobius":
            w_raw, c_raw = mobius_vellum_field(nx, ny)
        elif wash_mode == "hotspots":
            w_raw, c_raw = hotspots_vellum_field(nx, ny)
        elif wash_mode == "canon":
            w_raw, c_raw = canon_vellum_field(nx, ny)
        else:
            w_raw, c_raw = aperiodic_vellum_field(nx, ny)

        art_band = np.clip((ny - 0.13) / 0.06, 0.0, 1.0) * np.clip((0.79 - ny) / 0.06, 0.0, 1.0)
        warm_sh = gain * w_raw * art_band
        cool_sh = (0.85 * gain) * c_raw * art_band

    rgb_arr = np.zeros((h_px, w_px, 3), dtype=np.uint8)
    total_w = np.clip(strength + warm_sh + cool_sh, 0.0, 0.28)
    paper_w = 1.0 - total_w
    for ch in range(3):
        val = (
            PAPER[ch] * paper_w
            + PIGMENT[ch] * strength
            + RUBRIC_WASH[ch] * warm_sh
            + SLATE_WASH[ch] * cool_sh
        )
        rgb_arr[:, :, ch] = np.clip(np.round(val), 0, 255).astype(np.uint8)
    return Image.fromarray(rgb_arr, mode="RGB")


def export_wash_png(out_png: Path, wash_mode: str, seed: int = 17, profile: str = "full") -> Path:
    """Exports a standalone 96-dpi (`672 x 960 px`) mathematical vellum wash sheet."""
    img = make_texture(page_index=0, seed=seed, profile=profile, protected_boxes_pt=(), wash_mode=wash_mode)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, format="PNG", dpi=(DPI, DPI), optimize=True)
    return out_png


def _background_pdf_page(img: Image.Image):
    png_buf = io.BytesIO()
    img.save(png_buf, format="PNG", optimize=True)
    png_buf.seek(0)

    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=(PW, PH))
    c.drawImage(ImageReader(png_buf), 0, 0, width=PW, height=PH, mask=None)
    c.showPage()
    c.save()
    pdf_buf.seek(0)
    return PdfReader(pdf_buf).pages[0]


def apply(
    input_pdf: Path,
    output_pdf: Path,
    seed: int = 17,
    profile: str = "light",
    page_wash_map: Optional[Dict[int, str]] = None,
) -> None:
    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()
    wash_lookup = page_wash_map or {}

    default_protected = [(44.0, 52.0, PW - 44.0, PH - 52.0)]
    for idx, fg_page in enumerate(reader.pages):
        has_content = bool(fg_page.extract_text().strip()) or ("/Resources" in fg_page and "/XObject" in fg_page["/Resources"])
        w_mode = wash_lookup.get(idx, "none")
        tex = make_texture(
            idx,
            seed=seed,
            profile=profile,
            protected_boxes_pt=default_protected if has_content else (),
            wash_mode=w_mode,
        )
        # Attach the page first so pypdf can replace its content stream.
        bg_page = writer.add_page(_background_pdf_page(tex))
        bg_page.merge_page(fg_page)

    meta = dict(reader.metadata or {})
    meta["/Subject"] = f"{STAMP}:{profile}:seed={seed}"
    writer.add_metadata(meta)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pdf, "wb") as f:
        writer.write(f)


def main() -> None:
    ap = argparse.ArgumentParser(description="Apply deterministic Codex vellum finishing.")
    ap.add_argument("input_pdf", type=Path)
    ap.add_argument("output_pdf", type=Path)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--profile", choices=PROFILES, default="light")
    args = ap.parse_args()
    apply(args.input_pdf, args.output_pdf, seed=args.seed, profile=args.profile)


if __name__ == "__main__":
    main()
