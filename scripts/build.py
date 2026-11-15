#!/usr/bin/env python3
"""
Master deterministic build & verification orchestrator matching Codex-Intervallorum CLI:
  python3 scripts/build.py [--edition {all,reading,illustrated}] [--skip-tests] [--vellum-profile {light,full}]
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(cmd: list) -> None:
    res = subprocess.run(cmd, cwd=str(REPO))
    if res.returncode != 0:
        sys.exit(res.returncode)


def run_tests() -> None:
    for test_dir in (
        "common/illum/tests",
        "common/illustrations/tests",
        "binding/tests",
        "docs/objections/tests",
    ):
        run([PY, "-m", "unittest", "discover", "-s", test_dir, "-p", "test_*.py", "-v"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Build and validate Codex volume editions.")
    ap.add_argument("--edition", choices=["all", "reading", "illustrated"], default="all")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--vellum-profile", choices=["light", "full"], default="light")
    args = ap.parse_args()

    # ReportLab includes timestamps in the component PDFs and their document IDs.
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    run([PY, "scripts/check_project.py"])

    vol = json.loads((REPO / "volume.json").read_text(encoding="utf-8"))
    slug = vol["slug"]

    # 1. Build component books declared in volume.json
    for book in vol["books"]:
        build_script = REPO / "books" / book["id"] / "build.py"
        run([PY, str(build_script)])

    # 2. Run unit tests unless skipped
    if not args.skip_tests:
        run_tests()

    # 3. Assemble and validate Reading edition
    if args.edition in ("all", "reading"):
        run([PY, "-m", "binding.bind"])
        run([PY, "-m", "binding.validate", f"binding/out/{slug}_reading.pdf"])

    # 4. Assemble, vellum-finish, and validate Illustrated edition
    if args.edition in ("all", "illustrated"):
        run([PY, "-m", "binding.bind_illustrated", "--vellum-profile", args.vellum_profile])
        run([PY, "-m", "binding.validate", f"binding/out/illustrated/{slug}_illustrated.pdf"])

    # 5. Final post-build check
    run([PY, "scripts/check_project.py", "--built", "--edition", args.edition])
    print(f"[build] Completed edition={args.edition} (vellum={args.vellum_profile}) successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
