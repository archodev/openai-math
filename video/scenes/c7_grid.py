import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
import json
import textwrap

import numpy as np

from lib.voice import VoiceScene  # noqa: F401
from lib.style import *        # noqa: F401,F403
from lib.components import *   # noqa: F401,F403
from lib.grid import GridScene

ACC = YELLOW_          # chapter accent ("dp")


# ======================================================================= helpers
def _mtex(*s, **kw):
    # (lib/voice.py now keeps LaTeX output per scene and never cleans it up, so the
    # old compile-retry workaround is no longer needed)
    return MathTex(*s, **kw)


def _p(x, y):
    return np.array([x, y, 0.0])


def _cloud(xy, r, color, opacity=1.0):
    """Many tiny filled squares packed into ONE VMobject (cheap point cloud)."""
    xy = np.asarray(xy, dtype=float)
    n = len(xy)
    off = np.array([[-r, -r], [r, -r], [r, r], [-r, r], [-r, -r]])
    corners = xy[:, None, :] + off[None, :, :]                       # n x 5 x 2
    a, b = corners[:, :-1, :], corners[:, 1:, :]                     # n x 4 x 2
    quad = np.stack([a, a + (b - a) / 3, a + 2 * (b - a) / 3, b], axis=2)  # n x 4 x 4 x 2
    pts = np.zeros((n * 16, 3))
    pts[:, :2] = quad.reshape(-1, 2)
    vm = VMobject(stroke_width=0, fill_color=color, fill_opacity=opacity)
    vm.set_points(pts)
    return vm


def _segs(segs, color, width=1.6, opacity=1.0):
    """Many straight segments packed into ONE VMobject."""
    s = np.asarray(segs, dtype=float)                                # n x 2 x 2
    a, b = s[:, 0, :], s[:, 1, :]
    quad = np.stack([a, a + (b - a) / 3, a + 2 * (b - a) / 3, b], axis=1)  # n x 4 x 2
    pts = np.zeros((len(s) * 4, 3))
    pts[:, :2] = quad.reshape(-1, 2)
    vm = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity, fill_opacity=0)
    vm.set_points(pts)
    return vm


def _poly(xy, color, width=1.6, opacity=1.0, smooth=False):
    pts = [_p(x, y) for x, y in xy]
    vm = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity, fill_opacity=0)
    if smooth:
        vm.set_points_smoothly(pts)
    else:
        vm.set_points_as_corners(pts)
    return vm


def _arrow(a, b, color, width=2.4, tip=0.07):
    return Arrow(a, b, buff=0, color=color, stroke_width=width, tip_length=tip,
                 max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=40)


def _spin(center, direction, length, color, width=2.4, tip=0.07):
    d = np.asarray(direction, dtype=float)
    d = d / np.linalg.norm(d)
    return _arrow(center - d * length / 2, center + d * length / 2, color, width, tip)


# ======================================================================= 268 Haldane
def _ring_spins(L, center, R, length, settled=True, seed=7, width=2.4, tip=0.07, order=None):
    """Spin-one antiferromagnetic ring: radial arrows alternating out / in.
    `order` lists the site index of each submobject (used to grow the ring smoothly)."""
    rng = np.random.default_rng(seed)
    g = VGroup()
    angles = []
    order = list(range(L)) if order is None else order
    for k in order:
        a = PI / 2 + TAU * k / L
        u = np.array([np.cos(a), np.sin(a), 0.0])
        pos = center + R * u
        if settled:
            phi = a if k % 2 == 0 else a + PI
            col = ACC if k % 2 == 0 else WHITE_
        else:
            phi = rng.uniform(0, TAU)
            col = GREY_
        angles.append(phi)
        g.add(_spin(pos, [np.cos(phi), np.sin(phi), 0], length, col, width, tip))
    g.angles, g.order, g.L = angles, order, L
    return g


def _doubled_order(order):
    """Site order for a ring of twice the size, matching Transform's submobject padding
    [old_0, copy_0, old_1, copy_1, ...]: each old spin keeps its orientation (an outward
    spin at site i goes to site 2i, an inward one to 2i+1); the copy fills the other site."""
    new = []
    for i in order:
        new += [2 * i, 2 * i + 1] if i % 2 == 0 else [2 * i + 1, 2 * i]
    return new


def icon_haldane():
    c = _p(-0.55, 0.0)
    R = 0.33
    ring = Circle(radius=R, stroke_color=GREY_, stroke_width=1.5, stroke_opacity=0.6).move_to(c)
    spins = _ring_spins(8, c, R, 0.25, width=2.2, tip=0.07)
    x0, x1 = 0.2, 1.05
    y0, y1 = -0.34, 0.08
    e0 = Line(_p(x0, y0), _p(x1, y0), color=WHITE_, stroke_width=2.6)
    e1 = Line(_p(x0, y1), _p(x1, y1), color=WHITE_, stroke_width=1.8)
    band = VGroup(*[Line(_p(x0, y), _p(x1, y), color=GREY_, stroke_width=1.3, stroke_opacity=0.7)
                    for y in (0.19, 0.28, 0.36, 0.42)])
    gap = DoubleArrow(_p(0.45, y0 + 0.02), _p(0.45, y1 - 0.02), buff=0, color=ACC, stroke_width=2.2,
                      tip_length=0.07, max_tip_length_to_length_ratio=0.3,
                      max_stroke_width_to_length_ratio=40)
    lab = _mtex(r"\gamma", font_size=30, color=ACC).move_to(_p(0.66, (y0 + y1) / 2))
    return VGroup(ring, spins, e0, e1, band, gap, lab)


# design-space layout of the big Haldane card
_H = dict(c=_p(-1.35, 0.5), R=1.12, ex0=0.85, ex1=2.05, e0=-0.62, top=1.75, gx=1.3)
_H_LEN = {8: 0.5, 16: 0.36, 32: 0.24}
_H_GAP = {8: 1.0, 16: 0.9, 32: 0.86}     # schematic: finite-size gap settles, stays open


def _h_levels(L):
    """Excited levels above the gap (they crowd together as L grows; the gap does not close)."""
    e1 = _H["e0"] + _H_GAP[L]
    n = {8: 4, 16: 8, 32: 15}[L]
    ys = e1 + (_H["top"] - e1) * (np.arange(1, n + 1) / n) ** 1.1
    lines = VGroup(*[Line(_p(_H["ex0"], y), _p(_H["ex1"], y), color=GREY_, stroke_width=1.5,
                          stroke_opacity=0.75) for y in ys])
    e1l = Line(_p(_H["ex0"], e1), _p(_H["ex1"], e1), color=WHITE_, stroke_width=2.2)
    return e1l, lines


def _h_gap(L):
    e0 = _H["e0"]
    e1 = e0 + _H_GAP[L]
    arr = DoubleArrow(_p(_H["gx"], e0 + 0.03), _p(_H["gx"], e1 - 0.03), buff=0, color=ACC,
                      stroke_width=3, tip_length=0.13, max_tip_length_to_length_ratio=0.3,
                      max_stroke_width_to_length_ratio=40)
    lab = _mtex(r"\gamma_L", font_size=38, color=ACC).move_to(_p(_H["gx"] + 0.42, (e0 + e1) / 2))
    return arr, lab


def _h_Llabel():
    """'L = 8 / 16 / 32': the numbers sit on top of each other and cross-fade (a glyph
    Transform between numbers looks garbled mid-way)."""
    lhs = _mtex("L =", font_size=36, color=WHITE_)
    nums = VGroup(*[_mtex(str(L), font_size=36, color=WHITE_) for L in (8, 16, 32)])
    for n in nums:
        n.next_to(lhs, RIGHT, buff=0.16)
    VGroup(lhs, nums).move_to(_H["c"] + DOWN * (_H["R"] + 0.62))
    nums[1].set_opacity(0)
    nums[2].set_opacity(0)
    return VGroup(lhs, nums)


def big_haldane():
    """Ring + level diagram only; the bound formula is added by anim_haldane in the right
    text column (keeping it out of this group lets the picture sit centred on the card)."""
    c, R = _H["c"], _H["R"]
    ring = Circle(radius=R, stroke_color=GREY_, stroke_width=2, stroke_opacity=0.55).move_to(c)
    spins = _ring_spins(8, c, R, _H_LEN[8], settled=False, width=3.2, tip=0.13)
    s1 = _mtex(r"S = 1", font_size=34, color=GREY_).move_to(c)
    Llab = _h_Llabel()
    axis = Arrow(_p(0.6, -0.95), _p(0.6, 2.05), buff=0, color=GREY_, stroke_width=2,
                 tip_length=0.14, max_stroke_width_to_length_ratio=40)
    elab = _mtex("E", font_size=32, color=GREY_).next_to(axis.get_end(), RIGHT, buff=0.12)
    e0 = Line(_p(_H["ex0"], _H["e0"]), _p(_H["ex1"], _H["e0"]), color=WHITE_, stroke_width=3.2)
    e0lab = _mtex("E_0", font_size=32, color=WHITE_).next_to(e0, RIGHT, buff=0.12)
    e1, band = _h_levels(8)
    gap, glab = _h_gap(8)
    g = VGroup(ring, spins, s1, Llab, axis, elab, band, e1, e0, e0lab, gap, glab)
    g.parts = dict(ring=ring, spins=spins, Llab=Llab, band=band, e1=e1, gap=gap, glab=glab)
    g.w0, g.c0 = g.width, g.get_center()
    return g


_Z_NEW = 61        # parts created during the feature must draw above the dim layer (z 50)


def anim_haldane(scene, mob, T):
    """Beats are pinned to fractions of the f268 -> f268_end narration window, measured
    from the phrase pauses of the current audio (robust to small re-synthesis shifts):
      .12-.29 "a ring of spin-one quantum magnets"   .30-.43 "each pointing against ..."
      .46-.54 "keeps an energy gap"   .55-.69 "however long the ring grows"
      .71-.86 "Claimed for even-length rings"        .87-.99 "with an explicit lower bound"
    """
    P = mob.parts
    k = mob.width / mob.w0
    shift = mob.get_center() - k * mob.c0

    def place(m):
        VGroup(m).scale(k, about_point=ORIGIN).shift(shift)
        return m

    s0, s1 = scene.cue("f268"), scene.cue("f268_end")
    deadline = s1 - 0.5                     # the card starts collapsing at s1 - 0.45

    def at(f):
        return min(deadline, s0 + f * (s1 - s0))

    def play_to(f, *anims, **kw):
        rt = max(0.2, at(f) - scene.now)
        scene.play(*anims, run_time=rt, **kw)

    def adopt(*parts):
        for q in parts:
            scene.remove(q)
        mob.add(*parts)                     # collapses together with the card

    c, R = _H["c"], _H["R"]
    spins = P["spins"]
    rng = np.random.default_rng(3)
    # 0. a ring of spin-one quantum magnets, jittering
    scene.wait_until(at(0.12))
    play_to(0.285, *[Rotate(a, angle=rng.choice([-1, 1]) * rng.uniform(0.35, 0.7),
                            about_point=a.get_center(), rate_func=wiggle) for a in spins])
    # 1. ... each pointing against its neighbours (antiferromagnet)
    scene.wait_until(at(0.30))
    tgt = place(_ring_spins(8, c, R, _H_LEN[8], settled=True, width=3.2, tip=0.13))
    turns = []
    for arr, new, a0, a1 in zip(spins, tgt, spins.angles, tgt.angles):
        d = (a1 - a0 + PI) % TAU - PI
        turns.append(Transform(arr, new, path_arc=d))
    play_to(0.43, LaggedStart(*turns, lag_ratio=0.08), rate_func=smooth)
    # 2. ... keeps an energy gap, however long the ring grows
    scene.wait_until(at(0.46))
    play_to(0.535, Indicate(VGroup(P["gap"], P["glab"]), color=ACC, scale_factor=1.12))
    order = list(range(8))
    lhs, nums = P["Llab"]
    for i, (L, f0, f1) in enumerate(((16, 0.545, 0.61), (32, 0.62, 0.685))):
        scene.wait_until(at(f0))
        order = _doubled_order(order)
        new_sp = place(_ring_spins(L, c, R, _H_LEN[L], width=3.2 if L < 32 else 2.6,
                                   tip=0.13 if L < 32 else 0.1, order=order))
        e1n, bandn = _h_levels(L)
        gapn, glabn = _h_gap(L)
        place(VGroup(e1n, bandn, gapn, glabn))
        play_to(f1, Transform(spins, new_sp), Transform(P["band"], bandn),
                Transform(P["e1"], e1n), Transform(P["gap"], gapn), Transform(P["glab"], glabn),
                nums[i].animate.set_opacity(0), nums[i + 1].animate.set_opacity(1))
    # 3. claimed for even-length rings: the examples L = 8, 16, 32 become "L even"
    scene.wait_until(at(0.715))
    even = _mtex(r"L\ \text{even}", font_size=36, color=ACC)
    even.scale(k).move_to(VGroup(lhs, nums[2])).set_z_index(_Z_NEW)
    play_to(0.765, FadeOut(VGroup(lhs, nums[2]), shift=UP * 0.2 * k),
            FadeIn(even, shift=UP * 0.2 * k))
    adopt(even)
    # 4. ... with an explicit lower bound: written under the text column, which slides up
    card = next(m for m in scene.mobjects if len(m.submobjects) == 3 and m.submobjects[1] is mob)
    box, right = card[0], card[2]
    formula = _mtex(r"\liminf_{L\to\infty}\,\gamma_L", r"\ge", r"\frac{\log 20}{784}",
                    r"\approx 0.0038", r"> 0", font_size=36, color=WHITE_)
    formula[2:4].set_color(ACC)
    room = box.get_right()[0] - 0.35 - right.get_left()[0]
    if formula.width > room:
        formula.scale_to_fit_width(room)
    buff = 0.42
    block_h = right.height + buff + formula.height
    dy = (box.get_center()[1] + block_h / 2) - right.get_top()[1]
    formula.next_to(right.copy().shift(UP * dy), DOWN, buff=buff, aligned_edge=LEFT)
    formula.set_z_index(_Z_NEW)
    scene.wait_until(at(0.775))
    play_to(0.85, right.animate.shift(UP * dy), Write(formula))
    adopt(formula)
    # the bound itself, boxed as the narration names it
    frame = SurroundingRectangle(formula[2:4], color=ACC, buff=0.1, stroke_width=2.4,
                                 corner_radius=0.08).set_z_index(_Z_NEW)
    scene.wait_until(at(0.885))
    play_to(0.955, Create(frame))
    adopt(frame)


# ======================================================================= 145 Rokhlin
def _cat_points(n, N=520, seed=3):
    """A drop of dye (disc) pushed n times through Arnold's cat map (mixing of all orders)."""
    rng = np.random.default_rng(seed)
    r = 0.15 * np.sqrt(rng.random(N))
    th = TAU * rng.random(N)
    P = np.c_[0.3 + r * np.cos(th), 0.62 + r * np.sin(th)]
    A = np.array([[2, 1], [1, 1]])
    for _ in range(n):
        P = (P @ A.T) % 1.0
    return P


def _dye_panel(n, side, center, r=0.011, N=520):
    box = RoundedRectangle(width=side, height=side, corner_radius=0.05, stroke_color=GREY_,
                           stroke_width=1.4, stroke_opacity=0.8).move_to(center)
    P = _cat_points(n, N) * side + np.array(center[:2]) - side / 2
    return VGroup(box, _cloud(P, r, ACC, 0.95))


def icon_rokhlin():
    s = 0.66
    xs = (-0.82, 0.0, 0.82)
    panels = [_dye_panel(n, s, _p(x, 0)) for n, x in zip((0, 2, 6), xs)]
    arrows = VGroup(*[_arrow(_p(x + s / 2 + 0.025, 0), _p(x + 0.82 - s / 2 - 0.025, 0), GREY_, 1.6, 0.06)
                      for x in xs[:2]])
    return VGroup(*panels, arrows)


def big_rokhlin():
    g = _dye_panel(0, 4.2, ORIGIN, r=0.022, N=1400)
    g.w0, g.c0 = g.width, g.get_center()
    return g


def anim_rokhlin(scene, mob, T):
    k = mob.width / mob.w0
    for n, frac in ((1, 0.25), (2, 0.25), (6, 0.3)):
        new = _dye_panel(n, 4.2, ORIGIN, r=0.022, N=1400)
        VGroup(new).scale(k, about_point=ORIGIN).shift(mob.get_center() - k * mob.c0)
        scene.play(Transform(mob[1], new[1]), run_time=frac * T)


# ======================================================================= 146 standard map
def _std_orbit(K, th, p, n):
    out = np.empty((n, 2))
    for i in range(n):
        p = (p + K * np.sin(th) + PI) % TAU - PI
        th = (th + p) % TAU
        out[i] = th, p
    return out


def icon_standard_map():
    K = 2.2
    W, H = 2.1, 0.94
    sx, sy = W / (2 * TAU), H / TAU

    def tf(o):
        both = np.concatenate([o, o + [TAU, 0]])
        return np.c_[both[:, 0] * sx - W / 2, both[:, 1] * sy]

    chaos = _std_orbit(K, 0.3, 2.5, 1150)
    islands = np.concatenate([_std_orbit(K, PI + a, 0.0, 150) for a in (0.1, 0.25, 0.55)])
    frame = Rectangle(width=W, height=H, stroke_color=DIM, stroke_width=1.2)
    return VGroup(frame, _cloud(tf(chaos), 0.0085, ACC, 0.78), _cloud(tf(islands), 0.0075, WHITE_, 0.9))


# ======================================================================= 150 triangular billiard
def _billiard(V, p, ang, n):
    d = np.array([np.cos(ang), np.sin(ang)])
    pts = [p.copy()]
    for _ in range(n):
        best = None
        for i in range(3):
            a, b = V[i], V[(i + 1) % 3]
            e = b - a
            M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
            t, s = np.linalg.solve(M, a - p)
            if t > 1e-7 and -1e-9 <= s <= 1 + 1e-9 and (best is None or t < best[0]):
                best = (t, e)
        t, e = best
        p = p + t * d
        nrm = np.array([-e[1], e[0]]) / np.linalg.norm(e)
        d = d - 2 * np.dot(d, nrm) * nrm
        pts.append(p.copy())
    return np.array(pts)


def icon_billiard():
    V = [np.array([-1.0, -0.43]), np.array([1.05, -0.43]), np.array([-0.32, 0.46])]
    tri = Polygon(*[_p(*v) for v in V], stroke_color=WHITE_, stroke_width=2.2)
    path = _billiard(V, np.array([0.12, -0.43]), 1.13, 27)
    parts = VGroup()
    for (i0, i1), op in zip(((0, 10), (9, 19), (18, 28)), (0.25, 0.5, 0.9)):
        parts.add(_poly(path[i0:i1], ACC, 1.4, op))
    path[-1] = (path[-2] + path[-1]) / 2          # the ball is mid-flight on the last chord
    ball = Dot(_p(*path[-1]), radius=0.04, color=WHITE_)
    return VGroup(parts, tri, ball)


# ======================================================================= 213 percolation
def _perc(nx, ny, p, seed):
    rng = np.random.default_rng(seed)
    parent = list(range(nx * ny))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    bonds = []
    for i in range(nx):
        for j in range(ny):
            for di, dj in ((1, 0), (0, 1)):
                if i + di < nx and j + dj < ny and rng.random() < p:
                    a, b = i * ny + j, (i + di) * ny + j + dj
                    bonds.append((a, b))
                    parent[find(a)] = find(b)
    return bonds, [find(i) for i in range(nx * ny)]


def icon_percolation():
    nx, ny, h = 16, 7, 0.13
    best = None
    for seed in range(60):                   # a big, but non-spanning, critical cluster
        bonds, root = _perc(nx, ny, 0.5, seed)
        sizes = {}
        for r in root:
            sizes[r] = sizes.get(r, 0) + 1
        big = max(sizes, key=sizes.get)
        cols = {i // ny for i in range(nx * ny) if root[i] == big}
        rows = {i % ny for i in range(nx * ny) if root[i] == big}
        if 0 in cols and nx - 1 in cols or 0 in rows and ny - 1 in rows:
            continue
        if best is None or sizes[big] > best[0]:
            best = (sizes[big], bonds, root, big)
        if sizes[big] >= 30:
            break
    _, bonds, root, big = best
    xy = lambda i: ((i // ny - (nx - 1) / 2) * h, (i % ny - (ny - 1) / 2) * h)
    other = [(xy(a), xy(b)) for a, b in bonds if root[a] != big]
    main = [(xy(a), xy(b)) for a, b in bonds if root[a] == big]
    sites = _cloud([xy(i) for i in range(nx * ny)], 0.011, GREY_, 0.6)
    frame = Rectangle(width=nx * h, height=ny * h, stroke_color=DIM, stroke_width=1.2)
    return VGroup(frame, sites, _segs(other, GREY_, 1.5, 0.6), _segs(main, ACC, 2.4))


# ======================================================================= 214 Benjamini-Schramm
def icon_bs():
    # 3-regular tree (Bethe lattice) to depth 4, laid out radially
    depth, radii = 5, [0, 0.11, 0.21, 0.3, 0.385, 0.46]
    nodes, edges = [(0, None)], []          # (depth, parent)
    frontier = [0]
    for d in range(1, depth + 1):
        nf = []
        for v in frontier:
            for _ in range(3 if d == 1 else 2):
                nodes.append((d, v))
                edges.append((v, len(nodes) - 1))
                nf.append(len(nodes) - 1)
        frontier = nf
    leaves = frontier
    ang = {v: TAU * i / len(leaves) + 0.1 for i, v in enumerate(leaves)}
    for d in range(depth - 1, -1, -1):
        for v, (dv, _) in enumerate(nodes):
            if dv == d:
                ch = [ang[b] for a, b in edges if a == v]
                ang[v] = sum(ch) / len(ch)
    c = np.array([-0.62, 0.0])
    pos = {v: c + radii[d] * np.array([np.cos(ang[v]), np.sin(ang[v])]) for v, (d, _) in enumerate(nodes)}
    rng = np.random.default_rng(11)
    open_ = [rng.random() < 0.72 for _ in edges]
    parent = list(range(len(nodes)))

    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for (a, b), o in zip(edges, open_):
        if o:
            parent[find(a)] = find(b)
    reach = {}
    for v in leaves:
        reach[find(v)] = reach.get(find(v), 0) + 1
    order = sorted(reach, key=reach.get, reverse=True)[:3]
    cols = dict(zip(order, (ACC, WHITE_, GREY_)))
    groups = {r: [] for r in order}
    rest = []
    for (a, b), o in zip(edges, open_):
        r = find(a)
        if o and r in groups:
            groups[r].append((pos[a], pos[b]))
        else:
            rest.append((pos[a], pos[b]))
    tree = VGroup(_segs(rest, GREY_, 1.0, 0.35),
                  *[_segs(groups[r], cols[r], 2.1) for r in order if groups[r]])
    # p-axis: p_c < p_u, with the window between them highlighted
    xa, xb, y = 0.08, 1.08, -0.2
    xc, xu = 0.33, 0.8
    axis = Line(_p(xa, y), _p(xb, y), color=GREY_, stroke_width=1.6)
    win = Line(_p(xc, y), _p(xu, y), color=ACC, stroke_width=5)
    ticks = VGroup(*[Line(_p(x, y - 0.05), _p(x, y + 0.05), color=WHITE_, stroke_width=1.8)
                     for x in (xc, xu)])
    lc = _mtex("p_c", font_size=28, color=WHITE_).next_to(_p(xc, y + 0.05), UP, buff=0.07)
    lu = _mtex("p_u", font_size=28, color=WHITE_).next_to(_p(xu, y + 0.05), UP, buff=0.07)
    l0 = _mtex("0", font_size=22, color=GREY_).next_to(_p(xa, y), DOWN, buff=0.08)
    l1 = _mtex("1", font_size=22, color=GREY_).next_to(_p(xb, y), DOWN, buff=0.08)
    return VGroup(tree, axis, win, ticks, lc, lu, l0, l1)


# ======================================================================= 230 SLE
def _sle_trace(kappa, N, T, seed):
    """Chordal SLE_kappa trace by the vertical-slit Loewner discretisation."""
    rng = np.random.default_rng(seed)
    dt = T / N
    U = np.concatenate([[0.0], np.cumsum(rng.normal(0, np.sqrt(kappa * dt), N))])
    z = (U[1:] + 2j * np.sqrt(dt)).astype(complex)
    for j in range(N - 2, -1, -1):
        w = z[j + 1:]
        u = U[j + 1]
        s = np.sqrt((w - u) ** 2 - 4 * dt)
        s = np.where(s.imag < 0, -s, s)
        z[j + 1:] = u + s
    return np.concatenate([[0.0], z])


def icon_sle():
    tr = _sle_trace(4.0, 2500, 1.0, 2)
    x, y = -tr.real, tr.imag                       # mirrored: grows left to right
    sc = 2.0 / (x.max() - x.min())
    x = (x - x.min()) * sc - 1.0
    y = y * sc - 0.36
    base = Line(_p(-1.06, -0.36), _p(1.06, -0.36), color=GREY_, stroke_width=1.6)
    curve = _poly(np.c_[x, y][::2], ACC, 1.5)
    # cover a stretch of the curve by small balls (Hausdorff measure)
    r = 0.065
    centers = []
    for i in range(900, 1700, 3):
        q = np.array([x[i], y[i]])
        if not centers or min(np.linalg.norm(q - c) for c in centers) > 1.5 * r:
            centers.append(q)
    balls = VGroup(*[Circle(radius=r, stroke_color=WHITE_, stroke_width=1.1, stroke_opacity=0.75)
                     .move_to(_p(*q)) for q in centers[:14]])
    origin = Dot(_p(x[0], y[0]), radius=0.035, color=WHITE_)
    return VGroup(base, curve, balls, origin)


# ======================================================================= 238 Thorp shuffle
def icon_thorp():
    n, cw, chh = 8, 0.46, 0.065
    ys = np.linspace(0.38, -0.38, n)
    xl, xr = -0.78, 0.78
    coins = [0, 1, 1, 0]                            # coin flip per pair: who drops first
    order = []
    for i, c in enumerate(coins):
        order += [i, 4 + i] if c == 0 else [4 + i, i]
    col = lambda i: ACC if i < 4 else WHITE_
    left = VGroup(*[RoundedRectangle(width=cw, height=chh, corner_radius=0.015, stroke_width=0,
                                     fill_color=col(i), fill_opacity=0.9).move_to(_p(xl, ys[i]))
                    for i in range(n)])
    right = VGroup(*[RoundedRectangle(width=cw, height=chh, corner_radius=0.015, stroke_width=0,
                                      fill_color=col(i), fill_opacity=0.9).move_to(_p(xr, ys[j]))
                     for j, i in enumerate(order)])
    links = VGroup()
    for j, i in enumerate(order):
        a, b = _p(xl + cw / 2 + 0.04, ys[i]), _p(xr - cw / 2 - 0.04, ys[j])
        m = VMobject(stroke_color=col(i), stroke_width=1.3, stroke_opacity=0.55)
        m.set_points([a, a + RIGHT * 0.45, b + LEFT * 0.45, b])
        links.add(m)
    cut = DashedLine(_p(xl - cw / 2 - 0.05, 0), _p(xl + cw / 2 + 0.05, 0), color=GREY_,
                     stroke_width=1.2, dash_length=0.04)
    return VGroup(links, left, right, cut)


# ======================================================================= 221 Mezard-Parisi
def icon_spin_glass():
    V = [(-0.95, 0.22), (-0.72, -0.3), (-0.45, 0.36), (-0.2, -0.12), (0.05, 0.38),
         (0.1, -0.4), (0.36, 0.05), (0.62, 0.38), (0.66, -0.3), (0.95, 0.06)]
    E = [(0, 1, 1), (0, 2, -1), (1, 3, 1), (2, 3, 1), (2, 4, 1), (3, 5, -1), (3, 6, 1),
         (4, 6, -1), (5, 8, 1), (6, 7, 1), (6, 8, -1), (7, 9, 1), (8, 9, 1)]
    spins = [1, -1, -1, 1, 1, -1, -1, 1, 1, -1]
    pos, neg = [], []
    for a, b, J in E:
        pa, pb = np.array(V[a]), np.array(V[b])
        u = (pb - pa) / np.linalg.norm(pb - pa)
        pa, pb = pa + 0.1 * u, pb - 0.1 * u
        if J > 0:
            pos.append((pa, pb))
        else:                                       # dashed: split into short pieces
            L = np.linalg.norm(pb - pa)
            k = max(2, int(L / 0.07))
            for t in range(k):
                t0, t1 = t / k, (t + 0.55) / k
                neg.append((pa + (pb - pa) * t0, pa + (pb - pa) * t1))
    arrows = VGroup(*[_spin(_p(*v), [0, s, 0], 0.2, WHITE_, 2.0, 0.065) for v, s in zip(V, spins)])
    return VGroup(_segs(neg, GREY_, 1.5, 0.85), _segs(pos, ACC, 2.0, 0.9), arrows)


# ======================================================================= 261 Anderson
def icon_anderson():
    rng = np.random.default_rng(5)
    xs = np.linspace(-1.0, 1.0, 41)
    V = rng.random(len(xs))
    bars = _segs([((x, -0.46), (x, -0.46 + 0.17 * v)) for x, v in zip(xs, V)], GREY_, 2.0, 0.55)
    base_y, H, x0, xi = -0.2, 0.68, 0.08, 0.14
    amp = np.exp(-np.abs(xs - x0) / xi) * (0.65 + 0.35 * rng.random(len(xs)))
    amp = amp / amp.max()
    fine = np.linspace(-1.0, 1.0, 241)
    a = np.interp(fine, xs, amp)
    top = np.c_[fine, base_y + H * a]
    curve = _poly(top, ACC, 2.0)
    fill = Polygon(*[_p(*q) for q in top], _p(1.0, base_y), _p(-1.0, base_y), stroke_width=0,
                   fill_color=ACC, fill_opacity=0.2)
    axis = Line(_p(-1.02, base_y), _p(1.02, base_y), color=DIM, stroke_width=1.4)
    return VGroup(bars, fill, axis, curve)


# ======================================================================= 263 ionization
def icon_atom():
    c = _p(-0.52, 0.0)
    orbs = VGroup(*[Circle(radius=r, stroke_color=GREY_, stroke_width=1.3, stroke_opacity=0.7).move_to(c)
                    for r in (0.2, 0.38)])
    nuc = Dot(c, radius=0.075, color=ACC)
    plus = _mtex("+", font_size=20, color=BG).move_to(c)
    els = VGroup(*[Dot(c + r * np.array([np.cos(a), np.sin(a), 0]), radius=0.034, color=WHITE_)
                   for r, a in [(0.2, 0.5), (0.2, 0.5 + PI), (0.38, 1.6), (0.38, 2.9),
                                (0.38, 4.1), (0.38, 5.3)]])
    esc = ArcBetweenPoints(c + 0.44 * np.array([np.cos(0.55), np.sin(0.55), 0]), _p(0.68, 0.16),
                           angle=-0.5)
    trail = DashedVMobject(esc.set_stroke(GREY_, 1.4, 0.8), num_dashes=9)
    lone = Dot(_p(0.8, 0.12), radius=0.04, color=WHITE_)
    push = _arrow(_p(0.9, 0.1), _p(1.12, 0.06), GREY_, 1.6, 0.07)
    return VGroup(orbs, els, nuc, plus, trail, lone, push)


# ======================================================================= 260 Penrose
def icon_penrose():
    rs, zm, cx = 0.17, 0.4, -0.62
    z = np.linspace(-zm, zm, 61)
    r = rs + z ** 2 / (4 * rs)                    # Flamm's paraboloid (Schwarzschild slice)
    left = _poly(np.c_[cx - r, z], GREY_, 1.6, smooth=True)
    right = _poly(np.c_[cx + r, z], GREY_, 1.6, smooth=True)
    rings = VGroup()
    for zz, col, w, op in ((-zm, GREY_, 1.4, 0.8), (-0.22, DIM, 1.1, 1), (0.22, DIM, 1.1, 1),
                           (zm, GREY_, 1.4, 0.8)):
        rr = rs + zz ** 2 / (4 * rs)
        rings.add(Ellipse(width=2 * rr, height=0.42 * rr, stroke_color=col, stroke_width=w,
                          stroke_opacity=op).move_to(_p(cx, zz)))
    throat = Ellipse(width=2 * rs, height=0.42 * rs, stroke_color=ACC, stroke_width=2.6).move_to(_p(cx, 0))
    A = _mtex("A", font_size=24, color=ACC).next_to(throat, RIGHT, buff=0.06)
    form = _mtex(r"m \ge \sqrt{\frac{A}{16\pi}}", font_size=30, color=WHITE_)
    form.next_to(_p(cx + rs + 0.42 + 0.1, 0), RIGHT, buff=0)
    return VGroup(rings, left, right, throat, A, form)


# ======================================================================= 267 BEC
def icon_bec():
    x = np.linspace(-1.0, 1.0, 201)
    base = -0.42
    th = 0.3 * np.exp(-x ** 2 / (2 * 0.33 ** 2))
    spike = th + 0.86 * np.exp(-x ** 2 / (2 * 0.035 ** 2))
    xs = np.linspace(-0.16, 0.16, 81)
    sp = 0.3 * np.exp(-xs ** 2 / (2 * 0.33 ** 2)) + 0.86 * np.exp(-xs ** 2 / (2 * 0.035 ** 2))
    therm_fill = Polygon(*[_p(a, base + b) for a, b in zip(x, th)], _p(1.0, base), _p(-1.0, base),
                         stroke_width=0, fill_color=GREY_, fill_opacity=0.22)
    therm = _poly(np.c_[x, base + th], GREY_, 1.6)
    peak_fill = Polygon(*[_p(a, base + b) for a, b in zip(xs, sp)], stroke_width=0,
                        fill_color=ACC, fill_opacity=0.45)
    peak = _poly(np.c_[xs, base + sp], ACC, 2.2)
    axis = Line(_p(-1.04, base), _p(1.04, base), color=GREY_, stroke_width=1.5)
    return VGroup(therm_fill, peak_fill, therm, peak, axis)


# ======================================================================= 274 QAC0
def icon_qac0():
    ys = np.linspace(0.36, -0.36, 5)
    x0, x1 = -1.0, 0.82
    wires = VGroup(*[Line(_p(x0, y), _p(x1, y), color=GREY_, stroke_width=1.3, stroke_opacity=0.8)
                     for y in ys])
    g = 0.13

    def box(x, y):
        return Square(side_length=g, stroke_color=WHITE_, stroke_width=1.4, fill_color=CARD,
                      fill_opacity=1).move_to(_p(x, y))

    def toffoli(x, ctrl, targ):
        lo, hi = min(ctrl + [targ]), max(ctrl + [targ])
        v = Line(_p(x, ys[hi]), _p(x, ys[lo]), color=ACC, stroke_width=1.8)
        dots = VGroup(*[Dot(_p(x, ys[i]), radius=0.032, color=ACC) for i in ctrl])
        t = Circle(radius=0.065, stroke_color=ACC, stroke_width=1.8, fill_color=CARD,
                   fill_opacity=1).move_to(_p(x, ys[targ]))
        plus = VGroup(Line(t.get_top(), t.get_bottom()), Line(t.get_left(), t.get_right()))
        plus.set_stroke(ACC, 1.6)
        return VGroup(v, dots, t, plus)

    layers = VGroup(
        VGroup(*[box(-0.7, y) for y in ys]),
        toffoli(-0.35, [1, 2, 4], 0),
        toffoli(-0.05, [0, 3], 2),
        VGroup(*[box(0.25, y) for y in ys[[0, 2, 3]]]),
        toffoli(0.52, [1, 2, 3, 4], 0),
    )
    # measured output qubit
    mx = 0.95
    meter = VGroup(
        Rectangle(width=0.2, height=0.15, stroke_color=ACC, stroke_width=1.5, fill_color=CARD,
                  fill_opacity=1),
        Arc(radius=0.06, start_angle=PI * 0.15, angle=PI * 0.7, stroke_color=ACC,
            stroke_width=1.3).shift(DOWN * 0.03),
        Line(ORIGIN, UR * 0.065, color=ACC, stroke_width=1.3).shift(DOWN * 0.04),
    ).move_to(_p(mx, ys[0]))
    return VGroup(wires, layers, meter)


# ======================================================================= scene
ICONS = {
    "268": icon_haldane, "145": icon_rokhlin, "146": icon_standard_map, "150": icon_billiard,
    "213": icon_percolation, "214": icon_bs, "230": icon_sle, "238": icon_thorp,
    "221": icon_spin_glass, "261": icon_anderson, "263": icon_atom, "260": icon_penrose,
    "267": icon_bec, "274": icon_qac0,
}
FEATURES = {
    "268": dict(big=big_haldane, animate=anim_haldane),
    "145": dict(big=big_rokhlin, animate=anim_rokhlin),
}


def _tiles():
    spec = json.loads((VIDEO / "data" / "grids.json").read_text())["c7_grid"]
    out = []
    for d in spec:
        t = dict(num=d["num"], name=d["name"], verdict=d["verdict"], icon=ICONS.get(d["num"]))
        if d.get("caption"):
            t["feature"] = dict(caption=d["caption"], **FEATURES.get(d["num"], {}))
        out.append(t)
    return out


class C7Grid(GridScene):
    CHAPTER = "dp"
    COLS, ROWS = 5, 3
    TILES = _tiles()
