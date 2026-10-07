"""Narration script. One dict per scene, in playback order.

Each line is synthesized as one utterance. {cue} markers inside the text are
not spoken; their times are written to build/timing/<id>.json so the scene
can animate in sync. Grid scenes use {tNNN} (tile lights up), {fNNN} and
{fNNN_end} (featured tile zooms in / out).
"""

FAST = 1.2  # speed for rapid-fire name lists

SCENES = [
    # ------------------------------------------------------------------ intro
    dict(id="s01_open", lines=[
        "Here's an experiment. Take an AI model, and hand it about {problems}four thousand open problems in mathematics.",
        "Real research problems: {decades}some open for decades, a few for over a century.",
        "{hours}About three hours of thinking behind each result, on average.",
        dict(text="Then keep only what's worth keeping.", pause=0.45),
        "{papers}Seven hundred and twenty-two papers. {families}Three hundred and seventy-two families of results, {fields}across seventeen areas of mathematics.",
        "{kinds}Some are sharper bounds. {counter}Some are counterexamples. {famous}And some claim major progress on problems with very famous names.",
        dict(text="{zeta}The zeros of the zeta function. {pi}How well fractions can approximate pi. {kakeya}The Kakeya conjecture. {ugc}The Unique Games Conjecture. {plane}How many colors it takes to paint the plane.", speed=1.08),
        "{title}This is a guided tour of the highlights: fast, but from the ground up.",
    ], tail=1.4),
    dict(id="s02_rules", lines=[
        "{preprint}First, ground rules. These are preprints, written by an internal OpenAI model.",
        "{procedure}Most came from one fixed procedure; {exceptions}a few, like the zeta function and Hodge conjecture work, were exceptions.",
        "{lean}Two hundred and thirty-five of the families come with Lean formalizations: {code}proofs written as code, where a computer checks every logical step.",
        "{badge}Whenever you see this badge, that family has one, covering at least part of the result.",
        "{rest}The rest haven't had that scrutiny yet, and the repository warns that some could have issues.",
        "{claims}So everything you're about to hear is what the papers claim.",
        "{plan}We'll go field by field. {big}The biggest problems get a proper explanation; {rapid}the rest get the rapid-fire treatment.",
    ]),

    # ------------------------------------------------------------------ 1. number theory
    dict(id="c1_card", lines=["Part one. Number theory: the study of whole numbers and primes."], tail=0.9),
    dict(id="c1_qrh", lines=[
        "Start with the most famous function in mathematics: {zeta}the Riemann zeta function.",
        "{sum}Add up one over n to the s, over every whole number n, {complex}carefully extend it to complex inputs, and its zeros turn out to control how the primes are spread out.",
        "{strip}The interesting zeros live in a vertical strip, between real part zero and one. {line}The Riemann Hypothesis says they all sit on the middle line, at one half. {open}That's still open.",
        "{edge}A zero near the right-hand edge would wreck our control of the primes. {sliver}Yet for over a century, the best anyone could prove was a zero-free zone that gets thinner and thinner as you climb.",
        "{quasi}The quasi-Riemann hypothesis asks for much less: some fixed wall, anywhere short of the edge, that no zero ever crosses.",
        "{claim}This paper claims the wall is at seven eighths. {cousins}No zero of zeta, or of its cousins, the Dirichlet L-functions, has real part bigger than seven eighths.",
        "{notrh}Not the Riemann Hypothesis, {margin}but a fixed margin no one had before, {siegel}enough to rule out the notorious Landau-Siegel zeros: hypothetical rogue zeros hugging the edge.",
    ]),
    dict(id="c1_pi", lines=[
        "{pi}Next, pi. It isn't a fraction, but some fractions get remarkably close: {f22}twenty-two sevenths, {f355}or three fifty-five over one thirteen, right to six decimal places.",
        "{measure}The question is how close, compared to the size of the denominator. {dirichlet}For any irrational number, there are infinitely many fractions within about one over q squared.",
        "{exponent}The irrationality exponent asks whether you can do better infinitely often, say, one over q cubed. {record}For pi, the best anyone had proven was that this exponent is at most about seven point one.",
        "{claim}The paper claims the answer is two, the smallest possible: {typical}in the long run, pi is no easier to approximate than a typical number.",
        "{flint}As a bonus, it settles a well-known puzzle: the Flint Hills series, a sum built from sines of whole numbers, converges.",
    ]),
    dict(id="c1_grid", head=1.2, lines=[
        "Rapid fire. {f005}Catalan's constant: one, minus a ninth, plus a twenty-fifth, minus a forty-ninth, and so on, is irrational.{f005_end}",
        "{f004}Hilbert's tenth problem, for fractions: no single algorithm can tell, for every whole-number polynomial equation, whether it has a solution in fractions.{f004_end}",
        dict(text="Plus: {t002}the full Birch and Swinnerton-Dyer formula in low rank, {t006}Goldfeld's conjecture, {t030}modularity over imaginary quadratic fields, {t025}Erdős's short Egyptian fractions, {t028}the Gaussian moat, {t029}the infinitude half of Artin's conjecture, {t013}Ostmann's inverse Goldbach problem, {t026}large prime gaps, {t007}two-point Chowla, {t008}and Deligne–Drinfeld.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ 2. algebraic geometry
    dict(id="c2_card", lines=["Part two. Algebraic geometry: shapes cut out by polynomial equations."], tail=0.9),
    dict(id="c2_hodge", lines=[
        "{hodge}Here lives one of the seven Millennium Prize Problems: the Hodge conjecture.",
        "{shape}A shape defined by polynomial equations has holes and loops, which topology can measure. {cycles}Some of them are traced out by smaller polynomial shapes sitting inside it.",
        "{conj}The conjecture says that every class passing a certain symmetry test, a Hodge class, is built from such pieces, allowing fractional amounts.",
        "{open}The full conjecture is still open, {claim}but this paper claims it for an important family, in every dimension: {cm}abelian varieties with complex multiplication. Think many-dimensional donuts with extra symmetry.",
        "{tate}By older work of Milne, that would also give the Tate conjecture for abelian varieties over finite fields. {k3}Companion papers claim the same for products of K3 surfaces.",
    ]),
    dict(id="c2_grid", head=1.2, lines=[
        "{f047}Zariski's cancellation problem: if a shape, times a line, is ordinary five-dimensional space, must the shape be ordinary four-space? Over the complex numbers, the paper's answer is no.{f047_end}",
        dict(text="Plus {t039}Nagata's conjecture, {t038}Fujita's freeness conjecture, {t040}Bloch's conjecture for surfaces, {t050}a counterexample to Griffiths positivity, {t051}Kobayashi's ampleness conjecture, {t062}LeBrun–Salamon, {t063}the generalized Mukai conjecture, {t059}Zariski's multiplicity conjecture, disproved, {t060}the global spherical shell conjecture, {t058}Kollár–Pardon, {t057}and Campana's abelianity conjecture.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ 3. analysis
    dict(id="c3_card", lines=["Part three. Analysis and geometry: functions, waves, and shapes."], tail=0.9),
    dict(id="c3_kakeya", lines=[
        "{needle}Take a needle, one unit long. How much area do you need to turn it all the way around?",
        "{besi}In 1928, Besicovitch found a shocking answer: as little as you want. {zero}You can even fit a needle pointing in every direction into a set of zero area.",
        "{conj}The Kakeya conjecture says these sets still can't be thin in another sense: their dimension. {ndim}In n-dimensional space, they should be fully n-dimensional.",
        "{wz}In 2025, Hong Wang and Joshua Zahl proved this in three dimensions: a celebrated result.",
        "{claim3}Building on their work, one paper claims the stronger, quantitative version in three dimensions, the maximal conjecture: {tubes}thin tubes pointing in different directions can't pile up too much.",
        "{claim4}A second paper claims the dimension conjecture in four dimensions. {five}Five and up remain open.",
    ]),
    dict(id="c3_mahler", lines=[
        "{shape}Take a convex shape, centered at the origin, and build its dual, the polar body. {stretch}Stretch the shape and the dual shrinks, so the product of their volumes stays the same.",
        "{max}That product is largest for a round ball, as has long been known. {mahler}In the late 1930s, Mahler asked: which shape makes it smallest?",
        "{claim}The papers claim the answer in every dimension. {cube}Among symmetric shapes: the cube, and its relatives. {simplex}Among all shapes: the simplex. A triangle, a tetrahedron, and their higher-dimensional cousins.",
    ]),
    dict(id="c3_grid", head=1.2, lines=[
        "{f073}Falconer's distance conjecture: if a dusty, fractal set has more than half the dimension of the space it lives in, the distances between its points take up a positive length of the number line. Claimed in every dimension.{f073_end}",
        "{f071}Koebe's circle domain conjecture, from 1908: any region with holes, even infinitely many, of any shapes, can be reshaped without distorting angles, so that every hole becomes a perfect circle, or a point.{f071_end}",
        dict(text="Plus {t072}Brennan's conjecture, {t075}Fourier series converging in L log L, {t078}Bochner–Riesz, {t079}local smoothing, {t077}and Fourier restriction for curved surfaces, all three in three dimensions, {t076}ultraflat Littlewood polynomials, {t084}the geometric case of Erdős's similarity conjecture, {t090}optimality of the triangular lattice, {t091}the log Brunn–Minkowski inequality, {t096}and the Gaussian propeller.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ 4. TCS
    dict(id="c4_card", lines=["Part four. Theoretical computer science: what can computers do efficiently, and what can't they?"], tail=0.9),
    dict(id="c4_ugc", lines=[
        "{graph}Picture a network where every node must pick a label, and every link carries a rule: {rule}if you pick this, your neighbor must pick exactly that. {unique}One choice forces a unique answer next door. That's a unique game.",
        "{promise}Suppose you're promised that ninety-nine percent of the rules can be satisfied at once. {conj}The Unique Games Conjecture, posed by Subhash Khot in 2002, says no efficient algorithm can tell that apart from a network where only one percent can, unless P equals NP.",
        "{why}Why care? It pins down how well we can approximate hard problems. {maxcut}Take Max-Cut: split a network into two teams, with as many links between them as possible. {gw}A famous 1995 algorithm always gets at least eighty-seven point eight percent of the best; {opt}the conjecture implies nothing efficient can do better.",
        "{claim}This paper claims a proof of the Unique Games Conjecture. {direct}Companions claim direct proofs that Max-Cut's eighty-seven point eight percent, and factor two for another classic problem, Vertex Cover, can't be beaten, unless P equals NP.",
    ]),
    dict(id="c4_matmul", lines=[
        "{mat}Multiplying two n by n matrices the schoolbook way takes about n cubed steps. {strassen}In 1969, Strassen showed you can do better, and ever since, the race has been on to pin down omega: the true exponent.",
        "{timeline}Decades of work inched it down: {r1}two point three seven six. {r2}Two point three seven three. {r3}Two point three seven one.",
        "{claim}This paper claims omega is at most nine fourths: two point two five, over the complex numbers. {caveat}It's a statement about how the cost grows for enormous matrices, not a faster algorithm for your laptop. {jump}But as jumps go, it's a big one.",
    ]),
    dict(id="c4_grid", head=1.2, lines=[
        "{f103}Coin flips versus memory: the paper claims randomness adds no power to computers with a tiny, logarithmic memory. L equals R L equals B P L.{f103_end}",
        "{f109}Multiplying n-digit numbers: since 1971, n log n was conjectured to be the speed limit on a standard model of computer. A new algorithm claims to beat it, by a sliver.{f109_end}",
        "{f138}And Subset Sum: do some of these numbers add up to a target? A randomized method claims two to the zero point four nine n time, breaking the two to the n over two barrier from 1974.{f138_end}",
        dict(text="Plus {t106}hardness of coloring three-colorable graphs, {t105}two-to-one games, {t104}mean-payoff games, {t108}a permanent versus determinant lower bound, {t113}approximately counting perfect matchings, {t132}a counterexample to quadratic sensitivity, {t124}scheduling on three machines, {t128}shortest superstrings, {t142}and factoring polynomials deterministically.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ 5. combinatorics
    dict(id="c5_card", lines=["Part five. Combinatorics: counting, coloring, and patterns."], tail=0.9),
    dict(id="c5_plane", lines=[
        "{paint}Paint every point of an infinite plane, with one rule: any two points exactly one inch apart must get different colors. {how}How many colors do you need?",
        "{seven}Seven is enough. Tile the plane with hexagons, just under an inch across, and color them in this repeating pattern.",
        "{four}And you need at least four. {spindle}Here's a small network of one-inch links, the Moser spindle, that can't be colored with three.",
        "{degrey}That's where things sat until 2018, when Aubrey de Grey found a network of more than fifteen hundred points that needs five.",
        "{claim}This paper claims at least six: every five-coloring of the plane has two points, one inch apart, with the same color. {range}If it holds, the answer is six, or seven.",
    ]),
    dict(id="c5_erdos", lines=[
        "{ap}An arithmetic progression is a run of evenly spaced numbers, like five, twelve, nineteen, twenty-six.",
        "{erdos}Erdős conjectured that if a set of whole numbers is big enough that adding up one over each of them gives infinity, it must contain progressions of every length. {primes}The primes pass that test, and Green and Tao famously proved they do contain arbitrarily long progressions.",
        "{claim}The paper claims Erdős's conjecture in full, by showing that sets without long progressions must thin out much faster than anyone had proved for lengths beyond three. {prize}It was one of Erdős's famous cash-prize problems.",
    ]),
    dict(id="c5_grid", head=1.2, lines=[
        "{f156}Borsuk asked whether every shape can be cut into one more piece than its dimension, each strictly narrower. The smallest known counterexample was in dimension sixty-three; the paper claims one in dimension nine.{f156_end}",
        "{f155}The periodic tiling conjecture: if a shape tiles space by sliding copies around, there's always a repeating pattern. Already known to fail in huge dimensions, it's now claimed false in three: the lowest possible, for tiles made of cubes.{f155_end}",
        "{f157}And Hadwiger's conjecture from 1943, linking graph coloring to hidden cliques, is claimed false, with large, random-like counterexamples.{f157_end}",
        dict(text="Plus {t180}Barnette's conjecture, {t173}Seymour's second neighborhood conjecture, {t161}counterexamples to Sidorenko, {t162}and to Ryser, {t164}Hindman's sums and products, {t165}crossing numbers of complete graphs, {t179}circulant Hadamard matrices, {t191}the Heilbronn triangle problem, {t187}and a game called Snaky, won in twenty-one moves.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ 6. algebra
    dict(id="c6_card", lines=["Part six. Algebra, groups, and logic: the rules of symmetry, and of mathematics itself."], tail=0.9),
    dict(id="c6_kaplansky", lines=[
        "{group}Take a group of symmetries, and build its group algebra: formal sums of group elements, which you add and multiply like polynomials.",
        "{torsion}If some symmetry returns to the start after a few repeats, it's easy to multiply two nonzero things and get zero. {conj}Kaplansky conjectured in the 1950s that without such looping, called torsion, it can never happen: no zero divisors.",
        "{gardam}In 2021, Giles Gardam disproved a sibling, Kaplansky's unit conjecture. {stood}The zero-divisor conjecture still stood.",
        "{claim}This paper claims a counterexample: a torsion-free group, built with the help of random graphs, where two nonzero elements, with coefficients mod two, multiply to exactly zero. {companion}A companion breaks Kaplansky's direct finiteness conjecture too.",
    ]),
    dict(id="c6_thompson", lines=[
        "{maps}Thompson's group F is made of bent-line maps of an interval: straight pieces, bends at points like one half or three quarters, and slopes that are powers of two.",
        "{amen}The question, open since 1979: is it amenable? {grid}Roughly, can you find finite chunks of the group with almost no boundary, the way you can on a grid, {tree}but never can on a tree?",
        "{both}Over the years, claimed solutions went both ways. {claim}This paper says no: Thompson's group F is not amenable.",
    ]),
    dict(id="c6_grid", head=1.2, lines=[
        "{f246}Cannon's conjecture: if a negatively curved group, seen from infinitely far away, looks like a sphere, then it comes from hyperbolic three-dimensional geometry.{f246_end}",
        "{f244}And in logic, the partition principle, from 1902: splitting a set never gives more pieces than elements. Does it imply the axiom of choice? The paper builds a universe of sets where it doesn't.{f244_end}",
        dict(text="Plus {t193}Serre's intersection multiplicities, {t194}Lech's conjecture, {t201}Kurosh's division ring problem, {t205}Saxl's conjecture, {t202}Alperin's weight conjecture, {t203}Donovan's conjecture, {t247}an infinite, finitely presented two-group, {t250}Boone–Higman, {t254}the Artin K pi one conjecture, {t241}and the rigidity of the Turing degrees.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ 7. dynamics, probability, physics
    dict(id="c7_card", lines=["Part seven. Dynamics, probability, and physics: things that move, mix, and fluctuate."], tail=0.9),
    dict(id="c7_hilbert16", lines=[
        "{flow}Picture a fluid swirling on a tabletop, where the velocity at every point is given by polynomials.",
        "{cycle}Some paths settle into isolated loops, called limit cycles: nearby paths spiral toward them, or away.",
        "{hilbert}In 1900, as part of his sixteenth problem, Hilbert asked how many limit cycles such a flow can have. {quad}It's notoriously hard. Even for degree two, nobody knew whether one upper limit covers every such flow.",
        "{claim}This paper claims that for every degree, there is a finite ceiling. {exists}It doesn't compute it, but it proves it exists. {lienard}A companion pins down one classic case exactly: a degree-five oscillator family has at most two limit cycles.",
    ]),
    dict(id="c7_mubs", lines=[
        "{measure}In quantum mechanics, two ways of measuring are mutually unbiased if knowing the result of one tells you nothing about the other, like position and momentum.",
        "{prime}In a dimension d that's a prime power, like two, three, four or five, you can fit d plus one such measurements. {six}Six is the first dimension that isn't, and for thirty-five years, the maximum could have been anything from three to seven.",
        "{claim}The paper claims exactly three, with a large, computer-assisted proof.",
    ]),
    dict(id="c7_grid", head=1.2, lines=[
        "{f268}Haldane's conjecture: a ring of spin-one quantum magnets, each pointing against its neighbors, keeps an energy gap however long the ring grows. Claimed for even-length rings, with an explicit lower bound.{f268_end}",
        dict(text="Plus {t145}Rokhlin's multiple mixing problem, {t146}chaos in the standard map, {t150}weak mixing in triangular billiards, {t213}critical percolation, {t214}the Benjamini–Schramm nonuniqueness conjecture, {t230}the exact size of S L E curves, {t238}the Thorp shuffle, {t221}Mézard–Parisi, {t261}Anderson localization, {t263}the ionization conjecture, {t260}Penrose inequalities, {t267}Bose–Einstein condensation, {t274}and parity in shallow quantum circuits.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ 8. operator algebras, topology, FA
    dict(id="c8_card", lines=["Part eight. Operator algebras, topology, and functional analysis: the mathematics of infinite dimensions, and of shape."], tail=0.9),
    dict(id="c8_fgf", lines=[
        "{free}Take the free group on two letters: every word you can spell with a, b, and their inverses. {tree}Its picture is an infinite tree.",
        "{vn}From any group, you can build an algebra of operators, its von Neumann algebra, which for a free group is infinite-dimensional. {question}Two letters, or three: do you get the same algebra? {groups}The groups themselves are certainly different.",
        "{history}The question goes back to Richard Kadison, and has been open for decades. {dichotomy}In the nineties, it was shown to be all or nothing: either all these free group algebras are the same, or they're all different.",
        "{claim}The paper claims: all the same. {invisible}With two or more letters, the number of letters is completely invisible to the algebra.",
    ]),
    dict(id="c8_grid", head=1.2, lines=[
        "{f288}Kadison's similarity problem, from 1955: can every bounded representation be straightened out by a single change of coordinates? The paper says yes.{f288_end}",
        "{f293}The hyperinvariant subspace problem, a stronger cousin of the famous invariant subspace problem: the paper builds an operator with no nontrivial hyperinvariant subspace, though the famous original stays open.{f293_end}",
        "{f304}The Hilbert–Smith conjecture: a locally compact group acting faithfully on a manifold must be a smooth Lie group, like the rotations. Claimed in every dimension.{f304_end}",
        "{f325}And Crouzeix's conjecture, in complete form: plug a matrix into a polynomial, even one whose coefficients are matrices too, and the result's size is at most twice the polynomial's maximum on the matrix's numerical range.{f325_end}",
        dict(text="Plus {t289}Kadison–Kastler, {t290}Connes' bicentralizer problem, {t296}the generator problem, {t285}Baum–Connes, disproved, {t309}the Kervaire invariant at the prime three, {t306}cosmetic surgery, {t315}Singer's conjecture in four dimensions, {t322}and Tingley's problem.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ 9. geometry & PDE
    dict(id="c9_card", lines=["Part nine. Geometry and differential equations: the shape of space, and the equations of nature."], tail=0.9),
    dict(id="c9_hotspots", lines=[
        "{plate}Take a flat metal plate, insulated around its edges, heat it unevenly, and wait.",
        "{mode}As the heat evens out, the leftover unevenness settles into one basic pattern. {question}Where are the hottest and coldest points? {rauch}Jeffrey Rauch asked in 1974: are they always on the boundary?",
        "{holes}Not always: in 1999, Burdzy and Werner found a counterexample with holes. {sc}But for shapes without holes, the question stayed open.",
        "{claim}This paper claims it for every smooth shape without holes: the hot and cold spots always sit on the edge.",
    ]),
    dict(id="c9_vlasov", lines=[
        "{plasma}A thin, hot plasma, like the solar wind, is a swarm of charged particles that rarely collide, moving through the electric and magnetic fields they create themselves.",
        "{eq}The relativistic Vlasov–Maxwell equations describe that feedback loop. {q}Do smooth solutions stay smooth forever, or can particles get kicked to infinite momentum? {open}In three dimensions, that's been open since the 1980s.",
        "{claim}The paper claims: smooth forever. {details}Global existence and uniqueness, for any reasonable starting plasma made of one kind of particle, with no smallness or symmetry assumptions.",
    ]),
    dict(id="c9_grid", head=1.2, lines=[
        "{f375}De Giorgi's conjecture, about phase transitions like oil separating from water: claimed in dimension eight, the hardest case.{f375_end}",
        "{f376}A fluid that computes: stir water just right, and a particle lands in a target exactly when a chosen computer program halts.{f376_end}",
        "{f345}And every sphere, in any dimension, however you dent or stretch it, has infinitely many different closed geodesics: think rubber bands, snapped tight.{f345_end}",
        dict(text="Plus {t338}Yau's uniformization conjecture, {t333}isometric immersions of surfaces in four dimensions, {t339}Katok's entropy rigidity conjecture, {t340}a nearby Lagrangian counterexample, {t343}symplectic ball packing, {t344}the metric Blaschke conjecture, {t342}Donaldson's tamed-to-compatible conjecture, {t352}a Calabi flow singularity, {t367}and free boundaries in dimension seven.", speed=FAST),
    ], tail=1.1),

    # ------------------------------------------------------------------ outro
    dict(id="s99_outro", lines=[
        "{mosaic}That's over a hundred and twenty results, out of three hundred and seventy-two.",
        "{caveat}Not all of them will survive. Mathematics has a long history of claimed proofs that cracked under scrutiny, {test}and the real test for these is expert checking, and formal verification.",
        "{lean}But two hundred and thirty-five families already have Lean proofs of at least part of the result, {public}and every paper is public, for anyone to check.",
        "{end}If even a fraction of these hold up, the way mathematics gets done is about to change. {link}The repository is linked below. Go take a look.",
    ], tail=2.6),
]
