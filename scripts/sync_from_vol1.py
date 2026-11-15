#!/usr/bin/env python3
"""
Syncs licensed typeface binaries (`common/fonts/` + `common/fonts/licenses/`) and
optionally verifies or imports `common/illustrations/guilloche.py` from a local
checkout of Volume I (`JosiahAlanLee/Codex-Intervallorum`).

Supports dry-run verification (`--check`) and copy execution (`--apply`).
"""

import argparse
import hashlib
from pathlib import Path
import shutil
import sys

REPO = Path(__file__).resolve().parents[1]
VOL1_GUILLOCHE_SHA256 = "e4a28ec0de2a1b274160ddbc2bb6b51b77cb8b8a4f528f4099c3ca6306a0eb00"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sync(vol1_dir: Path, apply_changes: bool = False, import_guilloche: bool = False) -> int:
    if not vol1_dir.is_dir():
        print(f"[sync_from_vol1] Volume I directory not found: {vol1_dir}", file=sys.stderr)
        return 1

    src_fonts = vol1_dir / "common" / "fonts"
    dst_fonts = REPO / "common" / "fonts"
    copied = 0
    found = 0

    if src_fonts.is_dir():
        for item in sorted(src_fonts.rglob("*")):
            if item.is_file():
                found += 1
                rel = item.relative_to(src_fonts)
                target = dst_fonts / rel
                if apply_changes:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
                    copied += 1
                else:
                    print(f"  [dry-run] Would copy common/fonts/{rel}")
    else:
        print(f"[sync_from_vol1] Warning: {src_fonts} not present in Volume I path.")

    src_guilloche = vol1_dir / "common" / "illustrations" / "guilloche.py"
    if src_guilloche.is_file():
        digest = sha256(src_guilloche)
        match_note = "matches canonical Vol. I SHA-256" if digest == VOL1_GUILLOCHE_SHA256 else f"SHA-256={digest[:12]}..."
        print(f"  [guilloche] Found Volume I guilloche.py ({match_note})")
        if apply_changes and import_guilloche:
            shutil.copy2(src_guilloche, REPO / "common" / "illustrations" / "guilloche.py")

    mode = "Applied" if apply_changes else "Checked (dry-run)"
    print(f"[sync_from_vol1] {mode}: {found} font/license files discovered, {copied} copied.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync licensed fonts from local Codex-Intervallorum clone.")
    ap.add_argument("--vol1", type=Path, required=True, help="Path to local Codex-Intervallorum checkout")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Dry-run check (default)")
    group.add_argument("--apply", action="store_true", help="Copy files into this template")
    ap.add_argument("--import-guilloche", action="store_true", help="Also overwrite guilloche.py from Volume I")
    args = ap.parse_args()
    return sync(args.vol1.resolve(), apply_changes=args.apply, import_guilloche=args.import_guilloche)


if __name__ == "__main__":
    sys.exit(main())
