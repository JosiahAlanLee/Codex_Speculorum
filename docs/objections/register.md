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
- 2026-11-15 · Author: accepted — b5dc318 prints the Liber I score from build_canon_score() (bars 3, 6, 8 corrected, close on S'); binding/tests/test_manuscript_claims.py now fails the build if the printed block and the generator diverge

## O-004 · 2026-11-14 · ChatGPT (Codex)
- Location: Liber I, section II
- Raised by: fresh reviewing instance reading the bound Books I–II draft
- Objection: The universal statement about powers of `(n + 1)/n` includes `n = 1`, for which the ratio is the octave `2/1` and every positive power is a power of two.
- Proposed: State the claim for integer `n > 1` and keep the octave as the exception.
- 2026-11-15 · Author: accepted — b5dc318 restricts the claim to n > 1 in Liber I §II and in the closing Quaestio, naming the octave 2/1 as the lone superparticular that closes

## O-005 · 2026-11-15 · ChatGPT (Codex)
- Location: Liber III, section III, and `solve_viol_acoustic_resonator()` in `common/illustrations/shader_plates.py`
- Raised by: fresh reviewing instance comparing the bound draft with the shipped solver
- Objection: Section III gives 4,603 nodes and a frequency ratio of 2.0004. The default solver returns 3,946 active grid nodes and a ratio of approximately 1.997325.
- Proposed: Derive the reported node count and ratio from the solver, or specify the discretization that reproduces the printed values.
- 2026-11-15 · Author: accepted — b5dc318 reports the default solver's 3,946 nodes and √(μ₃/μ₂) = 1.9973 (plate rail rounds to 2.00×); test_manuscript_claims.py holds the prose to solve_viol_acoustic_resonator()

## O-006 · 2026-11-15 · ChatGPT (Codex)
- Location: Liber III, section IV
- Raised by: fresh reviewing instance reading the bound draft
- Objection: The claimed octave isolation places a damper at the fundamental's pressure nodes. In a model with point coupling through pressure amplitude, the damping contribution for that mode scales with the squared amplitude at the contact and vanishes at the node. The numerical solve computes Neumann modes of the undamped cavity.
- Proposed: Specify the damping mechanism and test its coupling to each mode before claiming complete suppression of the fundamental and isolation of the octave.
- 2026-11-15 · Author: accepted — b5dc318 retags §IV [H] under an explicit point-coupling model and corrects the rule: u₂ is the longitudinal dipole and u₃ the transverse one, so poles (|u₃| < 0.01) are u₂ ports and waist-rim endpoints (|u₂| < 0.05, |u₃| ≈ 0.6) are u₃ ports; a waist damper suppresses u₃, not the fundamental; the undamped-modes caveat and a refuting measurement are stated

## O-007 · 2026-11-15 · ChatGPT (Codex)
- Location: Liber IV, sections I–II
- Raised by: fresh reviewing instance reading the bound draft
- Objection: The dialogue assumes the anti-diagonal rule has an index `g` among the polynomial witness predicates. With that assumption, the `g`-th diagonal entry would equal its own negation. A syntactic Gödel number for the formula by itself supplies a code for the formula, and a Diophantine representation requires a separate argument.
- Proposed: Let the anti-diagonal foil show why an inverted predicate falls outside the catalogue. Establish undecidability under the uniqueness promise by reducing membership in an undecidable recursively enumerable set to existence of its single-fold witness.
- 2026-11-15 · Author: accepted — b5dc318 drops the self-substitution of a Gödel number into a Diophantine predicate; the dialogue now shows the inverted row falls outside the catalogue, and undecidability under the uniqueness promise is proved by reduction from the halting set's single-fold polynomial, marked in §II as the press's corollary since lean/docs/242.md states it is not separately formalized

## O-008 · 2026-11-15 · Claude (Fable 5.1)
- Location: `books/01_liber_primus/manuscript/reading-edition.md` §III–IV, `books/04_liber_quartus/manuscript/reading-edition.md` §II, and `bibliography-records.json` (I/S4, III/S3, I/S6, IV/S4)
- Raised by: reviewing instance reading the bound Books I–IV draft against github.com/openai/math (lean/docs/369.md, 155.md, 242.md, 241.md, history.md) and arXiv:2610.30976
- Objection: (1) Liber I §IV claims thirty "thirds, fourths, and fifths (6:5, 5:4, 4:3, 3:2)"; the generator's vertical dyad set is exactly 1:1, 6:5, 5:4, 4:3 and no 3:2 occurs. (2) Liber I §III and I/S4 cite the Family 369 comparator as `StrictHotSpots.lean`; the file is `HotSpots.lean`, and I/S4 and III/S3 were two records for one source. (3) Liber IV §II presents both Family 242 propositions as settled "in machine-checked Lean"; the corpus scope note says the at-most-one-solution undecidability consequence is not separately formalized. (4) I/S6 omitted its authors (Lekili & Sheridan) and cited a Section 3.2 the inspection did not cover; the paper traces the error to a sign-convention mismatch, which is a slightly different moral than a bare plus-for-minus.
- Proposed: State the dyad set the score actually realizes; cite `HotSpots.lean` and merge I/S4 with III/S3; tag the Family 242 corollary as the press's own derivation; credit Lekili & Sheridan and describe the convention mismatch in the inspection note.
- 2026-11-15 · Author: accepted — b5dc318 incorporated in Liber I §III–IV, Liber IV §II, and bibliography-records.json
