# Repository Working Rules & Right of Reply

This volume belongs to the *Codex* series initiated in `Codex-Intervallorum`
(Volume I, October 2026). It pairs invented parables, procedural A4/7×10 plates,
and domain-isomorphic ciphers with explicit source accounts.

## 1. Epistemic Routing & Direct Statement

Every analytical claim in a reading manuscript carries an explicit tag defined
in the opening *Clavis*:

- `[E]` — Direct empirical observation or verified mathematical computation.
- `[D]` — Documented primary or archival source, inspected at the cited pages.
- `[H]` — Bounded hypothesis or model; states what observation counts against it.
- `[V]` — Adopted normative commitment (or explicitly declined; do not leave
  central commitments in indefinite committee review).
- `[F]` — Framed parable, worked workshop scene, or invented liturgical foil.

**Direct statement rule:** Introduce formal distinctions through a concrete `[F]`
scene first, state bounded claims positively rather than through repetitive
`"DOES NOT CLAIM"` disclaimers, and confine unfinished shelf-check accounting to
`bibliography-records.json` rather than body prose.

## 2. Right of Reply (`docs/objections/register.md`)

Before model-drafted or model-revised work is merged to `main` or bound into an
edition, the contributing or reviewing model reads the bound text and either:

1. Appends a structured objection in its own words to `docs/objections/register.md`, or
2. Records `"Right of reply: invited; no objection."` in the PR or review note.

Models operating without direct repository write access (e.g., Gemini / *Argon*)
may relay their entry verbatim through the author. An objection is not a veto;
it requires an explicit dated disposition (`accepted`, `overruled`, `deferred`,
or `withdrawn`). Earlier entries in `docs/objections/register.md` are never
deleted or rewritten, enforced in CI via:

```bash
python docs/objections/validate.py --base <earlier_register>
```

## 3. Native Plate & Cipher Invariants

- **No clipped PDF board mounts:** Every plate is drawn natively onto the shared
  `504 × 720 pt` (7 × 10 in) furniture (`#ede6d4` ground, `#161918` carbon ink,
  `#a32b24` rubric red) or exported as a clean two-layer A4 SVG.
- **Human-recoverable falsifier frames:** Biliteral border scales carry a single
  rubricated (`#a32b24`) corner origin tick and 6-bit grouping hairlines so a
  reader working from paper alone can locate bit 0 and decode the plate's
  falsifier.
- **Ground-sorted final seals:** Any multi-agent or lattice *Nota Clausa* field
  must emit strokes sorted strictly in `(y, x)` ground order so vector element
  ordering in SVG/PDF never leaks plaintext without the key.
