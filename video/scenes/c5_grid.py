import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
from lib.grid import GridScene

import itertools as it
import json

# =====================================================================
# Combinatorics rapid-fire grid.  Every tile gets a small line-art icon
# (~2.9 x 1.0 units, thin strokes, GOLD accent, WHITE/GREY neutrals, RED
# only for "this breaks the conjecture").  Three featured tiles get a big
# illustration plus a short animation timed to fractions of their line.
# =====================================================================

ACC = GOLD_


def mix(c1, c2, a):
    return ManimColor(c1).interpolate(ManimColor(c2), a)

SW = 1.6          # thin stroke
SW_HI = 2.6       # accent stroke
R_DOT = 0.045

MUTED = [mix(GOLD_, BG, 0.58), mix(GREY_, BG, 0.25),
         mix(WHITE_, BG, 0.42), mix(GREY_, BG, 0.6),
         mix(GOLD_, GREY_, 0.55)]


# ---------------------------------------------------------------- tiny helpers
def P(x, y):
    return np.array([x, y, 0.0])


def dot(p, color=WHITE_, r=R_DOT, hollow=False):
    d = Dot(p, radius=r, color=color)
    if hollow:
        d.set_fill(CARD, opacity=1).set_stroke(color, width=1.5, opacity=1)
    return d


def seg(a, b, color=GREY_, w=SW, opacity=1.0):
    return Line(a, b, color=color, stroke_width=w).set_stroke(opacity=opacity)


def arrow(a, b, color=GREY_, w=SW, tip=0.09, buff=0.0):
    return Arrow(a, b, buff=buff, color=color, stroke_width=w, tip_length=tip,
                 max_tip_length_to_length_ratio=0.45, max_stroke_width_to_length_ratio=20)


def red_x(center, s=0.1, w=3.0):
    c = np.array(center)
    return VGroup(Line(c + s * (UL), c + s * (DR), color=RED_, stroke_width=w),
                  Line(c + s * (UR), c + s * (DL), color=RED_, stroke_width=w))


def hide(m):
    """Make m invisible but remember its opacities (restored by unhide)."""
    for sm in m.get_family():
        if not hasattr(sm, "_fo"):
            sm._fo, sm._so = sm.get_fill_opacity(), sm.get_stroke_opacity()
        sm.set_fill(opacity=0, family=False)
        sm.set_stroke(opacity=0, family=False)
    return m


def _set_alpha(sm, a):
    if hasattr(sm, "_fo"):
        sm.set_fill(opacity=sm._fo * a, family=False)
        sm.set_stroke(opacity=sm._so * a, family=False)


# The featured visuals live inside the template's card (z-index 60), so every
# hidden part is built in big() and revealed in place.  These helpers start from
# the hidden state lazily (at the moment the animation begins), so nothing
# flashes while waiting for a beat, and they never add new top-level mobjects.
def reveal(m, shift=None, scale=1.0, **kw):
    fam, st = m.get_family(), {}

    def upd(mob, a):
        if not st:
            st["c"] = m.get_center().copy()
            st["p"] = [sm.points.copy() for sm in fam]
        for sm, p in zip(fam, st["p"]):
            _set_alpha(sm, a)
            if len(p):
                q = st["c"] + (p - st["c"]) * (scale + (1 - scale) * a) if scale != 1 else p
                sm.points = q - (shift * (1 - a) if shift is not None else 0)
    return UpdateFromAlphaFunc(m, upd, **kw)


def draw(m, **kw):
    fam, st = m.family_members_with_points(), []

    def upd(mob, a):
        if not st:
            st.extend(sm.copy() for sm in fam)
        for sm, b in zip(fam, st):
            _set_alpha(sm, 1)
            sm.pointwise_become_partial(b, 0, max(a, 1e-4))
    return UpdateFromAlphaFunc(m, upd, **kw)


def grow(m, edge=LEFT, x_only=False, **kw):
    fam, st = m.get_family(), {}

    def upd(mob, a):
        if not st:
            st["o"] = m.get_edge_center(edge).copy()
            st["p"] = [sm.points.copy() for sm in fam]
        k = max(a, 1e-3)
        for sm, p in zip(fam, st["p"]):
            _set_alpha(sm, min(1, 4 * a))
            if len(p):
                q = p.copy()
                if x_only:
                    q[:, 0] = st["o"][0] + (p[:, 0] - st["o"][0]) * k
                else:
                    q = st["o"] + (p - st["o"]) * k
                sm.points = q
    return UpdateFromAlphaFunc(m, upd, **kw)


def move_in(m, start, **kw):
    st = {}

    def upd(mob, a):
        if not st:
            st["e"] = m.get_center().copy()
        m.move_to(start + (st["e"] - start) * a)
        for sm in m.get_family():
            _set_alpha(sm, min(1, 3 * a))
    return UpdateFromAlphaFunc(m, upd, **kw)


# oblique "isometric" projection for unit cubes: x right, y = depth (up-right), z up
OB = (np.array([1.0, 0, 0]), np.array([0.42, 0.30, 0]), np.array([0, 1.0, 0]))


def cube_faces(cells, u, color_of, origin=ORIGIN, edge=BG, ew=0.9, cull=False):
    """Painter-sorted faces (front, top, right) of unit cubes.
    Returns list of (cell, face_mobject).  cull=True drops faces covered by a
    neighbouring cube (fine for static pictures)."""
    S = set(cells)
    def Q(x, y, z):
        return np.array(origin) + u * (x * OB[0] + y * OB[1] + z * OB[2])
    out = []
    for (x, y, z) in sorted(cells, key=lambda c: (-c[1], c[2], c[0])):
        col = color_of((x, y, z))
        quads = [
            ([Q(x, y, z), Q(x + 1, y, z), Q(x + 1, y, z + 1), Q(x, y, z + 1)], col),
            ([Q(x, y, z + 1), Q(x + 1, y, z + 1), Q(x + 1, y + 1, z + 1), Q(x, y + 1, z + 1)],
             mix(col, WHITE, 0.28)),
            ([Q(x + 1, y, z), Q(x + 1, y + 1, z), Q(x + 1, y + 1, z + 1), Q(x + 1, y, z + 1)],
             mix(col, BLACK, 0.38)),
        ]
        nb = [(x, y - 1, z), (x, y, z + 1), (x + 1, y, z)]
        for (pts, c), q in zip(quads, nb):
            if cull and q in S:
                continue
            f = Polygon(*pts, stroke_color=edge, stroke_width=ew, fill_color=c, fill_opacity=1.0)
            out.append(((x, y, z), f))
    return out


TILE_T = [(0, 0, 0), (0, 0, 1), (2, 0, 0), (2, 0, 1)]   # two pillars with a gap: a disconnected tile


def tiling_patch(nx, ny, layers, offsets):
    """Window of a translational tiling of Z^3 by TILE_T = {0,2}x{0}x{0,1}.
    Row (layer L, depth y) uses translates x0 in {s, s+1} + 4Z (s = offsets[L][y]).
    Returns {cell: copy_id} and list of copies (cells)."""
    owner, copies = {}, []
    for L in range(layers):
        for y in range(ny):
            s = offsets[L][y]
            for x0 in range(-4, nx + 2):
                if (x0 - s) % 4 not in (0, 1):
                    continue
                cells = [(x0 + dx, y, 2 * L + dz) for (dx, _, dz) in TILE_T]
                cells = [c for c in cells if 0 <= c[0] < nx]
                if not cells:
                    continue
                cid = len(copies)
                copies.append(cells)
                for c in cells:
                    assert c not in owner
                    owner[c] = cid
    assert len(owner) == nx * ny * 2 * layers
    return owner, copies


def color_copies(owner, copies, special, palette):
    """Greedy colouring of copies so face-adjacent copies differ; `special` gets GOLD."""
    adj = {i: set() for i in range(len(copies))}
    for (x, y, z), i in owner.items():
        for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            j = owner.get((x + d[0], y + d[1], z + d[2]))
            if j is not None and j != i:
                adj[i].add(j); adj[j].add(i)
    col = {special: -1}
    for i in range(len(copies)):
        if i == special:
            continue
        used = {col[j] for j in adj[i] if j in col}
        k = next(k for k in range(len(palette)) if k not in used)
        col[i] = k
    return {i: (ACC if c == -1 else palette[c]) for i, c in col.items()}


# =====================================================================
# ICONS (all designed at roughly their on-tile size, ~2.9 x 1.0)
# =====================================================================
def icon_borsuk():
    g = VGroup()
    c, r = P(-1.0, 0.0), 0.42
    for k in range(3):
        a0 = PI / 2 + k * TAU / 3
        s = Sector(radius=r, angle=TAU / 3, start_angle=a0).shift(c)
        mid = a0 + TAU / 6
        s.shift(0.055 * np.array([np.cos(mid), np.sin(mid), 0]))
        s.set_fill(ACC, opacity=[0.55, 0.36, 0.2][k]).set_stroke(ACC, width=1.4, opacity=1)
        g.add(s)
    g.add(arrow(P(-0.42, 0), P(0.02, 0), color=GREY_, w=1.6, tip=0.09))
    # the 9-dim set: lines through the origin; a perpendicular pair = a diameter pair
    o, L = P(0.58, 0.0), 0.44
    for a in (0, 30, 60, 90, 120, 150):
        d = np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0])
        hot = a in (30, 120)
        g.add(seg(o - L * d, o + L * d, color=RED_ if hot else GREY_, w=2.4 if hot else 1.3,
                  opacity=1 if hot else 0.8))
    d1 = np.array([np.cos(np.radians(30)), np.sin(np.radians(30)), 0])
    d2 = np.array([np.cos(np.radians(120)), np.sin(np.radians(120)), 0])
    e = 0.09
    g.add(VMobject(stroke_color=RED_, stroke_width=1.4).set_points_as_corners(
        [o + e * d1, o + e * (d1 + d2), o + e * d2]))
    g.add(dot(o, WHITE_, 0.04))
    g.add(tex(r"\mathbb{R}^9", 30, GREY_).move_to(P(1.32, 0.22)))
    return g


def icon_tiling():
    u = 0.215
    g = VGroup()
    # the tile (gold), left
    tile = VGroup(*[f for _, f in cube_faces(TILE_T, u, lambda c: ACC, origin=P(-1.45, -0.42), cull=True)])
    g.add(tile)
    g.add(arrow(P(-0.62, -0.05), P(-0.36, -0.05), color=GREY_, w=1.5, tip=0.08))
    # a window of translates: 6 wide, 1 deep, two layers of copies
    owner, copies = tiling_patch(6, 1, 2, offsets=[[0], [1]])
    special = owner[(2, 0, 2)]
    cmap = color_copies(owner, copies, special, MUTED)
    org = P(-0.22, -0.42)
    slab = VGroup(*[f for c, f in cube_faces(list(owner), u, lambda c: cmap[owner[c]], origin=org, cull=True)])
    g.add(slab)
    # "shift by one layer is a period?" -> no
    x_r = slab.get_right()[0] + 0.12
    a = Arrow(P(x_r, org[1] + u * 1.15), P(x_r, org[1] + u * 3.15), buff=0, color=RED_,
              stroke_width=2.4, tip_length=0.09, max_tip_length_to_length_ratio=0.3)
    g.add(a)
    g.add(red_x(a.get_center() + RIGHT * 0.17, s=0.065, w=2.6))
    return g


def icon_hadwiger():
    g = VGroup()
    gx = -1.0
    V = {
        "a1": P(gx - 0.13, 0.36), "a2": P(gx + 0.13, 0.36),
        "b1": P(gx - 0.44, 0.08), "b2": P(gx - 0.32, -0.19),
        "c1": P(gx + 0.44, 0.08), "c2": P(gx + 0.32, -0.19),
        "d1": P(gx - 0.12, -0.38), "d2": P(gx + 0.12, -0.38),
    }
    blobs = [("a1", "a2"), ("b1", "b2"), ("c1", "c2"), ("d1", "d2")]
    for p, q in blobs:
        A, B = V[p], V[q]
        v = B - A
        cap = RoundedRectangle(width=np.linalg.norm(v) + 0.2, height=0.2, corner_radius=0.1)
        cap.rotate(np.arctan2(v[1], v[0])).move_to((A + B) / 2)
        cap.set_fill(ACC, opacity=0.22).set_stroke(ACC, width=1.0, opacity=0.65)
        g.add(cap)
    E = [("a1", "a2"), ("b1", "b2"), ("c1", "c2"), ("d1", "d2"),
         ("a1", "b1"), ("a2", "c1"), ("b2", "d1"), ("c2", "d2"), ("a2", "d1"), ("b1", "c2")]
    for p, q in E:
        g.add(seg(V[p], V[q], GREY_, 1.3))
    for p in V.values():
        g.add(dot(p, WHITE_, 0.04))
    g.add(arrow(P(-0.4, 0), P(-0.08, 0), GREY_, 1.5, tip=0.08))
    kx = 0.38
    K = [P(kx, 0.36), P(kx - 0.36, 0.0), P(kx + 0.36, 0.0), P(kx, -0.36)]
    for i, j in it.combinations(range(4), 2):
        g.add(seg(K[i], K[j], ACC, 2.0))
    for p in K:
        g.add(dot(p, ACC, 0.055))
    g.add(tex(r"\chi > h", 32, RED_).next_to(P(0.9, 0.0), RIGHT, buff=0.0))
    return g


def icon_barnette():
    g = VGroup()
    out = [P(-0.95, 0.45), P(0, 0.45), P(0.95, 0.45), P(1.42, 0), P(0.95, -0.45), P(0, -0.45),
           P(-0.95, -0.45), P(-1.42, 0)]
    inn = [P(p[0] * 0.58, p[1] * 0.44) for p in out]
    n = 8
    ham = set()
    for k in range(n - 1):
        ham.add(("o", k, "o", k + 1)); ham.add(("i", k, "i", k + 1))
    ham.add(("o", 7, "i", 7)); ham.add(("o", 0, "i", 0))
    pos = {"o": out, "i": inn}
    edges = [("o", k, "o", (k + 1) % n) for k in range(n)] + \
            [("i", k, "i", (k + 1) % n) for k in range(n)] + [("o", k, "i", k) for k in range(n)]
    lo, hi = VGroup(), VGroup()
    for e in edges:
        a, i, b, j = e
        key = e if e in ham else (b, j, a, i)
        on = key in ham or (a, min(i, j), b, max(i, j)) in ham
        (hi if on else lo).add(seg(pos[a][i], pos[b][j], ACC if on else GREY_, 2.8 if on else 1.3,
                                   opacity=1 if on else 0.75))
    g.add(lo, hi)
    for k in range(n):   # bipartition: filled vs hollow
        g.add(dot(out[k], WHITE_, 0.048, hollow=(k % 2 == 1)))
        g.add(dot(inn[k], WHITE_, 0.048, hollow=((k + 1) % 2 == 1)))
    return g


def icon_seymour():
    g = VGroup()
    v = P(-1.25, -0.04)
    N1 = [P(-0.58, 0.26), P(-0.58, -0.04), P(-0.58, -0.34)]
    N2 = [P(0.08, 0.33), P(0.08, 0.09), P(0.08, -0.15), P(0.08, -0.39)]
    for X, col in ((N1, WHITE_), (N2, ACC)):
        top, bot = X[0][1], X[-1][1]
        box = RoundedRectangle(width=0.27, height=top - bot + 0.27, corner_radius=0.12)
        box.move_to(P(X[0][0], (top + bot) / 2))
        box.set_fill(col, opacity=0.07).set_stroke(col, width=1.0, opacity=0.45)
        g.add(box)
    for p in N1:
        g.add(arrow(v, p, GREY_, 1.5, tip=0.08, buff=0.085))
    for a, b in ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)):
        g.add(arrow(N1[a], N2[b], ACC, 1.6, tip=0.08, buff=0.075))
    g.add(dot(v, ACC, 0.065))
    for p in N1:
        g.add(dot(p, WHITE_, 0.045))
    for p in N2:
        g.add(dot(p, ACC, 0.045, hollow=True))
    g.add(tex("v", 26, ACC).next_to(v, DOWN, buff=0.08))
    f = MathTex(r"|N^{++}|", r"\ge", r"|N^{+}|", font_size=27, color=WHITE_)
    f[0].set_color(ACC)
    f.next_to(P(0.36, -0.04), RIGHT, buff=0)
    g.add(f)
    return g


def icon_sidorenko():
    g = VGroup()
    top = [P(-1.2 + 0.29 * i, 0.3) for i in range(4)]
    bot = [P(-1.345 + 0.29 * i, -0.3) for i in range(5)]
    E = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (0, 3), (1, 4), (2, 0)]
    for i, j in E:
        g.add(seg(top[i], bot[j], ACC, 1.6, opacity=0.9))
    for p in top:
        g.add(dot(p, WHITE_, 0.048))
    for p in bot:
        g.add(dot(p, WHITE_, 0.048, hollow=True))
    g.add(tex("H", 26, GREY_).next_to(P(-0.765, 0.3), UP, buff=0.1))
    f = MathTex(r"t_H(G)", r"<", r"p^{\,e(H)}", font_size=29, color=WHITE_)
    f[1].set_color(RED_)
    f.next_to(P(0.05, 0.0), RIGHT, buff=0.0)
    g.add(f)
    return g


def icon_ryser():
    g = VGroup()
    xs = [-1.32, -0.82, -0.32, 0.18]
    ys = [0.32, 0.0, -0.32]
    for x in xs:
        box = RoundedRectangle(width=0.24, height=0.9, corner_radius=0.1).move_to(P(x, 0))
        box.set_fill(GREY_, opacity=0.06).set_stroke(DIM, width=1.0)
        g.add(box)
    # four 4-edges (one vertex per part), pairwise intersecting
    H = [(0, 0, 0, 0), (0, 1, 1, 1), (1, 0, 1, 2), (2, 1, 0, 2)]
    cols = [ACC, WHITE_, mix(ACC, WHITE_, 0.5), GREY_]
    for e, c in zip(H, cols):
        pts = [P(xs[k], ys[e[k]]) for k in range(4)]
        curve = VMobject(stroke_color=c, stroke_width=2.0).set_points_smoothly(pts)
        curve.set_stroke(opacity=0.9)
        g.add(curve)
    for x in xs:
        for y in ys:
            g.add(dot(P(x, y), WHITE_, 0.042))
    f = MathTex(r"\tau", r">", r"r-1", font_size=32, color=WHITE_)
    f[1].set_color(RED_)
    f.move_to(P(1.05, 0))
    g.add(f)
    return g


def icon_hindman():
    g = VGroup()
    x0, dx = -1.32, 0.24
    X = lambda k: x0 + dx * (k - 1)
    gold = {2, 5, 7, 10}
    other = {1: WHITE_, 3: GREY_, 4: WHITE_, 6: GREY_, 8: GREY_, 9: WHITE_, 11: GREY_, 12: WHITE_}
    g.add(seg(P(X(1) - 0.12, 0), P(X(12) + 0.12, 0), DIM, 1.2))
    for k in range(1, 13):
        if k in gold:
            g.add(Circle(radius=0.085, color=ACC, stroke_width=1.4).move_to(P(X(k), 0)))
            g.add(dot(P(X(k), 0), ACC, 0.05))
        else:
            g.add(dot(P(X(k), 0), other[k], 0.038).set_opacity(0.85 if other[k] == WHITE_ else 1))
    for k in sorted(gold):
        g.add(tex(str(k), 22, ACC).next_to(P(X(k), 0), DOWN, buff=0.13))
    g.add(tex(r"2{+}5", 22, GREY_).next_to(P(X(7), 0), UP, buff=0.14))
    g.add(tex(r"2{\cdot}5", 22, GREY_).next_to(P(X(10), 0), UP, buff=0.14))
    return g


def icon_crossing():
    g = VGroup()
    c, R, r = P(-0.7, -0.08), 0.64, 0.22
    pts = [c + R * np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0]) for a in (90, 210, 330)]
    pts += [c + r * np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0]) for a in (90, 210, 330)]
    E = list(it.combinations(range(6), 2))
    for i, j in E:
        g.add(seg(pts[i], pts[j], GREY_, 1.3, opacity=0.9))
    # mark the crossings (exactly cr(K6) = 3 for this drawing)
    xs = []
    for (a, b), (p, q) in it.combinations(E, 2):
        if len({a, b, p, q}) < 4:
            continue
        A, B, C_, D = pts[a][:2], pts[b][:2], pts[p][:2], pts[q][:2]
        M = np.array([B - A, C_ - D]).T
        if abs(np.linalg.det(M)) < 1e-9:
            continue
        s, t = np.linalg.solve(M, C_ - A)
        if 1e-6 < s < 1 - 1e-6 and 1e-6 < t < 1 - 1e-6:
            xs.append(P(*(A + s * (B - A))))
    assert len(xs) == 3, len(xs)
    for x in xs:
        g.add(Circle(radius=0.055, color=ACC, stroke_width=2.0).move_to(x))
    for p in pts:
        g.add(dot(p, WHITE_, 0.042))
    g.add(tex(r"\mathrm{cr}(K_6)=3", 28, WHITE_).next_to(P(0.12, -0.02), RIGHT, buff=0))
    return g


def icon_hadamard():
    g = VGroup()
    n, cs = 4, 0.205
    org = P(-1.0, 0)
    for i in range(n):
        for j in range(n):
            ctr = org + P((j - 1.5) * cs, (1.5 - i) * cs)
            plus = ((j - i) % n) != 0          # circulant: first row (-1, 1, 1, 1)
            sq = Square(cs * 0.84).move_to(ctr)
            if plus:
                sq.set_fill(ACC, opacity=0.85).set_stroke(width=0)
                g.add(sq)
            else:
                sq.set_fill(opacity=0).set_stroke(WHITE_, width=1.4)
                g.add(sq, seg(ctr + LEFT * 0.045, ctr + RIGHT * 0.045, WHITE_, 1.6))
    hgt, wid = n * cs + 0.06, n * cs + 0.1
    for sgn in (-1, 1):
        x = org[0] + sgn * wid / 2
        br = VMobject(stroke_color=GREY_, stroke_width=1.5).set_points_as_corners(
            [P(x - sgn * 0.06, hgt / 2), P(x, hgt / 2), P(x, -hgt / 2), P(x - sgn * 0.06, -hgt / 2)])
        g.add(br)
    g.add(tex(r"n\in\{1,4\}", 32, WHITE_).move_to(P(0.6, 0)))
    return g


def icon_heilbronn():
    g = VGroup()
    side = 0.92
    c = P(-0.85, 0)
    g.add(Square(side).move_to(c).set_stroke(GREY_, width=1.4).set_fill(opacity=0))
    U = [(0.4, 0.4), (0.57, 0.38), (0.5, 0.54), (0.87, 0.1), (0.1, 0.26), (0.83, 0.69),
         (0.45, 0.1), (0.13, 0.65)]
    pts = [c + P((x - 0.5) * side, (y - 0.5) * side) for x, y in U]
    area = lambda a, b, d: abs((b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0])) / 2
    tri = min(it.combinations(range(len(U)), 3), key=lambda t: area(*[U[i] for i in t]))
    T = Polygon(*[pts[i] for i in tri]).set_fill(ACC, opacity=0.45).set_stroke(ACC, width=1.8)
    g.add(T)
    for i, p in enumerate(pts):
        g.add(dot(p, ACC if i in tri else WHITE_, 0.042))
    g.add(tex(r"\min\triangle \ge n^{-2+c}", 28, WHITE_).move_to(P(0.68, 0)))
    return g


def icon_snaky():
    g = VGroup()
    nx, ny, cs = 12, 4, 0.235
    org = P(-nx * cs / 2, -ny * cs / 2)
    C = lambda x, y: org + P((x + 0.5) * cs, (y + 0.5) * cs)
    grid = VGroup()
    for i in range(nx + 1):
        grid.add(seg(org + P(i * cs, 0), org + P(i * cs, ny * cs), DIM, 1.0))
    for j in range(ny + 1):
        grid.add(seg(org + P(0, j * cs), org + P(nx * cs, j * cs), DIM, 1.0))
    g.add(grid)
    S = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (4, 1)]           # Snaky
    off = (3, 1)
    for x, y in S:
        g.add(Square(cs * 0.8).move_to(C(x + off[0], y + off[1]))
              .set_fill(ACC, opacity=0.9).set_stroke(width=0))
    for x, y in [(9, 0)]:                                         # another Maker cell
        g.add(Square(cs * 0.8).move_to(C(x, y)).set_fill(ACC, opacity=0.45).set_stroke(width=0))
    for x, y in [(2, 1), (5, 2), (7, 1), (8, 2), (4, 0), (6, 3)]:  # Breaker cells
        g.add(Circle(radius=cs * 0.3).move_to(C(x, y)).set_fill(GREY_, opacity=0.9).set_stroke(width=0))
    return g


# =====================================================================
# FEATURED: big illustrations + animations
# =====================================================================
class Beats:
    """Schedule plays at fractions of the featured narration line, clipped to
    the window the grid template gives us."""

    def __init__(self, scene, num, run_time):
        self.s = scene
        self.t0 = scene.now
        self.t1 = scene.now + run_time
        self.a, self.b = scene.cue(f"f{num}"), scene.cue(f"f{num}_end")

    def at(self, frac):
        return min(max(self.a + frac * (self.b - self.a), self.t0), self.t1)

    def play(self, f0, f1, *anims, min_rt=0.35):
        start = max(self.at(f0), self.s.now)
        end = min(max(self.at(f1), start + min_rt), self.t1)
        self.s.wait_until(start)
        rt = end - self.s.now
        if rt < 0.15:
            rt = 0.15
        self.s.play(*anims, run_time=rt)


# ---------------------------------------------------------------- 156 Borsuk
def big_borsuk():
    g = VGroup()
    C, R = P(-1.3, 1.05), 1.0
    secs = VGroup()
    for k in range(3):
        a0 = PI / 2 + k * TAU / 3
        s = Sector(radius=R, angle=TAU / 3, start_angle=a0).shift(C)
        s.set_fill(ACC, opacity=0.3).set_stroke(ACC, width=2.2, opacity=0)
        s.mid = a0 + TAU / 6
        secs.add(s)
    rim = Circle(radius=R, color=ACC, stroke_width=2.2).move_to(C)
    diam = Line(C + R * LEFT, C + R * RIGHT, color=WHITE_, stroke_width=3)
    diam_dots = VGroup(dot(C + R * LEFT, WHITE_, 0.06), dot(C + R * RIGHT, WHITE_, 0.06))
    cuts = VGroup(*[Line(C, C + R * np.array([np.cos(a), np.sin(a), 0]), color=WHITE_, stroke_width=2.6)
                    for a in (PI / 2, PI / 2 + TAU / 3, PI / 2 + 2 * TAU / 3)])
    hide(cuts)
    # each piece's own diameter: the chord of its arc (length sqrt(3) R < 2R)
    chords = VGroup()
    for s in secs:
        a0 = s.mid - TAU / 6
        p = C + R * np.array([np.cos(a0), np.sin(a0), 0])
        q = C + R * np.array([np.cos(a0 + TAU / 3), np.sin(a0 + TAU / 3), 0])
        chords.add(Line(p, q, color=WHITE_, stroke_width=2.6))
    hide(chords)
    g.add(secs, rim, diam, diam_dots, cuts, chords)
    g.secs, g.rim, g.diam, g.diam_dots, g.cuts, g.chords, g.C = secs, rim, diam, diam_dots, cuts, chords, C

    d2 = tex(r"d=2", 46, WHITE_).move_to(P(0.75, 1.45)).align_to(P(0.35, 0), LEFT)
    pieces = VGroup(bold("3 pieces,", 28, ACC), txt("each narrower", 26, GREY_)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    pieces.next_to(d2, DOWN, buff=0.32).align_to(d2, LEFT)
    hide(pieces)
    g.add(d2, pieces)
    g.d2, g.pieces = d2, pieces

    sep = Line(P(-2.3, -0.38), P(2.3, -0.38), color=DIM, stroke_width=1.2)
    g.add(sep)
    lab = txt("smallest known counterexample", 26, GREY_).move_to(P(0, -0.8))
    dl = tex(r"d\,=", 76, WHITE_)
    n63 = tex("63", 76, WHITE_)
    ar = Arrow(LEFT * 0.4, RIGHT * 0.4, color=GREY_, stroke_width=4, buff=0, tip_length=0.2)
    n9 = tex("9", 100, YELLOW_)
    final = VGroup(dl, n63, ar, n9).arrange(RIGHT, buff=0.32).move_to(P(0, -1.75))
    n9.align_to(n63, DOWN)
    strike = Line(n63.get_corner(DL) + P(-0.06, 0.04), n63.get_corner(UR) + P(0.06, -0.04),
                  color=RED_, stroke_width=4)
    start = VGroup(dl, n63).copy().move_to(P(0, -1.75))
    g.final_63 = n63.get_center().copy()
    dl.move_to(start[0]); n63.move_to(start[1])
    hide(lab); hide(dl); hide(n63); hide(ar); hide(n9); hide(strike)
    g.add(sep, lab, dl, n63, ar, n9, strike)
    g.lab, g.dl, g.n63, g.ar, g.n9, g.strike = lab, dl, n63, ar, n9, strike
    return g


def anim_borsuk(scene, g, run_time):
    b = Beats(scene, "156", run_time)
    k = g.rim.width / 2.0                      # current scale of the big visual
    shifts = [0.2 * k * np.array([np.cos(s.mid), np.sin(s.mid), 0]) for s in g.secs]
    for ch, v in zip(g.chords, shifts):        # (still hidden) move chords with their pieces
        ch.shift(v)
    # 1) cut the disk into d+1 = 3 pieces; each piece is narrower than the disk
    b.play(0.14, 0.47, Succession(
        draw(g.cuts, run_time=1.0),
        AnimationGroup(
            *[s.animate.shift(v).set_stroke(opacity=1) for s, v in zip(g.secs, shifts)],
            *[c.animate.shift(v).set_stroke(opacity=0) for c, v in zip(g.cuts, shifts)],
            g.rim.animate.set_stroke(opacity=0),
            g.diam.animate.set_stroke(opacity=0),
            g.diam_dots.animate.set_opacity(0),
            run_time=1.4, group=g),
        AnimationGroup(*[draw(ch) for ch in g.chords], reveal(g.pieces, shift=UP * 0.12 * k),
                       lag_ratio=0.15, run_time=1.3, group=g),
        group=g))
    # 2) the old record
    b.play(0.52, 0.80, Succession(
        reveal(g.lab, shift=UP * 0.15 * k, run_time=1.0),
        Wait(run_time=1.4),
        AnimationGroup(reveal(g.dl), reveal(g.n63), run_time=1.0, group=g),
        group=g))
    # 3) ... and the claimed one
    v = g.strike.get_center() - g.n63.get_center()
    b.play(0.83, 0.93,
           g.dl.animate.shift(v), g.n63.animate.shift(v).set_color(GREY_),
           Succession(Wait(run_time=0.35), draw(g.strike, run_time=0.4), group=g),
           grow(g.ar, LEFT), reveal(g.n9, scale=1.6))


# ---------------------------------------------------------------- 155 periodic tiling
def big_tiling():
    g = VGroup()
    u = 0.36
    # the tile: two unit-cube pillars with a gap (a disconnected tile)
    tile = VGroup(*[f for _, f in cube_faces(TILE_T, u, lambda c: ACC, origin=P(-2.3, 1.38), cull=True)])
    tl = txt("one tile", 26, WHITE_).next_to(tile, RIGHT, buff=0.4).shift(UP * 0.13)
    tl2 = txt("need not be connected", 22, GREY_).next_to(tl, DOWN, buff=0.08, aligned_edge=LEFT)
    g.add(tile, tl, tl2)
    # a window of a tiling by translates (two layers of copies, rows shifted differently)
    nx, ny = 8, 3
    owner, copies = tiling_patch(nx, ny, 2, offsets=[[0, 1, 3], [2, 0, 1]])
    special = owner[(3, 0, 2)]
    cmap = color_copies(owner, copies, special, MUTED)
    org = P(-2.1, -0.82)
    faces = cube_faces(list(owner), u, lambda c: cmap[owner[c]], origin=org)
    slab = VGroup()
    by_copy = {}
    for cell, f in faces:
        slab.add(f)
        by_copy.setdefault(owner[cell], []).append(f)
    hide(slab)
    g.add(slab)
    # arrival order: bottom layer first, back rows first (same as painter order)
    order = sorted(by_copy, key=lambda i: (min(c[2] for c in copies[i]), -copies[i][0][1],
                                           min(c[0] for c in copies[i])))
    g.copy_groups = [VGroup(*by_copy[i]) for i in order]
    # shifting up by one layer of copies: is that a period?  (it is not, for this patch)
    xr = org[0] + u * (nx + 0.42 * 0.5) + 0.32
    yl = org[1] + u * (1.0 + 0.3 * 0.5)
    per = Arrow(P(xr, yl), P(xr, yl + 2 * u), buff=0, color=WHITE_, stroke_width=3.5,
                tip_length=0.16, max_tip_length_to_length_ratio=0.3)
    q = txt("period?", 24, WHITE_).next_to(per, RIGHT, buff=0.12)
    cross = red_x(per.get_center() + LEFT * 0.0, s=0.14, w=5)
    hide(per); hide(q); hide(cross)
    g.add(per, q, cross)
    g.per, g.q, g.cross = per, q, cross
    # bottom: which dimensions? 1, 2 always periodic; huge d fails (2024); 3 claimed
    def item(lab, ok, note=None):
        t = tex(lab, 34, WHITE_)
        mk = check_mark(GREEN_, size=0.26, width=4) if ok else red_x(ORIGIN, s=0.11, w=4.5)
        it_ = VGroup(t, mk).arrange(RIGHT, buff=0.14)
        if note:
            n = txt(note, 22, GREY_).next_to(it_, DOWN, buff=0.1)
            it_ = VGroup(it_, n)
        return it_
    d1, d2, d3 = item("d=1", True), item("d=2", True), item("d=3", False)
    row = VGroup(d1, d2, d3).arrange(RIGHT, buff=0.55).move_to(P(0, -1.9))
    dbig = item(r"d \gg 1", False)
    gt = txt("Greenfeld–Tao 2024", 22, GREY_).next_to(dbig, RIGHT, buff=0.25)
    dbig = VGroup(dbig, gt).move_to(P(0, -1.3))
    dots_ = VGroup()
    row = VGroup(dbig, row)
    box3 = SurroundingRectangle(d3, buff=0.1, corner_radius=0.08, color=RED_, stroke_width=2)
    hide(row); hide(box3)
    g.add(row, box3)
    g.d1, g.d2, g.d3, g.dots_, g.dbig, g.box3 = d1, d2, d3, dots_, dbig, box3
    g.w0 = g.width
    return g


def anim_tiling(scene, g, run_time):
    b = Beats(scene, "155", run_time)
    groups = g.copy_groups
    n = len(groups)
    k = g.width / g.w0                       # current scale of the big visual
    off = (UP * 0.55 + LEFT * 0.12) * k
    for grp in groups:
        for f in grp:
            f._base = f.points.copy()
    lag = 0.55 / max(1, n - 1)

    def slide(m, a):
        for i, grp in enumerate(groups):
            e = smooth(float(np.clip((a - i * lag) / (1 - lag * (n - 1)), 0, 1)))
            for f in grp:
                f.points = f._base + off * (1 - e)
                f.set_fill(opacity=e, family=False)
                f.set_stroke(opacity=e, family=False)
    # 1) "if a shape tiles space by sliding copies around, there's always a repeating pattern"
    b.play(0.15, 0.46, Succession(
        UpdateFromAlphaFunc(g, slide, rate_func=linear, run_time=2.7),
        AnimationGroup(draw(g.per), reveal(g.q, shift=RIGHT * 0.1 * k), run_time=1.0, group=g),
        group=g))
    # 2) "already known to fail in huge dimensions, it's now claimed false in three"
    b.play(0.50, 0.79, Succession(
        reveal(g.dbig, shift=UP * 0.1 * k, run_time=1.0),
        Wait(run_time=1.2),
        AnimationGroup(g.per.animate.set_color(RED_), g.q.animate.set_color(RED_),
                       draw(g.cross), reveal(g.d3, shift=UP * 0.1 * k), run_time=1.0, group=g),
        group=g))
    # 3) "the lowest possible": dimensions 1 and 2 always admit periodic tilings
    b.play(0.81, 0.93, LaggedStart(reveal(g.d2, shift=UP * 0.1 * k), reveal(g.d1, shift=UP * 0.1 * k),
                                   draw(g.box3), lag_ratio=0.35, group=g))


# ---------------------------------------------------------------- 157 Hadwiger
COLORS4 = [GOLD_, BLUE_, PINK_, PURPLE_]


def big_hadwiger():
    g = VGroup()
    G, R = P(-1.3, 1.0), 0.88
    hub = G
    rim = [G + R * np.array([np.cos(np.radians(90 + 72 * k)), np.sin(np.radians(90 + 72 * k)), 0])
           for k in range(5)]
    Vp = [hub] + rim
    E = [(0, k) for k in range(1, 6)] + [(k, k % 5 + 1) for k in range(1, 6)]
    edges = VGroup(*[seg(Vp[i], Vp[j], GREY_, 2.2, opacity=0.85) for i, j in E])
    verts = VGroup(*[Dot(p, radius=0.1, color=WHITE_) for p in Vp])
    coloring = [0, 1, 2, 1, 2, 3]          # proper 4-colouring of the 5-wheel
    # branch sets of a K4 minor: {hub}, {r0}, {r1, r2}, {r3, r4}
    sets = [[0], [1], [2, 3], [4, 5]]
    blobs = VGroup()
    for S in sets:
        if len(S) == 1:
            b = Circle(radius=0.24).move_to(Vp[S[0]])
        else:
            A, B = Vp[S[0]], Vp[S[1]]
            v = B - A
            b = RoundedRectangle(width=np.linalg.norm(v) + 0.48, height=0.48, corner_radius=0.24)
            b.rotate(np.arctan2(v[1], v[0])).move_to((A + B) / 2)
        b.set_fill(ACC, opacity=0.2).set_stroke(ACC, width=2, opacity=0.9)
        blobs.add(b)
    hide(blobs)
    chi = tex(r"\chi = 4", 36, WHITE_).next_to(G + DOWN * R, DOWN, buff=0.3)
    hide(chi)
    g.add(blobs, edges, verts, chi)
    # contracted K4
    K0, KR = P(1.55, 0.95), 0.78
    Kp = [K0] + [K0 + KR * np.array([np.cos(np.radians(a)), np.sin(np.radians(a)), 0]) for a in (90, 210, 330)]
    kedges = VGroup(*[seg(Kp[i], Kp[j], ACC, 3.0) for i, j in it.combinations(range(4), 2)])
    kdots = VGroup(*[Dot(p, radius=0.11, color=ACC) for p in Kp])
    klab = tex(r"K_4\ \text{minor}", 34, ACC).move_to(P(K0[0], chi.get_center()[1]))
    ar = Arrow(P(-0.1, 1.0), P(0.55, 1.0), color=GREY_, stroke_width=3, buff=0, tip_length=0.16)
    hide(kedges); hide(kdots); hide(klab); hide(ar)
    g.add(kedges, kdots, klab, ar)
    # bars: the claimed counterexample graphs (m vertices)
    sep = Line(P(-2.6, -0.55), P(2.6, -0.55), color=DIM, stroke_width=1.2)
    head = txt("random-like graphs on m vertices", 22, GREY_).move_to(P(0, -0.82))
    x0, L = -0.85, 3.3
    yr, yb = -1.32, [-1.66, -2.08]
    ruler = VGroup(Line(P(x0, yr), P(x0 + L, yr), color=GREY_, stroke_width=1.5))
    ticks = VGroup()
    for f_, lab in ((0, "0"), (0.5, "m/2"), (1, "m")):
        xx = x0 + f_ * L
        ruler.add(Line(P(xx, yr - 0.06), P(xx, yr + 0.06), color=GREY_, stroke_width=1.5))
        ticks.add(tex(lab, 24, GREY_).next_to(P(xx, yr + 0.06), UP, buff=0.05))
    guide = DashedLine(P(x0 + L / 2, yr - 0.06), P(x0 + L / 2, yb[1] - 0.2), color=GREY_,
                       stroke_width=1.3, dash_length=0.06).set_stroke(opacity=0.6)
    tracks = VGroup(ruler, ticks, guide)
    bars = VGroup(
        Rectangle(width=L * 0.5, height=0.3).move_to(P(x0 + L * 0.25, yb[0])).set_fill(RED_, 0.85).set_stroke(width=0),
        Rectangle(width=L * 0.35, height=0.3).move_to(P(x0 + L * 0.175, yb[1])).set_fill(ACC, 0.85).set_stroke(width=0),
    )
    names = VGroup(txt("colors", 22, WHITE_), txt("clique minor", 22, WHITE_))
    for nm, y in zip(names, yb):
        nm.next_to(P(x0, y), LEFT, buff=0.15)
    vals = VGroup(tex(r"\chi \ge m/2", 30, RED_), tex(r"h < 0.35\,m", 30, ACC))
    vals[0].next_to(P(x0 + L * 0.5, yb[0]), RIGHT, buff=0.18)
    vals[1].next_to(bars[1], RIGHT, buff=0.18)
    mlab = VGroup()
    lower = VGroup(head, tracks, bars, names, vals)
    hide(lower)
    g.add(sep, lower)
    g.edges, g.verts, g.blobs, g.chi, g.coloring = edges, verts, blobs, chi, coloring
    g.kedges, g.kdots, g.klab, g.ar, g.sets = kedges, kdots, klab, ar, sets
    g.head, g.tracks, g.bars, g.names, g.vals = head, tracks, bars, names, vals
    g.w0 = g.width
    return g


def anim_hadwiger(scene, g, run_time):
    b = Beats(scene, "157", run_time)
    k = g.width / g.w0
    # 1) colouring: this graph needs 4 colours
    b.play(0.30, 0.45,
           LaggedStart(*[v.animate.set_color(COLORS4[c]) for v, c in zip(g.verts, g.coloring)],
                       lag_ratio=0.12, group=g),
           reveal(g.chi, shift=UP * 0.1 * k))
    # 2) hidden clique: 4 connected blobs, pairwise touching -> contract to K4
    starts = [np.mean([g.verts[i].get_center() for i in S], axis=0) for S in g.sets]
    b.play(0.46, 0.58, Succession(
        reveal(g.blobs, run_time=0.6),
        AnimationGroup(grow(g.ar, LEFT), *[move_in(d, p) for d, p in zip(g.kdots, starts)],
                       run_time=0.8, group=g),
        AnimationGroup(draw(g.kedges), reveal(g.klab), run_time=0.7, group=g),
        group=g))
    # 3) the claimed counterexamples: far more colours than the clique minor allows
    b.play(0.62, 0.94, LaggedStart(
        AnimationGroup(reveal(g.head), reveal(g.tracks), reveal(g.names), group=g),
        AnimationGroup(grow(g.bars[1], LEFT, x_only=True), reveal(g.vals[1]), group=g),
        AnimationGroup(grow(g.bars[0], LEFT, x_only=True), reveal(g.vals[0]), group=g),
        lag_ratio=0.45, group=g))


# =====================================================================
# Tiles (names / verdicts / captions verbatim from data/grids.json)
# =====================================================================
ICONS = {
    "156": icon_borsuk, "155": icon_tiling, "157": icon_hadwiger, "180": icon_barnette,
    "173": icon_seymour, "161": icon_sidorenko, "162": icon_ryser, "164": icon_hindman,
    "165": icon_crossing, "179": icon_hadamard, "191": icon_heilbronn, "187": icon_snaky,
}
BIGS = {"156": (big_borsuk, anim_borsuk), "155": (big_tiling, anim_tiling),
        "157": (big_hadwiger, anim_hadwiger)}


def _tiles():
    spec = json.loads((VIDEO / "data" / "grids.json").read_text())["c5_grid"]
    out = []
    for d in spec:
        t = dict(num=d["num"], name=d["name"], verdict=d["verdict"], icon=ICONS[d["num"]])
        if d.get("caption"):
            big, anim = BIGS[d["num"]]
            t["feature"] = dict(caption=d["caption"], big=big, animate=anim)
        out.append(t)
    return out


class C5Grid(GridScene):
    CHAPTER = "co"
    TILES = _tiles()
