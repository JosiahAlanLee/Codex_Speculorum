# Liber IV · Testis Unicus, or Of the Sentence That Counts Its Own Absence

## I · Colloquium sub Gradu Decimo Nono: The Logician of Brünn and the Blind Scholiast

[F] Scene: A narrow cellar stair beneath a municipal library in Buenos Aires, lit by a
single green-shaded lamp. On the table lie a brass astrolabe divided into sixteen prime
sectors (`2, 3, 5, …, 53`) and an eight-by-eight abacus of boxwood counters. SCHOLIASTES
turns the outer ring of the astrolabe by touch; LOGOTHETA writes integer exponents in a
pocket ledger with a sharp pencil, numbering each speech as soon as it is spoken.

SCHOLIASTES: Why does your pencil scratch after every sentence I utter, Herr Doktor? It is
bad enough that the upstairs shelves drown every true book under ten thousand commentaries,
refutations, and counterfeit twins. Do not tell me you are manufacturing a commentary upon
our conversation before we have even finished having it.

LOGOTHETA: Not a commentary, Señor—an integer. To our first exchange I assign the prime 2,
to this second the prime 3, to the next 5, and so onward to the eighth prime, 19. Raise each
prime to the code of the words spoken at its turn and multiply them together: our entire
cellar dialogue collapses into one natural number N, no more ambiguous than a pebble.

SCHOLIASTES: A dreadful economy! Yet if a dialogue is merely a number, and a proof is merely
another number that divides or satisfies a polynomial equation, then I know what poisons
arithmetic just as it poisons my Library: *multiplicity*. For fifty years your Russian
colleagues have encoded halting machines as Diophantine polynomials, yet whenever a statement
is true, the equation spills forth swarms of auxiliary witnesses—redundant proofs echoing down
the galleries! Purge the duplicates, I say! Let a Sovereign Censor decree that every equation
on the shelves may possess *at most one* natural-number witness: either a single solitary
stone in the hand, or silence. Surely uniqueness restores order and lets us decide truth!

LOGOTHETA: You have just stated Yuri Matiyasevich's Single-Fold Conjecture of 1974—and walked
straight into its trap. Suppose the Censor grants your wish completely. Every recursively
enumerable set—every halting catalogue, every theorem-proving ledger—is rewritten as an
integer polynomial P(x, y₁, …, y_m) = 0 that admits *exactly one* natural-number witness tuple
for members and *none* for nonmembers. Have you tamed undecidability?

SCHOLIASTES: How could chaos survive when every true proposition has one unique certificate
and never a second?

LOGOTHETA: Slide your fingers down the rubricated diagonal of the eight-by-eight abacus on
this table—and turn to `Tabula VIII`, which is already engraving our eight exchanges. Eight
catalogue rows list whether the k-th polynomial vanishes on input k; below the frame sits the
inverted anti-diagonal register Δ_k = 1 − M[k, k], flipping every diagonal stone into an empty
crosshair and every crosshair into a stone. Ask your Censor to shelve Δ as the g-th row of his
own catalogue. He cannot: at column g the new row would have to disagree with itself. The
inverted rule is a perfectly good predicate, and it stands outside every catalogue built
from the rows it inverts. That is the whole of the diagonal, and it needs no stone to speak.

SCHOLIASTES: Then the Censor's uniqueness decree has not closed the catalogue—it has only
thinned it. But surely a thinned catalogue is at last decidable? With one chair per equation,
the machine need only look to see whether the chair is filled!

LOGOTHETA: Take the one ledger you already know no machine can finish: the halting catalogue,
which lists every program that ever stops. Your Censor's decree, granted in full, hands that
ledger a polynomial with exactly one chair per halting program and no chair at all for the
rest. Now set your machine to decide, for any equation that is promised at most one chair,
whether the chair is filled. Feed it the halting polynomial, program by program. It would
decide the halting catalogue. The promise of uniqueness is kept to the letter, and
undecidability walks straight through it, because nothing in the promise says how far down
the stair the single chair may stand. Worse still for your mirrors, Señor: at this, our eighth
turn—under prime 19, which shifts the cipher caption beneath `Tabula VIII` ("THIS CAPTION HAS
NO SECOND WITNESS")—you might hope that the hierarchy of unsolvable problems at least reflects
itself in a Crab Canon like `Liber I`, swapping one oracle degree with a twin. It does not. Every order-preserving symmetry of the
Turing degrees is the identity. At the summit of unsolvability, the mirror shows only one face,
and it cannot be reversed.

## II · Expositio Scholastica: Single-Fold Diophantine Equations and Turing Rigidity

[D] In 1931 Kurt Gödel arithmetized formal syntax via prime-power coding to construct
self-referential arithmetic propositions undecidable within any consistent recursively
axiomatized extension of elementary arithmetic ([IV/S1]). Four decades later, the
Davis–Putnam–Robinson–Matiyasevich (DPRM) theorem completed Gödel's bridge by resolving
Hilbert's Tenth Problem negatively: every recursively enumerable relation S in ℕⁿ admits a
polynomial P(x, y₁, …, y_m) over ℤ such that x belongs to S if and only if P(x, y) = 0 has
at least one solution y in ℕᵐ ([IV/S2]).

[D] Classical DPRM encodings rely on Pell equations x² − (a² − 1)y² = 1 to simulate
exponential computation histories, often admitting infinitely many or multiply-branched
witnesses when a computation can be padded. In 1974 Matiyasevich asked whether **single-fold**
polynomial representations always exist—eliminating all witness multiplicity ([IV/S3]).
Family 242 of the October 2026 OpenAI mathematical corpus (*Single-fold Diophantine
representations*, `SingleFold.lean`, [IV/S4]) settles the conjecture affirmatively in
machine-checked Lean:

> 1. Universal Single-Fold Representation: Every recursively enumerable subset S of Nⁿ
> (n ≥ 1) admits an integer polynomial P(x, y₁, …, y_m) that has **exactly one** complete
> natural-number witness tuple y in Nᵐ when x belongs to S, and **zero** solutions when x
> does not belong to S. This establishes both the single-fold and finite-fold Diophantine
> conjectures.

[E] The corpus's scope note states that the consequence below is *not* separately
formalized ([IV/S4]); this press derives it in one reduction. Let K be the halting set and
P_K its single-fold polynomial from (1). For every x the equation P_K(x, y) = 0 has at
most one solution, so every instance satisfies the at-most-one-solution promise. A decision
procedure for solvability under that promise, applied to P_K(x, ·), would decide membership
in K. Hence:

> 2. Undecidability Under a Uniqueness Promise: Deciding whether a polynomial Diophantine
> equation over N has a solution remains algorithmically undecidable even under the promise
> that it possesses **at most one** solution.

[D] Right beside Family 242 in the corpus stands Family 241 (`DegreeRigidity.lean`, *Rigidity
of the Turing degrees*, [IV/S5]), resolving the Slaman–Woodin rigidity problem: every order
automorphism of the full partial order (D, ≤_T) of Turing degrees of subsets of ℕ is the
identity map, requiring neither definability nor genericity hypotheses.

[H] Read together across *Codex Speculorum*, Families 242 and 241 close the philosophical arc
opened in `Liber I`: whereas musical scales (`Liber I`), planar lattices (`Liber II`), and
symmetric cavities (`Liber III`) admit rich involutions, periods, or dualities, the global map
of computability permits neither a decision algorithm under uniqueness nor a single nontrivial
relabeling symmetry.

## III · De Tabula Octava: Pell Hyperbolas, Cantor's Spine & the Rigid Poset

[E] How can a static pen-plotter sheet depict self-reference and single-fold witness geometry
without conflating finite illustration with infinite undecidability? `Tabula VIII` (*Speculum
Diophantinum*) separates what is finitely verified on the page from the asymptotic theorem it
signifies. Around the outer astrolabe ring stand the first sixteen primes (p = 2 through
p = 53), with rubric emphasis on p₈ = 19—the exact shift key of the plate's own `charakteres`
inscription.

[V] Inside the astrolabe, four lunette sheaves of Pell–Matiyasevich hyperbolas frame an
eight-by-eight predicate matrix M whose diagonal spine M[k, k] is inverted cell-for-cell into
the detached register Δ_k = 1 − M[k, k] below, demonstrating visually and programmatically
that Δ differs from every catalogued row r at column r. Four corner medallions contrast
multi-fold DPRM fibers (≥ 2 witnesses on a vertical fiber) against Family 242's single-fold
projection (≤ 1 witness per fiber, verified on Cantor's polynomial pairing), a Quine fixed-point
lemniscate, and a seven-element Hasse diagram verified by exhaustive 7! permutation search to
have trivial automorphism group Aut = {id} ([IV/S5]).

[PLATE: tabula_viii]

## IV · Criterion Falsificationis & Canon Quineanus

[E] In sound and modular synthesis, `Liber IV` corresponds to a self-describing byte-canon
whose eight-bit control word encodes its own step rule while flipping the diagonal bit at
each pass—generating a sequence that can verify any proposed witness halt in finite time yet
can never pre-compute all silent steps ahead of performance.

[V] What observation would refute `Liber IV` and overturn `Tabula VIII`? Either exhibiting a
recursively enumerable subset S of ℕⁿ that provably admits no single-fold integer polynomial
representation (refuting Family 242, [IV/S4]), or exhibiting a non-identity bijection of the
Turing degrees preserving ≤_T in both directions (refuting Family 241, [IV/S5]). The primary
refuting proposition—SOME ENUMERABLE SET LACKS A SINGLE FOLD POLYNOMIAL—runs clockwise around
the outer biliteral tick-scale of `Tabula VIII` from its rubricated corner mark.
