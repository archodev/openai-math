"""Director's notes per scene, consumed by the scene-building agents."""
import json
SPOT = {
"s01_open": dict(fam=None, cls="S01Open", notes="""Cold open + title. Beats:
{problems}: a field of ~4000 tiny dots (e.g. 80x50 grid, small Dots or one VMobject of squares; keep it cheap) fills the frame quickly with a counter '≈4,000 open problems'.
{decades}: a few dots flare with small labels of how old famous problems are (e.g. '1900', '1928', '1943' — keep generic, years only).
{hours}: a small clock/hourglass glyph with '≈ 3 h per result (average)'.
'Then keep only what's worth keeping': most dots fade, the survivors gather.
{papers}: survivors become a mosaic of paper first pages (use one pre-composited mosaic PNG built from video/assets/thumbs/*.png via PIL, cached in video/build/cache; zoom/drift it), big counter '722 papers'.
{families}: '372 result families'. {fields}: 17 subject colour bands / labels (subjects in data/catalog.json).
{kinds}/{counter}/{famous}: three quick chips: NEW BOUNDS / COUNTEREXAMPLES / FAMOUS PROBLEMS (use lib chips; RED for counterexamples).
Teaser, one quick vignette per cue ({zeta},{pi},{kakeya},{ugc},{plane}), each ~1.5 s, crisp and iconic: critical strip with zeros on the 1/2 line; pi ≈ 355/113 on a number line; a unit needle rotating; a small graph with coloured labels and arrow-rules on edges; hexagon 7-colouring patch.
{title}: Title card in serif: '4,000 Problems' with subtitle 'A rapid-fire tour of 372 AI-generated math results' and small line '722 preprints · 17 fields · 235 with Lean formalizations'. Hold until the end (scene tail is long), gentle motion.
"""),
"s02_rules": dict(fam=None, cls="S02Rules", notes="""Ground rules.
{preprint}: a few paper cards (paper_card for e.g. 003, 102, 158) fanned out with a 'PREPRINT' stamp-like chip. Small caption 'released by OpenAI · written by an internal model'.
{procedure}/{exceptions}: a small pipeline diagram 'problem → model (≈3 h) → paper', with two papers (zeta 003, Hodge 032) branching off a side path labelled 'exceptions'.
{lean}: a waffle chart of 372 small squares (one per family), 235 lit TEAL (Lean) — use CATALOG lean flags in catalog order — with counter '235 / 372'.
{code}: an actual Lean statement from the repo, typeset in mono (JetBrains Mono) in a code panel, e.g.
  theorem riemannZeta_ne_zero_of_seven_eighths_lt_re
      {s : ℂ} (hs : (7 / 8 : ℝ) < s.re) : riemannZeta s ≠ 0
  (from lean/ComparatorChallenges/QuasiRiemannHypothesis.lean) with a check mark sweep 'checked by computer'.
{badge}: lean_badge() zooms big to centre, then shrinks to a corner position, explaining it.
{rest}: the non-Lean squares (137) glow GREY_ with a small warning chip 'awaiting scrutiny'.
{claims}: big text 'what the papers claim' with 'claim' highlighted YELLOW_.
{plan}: a row of 9 chapter chips in their accent colours (CHAPTERS in lib/style.py), then {big}: one chip expands into a 'SPOTLIGHT' card icon, {rapid}: a mini 4x3 grid icon labelled 'RAPID FIRE'.
"""),
"c1_qrh": dict(fam="003", cls="C1Qrh", notes="""Quasi-Riemann hypothesis. Accent BLUE_.
{zeta}: big tex '\\zeta(s)'. {sum}: \\zeta(s)=\\sum_{n\\ge1} 1/n^s (maybe partial sums 1 + 1/2^s + 1/3^s ...). {complex}: transition to complex plane axes (Re, Im); optional tiny prime staircase inset.
{strip}: shade critical strip 0<Re s<1 (accent, low opacity). {line}: dashed critical line at Re s = 1/2 with true zeros as dots at heights 14.13, 21.02, 25.01, 30.42, 32.94, 37.59, 40.92, 43.33, 48.01, 49.77 (scale the y axis so several are visible; climb upward = shift content down). Label 'Riemann Hypothesis: all zeros here?' {open}: small 'OPEN' chip.
{edge}: highlight the right edge Re s = 1 in RED_. {sliver}: classical zero-free region: thin region hugging Re s=1 whose width shrinks like c/log t as you climb (draw the curve σ = 1 - c/log(t)), animate climbing to show it thinning.
{quasi}: a vertical wall line somewhere left of 1 with '?' — 'some fixed σ₀ < 1'.
{claim}: the wall snaps to 7/8 (label 7/8), band 7/8<Re s<1 fills YELLOW_ low opacity labelled 'zero-free', climb further to show it never narrows. paper_card('003') + paper_tag.
{cousins}: label L(s,χ) copies / 'every Dirichlet L-function'. {notrh}: brief note that the 1/2 line is still a question (RH remains open). {siegel}: a single hypothetical real zero near 1 on the real axis gets crossed out (Landau–Siegel).
End banner: tex '\\zeta(s)\\neq0,\\ L(s,\\chi)\\neq0\\ \\text{ for }\\ \\Re s>\\tfrac78', lean=True.
"""),
"c1_pi": dict(fam="017", cls="C1Pi", notes="""Irrationality exponent of pi. Accent BLUE_.
{pi}: big π with decimals 3.14159265358979...; {f22}: 22/7 = 3.142857... on a zoomable number line near π; {f355}: 355/113 = 3.14159292..., zoom in to show how close (error 2.7e-7).
{measure}: |π − p/q| vs q. {dirichlet}: a plot: x-axis q (log scale optional), show the band 1/q^2 and points for convergents of π (3/1, 22/7, 333/106, 355/113, 103993/33102, ...) all inside the 1/q^2 envelope (true values!).
{exponent}: tex '|\\pi - p/q| < 1/q^{\\mu}' with μ highlighted; {record}: history bar for proven upper bounds on μ(π): Mahler 1953: 42; Mignotte 1974: 20; Hata 1993: 8.02; Salikhov 2008: 7.61; Zeilberger–Zudilin 2020: 7.10 (bars shrinking).
{claim}: bar drops to 2 (YELLOW_), 'μ(π) = 2'. paper_card('017') + paper_tag. {typical}: 'same as almost every real number'.
{flint}: tex '\\sum_{n\\ge1} \\frac{1}{n^3\\sin^2 n}' with label 'Flint Hills series: converges' (a partial-sums plot is optional; if you plot, compute true values).
End banner: '\\mu(\\pi)=2', lean=True.
"""),
"c2_hodge": dict(fam="032", cls="C2Hodge", notes="""Hodge conjecture for CM abelian varieties. Accent PURPLE_.
{hodge}: title 'The Hodge Conjecture' with a small chip 'Millennium Prize Problem'.
{shape}: a 2D drawing of a torus/donut (or genus-2 surface outline) with loops (cycles) drawn on it in different colours. {cycles}: some loops highlighted as 'algebraic' (traced by polynomial sub-shapes).
{conj}: schematic: set 'Hodge classes' ⊆ 'algebraic?' — conjecture says Hodge class ⇒ built from algebraic pieces (rational combinations).
{open}: chip 'general case: OPEN'. {claim}: paper_card('032') + paper_tag. {cm}: a lattice in the complex plane with extra symmetry (e.g. square lattice Z[i] or hexagonal Z[ω]) folding into a torus — 'abelian variety with complex multiplication'; 'every dimension'.
{tate}: arrow 'Milne (1999/2002) ⇒ Tate conjecture for abelian varieties over finite fields'. {k3}: chip 'companions: products of K3 surfaces'.
End banner: 'Rational Hodge conjecture for all CM abelian varieties' (no Lean for this family: lean=False). Be careful: special case only, rational coefficients.
"""),
"c3_kakeya": dict(fam="074", cls="C3Kakeya", notes="""Kakeya. Accent TEAL_.
{needle}: a unit segment rotating 360° in the plane (sweeping a disk/deltoid area shaded). {besi}: Besicovitch: show a Perron-tree-style picture: a triangle cut into 2^k thin sub-triangles that slide horizontally to overlap, so total area visibly shrinks while all directions remain (animate the slide). {zero}: 'area → 0' label.
{conj}: tex 'K\\subset\\mathbb R^n \\text{ contains a unit segment in every direction} \\Rightarrow \\dim K = n'. {ndim}: dims table: n=2 ✓ Davies 1971; n=3 ✓ Wang–Zahl 2025 (human, label it so); n=4 ?; n≥5 ?.
{wz}: highlight the n=3 row with 'Hong Wang & Joshua Zahl, 2025'.
{claim3}: paper_card('074') + paper_tag; row 'n=3, maximal version' gets YELLOW_ 'claimed'. {tubes}: many thin tubes (long thin rectangles) through a region in many directions, overlapping but not piling up too much (a 2D illustration of the maximal estimate).
{claim4}: n=4 row → 'claimed' YELLOW_. {five}: n≥5 row stays '?' with 'open'.
End banner: '3D: Kakeya maximal conjecture · 4D: Kakeya sets have full dimension' (lean=False).
"""),
"c3_mahler": dict(fam="087", cls="C3Mahler", notes="""Mahler conjecture. Accent TEAL_.
{shape}: a convex shape K (start: a square [-1,1]^2) and its polar K° (the diamond |x|+|y|≤1) side by side or overlaid; formula K° = {y : x·y ≤ 1 ∀x∈K}.
{stretch}: stretch K horizontally by t (rectangle) and K° shrinks correspondingly (diamond squashed) — live labels vol(K)·vol(K°) staying = 8.
{max}: the disk (unit circle, polar = itself), product π² ≈ 9.87, label 'maximum (Blaschke–Santaló)'. {mahler}: 'Mahler (late 1930s): minimum?'.
{claim}: paper_card('087') + paper_tag. {cube}: symmetric minimizers: square ↔ diamond (product 8 in 2D; in general 4^n/n!), note 'cube, octahedron & relatives (Hanner polytopes)'. {simplex}: triangle centred at its centroid and its polar (another triangle) product 27/4 = 6.75; general formula (n+1)^{n+1}/(n!)^2.
End banner: tex: '\\text{vol}(K)\\,\\text{vol}(K^\\circ)\\ \\ge\\ \\frac{4^n}{n!}\\ (\\text{symmetric}),\\quad \\frac{(n+1)^{n+1}}{(n!)^2}\\ (\\text{general})', lean=True.
"""),
"c4_ugc": dict(fam="102", cls="C4Ugc", notes="""Unique Games Conjecture. Accent GREEN_.
{graph}: a network of ~10-12 nodes; {rule}: each node gets a label (one of k=4 colours shown as coloured rings); edges carry a permutation arrow 'red→blue' etc. {unique}: choosing one node's label forces its neighbour (animate propagation along a path).
{promise}: two panels: '99% of rules satisfiable' (mostly GREEN_ edges) vs '1% satisfiable' (mostly RED_) — {conj}: between them 'no efficient algorithm can tell these apart (unless P = NP)'; 'Khot, 2002'.
{why}/{maxcut}: Max-Cut: split nodes into two teams (two colours/sides), cut edges highlighted. {gw}: a gauge/number line 0..1 with 0.878 marked 'Goemans–Williamson 1995'. {opt}: 'UGC ⇒ 0.878 is optimal' (KKMO 2007).
{claim}: paper_card('102') + paper_tag, 'Unique Games Conjecture: claimed proof'. {direct}: chips: 'Max-Cut: 0.878 optimal', 'Vertex Cover: factor 2 optimal' (unless P = NP).
End banner: 'Unique Games Conjecture: NP-hard to distinguish 99%-satisfiable from 1%' (lean=True).
"""),
"c4_matmul": dict(fam="107", cls="C4Matmul", notes="""Matrix multiplication exponent. Accent GREEN_.
{mat}: two small matrices; animate a row×column dot product producing one entry; then 'n³' as a cube of n×n×n little cubes or a counter. {strassen}: 'Strassen 1969: 7 multiplications instead of 8 for 2×2 → n^{2.807}'.
{timeline}: horizontal number line from 2 to 3 labelled ω. Markers: 3 (schoolbook), 2.807 (Strassen 1969), 2.376 (Coppersmith–Winograd 1990) at {r1}, 2.373 (2010s: Stothers / Vassilevska Williams / Le Gall) at {r2}, 2.371 (2020s; best previous 2.3712) at {r3} — crowding near 2.37 visible (zoom inset helps).
{claim}: a marker jumps to 2.25 = 9/4 (YELLOW_), arc showing the jump. paper_card('107') + paper_tag. 'over ℂ'. {caveat}: chip 'asymptotic — not a practical algorithm'. {jump}: emphasize the gap between 2.371 and 2.25.
End banner: '\\omega \\le 9/4' (over ℂ), lean=True.
"""),
"c5_plane": dict(fam="158", cls="C5Plane", notes="""Chromatic number of the plane. Accent GOLD_.
{paint}: two points distance 1 with a ruler-like link, they get different colours; {how}: '?' colours.
{seven}: hexagonal tiling coloured with 7 colours in the standard pattern (each hexagon's 6 neighbours all distinct colours; same colours repeat on a lattice spanned by (2,1)-type offsets so same-coloured hexagons are >1 apart). Hex diameter just under 1 (label). Must be CORRECT.
{four}: label 'at least 4'. {spindle}: the Moser spindle: 7 vertices, 11 unit edges, exact coordinates (two rhombi of two equilateral triangles each, sharing a vertex, rotated so tips are distance 1). Try 3 colours and show the forced conflict.
{degrey}: de Grey 2018: a dense schematic 'graph with 1,581 vertices needs 5 colours' (a decorative unit-distance-like graph; label clearly as schematic).
{claim}: a bounds number line 1..8 with interval [4,7] → [5,7] (2018) → [6,7] (claim, YELLOW_). paper_card('158') + paper_tag. {range}: '6 or 7?'.
End banner: 'χ(ℝ²) ≥ 6: every 5-colouring has two same-coloured points at distance 1', lean=True.
"""),
"c5_erdos": dict(fam="159", cls="C5Erdos", notes="""Erdős reciprocal-sum conjecture. Accent GOLD_.
{ap}: a strip of integers 1..30 (or 1..60 in rows); highlight 5, 12, 19, 26 with equal-gap arcs (+7).
{erdos}: tex '\\sum_{a\\in A} \\frac1a = \\infty \\ \\Rightarrow\\ A \\text{ has arbitrarily long APs}'. {primes}: primes highlighted on the strip; partial sums of 1/p growing slowly (they diverge like log log x) — a small plot is fine; then 7, 37, 67, 97, 127, 157 (six primes, step 30) shown as an AP; 'Green–Tao 2004/2008'.
{claim}: paper_card('159') + paper_tag; 'every length k'. {prize}: a small '$' prize chip 'Erdős prize problem'.
End banner: 'Divergent ∑1/a ⇒ arithmetic progressions of every length', lean=True.
"""),
"c6_kaplansky": dict(fam="196", cls="C6Kaplansky", notes="""Kaplansky zero-divisor conjecture. Accent PINK_.
{group}: a Cayley-graph-like lattice of group elements; group algebra elements drawn as sets of highlighted vertices (coefficients 0/1 mod 2), e.g. α = g + h + k.
{torsion}: a 3-cycle (g with g³=1): (1 + g)(1 + g + g²) = 0 in F₂? careful: over F2, (1+g)(1+g+g²) = 1 + g³ = 0 when g³=1. Show tex (1-g)(1+g+g^2)=1-g^3=0. {conj}: 'Kaplansky (1950s): torsion-free ⇒ no zero divisors', 'α β ≠ 0'.
{gardam}: chip 'Gardam 2021: unit conjecture ✗ (different conjecture)'. {stood}: 'zero-divisor conjecture: open'.
{claim}: paper_card('196') + paper_tag; illustrate α·β = 0 with coefficient dots that cancel in pairs mod 2 (schematic, label as illustration); 'built from random graphs', 'finitely presented, torsion-free'. {companion}: chip 'direct finiteness: also broken (family 197)'.
End banner: 'A torsion-free group G with nonzero α, β ∈ 𝔽₂[G], αβ = 0', lean=True.
"""),
"c6_thompson": dict(fam="248", cls="C6Thompson", notes="""Thompson's group F nonamenable. Accent PINK_.
{maps}: axes [0,1]×[0,1]; draw the generator x₀ of F: piecewise linear through (0,0),(1/4,1/2)? (standard x0: [0,1/2]→[0,1/4] slope 1/2, [1/2,3/4]→[1/4,1/2] slope 1, [3/4,1]→[1/2,1] slope 2). Animate composition/another map; label breakpoints 1/2, 3/4 and slopes 1/2, 1, 2.
{amen}: 'amenable?' — {grid}: on a square grid, a big square chunk: boundary small relative to size (ratio → 0 as it grows, animate growth). {tree}: on a binary/4-regular tree, any chunk has boundary comparable to its size (ratio stays ≥ constant).
{both}: chips 'claimed amenable (2009)' / 'claimed non-amenable' crossing. {claim}: paper_card('248') + paper_tag; 'F is not amenable' (Geoghegan's 1979 conjecture).
End banner: 'Thompson's group F is non-amenable', lean=True.
"""),
"c7_hilbert16": dict(fam="143", cls="C7Hilbert16", notes="""Hilbert's 16th problem (uniform bounds). Accent YELLOW_ (use YELLOW_/GOLD_).
{flow}: a polynomial planar vector field drawn as moving streamlines/particles (e.g. van der Pol x'=y, y'=μ(1−x²)y−x, polynomial degree 3) with particles flowing (updaters; keep ≤ ~150 particles with short trails or StreamLines with modest density).
{cycle}: the limit cycle highlighted; trajectories from inside and outside spiral onto it.
{hilbert}: 'Hilbert, 1900 — Problem 16'. Show a field with nested multiple limit cycles (alternating stable/unstable) for illustration (e.g. a Liénard system or polar-form r' = r·sin(πr)-type made polynomial; must be genuinely polynomial or clearly labelled 'illustration').
{quad}: 'degree 2: at least 4 cycles known (1979–80) — finite upper bound? unknown'.
{claim}: paper_card('143') + paper_tag; a ceiling bar labelled 'B(d) < ∞ for every degree d'. {exists}: '(exists — not computed)'. {lienard}: chip 'quintic Liénard: at most 2 (Lean-checked companion)'.
End banner: '# limit cycles ≤ B(d) for every degree-d polynomial vector field', lean=True (Lean covers the Liénard companion only — banner should not claim the uniform bound is Lean-checked; set lean=False on the banner and show the Lean chip next to the Liénard line instead).
"""),
"c7_mubs": dict(fam="266", cls="C7Mubs", notes="""Mutually unbiased bases in dimension 6. Accent YELLOW_.
{measure}: 2D cartoon: basis A = two perpendicular arrows; basis B rotated 45°; projections of B vectors onto A all equal (1/√2) — 'unbiased: every outcome equally likely'. Position/momentum labels.
{prime}: table of dimensions d = 2,3,4,5,7,8,9 with 'd+1 bases' ✓ (prime powers). {six}: d = 6 highlighted with range '3 ≤ N(6) ≤ 7' and '?', 'Zauner 1991'.
{claim}: paper_card('266') + paper_tag; '?' collapses to N(6) = 3; chip 'computer-assisted proof'.
End banner: 'N(6) = 3: no four mutually unbiased bases in ℂ⁶', lean=True.
"""),
"c8_fgf": dict(fam="287", cls="C8Fgf", notes="""Free group factor isomorphism. Accent SKY_.
{free}: words in a, b, a⁻¹, b⁻¹ appearing; {tree}: Cayley graph of F₂ (4-regular tree drawn fractally, edges halving each level, colour a horizontal, b vertical); also F₃ (6-regular) next to it.
{vn}: each tree flows into a box 'L(F₂)' / 'L(F₃)' (von Neumann algebra). {question}: '≅ ?' between them. {groups}: 'F₂ ≇ F₃' small note (groups differ).
{history}: 'Kadison' question chip; {dichotomy}: a row L(F₂), L(F₃), L(F₄), …, L(F_∞) with 'all equal OR all different' (Dykema, Rădulescu 1994).
{claim}: paper_card('287') + paper_tag; '?' becomes '≅' and all links in the row light up. {invisible}: the trees fade, leaving one box.
End banner: tex 'L(\\mathbb F_2)\\cong L(\\mathbb F_3)\\cong\\cdots\\cong L(\\mathbb F_\\infty)', lean=True.
"""),
"c9_hotspots": dict(fam="369", cls="C9Hotspots", notes="""Hot spots conjecture. Accent ORANGE_.
{plate}: a smooth blob-shaped plate (simply connected), {mode}: a heat-map of its first nonconstant Neumann eigenfunction — COMPUTE it (finite differences on a grid mask, scipy.sparse.linalg.eigsh, Neumann boundary via masked Laplacian) and bake to PNG (cache), colormap cold blue→hot orange/red. Animate from noisy random heat to the mode (crossfade a few precomputed frames of heat flow if cheap, else crossfade noise→mode).
{question}: mark the hottest and coldest points (they should be on the boundary for your domain — verify numerically!). {rauch}: 'Rauch, 1974'.
{holes}: a domain with holes (schematic) where a hot spot sits inside, labelled 'Burdzy–Werner 1999 counterexample (with holes)'. {sc}: 'no holes: open'.
{claim}: paper_card('369') + paper_tag; back to the blob: extremes pinned on the edge, 'no interior critical point'.
End banner: 'Smooth simply connected planar domains: hot & cold spots lie on the boundary', lean=True.
"""),
"c9_vlasov": dict(fam="362", cls="C9Vlasov", notes="""Relativistic Vlasov–Maxwell. Accent ORANGE_.
{plasma}: ~150-200 charged particles (two colours not needed: one species; use ORANGE_ dots with faint trails) swirling; faint field lines/arrows (E and B) around them.
{eq}: the equations in tex (compact form): \\partial_t f + \\hat v\\cdot\\nabla_x f + (E + \\hat v\\times B)\\cdot\\nabla_p f = 0 and Maxwell (\\partial_t E = \\nabla\\times B - j,\\ \\partial_t B = -\\nabla\\times E), with \\hat v = p/\\sqrt{1+|p|^2}.
{q}: a 'momentum' gauge; one particle accelerating towards '∞?'. {open}: 'Glassey–Strauss 1986: smooth as long as momenta stay bounded' + 'open since the 1980s'.
{claim}: paper_card('362') + paper_tag; gauge stays finite, particles keep swirling smoothly; 'smooth forever'. {details}: chips 'global existence', 'uniqueness', 'no smallness', 'no symmetry', and small note 'one species, 3D, relativistic'.
End banner: 'Global smooth solutions for 3D relativistic Vlasov–Maxwell', lean=True.
"""),
"s99_outro": dict(fam=None, cls="S99Outro", notes="""Outro.
{mosaic}: the full mosaic of all 372 first pages (pre-composited PNG grid, e.g. 31×12, built from video/assets/thumbs) zooming out slowly; the 125 named families (spotlights + grid items; list in video/data/named.json) brightened, others dimmed; counter '125 / 372'.
{caveat}: a gentle 'cracks' motif: a few tiles get a RED_ question mark; caption 'expert checking + formal verification'.
{test}: chips 'peer review', 'Lean'.
{lean}: the 235 Lean families light up TEAL_ (overlay on mosaic or waffle), counter '235 with Lean formalizations'. {public}: 'all public'.
{end}: closing line in serif: 'If even a fraction hold up…'. {link}: end card: 'github.com/openai/math' (mono), and video title '4,000 Problems' small; hold until the end.
"""),
}
json.dump(SPOT, open(__file__.replace('scene_specs.py','scene_specs.json'),'w'), indent=1, ensure_ascii=False)

T = lambda n, name, v, cap=None: dict(num=n, name=name, verdict=v, caption=cap)
GRIDS = {
"c1_grid": [T("005","Catalan's constant is irrational","proved","G = 1 − 1/9 + 1/25 − 1/49 + ⋯ is not a fraction."),
            T("004","Hilbert's tenth problem over ℚ","resolved","No algorithm decides whether a polynomial equation has a rational solution."),
            T("002","Full BSD formula in Selmer corank ≤ 1","proved"), T("006","Goldfeld's conjecture","proved"),
            T("030","Modularity over imaginary quadratic fields","proved"), T("025","Erdős's short Egyptian fractions","proved"),
            T("028","The Gaussian moat conjecture","proved"), T("029","Artin's primitive roots: infinitely many","proved"),
            T("013","Ostmann's inverse Goldbach problem","proved"), T("026","Positive density of large prime gaps","proved"),
            T("007","Two-point Chowla conjecture","proved"), T("008","Deligne–Drinfeld conjecture","proved")],
"c2_grid": [T("047","Zariski cancellation fails over ℂ","counterexample","X × line ≅ 5-space, yet X is not 4-space."),
            T("039","Nagata's conjecture","proved","Curves through r ≥ 10 general points: Σ mᵢ < d·√r."),
            T("038","Fujita's freeness conjecture","proved"), T("040","Bloch's conjecture for surfaces","proved"),
            T("050","Griffiths positivity conjecture","counterexample"), T("051","Kobayashi's canonical-ampleness conjecture","proved"),
            T("062","LeBrun–Salamon conjecture","proved"), T("063","Generalized Mukai conjecture","proved"),
            T("059","Zariski's multiplicity conjecture","counterexample"), T("060","Global spherical shell conjecture","proved"),
            T("058","Kollár–Pardon universal covers","proved"), T("057","Campana's abelianity conjecture","proved")],
"c3_grid": [T("073","Falconer distance conjecture","proved","dim E > d/2 ⟹ the distance set has positive length."),
            T("071","Koebe's circle-domain conjecture","proved","Any domain can be mapped conformally so every hole is a disk or a point."),
            T("072","Brennan's conjecture","proved"), T("075","L log L Fourier convergence","proved"),
            T("078","Bochner–Riesz in 3D","proved"), T("079","Local smoothing in 3D","proved"),
            T("077","Fourier restriction for curved surfaces","proved"), T("076","Ultraflat Littlewood polynomials","construction"),
            T("084","Erdős similarity (geometric case)","resolved"), T("090","Universal optimality of the triangular lattice","proved"),
            T("091","Log Brunn–Minkowski inequality","proved"), T("096","Gaussian propeller conjecture","proved")],
"c4_grid": [T("103","L = RL = BPL","proved","Coin flips add no power to log-space computation."),
            T("109","Integer multiplication below n log n","algorithm","O(n (log n)^(1−κ)) with κ = 2⁻¹⁸²: a sliver past n log n."),
            T("138","Subset Sum in 2^0.49n","algorithm","Beats the 2^(n/2) meet-in-the-middle barrier (1974)."),
            T("106","Coloring 3-colorable graphs is NP-hard","hardness"), T("105","2-to-1 games, perfect completeness","hardness"),
            T("104","Quasipolynomial mean-payoff games","algorithm"), T("108","Permanent vs determinant: Ω(n³)","bound"),
            T("113","Counting perfect matchings (FPRAS)","algorithm"), T("132","Sensitivity vs block sensitivity","counterexample"),
            T("124","Scheduling on three machines","algorithm"), T("128","Shortest superstring: factor 2","algorithm"),
            T("142","Deterministic factoring over 𝔽ₚ","algorithm")],
"c5_grid": [T("156","Borsuk fails in dimension 9","counterexample","A 9-dimensional set that can't be cut into 10 narrower pieces."),
            T("155","Periodic tiling fails in 3D","counterexample","One tile fills ℤ³ by translations, but never periodically."),
            T("157","Hadwiger's conjecture","counterexample","Graphs needing more colors than their largest clique minor."),
            T("180","Barnette's conjecture","proved"), T("173","Seymour's second-neighborhood conjecture","proved"),
            T("161","Sidorenko's conjecture","counterexample"), T("162","Ryser's covering conjecture","counterexample"),
            T("164","Hindman's sums & products","proved"), T("165","Crossing numbers of complete graphs","exact"),
            T("179","Circulant Hadamard conjecture","proved"), T("191","Heilbronn triangle problem","bound"),
            T("187","Snaky in 21 Maker moves","resolved")],
"c6_grid": [T("246","Cannon's conjecture","proved","Sphere at infinity ⟹ hyperbolic 3-manifold group."),
            T("244","Partition principle ⇏ choice","independent","A universe of sets where PP holds but AC fails."),
            T("193","Serre's intersection multiplicity","proved"), T("194","Lech's conjecture","proved"),
            T("201","Kurosh's division-ring problem","counterexample"), T("205","Saxl's conjecture","proved"),
            T("202","Blockwise Alperin weight conjecture","proved"), T("203","Donovan's conjecture","proved"),
            T("247","Infinite f.p. residually finite 2-group","construction"), T("250","Boone–Higman conjecture","proved"),
            T("254","Artin K(π,1) conjecture","proved"), T("241","Rigidity of the Turing degrees","proved")],
"c7_grid": [T("268","Spin-one Haldane gap","proved","The energy gap stays positive for every even ring length."),
            T("145","Rokhlin's multiple-mixing problem","proved","Mixing ⟹ mixing of all orders, for a single transformation."),
            T("146","Positive entropy of the standard map","proved"), T("150","Weak mixing of triangular billiards","proved"),
            T("213","No infinite critical clusters","proved"), T("214","Benjamini–Schramm: p_c < p_u","proved"),
            T("230","Exact Hausdorff measure for SLE","exact"), T("238","Thorp shuffle mixes in Θ(log N)","exact"),
            T("221","Mézard–Parisi formula","proved"), T("261","Anderson localization in 2D","proved"),
            T("263","Ionization conjecture","proved"), T("260","Spacetime Penrose inequalities","proved"),
            T("267","Bose–Einstein condensation","proved"), T("274","Parity is not in QAC⁰","proved")],
"c8_grid": [T("288","Kadison's similarity problem","resolved","Every bounded representation is similar to a *-representation."),
            T("293","Hyperinvariant subspace problem","counterexample","An operator with no hyperinvariant subspace."),
            T("304","Hilbert–Smith conjecture","proved","Faithful actions on manifolds force Lie groups, in every dimension."),
            T("325","Complete Crouzeix conjecture","proved","‖p(A)‖ ≤ 2 · max of |p| over the numerical range W(A)."),
            T("289","Strong Kadison–Kastler conjecture","proved"), T("290","Connes' bicentralizer conjecture","proved"),
            T("296","Generator problem for II₁ factors","resolved"), T("285","Baum–Connes conjecture","counterexample"),
            T("309","Kervaire invariant at p = 3","resolved"), T("306","Purely cosmetic surgery conjecture","proved"),
            T("315","Singer conjecture in 4D","proved"), T("322","Tingley's problem","resolved")],
"c9_grid": [T("375","De Giorgi's conjecture in ℝ⁸","proved","Monotone Allen–Cahn solutions in dimension 8 are flat."),
            T("376","Navier–Stokes flows that compute","construction","A forced fluid, starting at rest, that simulates any Turing machine."),
            T("345","Infinitely many closed geodesics","proved","Every metric on a sphere has infinitely many closed geodesics."),
            T("338","Yau's uniformization conjecture","proved"), T("333","Isometric immersions into ℝ⁴","proved"),
            T("339","Katok's entropy rigidity","proved"), T("340","Nearby Lagrangian conjecture","counterexample"),
            T("343","Symplectic ball packing","resolved"), T("344","Metric Blaschke conjecture","proved"),
            T("342","Donaldson's tamed-to-compatible conjecture","proved"), T("352","Calabi flow singularity","counterexample"),
            T("367","Bernoulli free boundaries: dimension 7","exact")],
}
json.dump(GRIDS, open(__file__.replace('scene_specs.py','grids.json'),'w'), indent=1, ensure_ascii=False)
named = sorted({t['num'] for g in GRIDS.values() for t in g} | {v['fam'] for v in SPOT.values() if v['fam']})
json.dump(named, open(__file__.replace('scene_specs.py','named.json'),'w'))
print(len(named), 'named')
