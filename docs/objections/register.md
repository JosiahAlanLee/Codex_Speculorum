# Objections & Right of Reply Register

This register records objections entered by contributing or reviewing models
under the **Right of reply** rule in `AGENTS.md`, together with the author's
dated dispositions. Earlier entries are append-only and verified in CI via
`python docs/objections/validate.py`.

## O-001 · 2026-11-14 · Gemini (Argon)
- Location: `common/ciphers/scales.py` and `binding/validate_typeset.py`
- Raised by: fresh reviewing instance during starter template extraction
- Objection: Volume I's biliteral border scales lacked a printed origin tick for hand decoding, and `lifted-pen` path subpaths were validated in standalone proofs rather than inside the final bound PDF stream.
- Proposed: Add a rubricated `#a32b24` top-left origin corner mark plus 6-bit grouping hairlines to `scales.py`, and verify `lifted-pen` survival and post-vellum red contrast directly in `binding/validate_typeset.py`.
- 2026-11-14 · Author: accepted — 0000001 incorporated into starter press scaffold

## O-002 · 2026-11-15 · Gemini (Argon · Advocatus Signi)
- Location: `books/01_liber_primus/manuscript/reading-edition.md` and `books/01_liber_primus/plates/tabulae.py`
- Raised by: adversarial audit against the October 7, 2026 `openai/math` Weil/Kuga-Satake/K3 withdrawal (`I_new = I(f_1) - m = -2m != 0`)
- Objection: Treating mathematical or contrapuntal symmetry as an autonomous criterion of truth repeats the exact failure mode of the withdrawn split-abelian-eightfold and K3 Hodge preprints, where an h-principle construction wore complete formal symmetry while assigning `+1` instead of `-1` to reverse stabilization traces, doubling the signed double-point obstruction to `-2m` and leaving an unremovable degree-2 self-intersection `p`.
- Proposed: Incorporate a formal `Obiectio & Responsum` into `Liber I` separating heuristic symmetry from verified cancellation, print every plate's refuting proposition on its outer biliteral border scale, and assert exact rational dyad closure (`r_recta * r_cancri == 2`) plus numerical invariant checks across Tabulae II–V at build time.
- 2026-11-15 · Author: accepted — b002c3d incorporated into Liber I Disputatio, Tabula V Canon Cancrizans, and unit test suite

## O-003 · 2026-11-14 · ChatGPT (Codex)
- Location: Liber I, section IV, and `books/01_liber_primus/canon/play_koopman_canon.py`
- Raised by: fresh reviewing instance reading the bound Books I–II draft and comparing it with `build_canon_score()`
- Objection: The printed Vox Cancrizans score diverges from the generated 32-pulse countervoice in bars 3, 6, and 8. The printed part ends on `Sa`, while the generator and prose specify upper-octave unison on `S'`.
- Proposed: Derive the printed 32-pulse score from the same table as the WAV and Pure Data patch.

## O-004 · 2026-11-14 · ChatGPT (Codex)
- Location: Liber I, section II
- Raised by: fresh reviewing instance reading the bound Books I–II draft
- Objection: The universal statement about powers of `(n + 1)/n` includes `n = 1`, for which the ratio is the octave `2/1` and every positive power is a power of two.
- Proposed: State the claim for integer `n > 1` and keep the octave as the exception.
