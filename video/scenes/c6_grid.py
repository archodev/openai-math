import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
from lib.grid import GridScene

import json

ACC = PINK_          # chapter accent (Algebra, Groups & Logic)
SW = 2.0             # main stroke
SW2 = 1.2            # secondary stroke
Z_FEAT = 61          # above the feature card (z=60) and the dimmer (z=50)


# =====================================================================
# small helpers
# =====================================================================
def P(x, y):
    return np.array([x, y, 0.0])


def _arrow(a, b, color=GREY_, sw=1.6, tip=0.09):
    return Arrow(P(*a), P(*b), buff=0, color=color, stroke_width=sw, tip_length=tip,
                 max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=40)


def _curved(a, b, angle, color=ACC, sw=1.6, tip=0.08):
    return CurvedArrow(P(*a), P(*b), angle=angle, color=color, stroke_width=sw,
                       tip_length=tip)


def _path(polylines, color=GREY_, sw=SW2, opacity=1.0, closed=False):
    """One VMobject made of many polylines (keeps submobject counts low)."""
    vm = VMobject(stroke_color=color, stroke_width=sw, stroke_opacity=opacity)
    for pl in polylines:
        pts = [np.array(p, dtype=float) if len(p) == 3 else P(*p) for p in pl]
        if closed:
            pts = pts + [pts[0]]
        vm.start_new_path(pts[0])
        vm.add_points_as_corners(pts[1:])
    return vm


def _boxes(cells, s, color=WHITE_, sw=1.0, fill=0.1, origin=(0, 0)):
    """Young-diagram style boxes, all in a single VMobject (one subpath per box)."""
    ox, oy = origin
    polys = []
    for (j, i) in cells:
        x0, y0 = ox + j * s, oy - i * s
        polys.append([(x0, y0), (x0 + s, y0), (x0 + s, y0 - s), (x0, y0 - s)])
    vm = _path(polys, color=color, sw=sw, closed=True)
    vm.set_fill(color, opacity=fill)
    return vm


def _young(rows, s, **kw):
    return _boxes([(j, i) for i, r in enumerate(rows) for j in range(r)], s, **kw)


# =====================================================================
# hyperbolic plane (Poincare disk) -- exact {p,q} tilings
# =====================================================================
def _circ3(z1, z2, z3):
    ax, ay, bx, by, cx, cy = z1.real, z1.imag, z2.real, z2.imag, z3.real, z3.imag
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay)
          + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx)
          + (cx * cx + cy * cy) * (bx - ax)) / d
    c = complex(ux, uy)
    return c, abs(z1 - c)


def _through_origin(a, b):
    return abs(a) < 1e-9 or abs(b) < 1e-9 or abs((np.conj(a) * b).imag) < 1e-9


def _reflector(a, b):
    """Hyperbolic reflection in the geodesic through a, b."""
    if _through_origin(a, b):
        u = a / abs(a) if abs(a) > 1e-9 else b / abs(b)
        return lambda z: u * u * np.conj(z)
    c, r = _circ3(a, b, 1 / np.conj(a))
    return lambda z: c + r * r / np.conj(z - c)


def _geodesic(a, b, n=10):
    if _through_origin(a, b):
        return [a + (b - a) * t for t in np.linspace(0, 1, n)]
    c, r = _circ3(a, b, 1 / np.conj(a))
    ta, tb = np.angle(a - c), np.angle(b - c)
    d = (tb - ta + np.pi) % (2 * np.pi) - np.pi
    return [c + r * np.exp(1j * (ta + d * t)) for t in np.linspace(0, 1, n)]


def hyp_tiling(p=5, q=4, depth=4, min_size=0.03, rot=np.pi / 2):
    """Tiles of the regular {p,q} tiling reachable within `depth` edge-reflections
    of the central tile.  Returns (tiles, adjacency); tile = dict(v, c, d)."""
    R = np.arccosh(1 / np.tan(np.pi / p) / np.tan(np.pi / q))
    r = np.tanh(R / 2)
    v0 = [r * np.exp(1j * (rot + 2 * np.pi * k / p)) for k in range(p)]
    tiles = [dict(v=v0, c=0j, d=0)]
    centers = [0j]

    def find(z):
        arr = np.abs(np.array(centers) - z)
        j = int(np.argmin(arr))
        return j if arr[j] < 1e-6 else None

    frontier = [0]
    for d in range(1, depth + 1):
        nxt = []
        for ti in frontier:
            t = tiles[ti]
            for k in range(p):
                f = _reflector(t["v"][k], t["v"][(k + 1) % p])
                nc = f(t["c"])
                if find(nc) is not None:
                    continue
                nv = [f(z) for z in t["v"]]
                if max(abs(nv[i] - nv[(i + 1) % p]) for i in range(p)) < min_size:
                    continue
                tiles.append(dict(v=nv, c=nc, d=d))
                centers.append(nc)
                nxt.append(len(tiles) - 1)
        frontier = nxt
    adj = set()
    for ti, t in enumerate(tiles):
        for k in range(p):
            j = find(_reflector(t["v"][k], t["v"][(k + 1) % p])(t["c"]))
            if j is not None and j != ti:
                adj.add((min(ti, j), max(ti, j)))
    return tiles, adj


def _tiling_edges(tiles, n=9):
    seen, lines = set(), []
    for t in tiles:
        vs = t["v"]
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            m = (a + b) / 2
            key = (round(m.real, 5), round(m.imag, 5))
            if key in seen:
                continue
            seen.add(key)
            lines.append(_geodesic(a, b, n))
    return lines


def _to_xy(zs, R, C=(0, 0)):
    return [P(C[0] + R * z.real, C[1] + R * z.imag) for z in zs]


def _tile_poly(t, R, C=(0, 0), n=7):
    vs = t["v"]
    pts = []
    for k in range(len(vs)):
        pts += _geodesic(vs[k], vs[(k + 1) % len(vs)], n)[:-1]
    return _to_xy(pts, R, C)


# =====================================================================
# ICONS (each ~2.8 x 0.95 units)
# =====================================================================
def _sphere(r, color=ACC, sw=2.2, sw2=1.0, op2=0.75):
    return VGroup(
        Circle(radius=r, stroke_color=color, stroke_width=sw),
        Ellipse(width=2 * r, height=0.56 * r, stroke_color=GREY_, stroke_width=sw2,
                stroke_opacity=op2),
        Ellipse(width=0.7 * r, height=2 * r, stroke_color=GREY_, stroke_width=sw2,
                stroke_opacity=op2),
    )


def ic_246():
    """Cannon: a sphere at infinity  =>  a tiling of hyperbolic space."""
    sph = _sphere(0.44).move_to(P(-0.95, 0))
    arr = tex(r"\Longrightarrow", 34, GREY_).move_to(P(-0.05, 0))
    R, C = 0.47, (0.95, 0)
    tiles, _ = hyp_tiling(5, 4, depth=3, min_size=0.06)
    til = _path([_to_xy(l, R, C) for l in _tiling_edges(tiles, 7)], GREY_, sw=0.8)
    fund = Polygon(*_tile_poly(tiles[0], R, C), stroke_width=0, fill_color=ACC,
                   fill_opacity=0.45)
    rim = Circle(radius=R, stroke_color=ACC, stroke_width=2.2).move_to(P(*C))
    return VGroup(sph, arr, fund, til, rim)


def _partition_regions(w, h, cuts, n=72):
    """Clip an ellipse (centred at 0) by half-planes; cuts: list of lists of
    (a, b, c) meaning a*x + b*y <= c."""
    ell = [np.array([w / 2 * np.cos(t), h / 2 * np.sin(t)])
           for t in np.linspace(0, 2 * np.pi, n, endpoint=False)]
    regs = []
    for hs in cuts:
        poly = ell
        for (a, b, c) in hs:
            out = []
            for i in range(len(poly)):
                p0, p1 = poly[i], poly[(i + 1) % len(poly)]
                f0, f1 = a * p0[0] + b * p0[1] - c, a * p1[0] + b * p1[1] - c
                if f0 <= 0:
                    out.append(p0)
                if f0 * f1 < 0:
                    out.append(p0 + f0 / (f0 - f1) * (p1 - p0))
            poly = out
        regs.append(poly)
    return regs


TINTS = [0.14, 0.30, 0.48, 0.66]


def ic_244():
    """Partition principle: pieces of X map back into X injectively."""
    w, h, cx = 1.3, 0.92, -0.62
    cuts = [[(1, 0.35, -0.12)],
            [(-1, -0.35, 0.12), (0, 1, 0.02)],
            [(-1, -0.35, 0.12), (0, -1, -0.02)]]
    regs = _partition_regions(w, h, cuts)
    pieces = VGroup(*[Polygon(*[P(cx + q[0], q[1]) for q in r], stroke_color=ACC,
                              stroke_width=1.3, fill_color=ACC, fill_opacity=TINTS[i])
                      for i, r in enumerate(regs)])
    X = Ellipse(width=w, height=h, stroke_color=WHITE_, stroke_width=1.8).move_to(P(cx, 0))
    dpos = [(-0.42, 0.13), (-0.33, -0.17), (-0.47, -0.06),
            (0.06, 0.25), (0.33, 0.13), (0.1, -0.22), (0.38, -0.12)]
    dots = VGroup(*[Dot(P(cx + x, y), radius=0.035, color=WHITE_) for x, y in dpos])
    ys = [0.3, 0.0, -0.3]
    nodes = VGroup(*[RoundedRectangle(width=0.16, height=0.16, corner_radius=0.04,
                                      stroke_color=ACC, stroke_width=1.3, fill_color=ACC,
                                      fill_opacity=TINTS[i]).move_to(P(1.0, y))
                     for i, y in enumerate(ys)])
    targets = [3, 4, 6]   # three distinct points of X
    arrows = VGroup(*[_curved((0.9, ys[i]), (cx + dpos[j][0] + 0.04, dpos[j][1]),
                              angle=0.5 if i < 2 else -0.4, sw=1.4, tip=0.07)
                      for i, j in enumerate(targets)])
    return VGroup(pieces, X, dots, nodes, arrows)


def ic_193():
    """Serre: two subvarieties meeting at a point, multiplicity chi > 0."""
    x0 = -0.95
    xs = np.linspace(-0.56, 0.56, 30)
    M = VMobject(stroke_color=ACC, stroke_width=2.2).set_points_smoothly(
        [P(x + x0, 1.5 * x ** 3 + 0.25 * x) for x in xs])
    N = VMobject(stroke_color=WHITE_, stroke_width=1.8).set_points_smoothly(
        [P(x + x0, -0.5 * x + 0.75 * x ** 2) for x in xs])
    loc = DashedVMobject(Circle(radius=0.27, stroke_color=GREY_, stroke_width=1.1),
                         num_dashes=14).move_to(P(x0, 0))
    pt = Dot(P(x0, 0), radius=0.045, color=WHITE_)
    f = MathTex(r"\chi(", "M", ",", "N", r")>0", font_size=32, color=WHITE_)
    f[1].set_color(ACC)
    f.move_to(P(0.78, 0))
    return VGroup(loc, N, M, pt, f)


def ic_194():
    """Lech: multiplicity can only grow along a flat map, e(R) <= e(S)."""
    ts = np.linspace(-1.22, 1.22, 60)
    raw = [P(0.5 * (t * t - 1), 0.5 * (t ** 3 - t)) for t in ts]   # nodal cubic
    arr = np.array(raw)
    shift = P(-1.42, 0) - (arr.min(axis=0) + arr.max(axis=0)) / 2
    node = VMobject(stroke_color=ACC, stroke_width=2.0).set_points_smoothly(
        [q + shift for q in raw])
    nd = Dot(shift, radius=0.042, color=WHITE_)          # the node (t = +-1) is the origin
    th = np.linspace(0, np.pi, 90)
    rose = VMobject(stroke_color=WHITE_, stroke_width=1.8).set_points_smoothly(
        [P(1.3 + 0.4 * np.cos(3 * a) * np.cos(a), 0.4 * np.cos(3 * a) * np.sin(a)) for a in th])
    rd = Dot(P(1.3, 0), radius=0.042, color=ACC)     # ordinary triple point
    f = MathTex(r"e(R)\le e(S)", font_size=30, color=WHITE_).move_to(P(0, 0))
    return VGroup(node, nd, f, rose, rd)


def _grid(n, s, color=GREY_, sw=1.0):
    lines = []
    for k in range(1, n):
        lines.append([(-s / 2 + k * s / n, -s / 2), (-s / 2 + k * s / n, s / 2)])
        lines.append([(-s / 2, -s / 2 + k * s / n), (s / 2, -s / 2 + k * s / n)])
    inner = _path(lines, color, sw=sw * 0.8, opacity=0.8) if lines else VMobject()
    box = Square(side_length=s, stroke_color=WHITE_, stroke_width=sw * 1.3)
    return VGroup(box, inner)


def ic_201():
    """Kurosh: two generators, yet the dimension over the centre is infinite."""
    gens = MathTex(r"\langle a,b\rangle", font_size=30, color=ACC).move_to(P(-1.2, 0))
    sizes = [(1, 0.2), (2, 0.34), (4, 0.52), (8, 0.78)]
    x = -0.72
    grids = VGroup()
    for n, s in sizes:
        g = _grid(n, s)
        g.move_to(P(x + s / 2, 0))
        x += s + 0.13
        grids.add(g)
    dots = tex(r"\cdots", 30, GREY_).move_to(P(x + 0.08, 0))
    inf = tex(r"\infty", 40, RED_).next_to(dots, RIGHT, buff=0.1)
    return VGroup(gens, grids, dots, inf)


def ic_205():
    """Saxl: (staircase) tensor (staircase) contains every irreducible."""
    s = 0.2
    stair = _young([4, 3, 2, 1], s, color=ACC, sw=1.4, fill=0.35)
    stair.move_to(P(-1.05, 0))
    sq = MathTex(r"\otimes 2", font_size=26, color=ACC)
    sq.next_to(stair, RIGHT, buff=0.04).align_to(stair, UP)
    sup = tex(r"\supseteq", 36, WHITE_).move_to(P(-0.25, 0))
    t = 0.1
    small = VGroup(
        _young([5, 3, 2], t, sw=0.9),
        _young([3, 3, 2, 1, 1], t, sw=0.9),
        _young([4, 4, 1, 1], t, sw=0.9),
        _young([2, 2, 2, 2, 2], t, sw=0.9),
    )
    small.arrange(RIGHT, buff=0.14, aligned_edge=UP)
    small.next_to(sup, RIGHT, buff=0.16)
    small.align_to(stair, UP).shift(DOWN * 0.1)
    dots = tex(r"\cdots", 26, GREY_).next_to(small, RIGHT, buff=0.08)
    return VGroup(stair, sq, sup, small, dots)


def ic_202():
    """Alperin: inside one block, Brauer characters match weights one-to-one."""
    S = 0.86
    outer = Square(side_length=S, stroke_color=GREY_, stroke_width=1.2).move_to(P(-0.95, 0))
    tl = outer.get_corner(UL)
    blocks = VGroup()
    off = 0
    for i, b in enumerate([0.36, 0.28, 0.22]):
        sq = Square(side_length=b, stroke_color=ACC if i == 1 else GREY_,
                    stroke_width=1.6 if i == 1 else 1.0,
                    fill_color=ACC if i == 1 else GREY_, fill_opacity=0.4 if i == 1 else 0.12)
        sq.move_to(tl + P(off + b / 2, -off - b / 2))
        off += b
        blocks.add(sq)
    arr = _arrow((-0.38, 0), (0.0, 0), GREY_, sw=1.5)
    xs = [0.3, 0.6, 0.9, 1.2]
    top = VGroup(*[Dot(P(x, 0.22), radius=0.05, color=ACC) for x in xs])
    bot = VGroup(*[Square(side_length=0.085, stroke_width=0, fill_color=WHITE_, fill_opacity=1)
                   .rotate(PI / 4).move_to(P(x, -0.22)) for x in xs])
    links = _path([[(x, 0.16), (x, -0.16)] for x in xs], GREY_, sw=1.1)
    return VGroup(outer, blocks, arr, links, top, bot)


def _block_glyph(kind, s, color, op_stroke=1.0, op_fill=0.3, sw=1.0):
    box = Square(side_length=s, stroke_color=color, stroke_width=sw, stroke_opacity=op_stroke)
    fr = {1: [0.62], 2: [0.5, 0.3], 3: [0.4, 0.32, 0.2]}[kind]
    tl = box.get_corner(UL)
    polys, off = [], 0
    for f in fr:
        b = f * s
        x0, y0 = tl[0] + off, tl[1] - off
        polys.append([(x0, y0), (x0 + b, y0), (x0 + b, y0 - b), (x0, y0 - b)])
        off += b
    inner = _path(polys, color, sw=0, closed=True).set_fill(color, opacity=op_fill)
    return VGroup(box, inner)


def ic_203():
    """Donovan: infinitely many blocks, only finitely many Morita types."""
    kinds = [2, 1, 3, 3, 1, 2, 1, 3, 2, 2, 3, 1]
    left = VGroup()
    s = 0.22
    for idx, k in enumerate(kinds):
        r, c = divmod(idx, 4)
        op = [0.35, 0.6, 0.85, 1.0][c]
        g = _block_glyph(k, s, WHITE_, op_stroke=op, op_fill=0.25 * op, sw=1.0)
        g.move_to(P(-0.95 + c * 0.32, 0.32 - r * 0.32))
        left.add(g)
    dots = tex(r"\cdots", 28, GREY_).move_to(P(-1.48, 0))
    arr = _arrow((0.12, 0), (0.5, 0), GREY_, sw=1.5)
    right = VGroup(*[_block_glyph(k, 0.26, ACC, op_fill=0.45, sw=1.6) for k in (1, 2, 3)])
    right.arrange(DOWN, buff=0.07).move_to(P(0.82, 0))
    brace = RoundedRectangle(width=0.44, height=right.height + 0.14, corner_radius=0.08,
                             stroke_color=ACC, stroke_width=1.0, stroke_opacity=0.6).move_to(right)
    return VGroup(dots, left, arr, brace, right)


def _cycle(n, r, base, color=ACC, sw=1.5, dot_r=0.028):
    """Loop of n vertices sitting on top of `base` (base is one of the vertices)."""
    c = base + UP * r
    loop = Circle(radius=r, stroke_color=color, stroke_width=sw).move_to(c)
    pts = [c + r * np.array([np.cos(-PI / 2 + TAU * k / n), np.sin(-PI / 2 + TAU * k / n), 0])
           for k in range(1, n)]
    dots = VGroup(*[Dot(p, radius=dot_r, color=color) for p in pts])
    return VGroup(loop, dots)


def ic_247():
    """2-group: every element sits on a loop of length 2^k, yet the group is infinite."""
    y0 = -0.4
    xs = [-1.0, -0.55, 0.05, 0.92]
    loops = VGroup(*[_cycle(n, r, P(x, y0)) for n, r, x in
                     zip([2, 4, 8, 16], [0.1, 0.16, 0.25, 0.38], xs)])
    base = Line(P(-1.32, y0), P(1.42, y0), stroke_color=GREY_, stroke_width=1.4)
    nodes = VGroup(*[Dot(P(x, y0), radius=0.045, color=WHITE_) for x in xs])
    ld = tex(r"\cdots", 26, GREY_).next_to(base, LEFT, buff=0.06)
    rd = tex(r"\cdots", 26, GREY_).next_to(base, RIGHT, buff=0.06)
    return VGroup(base, loops, nodes, ld, rd)


def _small_graph(scale=1.0, color=WHITE_, sw=1.4, r=0.035):
    pts = [P(x * scale, y * scale) for x, y in
           [(-0.2, 0.13), (0.0, 0.2), (0.2, 0.13), (-0.2, -0.13), (0.0, -0.2), (0.2, -0.13)]]
    E = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (2, 5), (1, 4)]
    edges = _path([[pts[a], pts[b]] for a, b in E], color, sw=sw)
    dots = VGroup(*[Dot(p, radius=r, color=color) for p in pts])
    return VGroup(edges, dots)


def ic_250():
    """Boone-Higman: a group with solvable word problem sits inside a simple group."""
    G = _small_graph(1.0).move_to(P(-1.0, 0))
    hook = tex(r"\hookrightarrow", 36, GREY_).move_to(P(-0.3, 0))
    Rr = 0.46
    S = Circle(radius=Rr, stroke_color=ACC, stroke_width=2.0, fill_color=ACC,
               fill_opacity=0.08).move_to(P(0.6, 0))
    # faint hexagonal-ish lattice patch filling S
    lat_pts = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            p = P(0.6 + 0.15 * i + 0.075 * (j % 2), 0.13 * j)
            if np.linalg.norm(p - P(0.6, 0)) < Rr - 0.06:
                lat_pts.append(p)
    lat = VGroup(*[Dot(p, radius=0.016, color=ACC, fill_opacity=0.55) for p in lat_pts])
    Gin = _small_graph(0.8, WHITE_, sw=1.2, r=0.028).move_to(P(0.6, 0))
    return VGroup(G, hook, S, lat, Gin)


def ic_254():
    """Artin groups: a braid (the braid group is the type-A Artin group)."""
    n, gap, L = 4, 0.24, 0.34
    word = [(0, +1), (1, -1), (2, +1), (0, +1), (1, +1), (2, -1)]
    x0 = -1.3
    ys = [(1.5 - k) * gap for k in range(n)]
    pos = list(range(n))          # pos[strand] = slot
    colors = [ACC, WHITE_, GREY_, WHITE_]
    pieces = [[] for _ in range(n)]
    x = x0
    pad = 0.18
    for s in range(n):
        pieces[s].append(("line", P(x0 - pad, ys[s]), P(x0, ys[s])))
    for (i, sign) in word:
        a = pos.index(i)
        b = pos.index(i + 1)
        for s in range(n):
            if s not in (a, b):
                pieces[s].append(("line", P(x, ys[pos[s]]), P(x + L, ys[pos[s]])))
        over, under = (a, b) if sign > 0 else (b, a)
        for s in (a, b):
            y_from = ys[pos[s]]
            y_to = ys[i + 1] if pos[s] == i else ys[i]
            pieces[s].append(("over" if s == over else "under", P(x, y_from), P(x + L, y_to)))
        pos[a], pos[b] = pos[b], pos[a]
        x += L
    for s in range(n):
        pieces[s].append(("line", P(x, ys[pos[s]]), P(x + pad, ys[pos[s]])))
    strands = VGroup()
    for s in range(n):
        vm = VMobject(stroke_color=colors[s], stroke_width=2.0)
        for kind, a, b in pieces[s]:
            if kind == "line":
                vm.start_new_path(a)
                vm.add_line_to(b)
                continue
            dx = (b[0] - a[0]) * 0.5
            cb = CubicBezier(a, a + RIGHT * dx, b - RIGHT * dx, b)
            if kind == "over":
                vm.start_new_path(a)
                vm.add_cubic_bezier_curve_to(a + RIGHT * dx, b - RIGHT * dx, b)
            else:
                for lo, hi in ((0, 0.36), (0.64, 1)):
                    part = VMobject()
                    part.pointwise_become_partial(cb, lo, hi)
                    vm.start_new_path(part.points[0])
                    for k in range(0, len(part.points), 4):
                        vm.add_cubic_bezier_curve_to(*part.points[k + 1:k + 4])
        strands.add(vm)
    ends = VGroup(*[Dot(P(xx, y), radius=0.03, color=GREY_)
                    for xx in (x0 - pad, x + pad) for y in ys])
    bars = _path([[(x0 - pad, ys[0] + 0.1), (x0 - pad, ys[-1] - 0.1)],
                  [(x + pad, ys[0] + 0.1), (x + pad, ys[-1] - 0.1)]], GREY_, sw=1.2,
                 opacity=0.7)
    return VGroup(bars, strands, ends)


def ic_241():
    """Turing degrees: an irregular partial order whose only automorphism is id."""
    nodes = {
        "0": (-0.55, -0.42),
        "a": (-1.05, -0.08), "b": (-0.6, -0.04), "c": (-0.08, -0.12),
        "d": (-1.25, 0.3), "e": (-0.82, 0.26), "f": (-0.35, 0.3), "g": (0.05, 0.22),
        "h": (-1.02, 0.5), "i": (-0.55, 0.52), "j": (-0.12, 0.5),
    }
    E = [("0", "a"), ("0", "b"), ("0", "c"), ("a", "d"), ("a", "e"), ("b", "e"), ("b", "f"),
         ("c", "f"), ("c", "g"), ("d", "h"), ("e", "h"), ("e", "i"), ("f", "i"), ("f", "j"),
         ("g", "j")]
    edges = _path([[nodes[u], nodes[v]] for u, v in E], GREY_, sw=1.2)
    dots = VGroup(*[Dot(P(*nodes[k]), radius=0.05 if k == "0" else 0.036,
                        color=ACC if k == "0" else WHITE_) for k in nodes])
    up = VGroup(*[tex(r"\vdots", 22, GREY_).move_to(P(x, 0.66)) for x in (-1.02, -0.55, -0.12)])
    up.shift(UP * 0.0)
    f = MathTex(r"\pi=\mathrm{id}", font_size=30, color=WHITE_)
    f[0][0].set_color(ACC)
    f.move_to(P(0.85, 0.02))
    return VGroup(edges, dots, f)


# =====================================================================
# FEATURED 246: Cannon's conjecture
# =====================================================================
FW, FH = 5.2, 4.4          # canonical frame of the big visuals (scale ~1 on the card)
CAN_R, CAN_C = 1.7, (0.0, 0.42)
CAN_V = None               # rotation centre (a vertex of the central tile), set below


def _frame():
    return Rectangle(width=FW, height=FH, stroke_opacity=0, stroke_width=0, fill_opacity=0)


def _cannon_parts():
    global CAN_V
    R, C = CAN_R, CAN_C
    tiles, _ = hyp_tiling(5, 4, depth=5, min_size=0.028)
    gtiles, gadj = hyp_tiling(5, 4, depth=3, min_size=0.05)
    CAN_V = tiles[0]["v"][0]
    # Cayley graph = dual graph of the tiling: one vertex per tile, edges across shared sides
    layers = []
    maxd = max(t["d"] for t in gtiles)
    for d in range(1, maxd + 1):
        segs = [g for (i, j) in sorted(gadj) if max(gtiles[i]["d"], gtiles[j]["d"]) == d
                for g in [_to_xy(_geodesic(gtiles[i]["c"], gtiles[j]["c"], 9), R, C)]]
        edges = VGroup(*[_path([sg], WHITE_, sw=1.5, opacity=0.9) for sg in segs])
        dots = VGroup(*[Dot(_to_xy([t["c"]], R, C)[0],
                            radius=0.06 * R * (1 - abs(t["c"]) ** 2) / 1.0, color=WHITE_)
                        for t in gtiles if t["d"] == d])
        layers.append(VGroup(edges, dots))
    e_dot = Dot(P(*C), radius=0.06 * R, color=ACC)
    faint = Circle(radius=R, stroke_color=DIM, stroke_width=1.6).move_to(P(*C))
    rim = Circle(radius=R, stroke_color=ACC, stroke_width=3.2).move_to(P(*C))
    rim_glow = glow(rim, ACC, layers=5, width=22, opacity=0.07)
    lat = VGroup(
        Ellipse(width=2 * R, height=0.5 * R, stroke_color=ACC, stroke_width=1.3,
                stroke_opacity=0.55),
        Ellipse(width=0.62 * R, height=2 * R, stroke_color=ACC, stroke_width=1.3,
                stroke_opacity=0.55),
    ).move_to(P(*C))
    til = _path([_to_xy(l, R, C) for l in _tiling_edges(tiles, 9)], ACC, sw=1.1, opacity=0.75)
    fund = Polygon(*_tile_poly(tiles[0], R, C, 9), stroke_width=0, fill_color=ACC,
                   fill_opacity=0.35)
    lab = MathTex(r"\partial G\cong S^2", r"\;\Longrightarrow\;", r"G\curvearrowright\mathbb{H}^3",
                  font_size=40, color=WHITE_)
    lab[0].set_color(ACC)
    lab.move_to(P(0, -1.82))
    return dict(layers=layers, e_dot=e_dot, faint=faint, rim=rim, rim_glow=rim_glow, lat=lat,
                til=til, fund=fund, lab=lab)


def big_246():
    p = _cannon_parts()
    return VGroup(_frame(), p["faint"], p["e_dot"])


def _place(m, mob):
    """Map a mobject built in the canonical big-frame coordinates onto `mob`."""
    s = mob[0].width / FW
    m.scale(s, about_point=ORIGIN).shift(mob[0].get_center())
    m.set_z_index(Z_FEAT)
    return m


def _adopt(scene, mob, *parts):
    """Hand freshly animated parts over to the feature card (so they collapse with it)."""
    for q in parts:
        scene.remove(q)
    mob.add(*parts)


def anim_246(scene, mob, rt):
    p = _cannon_parts()
    s = mob[0].width / FW
    for k in ("layers", "rim", "rim_glow", "lat", "til", "fund", "lab"):
        if isinstance(p[k], list):
            for q in p[k]:
                _place(q, mob)
        else:
            _place(p[k], mob)
    layers = VGroup(*p["layers"])
    e_dot = mob[2]                       # identity vertex: drawn above the graph edges
    e_dot.set_z_index(Z_FEAT + 1)
    # 1) the group, seen from further and further away: Cayley graph grows outward
    t1 = 0.33 * rt
    scene.play(LaggedStart(*[AnimationGroup(Create(L[0], lag_ratio=0), FadeIn(L[1], scale=0.5))
                             for L in p["layers"]], lag_ratio=0.75),
               run_time=t1, rate_func=linear)
    _adopt(scene, mob, layers)
    # 2) ... its boundary at infinity is a 2-sphere
    t2 = 0.22 * rt
    scene.play(FadeIn(p["rim_glow"]), Create(p["rim"]), Create(p["lat"], lag_ratio=0.3),
               Write(p["lab"][0]), run_time=t2)
    _adopt(scene, mob, p["rim_glow"], p["rim"], p["lat"], p["lab"][0])
    # 3) ... and the group comes from hyperbolic geometry: tiles appear, a symmetry acts
    t3a, t3b = 0.17 * rt, 0.26 * rt
    scene.play(Create(p["til"]), FadeIn(p["fund"]), layers.animate.set_stroke(opacity=0.5),
               Write(p["lab"][1:]), run_time=t3a)
    _adopt(scene, mob, p["til"], p["fund"], p["lab"][1:])
    Cx = mob[0].get_center()[0] + s * CAN_C[0]
    Cy = mob[0].get_center()[1] + s * CAN_C[1]
    Rs = s * CAN_R
    v = CAN_V
    moving = VGroup(p["til"], p["fund"], layers, e_dot)   # e rides along with its tile
    orig = [(m, m.points.copy()) for m in moving.family_members_with_points()]

    def swirl(_, a):
        th = a * PI / 2
        e = np.exp(1j * th)
        for m, pts in orig:
            z = ((pts[:, 0] - Cx) + 1j * (pts[:, 1] - Cy)) / Rs
            u = (z - v) / (1 - np.conj(v) * z)
            w = (e * u + v) / (1 + np.conj(v) * e * u)
            new = pts.copy()
            new[:, 0] = Cx + Rs * w.real
            new[:, 1] = Cy + Rs * w.imag
            m.points = new

    scene.play(UpdateFromAlphaFunc(moving, swirl), run_time=t3b, rate_func=smooth)


# =====================================================================
# FEATURED 244: the partition principle does not imply choice
# =====================================================================
PP_W, PP_H, PP_C = 2.2, 2.6, (-1.25, -0.25)
PP_CUTS = [(0.68, 0.12), (0.02, -0.10), (-0.66, 0.14)]      # band boundaries y = b + m x
PP_DOTS = [  # (x, y) relative to the centre of X, three per band (top to bottom)
    (-0.45, 0.88), (0.0, 1.0), (0.4, 0.86),
    (-0.7, 0.36), (-0.15, 0.3), (0.5, 0.45),
    (-0.6, -0.3), (0.05, -0.4), (0.6, -0.25),
    (-0.35, -0.98), (0.15, -1.08), (0.55, -0.85),
]
PP_INJ = [4, 7, 11, 9]     # piece i -> a distinct point of X (order preserving, no crossings)
PP_NODE_X = 1.75


def _pp_parts():
    cx, cy = PP_C
    (b0, m0), (b1, m1), (b2, m2) = PP_CUTS
    cuts = [[(m0, -1, -b0)],
            [(-m0, 1, b0), (m1, -1, -b1)],
            [(-m1, 1, b1), (m2, -1, -b2)],
            [(-m2, 1, b2)]]
    regs = _partition_regions(PP_W, PP_H, cuts, n=120)
    pieces = VGroup(*[Polygon(*[P(cx + q[0], cy + q[1]) for q in r], stroke_color=ACC,
                              stroke_width=1.8, fill_color=ACC, fill_opacity=TINTS[i])
                      for i, r in enumerate(regs)])
    X = Ellipse(width=PP_W, height=PP_H, stroke_color=WHITE_, stroke_width=2.4).move_to(P(cx, cy))
    Xl = MathTex("X", font_size=36, color=WHITE_).move_to(P(-2.28, 0.86))
    dots = VGroup(*[Dot(P(cx + x, cy + y), radius=0.055, color=WHITE_) for x, y in PP_DOTS])
    band_y = [np.mean([q[1] for q in r]) for r in regs]
    ys = [0.6, 0.05, -0.5, -1.05]
    nodes = VGroup(*[RoundedRectangle(width=0.3, height=0.3, corner_radius=0.07,
                                      stroke_color=ACC, stroke_width=1.8, fill_color=ACC,
                                      fill_opacity=TINTS[i]).move_to(P(PP_NODE_X, cy + y))
                     for i, y in enumerate(ys)])
    # surjection X ->> X/~ : every point goes to its piece
    surj = VGroup()
    for i, y in enumerate(band_y):
        hw = PP_W / 2 * np.sqrt(max(0.0, 1 - (2 * y / PP_H) ** 2))
        a = P(cx + hw + 0.05, cy + y)
        b = nodes[i].get_left() + LEFT * 0.06
        surj.add(Arrow(a, b, buff=0, color=GREY_, stroke_width=1.8, tip_length=0.12,
                       max_tip_length_to_length_ratio=0.2))
    Yl = txt("pieces", 22, ACC, weight=SEMIBOLD)
    Yl.next_to(nodes[0], UP, buff=0.12)
    # partition principle: the pieces inject back into X
    inj = VGroup()
    for i, j in enumerate(PP_INJ):
        a = nodes[i].get_corner(DL) + P(0.02, 0.02)
        b = dots[j].get_center()
        d = b - a
        b = b - d / np.linalg.norm(d) * 0.08
        inj.add(CurvedArrow(a, b, angle=-0.3, color=ACC, stroke_width=2.2, tip_length=0.14))
    title = MathTex(r"\mathrm{PP}", r"\overset{?}{\Longrightarrow}", r"\mathrm{AC}",
                    font_size=46, color=WHITE_)
    title_no = MathTex(r"\mathrm{PP}", r"\not\Longrightarrow", r"\mathrm{AC}",
                       font_size=46, color=WHITE_)
    title.move_to(P(-0.8, 1.9))
    title_no.move_to(title, aligned_edge=LEFT)
    title_no[1].set_color(ACC)
    levi = txt("Levi, 1902", 24, GREY_).next_to(title, RIGHT, buff=0.45).shift(DOWN * 0.04)
    box = RoundedRectangle(width=FW - 0.1, height=3.55, corner_radius=0.16, stroke_color=GREY_,
                           stroke_width=1.6).move_to(P(0, -0.45))
    lt = txt("a universe of sets (ZF)", 22, GREY_)
    lt.move_to(box.get_corner(UL) + P(lt.width / 2 + 0.3, 0))
    bg = Rectangle(width=lt.width + 0.2, height=lt.height + 0.1, stroke_width=0,
                   fill_color=CARD, fill_opacity=1).move_to(lt)
    boxl = VGroup(bg, lt)
    verdict = VGroup(txt("PP holds", 24, GREEN_, weight=SEMIBOLD),
                     txt("AC fails", 24, RED_, weight=SEMIBOLD)).arrange(RIGHT, buff=0.4)
    verdict.move_to(box.get_corner(DR) + P(-verdict.width / 2 - 0.22, verdict.height / 2 + 0.2))
    return dict(pieces=pieces, X=X, Xl=Xl, dots=dots, nodes=nodes, surj=surj, Yl=Yl, inj=inj,
                title=title, title_no=title_no, levi=levi, box=box, boxl=boxl, verdict=verdict)


def big_244():
    p = _pp_parts()
    return VGroup(_frame(), p["title"], p["levi"], p["X"], p["Xl"], p["dots"])


def anim_244(scene, mob, rt):
    p = _pp_parts()
    for k in ("pieces", "nodes", "surj", "Yl", "inj", "title_no", "box", "boxl", "verdict"):
        _place(p[k], mob)
    title = mob[1]
    X, dots = mob[3], mob[5]
    for m in (X, dots):
        m.set_z_index(Z_FEAT + 1)
    # 1) partition X into pieces; the set of pieces X/~ is a surjective image of X
    t1 = 0.28 * rt
    scene.play(FadeIn(p["pieces"], lag_ratio=0.25), FadeIn(p["nodes"], lag_ratio=0.25),
               LaggedStart(*[GrowArrow(a) for a in p["surj"]], lag_ratio=0.2),
               FadeIn(p["Yl"]),
               run_time=t1)
    # keep X and the dots above the tinted pieces
    _adopt(scene, mob, p["pieces"], p["nodes"], p["surj"], p["Yl"])
    # 2) partition principle: the pieces inject back into X
    t2 = 0.26 * rt
    scene.play(LaggedStart(*[Create(a) for a in p["inj"]], lag_ratio=0.3),
               p["surj"].animate.set_opacity(0.22), run_time=t2)
    _adopt(scene, mob, p["inj"])
    scene.wait(0.14 * rt)
    # 3) the paper's universe of sets: PP holds, AC fails
    t3 = 0.28 * rt
    scene.play(Create(p["box"]), FadeIn(p["boxl"]), Transform(title[1], p["title_no"][1]),
               LaggedStart(FadeIn(p["verdict"][0], shift=UP * 0.1),
                           FadeIn(p["verdict"][1], shift=UP * 0.1), lag_ratio=0.5),
               run_time=t3)
    _adopt(scene, mob, p["box"], p["boxl"], p["verdict"])


# =====================================================================
# scene
# =====================================================================
ICONS = {"246": ic_246, "244": ic_244, "193": ic_193, "194": ic_194, "201": ic_201,
         "205": ic_205, "202": ic_202, "203": ic_203, "247": ic_247, "250": ic_250,
         "254": ic_254, "241": ic_241}
FEATURE = {"246": (big_246, anim_246), "244": (big_244, anim_244)}


def _tiles():
    spec = json.loads((VIDEO / "data" / "grids.json").read_text())["c6_grid"]
    out = []
    for d in spec:
        t = dict(num=d["num"], name=d["name"], verdict=d["verdict"], icon=ICONS[d["num"]])
        if d.get("caption"):
            big, anim = FEATURE[d["num"]]
            t["feature"] = dict(caption=d["caption"], big=big, animate=anim)
        out.append(t)
    return out


class C6Grid(GridScene):
    CHAPTER = "al"
    TILES = _tiles()
