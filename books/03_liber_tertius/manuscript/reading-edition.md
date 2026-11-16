# Liber III · Cista Resonantiae, or Of the Sounding Rim Without an Interior Stillness

## I · Colloquium in Officina Sonorum: The Doctor of Wittenberg and the Blind Lutemaker

[F] Scene: A stone-walled lutemaker's cellar beneath an acoustic whispering dome. On the
workbench rest three instruments: an unpierced viol belly carved with deep inward C-bouts
and inlaid purfling, a twin belly pierced by two symmetric sound-holes, and a hollow
twelve-spiked bronze star cast as a three-dimensional chamber. CHLADNIUS holds a rosined
horsehair bow and a glass phial of white Elbe quartz sand; LUTIFEX tests the unpierced
spruce belly with his fingertips, listening for a dead spot.

LUTIFEX: For forty winters I have shaved spruce bellies by touch, Doctor, hoping to carve
one unpierced table whose gravest voice hides a secret hearth—a point deep inside the wood
where the breath stands at a summit or rests on a saddle without ever betraying itself at
the purfling rim. Look how sharply I have pinched these C-bouts inward! Surely that narrow
waist bottles the wave inside the upper and lower lobes?

CHLADNIUS: Sprinkle a pinch of Wittenberg sand across the belly before you trust your
waist, Master Lutemaker. When I draw horsehair down a free brass plate, the grains leap
away from the roaring antinodes as if scalded, marching until they find the nodal line of
silence. Watch your unpierced table now: every grain flees both bouts and gathers in a
single quiet ribbon across the waist, while the fiercest excursion—heat and clangour
alike—crowds onto the outer purfling!

LUTIFEX: Yet your brass sheet bends like a spring, whereas the air sealed inside my shallow
stone sound-chest presses equally against rigid walls that neither bend nor leak. Does the
air obey the same exile to the border?

CHLADNIUS: Even more strictly than my brass! A free metal plate answers a fourth-order law
of bending stiffness, where Poisson's cross-curvature complicates the rim. Your sealed
planar sound-chest—or an insulated copper lamina cooling in the dark—answers the pure
second-order Neumann law: zero flux through the wall, normal derivative vanishing at every
point of the rim. Ask where the slowest-dying mode can hide a stationary point inside the
chamber, and the answer on a smooth unpierced floor is: nowhere at all.

LUTIFEX: Nowhere? Not even a saddle point in the pinch of the C-bouts, where the wave
climbs toward both bouts and dips toward the ribs?

CHLADNIUS: Not even a saddle! If the chamber is planar, bounded, smooth, and simply
connected—without a single sound-hole—every nonzero fundamental Neumann mode maintains a
nonvanishing gradient across the entire interior. Every line of equal pressure is an
uncrossed thread running cleanly from rim to rim.

LUTIFEX: Then why did my grandfather teach me to slice two *f*-holes beside the bridge?

CHLADNIUS: Touch your second belly, where the twin *f*-holes sever simple connectivity.
Once two islands pierce the plane, reflected paths can loop around the apertures and
conspire to trap the strict maximum at an interior point between them. And if you leave
the flat workbench altogether and blow into that three-dimensional spiked bronze star—even
though it has no hole at all and sees every ray from its center—dimension three betrays
the rim a second time, gathering the unique hottest point right at its silent heart.

## II · Expositio Scholastica: Rauch's Conjecture and the Simply Connected Theorem

[D] In 1974 Jeffrey Rauch posed the Hot-Spots Problem for an insulated domain Ω with
outward unit normal ν: if heat or acoustic potential evolves under the Neumann Laplacian
−Δu = μu in Ω with homogeneous zero-flux boundary condition ∂u/∂ν = 0 on ∂Ω, its
discrete spectrum begins at the constant equilibrium mode 0 = μ₁(Ω) < μ₂(Ω) ≤ μ₃(Ω) ≤ …
Because higher modes decay exponentially faster than e^(−μ₂ t), any generic zero-mean
initial state asymptotically aligns with a first nonconstant Neumann eigenfunction u in
the eigenspace E₂(Ω) ([III/S2]). Rauch conjectured that the hottest and coldest points of
every such mode u must lie on ∂Ω.

[D] Topology and dimension sharply delimit where Rauch's intuition survives. In 1999
Krzysztof Burdzy and Wendelin Werner disproved the unrestricted conjecture in the plane by
constructing a bounded doubly connected domain (with two holes) whose simple second Neumann
eigenfunction attains its strict global maximum at an interior point ([III/S2]). Conversely,
for planar domains *without* holes, partial milestones established boundary extrema on lip
domains, symmetric convex bodies, and arbitrary Euclidean triangles, culminating in sharp
near-boundary rigidity on all bounded convex planar domains ([III/S4]).

[D] Family 369 of the October 2026 OpenAI mathematical corpus (HotSpots.lean, accompanying
*Strict hot spots and absence of interior critical points on smooth simply connected planar
domains*, [III/S3]) proves the strongest interior formulation across all smooth bounded
simply connected planar domains—convex or non-convex, simple or multiple:

> 1. Absence of Interior Critical Points: Let Ω in R² be any nonempty smooth bounded
> simply connected planar domain, and let u be any nonzero eigenfunction in the first
> positive Neumann eigenspace E₂(Ω). Then the gradient of u vanishes nowhere in the
> interior Ω (∇u(x) ≠ 0 for every x in Ω), even when the eigenvalue μ₂(Ω) has
> multiplicity greater than one.

> 2. Strict Boundary Extrema & Smooth Foliation: Consequently, u attains neither its
> global maximum nor its global minimum—nor any interior saddle point—inside Ω; every
> interior level set {x in Ω : u(x) = c} is locally a smooth uncrossed curve meeting ∂Ω.

[H] Just as Liber II revealed dimension three as the exact threshold where translational
periodicity breaks, an October 2026 construction by Rami Atar and Krzysztof Burdzy proves
that simple connectivity—and even starlikeness—no longer protects the boundary in R³:
there exists a bounded starlike Lipschitz chamber in R³ with simple μ₂ whose eigenfunction
attains its unique global maximum at the interior origin 0 ([III/S5]).

## III · De Tabula Septima: Biharmonic Brass vs. Neumann Air and the Waisted Viol

[E] Physical candor requires separating two classic instruments that share Chladni's sand
metaphor ([III/S1]). A thin free-edged brass plate obeys the fourth-order Kirchhoff–Love
biharmonic equation Δ²w = λw with coupled bending-moment and shear boundary operators,
whose higher modes readily form closed interior nodal rings. By contrast, a shallow
rigid-walled acoustic resonator cavity (acoustic pressure p satisfying −Δp = (ω/c)²p with
zero normal wall velocity ∂p/∂ν = 0) or an insulated thermal sheet obeys the exact
second-order Neumann problem governed by Family 369 ([III/S3]).

[V] Tabula VII (*Cista Resonantiae Chladniana*) tests Family 369 numerically on a smooth,
markedly **non-convex** waisted viol contour Φ_viol(x, y) ≤ 1 (pinched 30% inward at the
C-bouts; 3,946 finite-volume nodes on the default 0.90 mm grid of
`solve_viol_acoustic_resonator()`). [E] Solving the discrete Neumann eigenproblem confirms
mean(u₂) = 0, places both global extrema strictly on the purfling rim (P₊ at the upper
bowing crown and P₋ at the lower bout), and verifies min |∇u₂| > 0 across every interior
node despite the non-convex waist constriction. The pinched C-bouts tune the second
positive mode μ₃ to within a seventh of a percent of a luthiery octave above the
fundamental (√(μ₃ / μ₂) = 1.9973 on that grid; the rail on the plate rounds it to
2.00×), and `test_manuscript_claims.py` holds this prose to the solver's output. The
rail runs beneath four spandrel foils contrasting higher overtones (u₄, u₅) against the
two-hole planar trap ([III/S2]) and the three-dimensional starlike trap ([III/S5]).

[PLATE: tabula_vii]

## IV · Criterion Falsificationis & Canon Resonantiae

[H] For the lutemaker and modular synthesist alike, the solved modes suggest a patching
rule on any unpierced planar resonator, under the model in which a point driver or damper
exchanges energy with each mode in proportion to that mode's amplitude at the contact
(squared, for a damper). The two lowest modes of the waisted plate are separable by port
alone: u₂ is the longitudinal dipole, with its nodal ribbon across the waist, while the
2.00× mode u₃ is the transverse dipole, with its nodal line running the length of the
long axis. [E] At the poles P₊ and P₋ the solver gives |u₂| = 1 and |u₃| < 0.01; at the
two rim endpoints of the waist ribbon it gives |u₂| < 0.05 and |u₃| ≈ 0.6. [H] Bowing at
P₊ therefore couples maximally into the fundamental and leaves the octave silent; driving
at either waist-rim endpoint excites u₃ while leaving u₂ silent. A damper at the waist
rim suppresses u₃, not the fundamental; to quiet u₂ one damps at a pole. The numerical
solve computes undamped Neumann modes only. A measured transfer function in which a
waist-rim drive excited u₂, or a pole drive excited u₃, would refute this rule without
touching Family 369.

[V] What observation would refute Liber III and overturn Tabula VII? Exhibiting a nonempty
smooth bounded simply connected domain Ω in R² together with a nonzero eigenfunction u in
its first positive Neumann eigenspace E₂(Ω) and an interior point x₀ in Ω where ∇u(x₀) = 0
(an interior hot spot, cold spot, or saddle). That exact refuting proposition—A SIMPLY
CONNECTED SMOOTH PLATE HIDES AN INTERIOR HOT SPOT—is engraved in biliteral ticks clockwise
around the outer frame of Tabula VII from its rubricated corner mark.
