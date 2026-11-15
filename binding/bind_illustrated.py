#!/usr/bin/env python3
"""
Assembles the ungrounded vector omnibus and finishes it through `binding/vellum.py`
(dynamically mapping every book's `out/plates-map.json` plate leaves to their
paired 96-dpi `hopf`, `mobius`, `hotspots`, `canon`, and `aperiodic` washes)
to produce `binding/out/illustrated/<slug>_illustrated.pdf`.
"""

import argparse
import json
from pathlib import Path
import tempfile
from typing import Dict

from binding import bind, vellum

REPO = Path(__file__).resolve().parents[1]


def _shader_wash_map_from_log(log_data: Dict) -> Dict[int, str]:
    wash_map: Dict[int, str] = {}
    for b in log_data.get("books", []):
        bid = b.get("id", "")
        plates_manifest = REPO / "books" / bid / "out" / "plates-map.json"
        if not plates_manifest.is_file():
            continue
        pmeta = json.loads(plates_manifest.read_text(encoding="utf-8"))
        pmap = b.get("body_page_map", {})
        for info in pmeta.values():
            leaf_str = str(info["leaf"])
            w_mode = info.get("wash", "none")
            if leaf_str in pmap and w_mode != "none":
                wash_map[int(pmap[leaf_str]) - 1] = w_mode
    return wash_map


def build_illustrated(vellum_profile: str = "light", seed: int = 17) -> Path:
    vol = json.loads((REPO / "volume.json").read_text(encoding="utf-8"))
    out_dir = REPO / "binding" / "out" / "illustrated"
    out_dir.mkdir(parents=True, exist_ok=True)
    final_pdf = out_dir / f"{vol['slug']}_illustrated.pdf"

    with tempfile.TemporaryDirectory() as tmp:
        raw_vec_pdf = Path(tmp) / "raw_illustrated.pdf"
        bind.bind_edition(edition="illustrated", out_pdf=raw_vec_pdf, paint_ground=False)
        log_text = (Path(tmp) / "binding-log.json").read_text(encoding="utf-8")
        (out_dir / "binding-log.json").write_text(log_text, encoding="utf-8")
        wash_map = _shader_wash_map_from_log(json.loads(log_text))
        vellum.apply(raw_vec_pdf, final_pdf, seed=seed, profile=vellum_profile, page_wash_map=wash_map)

    print(f"[bind_illustrated] Wrote {final_pdf.relative_to(REPO)} (vellum={vellum_profile}, shader_washes={len(wash_map)})")
    return final_pdf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vellum-profile", choices=vellum.PROFILES, default="light")
    ap.add_argument("--seed", type=int, default=17)
    args = ap.parse_args()
    build_illustrated(vellum_profile=args.vellum_profile, seed=args.seed)


if __name__ == "__main__":
    main()
