# Liber II · Bibliotheca Sine Periodo, or Of the Single Stone That Never Repeats

## I · Colloquium in Fornice Triplici: The Engraver of Leeuwarden and the Blind Keeper

[F] Scene: A low parapet encircling the ventilation shaft of an upper gallery. Four
walls of walnut shelves frame a central chasm through which lower and higher stories
descend and rise out of sight. SCULPTOR carries an inked pearwood block scored with
interlocking horsemen and a stepped ashlar template cut from boxwood; CUSTOS rests
one hand on the brass railing, counting courses by touch.

CUSTOS: You have climbed three nights without sleeping, Master Engraver, yet you
carry only one wooden mould. Even a blind cataloguer knows that a library built
from a single unrotated block must eventually repeat its own rooms. That is my sole
consolation in this abyss: walk far enough along any axis and disorder itself
recurs as the Order.

SCULPTOR: On a flat sheet of paper, Keeper, I used to share both your grief and
your consolation. In my workshop at Leeuwarden I carved birds, fishes, and horsemen
that lock together without ever turning the block—neither quarter-turn nor mirror
flip, pure sliding from left to right and bottom to top. Try as I might to make
a single unrotated figure wander forever on the plane, the paper always forced a
lattice upon me. Two independent steps, and the whole meadow repeated like damask.

CUSTOS: Then your chisel confirms my shelves. What holds on one floor must hold
across all floors: add a vertical shaft to your two corridors, and you merely add
a third period vector—so many galleries East, so many North, so many stories Up—after
which every bookcase and every stair stands again in its identical place.

SCULPTOR: Put your fingers into the notch of this boxwood stone before you bless
the third axis. On a flat floor of two coordinates, every tile spends both of its
directions merely closing its own perimeter; there is no spare room left to keep a
secret ledger. Give the mason a third coordinate—this vertical shaft between your
floors—and two axes can compute an unending carry-chain while the third axis slides
each corridor past its neighbour without leaving a pinhole of empty air.

CUSTOS: Wait—you are not turning the block? Every stone in the vault faces North
just as it left the mould?

SCULPTOR: Not a stone is rotated by a single degree, nor shaved, nor mirrored. Every
joint sits flush against its fellow; every cubic inch of mortar-space is filled
exactly once. Yet if your Eternal Traveler drops a plumb-line down this shaft and
paces off any candidate period—ten stories, a thousand, ten million—some corridor
further along the shear refuses to return to phase.

CUSTOS: Then the traveler's Order was never a law of space—it was only an artifact
of flat paper! We imagined only two fates for the Library: either lawless rubble,
or an infinite wallpaper condemned to recite the same shelf forever. You tell me
there is a third architecture: a house governed by a single rigid stone, lawful at
every seam, in which no three independent journeys ever bring the walker home.

SCULPTOR: Feel along the rubricated course beside your thumb, Keeper. On the left
medallion above the arch I have carved the flat floor of dimension two, where the
grid locks fast; on the right, the sheared strata of dimension three, where the
lattice breaks. The stone did not grow unruly when it entered space—space grew
wide enough to remember without repeating.

## II · Expositio Scholastica: The Sharp Threshold at Dimension Three

[D] The question debated at the shaft is the Periodic Tiling Conjecture for
translational monotiles: if a single finite subset T of the integer lattice ℤᵈ
(or a bounded measurable set in ℝᵈ) tiles the whole space by pure translations
T + A = ℤᵈ, must T admit at least one fully periodic tiling—that is, a placement
set A invariant under a finite-index subgroup P of ℤᵈ?

[D] Across the first two dimensions, the Engraver's planar experience is exact law.
In dimension d = 1, a finite window argument shows that every translational tiling
of ℤ is periodic. In dimension d = 2, Siddhartha Bhattacharya proved in 2020
that every finite subset of ℤ² admitting a translational tiling also admits a
fully periodic tiling ([II/S1]). When Rachel Greenfeld and Terence Tao subsequently
shattered the conjecture in 2022 by encoding p-adically structured functional
equations into translational matching rules, their counterexample required a
sufficiently high ambient dimension d ([II/S2]), leaving open where between the
plane and high-dimensional space periodic compulsion gives way.

[D] Family 155 of the October 2026 OpenAI mathematical corpus (PeriodicTilingThree.lean,
accompanying *A translational tile with no fully periodic tiling in dimension three*,
[II/S3]) resolves the threshold at the sharpest possible integer: dimension three.
The machine-checked Lean theorem (OAI.PeriodicTilingThree.periodic_tiling_counterexample_and_minimality,
[II/S3]) establishes two paired propositions:

> 1. Counterexample in Z³ and R³: There exists a nonempty finite subset T of
> Z³ that tiles Z³ bijectively ((t, a) ↦ t + a), yet no tiling set A
> for T is invariant under any finite-index subgroup P of Z³. Moreover, its
> unit-cube thickening K = T + [0, 1]³ tiles R³ almost everywhere while
> admitting no Euclidean fully periodic tiling under any real basis of R³.

> 2. Sharp Minimality: d = 3 is the least natural number d for which a finite
> translational tile of Zᵈ tiles without admitting any fully periodic tiling.

[H] Viewed beside Borges's closing conjecture in *La biblioteca de Babel* ([II/S4]),
Family 155 severs local uniformity from periodic recurrence at the exact dimension
of physical architecture: one floor (d = 2) forces a repeating lattice; a building
with stories (d = 3) does not.

## III · De Figura Fornicis: Weakly Sheared Courses vs. Forced Aperiodicity

[E] Epistemic precision requires distinguishing two ways non-periodicity enters a
three-dimensional vault. In Tabula VI (*Fornix Sine Periodo*), our cutaway
amphitheater engraves an explicit four-cube stepped voussoir T₀ = {(0,0,0), (1,0,0),
(1,0,1), (2,0,1)} translated across y-corridors by the non-periodic skew offsets
(Thue-Morse(y), Sturmian(y)). Programmatic verification confirms that every uncut
course partitions ℤ³ with zero gaps and zero overlaps, while hidden-surface
elimination on the isometric triangle lattice fuses coplanar voxel faces into solid
ashlar blocks and marks the skew-shear witness courses in #a32b24 rubric ink.

[V] Yet T₀ alone only *permits* non-periodicity: an uninspired mason could set
both shear sequences to zero and lay a periodic wall. What makes Family 155's finite
tile T in ℤ³ ([II/S3]) decisive is that its finite support acts as a rigid
combinatorial lock that outlaws the zero-shear choice altogether: any attempt
to impose three linearly independent period vectors v₁, v₂, v₃ forces two
translates T + a₁ and T + a₂ to collide.

[PLATE: tabula_vi]

## IV · Criterion Falsificationis & Canon Polymetricus

[E] Musically, the passage from d = 2 to d = 3 mirrors the passage from a closed
two-voice canon (Liber I, Tabula V) to a three-axis skew-product score in which
bar-lines lock locally along two voices while sliding along the third by a binary
carry sequence (popcount(y) mod 2) paired with an irrational Sturmian rotation
(⌊(y + 2)/φ⌋ − ⌊(y + 1)/φ⌋). Every local bar-joint resolves cleanly;
no global repeat sign ever encloses all three staves at once.

[V] What observation would refute Liber II and overturn Tabula VI? Exhibiting
either a planar finite tile T in ℤ² with a translational tiling and no periodic
tiling (contradicting [II/S1]), or exhibiting for Family 155's three-dimensional
tile T ([II/S3]) a valid tiling complement A in ℤ³ together with three
linearly independent integer period vectors v₁, v₂, v₃ satisfying A + vᵢ = A.
That exact refuting proposition—EVERY TRANSLATIONAL TILE IN THREE SPACE HAS A PERIOD—runs
clockwise around the outer biliteral tick-scale of Tabula VI from its red
corner mark.
