#!/usr/bin/env python3
"""
Validates the append-only Right of Reply register (`docs/objections/register.md`).
Preserves the exact entry, required-field, disposition, and --base immutability
grammar from JosiahAlanLee/Codex-Intervallorum.
"""

import argparse
from datetime import date
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]
DEFAULT_REGISTER = REPO / "docs" / "objections" / "register.md"

ENTRY_RE = re.compile(r"^## (O-(\d{3,})) · (\d{4}-\d{2}-\d{2}) · (\S.*)$")
FIELD_RE = re.compile(r"^- (Location|Raised by|Objection|Proposed): (.*)$")
EVENT_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) · (Author|Objector|Note): (.*)$")
DASH_SPLIT_RE = re.compile(r"\s+(?:—|–|--?)\s+")
PR_OR_HASH_RE = re.compile(r"(?:#\d+|\b[0-9a-f]{7,40}\b)")

REQUIRED = ("Location", "Raised by", "Objection")


def _valid_iso_date(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def parse_register(text: str) -> List[Dict]:
    lines = text.splitlines()
    entries: List[Dict] = []
    cur: Optional[Dict] = None

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped:
            continue

        m_entry = ENTRY_RE.match(raw)
        if m_entry:
            if cur is not None:
                entries.append(cur)
            oid, num_s, d_str, model = m_entry.groups()
            if not _valid_iso_date(d_str):
                raise ValueError(f"Line {lineno}: invalid ISO date '{d_str}' in heading {oid}.")
            expected_num = len(entries) + 1
            if int(num_s) != expected_num:
                raise ValueError(f"Line {lineno}: expected sequential O-{expected_num:03d}, got {oid}.")
            cur = {
                "id": oid,
                "date": d_str,
                "model": model,
                "fields": {},
                "events": [],
                "lineno": lineno,
            }
            continue

        if cur is None:
            # Introductory prose/headings above first ## O-001 entry are permitted
            if raw.startswith("## O-"):
                raise ValueError(f"Line {lineno}: malformed entry heading: {raw}")
            continue

        m_field = FIELD_RE.match(raw)
        if m_field:
            if cur["events"]:
                raise ValueError(f"Line {lineno}: field '{m_field.group(1)}' cannot appear after dated events in {cur['id']}.")
            fname, fval = m_field.groups()
            if fname in cur["fields"]:
                raise ValueError(f"Line {lineno}: duplicate field '{fname}' in {cur['id']}.")
            if not fval.strip():
                raise ValueError(f"Line {lineno}: empty field '{fname}' in {cur['id']}.")
            cur["fields"][fname] = fval.strip()
            continue

        m_event = EVENT_RE.match(raw)
        if m_event:
            ev_date, actor, body = m_event.groups()
            if not _valid_iso_date(ev_date):
                raise ValueError(f"Line {lineno}: invalid event date '{ev_date}' in {cur['id']}.")
            body = body.strip()
            if not body:
                raise ValueError(f"Line {lineno}: empty {actor} event in {cur['id']}.")

            if actor == "Author":
                parts = DASH_SPLIT_RE.split(body, maxsplit=1)
                if len(parts) != 2 or parts[0] not in ("accepted", "overruled", "deferred") or not parts[1].strip():
                    raise ValueError(
                        f"Line {lineno}: Author event in {cur['id']} must be "
                        "'accepted|overruled|deferred — <detail>'."
                    )
                verb, detail = parts[0], parts[1].strip()
                if verb == "accepted" and not PR_OR_HASH_RE.search(detail):
                    raise ValueError(f"Line {lineno}: 'accepted' in {cur['id']} requires a PR (#N) or 7-40 char commit hash.")
                if verb == "overruled":
                    if "Given:" not in detail:
                        raise ValueError(f"Line {lineno}: 'overruled' in {cur['id']} must include 'Given: <location>'.")
                    before_given, after_given = detail.split("Given:", 1)
                    if len(before_given.strip().split()) < 3 or not after_given.strip():
                        raise ValueError(
                            f"Line {lineno}: 'overruled' in {cur['id']} needs >=3 words of reason before 'Given:' and a location after."
                        )
            elif actor == "Objector":
                parts = DASH_SPLIT_RE.split(body, maxsplit=1)
                if len(parts) != 2 or parts[0] != "withdrawn" or not parts[1].strip():
                    raise ValueError(f"Line {lineno}: Objector event in {cur['id']} must be 'withdrawn — <reason>'.")

            cur["events"].append({"date": ev_date, "actor": actor, "body": body})
            continue

        raise ValueError(f"Line {lineno}: unrecognized line inside {cur['id']}: {raw}")

    if cur is not None:
        entries.append(cur)

    for entry in entries:
        for req in REQUIRED:
            if req not in entry["fields"]:
                raise ValueError(f"Entry {entry['id']} missing required field '{req}'.")

    return entries


def status(entry: Dict) -> str:
    state = "open"
    for ev in entry["events"]:
        if ev["actor"] in ("Author", "Objector"):
            state = DASH_SPLIT_RE.split(ev["body"], maxsplit=1)[0]
    return state


def append_only(base_text: str, head_text: str) -> None:
    """Verifies every non-empty line from the first entry heading onward in base survives in order in head."""
    def tail_from_first_entry(txt: str) -> List[str]:
        ls = txt.splitlines()
        for idx, line in enumerate(ls):
            if ENTRY_RE.match(line):
                return [l for l in ls[idx:] if l.strip()]
        return []

    base_lines = tail_from_first_entry(base_text)
    head_lines = tail_from_first_entry(head_text)
    h_idx = 0
    for b_line in base_lines:
        while h_idx < len(head_lines) and head_lines[h_idx] != b_line:
            h_idx += 1
        if h_idx == len(head_lines):
            raise ValueError(f"Append-only violation: historical line removed or altered: {b_line}")
        h_idx += 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Right of Reply register.")
    ap.add_argument("register", nargs="?", default=str(DEFAULT_REGISTER))
    ap.add_argument("--base", help="Earlier register.md path to verify append-only history")
    args = ap.parse_args(argv)

    reg_path = Path(args.register)
    head_text = reg_path.read_text(encoding="utf-8")
    entries = parse_register(head_text)
    if args.base:
        base_text = Path(args.base).read_text(encoding="utf-8")
        parse_register(base_text)
        append_only(base_text, head_text)

    summary = ", ".join(f"{e['id']}={status(e)}" for e in entries) or "empty"
    print(f"[objections] OK ({len(entries)} entries: {summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
