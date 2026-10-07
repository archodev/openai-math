import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
from lib.grid import GridScene

import json

import numpy as np

# Rapid-fire grid: Analysis & Convex Geometry (accent TEAL_).
# Every icon is a small vector pictogram (~2.9 x 1.0 units), thin strokes,
# TEAL_ accent + WHITE_/GREY_; featured tiles (Falconer, Koebe) get a big
# visual plus a short animation on the zoomed card.

ACC = TEAL_
FILL = 0.14


# ---------------------------------------------------------------- helpers
def _p3(p):
    return np.array([float(p[0]), float(p[1]), 0.0])


def curve(pts, color=ACC, width=2.0, opacity=1.0, smooth=True, closed=False):
    pts = [_p3(p) for p in pts]
    if closed:
        pts = pts + [pts[0]]
    m = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
    if smooth:
        m.set_points_smoothly(pts)
    else:
        m.set_points_as_corners(pts)
    m.set_fill(opacity=0)
    return m


def ccurve(zs, **kw):
    return curve([(z.real, z.imag) for z in zs], **kw)


def region(outer, holes=(), color=ACC, opacity=FILL):
    """Filled region (no stroke): outer closed complex curve minus holes
    (holes are reversed so the non-zero winding rule leaves them empty)."""
    m = ccurve(list(outer), closed=True)
    for h in holes:
        hm = ccurve(list(h)[::-1], closed=True)
        m.append_points(hm.points)
    m.set_stroke(width=0, opacity=0).set_fill(color, opacity=opacity)
    return m


def r_arrow(x0, x1, y=0.0, color=GREY_, width=2.0):
    return Arrow([x0, y, 0], [x1, y, 0], buff=0, stroke_width=width, color=color,
                 tip_length=0.11, max_tip_length_to_length_ratio=0.4,
                 max_stroke_width_to_length_ratio=8)


def circle_pts(c, r, n=96):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return c + r * np.exp(1j * t)


# ================================================================ 073 Falconer
def cantor_squares(level):
    """4-corner Cantor dust with ratio 1/3 (Hausdorff dim log4/log3 ~ 1.26).
    Returns lower-left corners (unit square) and the side of each square."""
    sq, s = [(0.0, 0.0)], 1.0
    for _ in range(level):
        s /= 3
        sq = [(x + dx * 2 * s, y + dy * 2 * s) for (x, y) in sq for dx in (0, 1) for dy in (0, 1)]
    return sq, s


def _falconer_pairs(sqs, s, n, seed=4, lo=0.16, hi=1.36):
    """Pairs of genuine points of E (corner + s*(1/4 or 3/4): 1/4 and 3/4 lie in
    the middle-thirds Cantor set) with distances spread over (0, sqrt 2)."""
    rng = np.random.default_rng(seed)
    pts = []
    for (x, y) in sqs:
        ox, oy = rng.choice([0.25, 0.75], 2)
        pts.append(np.array([x + ox * s, y + oy * s]))
    pts = np.array(pts)
    m = len(pts)
    cand = [(i, j, np.linalg.norm(pts[i] - pts[j])) for i in range(m) for j in range(i + 1, m)]
    targets = np.linspace(lo, hi, n) + rng.uniform(-0.4, 0.4, n) * (hi - lo) / max(n - 1, 1)
    chosen, ends = [], set()
    for tgt in targets:
        best = min((c for c in cand if c not in chosen),
                   key=lambda c: abs(c[2] - tgt) + 0.03 * ((c[0] in ends) + (c[1] in ends)))
        chosen.append(best)
        ends.update(best[:2])
    return pts, chosen


def icon_falconer():
    S = 0.96
    org = np.array([-1.45, -S / 2, 0])
    sqs, s = cantor_squares(2)
    frame = Square(S, stroke_color=DIM, stroke_width=1.0).move_to(org + [S / 2, S / 2, 0])
    dust = VGroup(*[Square(s * S, stroke_width=0, fill_color=ACC, fill_opacity=0.95)
                    .move_to(org + [(x + s / 2) * S, (y + s / 2) * S, 0]) for x, y in sqs])
    pts, pairs = _falconer_pairs(sqs, s, 3, seed=2)
    segs = VGroup(*[Line(org + [*pts[i] * S, 0], org + [*pts[j] * S, 0], stroke_color=WHITE_,
                         stroke_width=1.4) for i, j, _ in pairs])
    arr = r_arrow(-0.33, 0.07, 0.0)
    x0, y0 = 0.25, -0.12
    L = np.sqrt(2) * S
    axis = Line([x0 - 0.05, y0, 0], [x0 + L + 0.18, y0, 0], stroke_color=GREY_, stroke_width=1.4)
    bar = Rectangle(width=L, height=0.13, stroke_width=0, fill_color=YELLOW_, fill_opacity=0.55)
    bar.move_to([x0 + L / 2, y0, 0])
    ticks = VGroup(*[Line([x0 + d * S, y0 - 0.12, 0], [x0 + d * S, y0 + 0.12, 0], stroke_color=WHITE_,
                          stroke_width=1.6) for _, _, d in pairs])
    return VGroup(frame, dust, segs, arr, axis, bar, ticks)


def falconer_big():
    S = 2.4                       # side of the unit square [0,1]^2 on screen
    org = np.array([0.0, 1.0, 0])
    sqs, s = cantor_squares(3)
    frame = Square(S, stroke_color=DIM, stroke_width=1.2).move_to(org + [S / 2, S / 2, 0])
    dust = VGroup(*[Square(s * S, stroke_width=0, fill_color=ACC, fill_opacity=0.95)
                    .move_to(org + [(x + s / 2) * S, (y + s / 2) * S, 0]) for x, y in sqs])
    e_lab = tex("E", 36, ACC).next_to(frame, LEFT, buff=0.18).align_to(frame, UP)
    dim1 = tex(r"\dim E \approx 1.26", 30, WHITE_)
    dim2 = tex(r"> d/2 = 1", 30, ACC)
    dimlab = VGroup(dim1, dim2).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    dimlab.next_to(frame, RIGHT, buff=0.35).shift(UP * 0.35)
    # "Claimed in every dimension": the picture is d = 2, the claim is every d
    every = tex(r"d = 2, 3, 4, \dots", 28, YELLOW_)
    every.next_to(dimlab, DOWN, aligned_edge=LEFT, buff=0.42)

    L = np.sqrt(2) * S            # diameter of the square = largest distance
    y0 = -0.62
    axis = Line([-0.08, y0, 0], [L + 0.3, y0, 0], stroke_color=GREY_, stroke_width=2)
    end_ticks = VGroup(*[Line([x, y0 - 0.09, 0], [x, y0 + 0.09, 0], stroke_color=GREY_, stroke_width=2)
                         for x in (0.0, L)])
    n0 = tex("0", 26, GREY_).next_to(end_ticks[0], DOWN, buff=0.12)
    n1 = tex(r"\sqrt2", 26, GREY_).next_to(end_ticks[1], DOWN, buff=0.12)
    d_lab = tex(r"\Delta(E)", 30, WHITE_).next_to(axis, RIGHT, buff=0.15)

    pts, pairs = _falconer_pairs(sqs, s, 14, seed=4)
    pairs = sorted(pairs, key=lambda c: c[2])
    P = lambda i: org + np.array([*(pts[i] * S), 0])  # noqa: E731
    segs = VGroup(*[Line(P(i), P(j), stroke_color=WHITE_, stroke_width=2.0) for i, j, _ in pairs])
    flyers = segs.copy()
    # each distance as a rod [0, d] on its own row (sorted -> a staircase)
    rods = VGroup(*[Line([0, y0 + 0.17 + 0.078 * k, 0], [d * S, y0 + 0.17 + 0.078 * k, 0])
                    for k, (_, _, d) in enumerate(pairs)])
    ticks = VGroup(*[Line([d * S, y0 - 0.14, 0], [d * S, y0 + 0.14, 0]) for _, _, d in pairs])
    bar = Rectangle(width=L, height=0.2, stroke_width=0, fill_color=YELLOW_, fill_opacity=0.5)
    bar.move_to([L / 2, y0, 0])
    lenlab = txt("length > 0", 26, YELLOW_, weight=SEMIBOLD).move_to([L / 2, y0 - 0.62, 0])

    for m in (segs, flyers, rods, ticks):
        m.set_stroke(WHITE_, width=2.0, opacity=0)
    bar.set_fill(opacity=0)
    lenlab.set_opacity(0)
    every.set_opacity(0)

    vis = VGroup(frame, dust, e_lab, dimlab, every, axis, end_ticks, n0, n1, d_lab,
                 bar, segs, rods, ticks, flyers, lenlab)
    vis.segs, vis.flyers, vis.rods, vis.ticks = segs, flyers, rods, ticks
    vis.bar, vis.lenlab, vis.dimlab, vis.every, vis.dust = bar, lenlab, dimlab, every, dust
    return vis


def _rigid_to(line, target):
    """Rotate + translate `line` (length preserved) onto the horizontal `target`."""
    p, q = line.get_start().copy(), line.get_end().copy()
    if q[0] < p[0]:
        p, q = q, p
    v = q - p
    ln = np.linalg.norm(v)
    th0 = np.arctan2(v[1], v[0])
    m0, m1 = (p + q) / 2, (target.get_start() + target.get_end()) / 2

    def upd(mob, alpha):
        th = th0 * (1 - alpha)
        m = (1 - alpha) * m0 + alpha * m1
        u = np.array([np.cos(th), np.sin(th), 0]) * ln / 2
        mob.put_start_and_end_on(m - u, m + u)

    return UpdateFromAlphaFunc(line, upd, rate_func=smooth)


def _beats(scene, rt):
    """Schedule helpers in fractions f of the feature window [now, now + rt]
    (the window spans one narration line, so fractions track the words)."""
    t0 = scene.now

    def at(f):
        if t0 + f * rt - scene.now > 1.0 / config.frame_rate:   # skip sub-frame waits
            scene.wait_until(t0 + f * rt)

    def span(f0, f1, *anims, **kw):
        at(f0)
        scene.play(*anims, run_time=max(0.25, t0 + f1 * rt - scene.now), **kw)

    return at, span


def falconer_animate(scene, vis, rt):
    # Beats of L0 ("Falconer's distance conjecture: if a dusty, fractal set has
    # more than half the dimension of the space it lives in, the distances
    # between its points take up a positive length of the number line.
    # Claimed in every dimension."), as fractions of the card's lifetime.
    at, span = _beats(scene, rt)
    # 1. "a dusty, fractal set": a shimmer sweeps across the Cantor dust
    sq = sorted(vis.dust, key=lambda m: m.get_center()[0] + m.get_center()[1])
    span(0.12, 0.26, LaggedStart(*[m.animate(rate_func=there_and_back).set_fill(WHITE_).scale(1.35)
                                   for m in sq], lag_ratio=0.04))
    # 2. "more than half the dimension"
    span(0.29, 0.38, Indicate(vis.dimlab[1], color=YELLOW_, scale_factor=1.2))
    # 3. "the distances between its points": segments between pairs of points of E
    vis.segs.set_stroke(opacity=0.95)
    span(0.45, 0.59, LaggedStart(*[Create(s) for s in vis.segs], lag_ratio=0.18))
    # 4. each distance is measured: the segment swings rigidly down onto the line
    vis.flyers.set_stroke(opacity=1.0)
    order = list(range(len(vis.flyers)))
    np.random.default_rng(1).shuffle(order)
    span(0.59, 0.72, LaggedStart(*[_rigid_to(vis.flyers[k], vis.rods[k]) for k in order],
                                 lag_ratio=0.12),
         vis.segs.animate.set_stroke(opacity=0.22))
    # 5. ... and recorded as a point of the distance set
    targets = [t.copy().set_stroke(WHITE_, width=2.2, opacity=1.0) for t in vis.ticks]
    span(0.72, 0.77, LaggedStart(*[Transform(f, t) for f, t in zip(vis.flyers, targets)],
                                 lag_ratio=0.06))
    # 6. "take up a positive length of the number line"
    vis.bar.set_fill(YELLOW_, opacity=0.5)
    vis.lenlab.set_opacity(1.0)
    span(0.77, 0.86, GrowFromEdge(vis.bar, LEFT), FadeIn(vis.lenlab, shift=UP * 0.12))
    # 7. "Claimed in every dimension"
    vis.every.set_opacity(1.0)
    span(0.90, 0.97, FadeIn(vis.every, shift=UP * 0.12))


# ================================================================ 071 Koebe
# Circle domain D: |z| < 2 minus four round holes, plus a Cantor dust of point
# holes. The irregular domain is f(D) for an explicit univalent analytic f
# (terms with poles inside the holes, plus a polynomial perturbation), so the
# morph f -> id is a genuine family of conformal maps: mesh stays orthogonal.
KR = 2.0
K_HOLES = [  # centre, radius, [(m, |alpha|, arg alpha)]
    (complex(-0.92, 0.62), 0.42, [(1, 0.30, 0.9), (2, 0.16, 2.4)]),
    (complex(0.84, 0.80), 0.34, [(3, 0.22, 0.3), (1, 0.12, 1.0)]),
    (complex(0.70, -0.62), 0.45, [(1, 0.22, 2.2), (3, 0.12, 0.7)]),
    (complex(-0.58, -0.98), 0.26, [(1, 0.70, 0.5)]),
]
K_OUTER = [(1, 0.09, 0.6), (2, 0.05, 2.0), (4, 0.025, 0.3)]
K_DUST_C, K_DUST_W = complex(0.06, 0.02), 0.42


def kf(z):
    z = np.asarray(z, dtype=complex)
    w = z.copy()
    for c, r, terms in K_HOLES:
        for m, a, ph in terms:
            w = w + a * np.exp(1j * ph) * r ** (m + 1) / (z - c) ** m
    for m, b, ph in K_OUTER:
        w = w + b * np.exp(1j * ph) * KR * (z / KR) ** (m + 1)
    return w


def _k_mesh_segments(step=0.4):
    segs = []
    ks = np.arange(-4, 5) * step
    for vertical in (True, False):
        for x0 in ks:
            h = np.sqrt(KR ** 2 - x0 ** 2) - 0.0
            ivs = [(-h, h)]
            for c, r, _ in K_HOLES:
                cx, cy = (c.real, c.imag) if vertical else (c.imag, c.real)
                if abs(x0 - cx) < r:
                    hh = np.sqrt(r ** 2 - (x0 - cx) ** 2)
                    lo, hi = cy - hh, cy + hh
                    new = []
                    for a, b in ivs:
                        if hi <= a or lo >= b:
                            new.append((a, b))
                        else:
                            if lo > a:
                                new.append((a, lo))
                            if hi < b:
                                new.append((hi, b))
                    ivs = new
            for a, b in ivs:
                if b - a < 0.06:
                    continue
                n = max(6, int((b - a) / 0.07))
                t = np.linspace(a, b, n)
                zs = (x0 + 1j * t) if vertical else (t + 1j * x0)
                segs.append(zs)
    return segs


def _k_dust(level):
    sq, s = cantor_squares(level)
    return [K_DUST_C + K_DUST_W * complex(x + s / 2 - 0.5, y + s / 2 - 0.5) for x, y in sq]


def koebe_domain(scale=1.0, warped=True, mesh=True, dust_level=2, hole_w=2.0, outer_w=2.4,
                 dot_r=0.03):
    F = kf if warped else (lambda z: np.asarray(z, dtype=complex))
    outer = F(circle_pts(0, KR, 160)) * scale
    holes = [F(circle_pts(c, r, 96)) * scale for c, r, _ in K_HOLES]
    fill = region(outer, holes, ACC, 0.12)
    o_line = ccurve(outer, closed=True, color=ACC, width=outer_w)
    h_lines = VGroup(*[ccurve(h, closed=True, color=WHITE_, width=hole_w) for h in holes])
    g = VGroup(fill)
    if mesh:
        mesh_g = VGroup(*[ccurve(F(zs) * scale, color=ACC, width=1.1, opacity=0.38)
                          for zs in _k_mesh_segments()])
    else:
        mesh_g = VGroup()
    dz = F(np.array(_k_dust(dust_level))) * scale
    dust = VGroup(*[Dot([w.real, w.imag, 0], radius=dot_r, color=WHITE_) for w in dz])
    g.add(mesh_g, o_line, h_lines, dust)
    g.fill_, g.mesh, g.outer, g.holes, g.dust = fill, mesh_g, o_line, h_lines, dust
    g.pieces = [fill, *mesh_g, o_line, *h_lines, *dust]
    return g


def icon_koebe():
    sc = 0.235
    w = koebe_domain(sc, warped=True, mesh=False, dust_level=1, hole_w=1.4, outer_w=1.8, dot_r=0.014)
    r = koebe_domain(sc, warped=False, mesh=False, dust_level=1, hole_w=1.4, outer_w=1.8, dot_r=0.014)
    w.move_to(LEFT * 0.92)
    r.move_to(RIGHT * 0.92)
    arr = r_arrow(-0.24, 0.24)
    return VGroup(w, arr, r)


def koebe_big():
    w = koebe_domain(1.0, warped=True, mesh=True, dust_level=2)
    r = koebe_domain(1.0, warped=False, mesh=True, dust_level=2)
    r.set_opacity(0)          # hidden: target geometry, carried along by scaling
    w.mesh.set_stroke(opacity=0)   # the conformal grid is drawn in on the card
    # "from 1908": tucked into the empty upper-left corner, clear of both the
    # warped and the round outer boundary
    year = txt("1908", 30, GREY_, weight=SEMIBOLD).move_to([-2.0, 2.0, 0], aligned_edge=UL)
    year.set_opacity(0)
    vis = VGroup(w, r, year)
    vis.W, vis.R, vis.year = w, r, year
    return vis


def _flash(m, color=YELLOW_, width=5, tw=0.7):
    f = m.copy().set_fill(opacity=0).set_stroke(color, width=width, opacity=1)
    f.set_z_index(65)   # above the zoomed card (z 60)
    return ShowPassingFlash(f, time_width=tw)


def _late(a0, a1=1.0):
    """rate_func that holds still, then eases over [a0, a1] of the animation."""
    return lambda a: smooth(float(np.clip((a - a0) / (a1 - a0), 0, 1)))


def koebe_animate(scene, vis, rt):
    # Beats of L1 ("Koebe's circle domain conjecture, from 1908: any region with
    # holes, even infinitely many, of any shapes, can be reshaped without
    # distorting angles, so that every hole becomes a perfect circle, or a point.")
    W, R = vis.W, vis.R
    at, span = _beats(scene, rt)
    # 0. the conformal grid is drawn on the region; "from 1908"
    W.mesh.set_stroke(opacity=0.38)
    vis.year.set_opacity(1.0)
    span(0.03, 0.20, LaggedStart(*[Create(m) for m in W.mesh], lag_ratio=0.03),
         FadeIn(vis.year, shift=DOWN * 0.1, rate_func=_late(0.45)))
    # 1. "any region with holes": trace the outer boundary, then each hole
    span(0.24, 0.39, LaggedStart(_flash(W.outer, WHITE_, 4, 0.5), *[_flash(h) for h in W.holes],
                                 lag_ratio=0.3))
    # 2. "even infinitely many": the Cantor dust of point-holes
    span(0.385, 0.48, Indicate(W.dust, color=YELLOW_, scale_factor=1.35))
    # 3. "reshaped without distorting angles": the conformal family
    #    z -> (1-s) f(z) + s z; every intermediate map is analytic, so the mesh
    #    stays orthogonal (angles preserved)
    anims = []
    for wp, rp in zip(W.pieces, R.pieces):
        t = rp.copy()
        t.match_style(wp)
        anims.append(Transform(wp, t))
    span(0.52, 0.83, *anims, rate_func=smooth)
    # 4. "every hole becomes a perfect circle, or a point"
    span(0.84, 0.93, LaggedStart(*[_flash(h, tw=0.8) for h in W.holes], lag_ratio=0.15))
    span(0.93, 1.0, Indicate(W.dust, color=YELLOW_, scale_factor=1.35))


# ================================================================ 072 Brennan
def icon_brennan():
    t = np.linspace(0, 2 * np.pi, 220, endpoint=False)
    r = 0.43 * (1 + 0.26 * np.cos(5 * t + 0.4) + 0.08 * np.cos(9 * t + 1.1) + 0.05 * np.cos(14 * t))
    zs = r * np.exp(1j * t) - 0.95
    dom = VGroup(region(zs, color=ACC, opacity=FILL), ccurve(zs, closed=True, color=ACC, width=2.0))
    disk = Circle(radius=0.43, stroke_color=ACC, stroke_width=2.0, fill_color=ACC,
                  fill_opacity=FILL).move_to(RIGHT * 0.95)
    c1 = Dot([-0.95, 0, 0], radius=0.03, color=WHITE_)
    c2 = Dot([0.95, 0, 0], radius=0.03, color=WHITE_)
    arr = r_arrow(-0.3, 0.3, -0.02)
    phi = tex(r"\varphi", 28, GREY_).next_to(arr, UP, buff=0.05)
    # a few radii of the disk = images of curves leaving the centre
    rays = VGroup(*[Line([0.95, 0, 0], [0.95 + 0.43 * np.cos(a), 0.43 * np.sin(a), 0],
                         stroke_color=ACC, stroke_width=1.0, stroke_opacity=0.45)
                    for a in np.linspace(0, 2 * np.pi, 10, endpoint=False)])
    return VGroup(dom, disk, rays, c1, c2, arr, phi)


# ================================================================ 075 L log L
def icon_llogl():
    M = 4096
    x = np.linspace(-np.pi, np.pi, M, endpoint=False)
    f = np.where(np.sin(x) > 0, 0.36, -0.30) + 0.12 * x / np.pi
    f = np.where((x > 1.75) & (x < 2.25), 0.05, f)
    F = np.fft.fft(f) / M
    k = np.fft.fftfreq(M, 1 / M)

    def S(N):
        G = np.where(np.abs(k) <= N, F, 0)
        return np.real(np.fft.ifft(G) * M)

    W = 2.8
    X = x / np.pi * W / 2
    sub = slice(None, None, 8)
    out = VGroup(Line([-W / 2, 0, 0], [W / 2, 0, 0], stroke_color=DIM, stroke_width=1.2))
    out.add(curve(np.c_[X[sub], f[sub]], color=GREY_, width=1.3, opacity=0.9, smooth=False))
    for N, op, wd in ((3, 0.30, 1.6), (9, 0.55, 1.8), (40, 1.0, 2.0)):
        y = S(N)
        out.add(curve(np.c_[X[sub], y[sub]], color=ACC, width=wd, opacity=op, smooth=False))
    return out


# ================================================================ 078 Bochner-Riesz
def icon_bochner_riesz():
    rx, ry, base, H, dlt = 0.88, 0.22, -0.34, 0.62, 0.3

    def P(x1, x2):
        m = np.clip(1 - x1 ** 2 - x2 ** 2, 0, None) ** dlt
        return np.c_[rx * x1, base + ry * x2 + H * m]

    g = VGroup()
    th = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    disk = Ellipse(width=2 * rx, height=2 * ry, stroke_color=ACC, stroke_width=1.6,
                   fill_color=ACC, fill_opacity=0.18).move_to([0, base, 0])
    g.add(disk)
    s = np.sin(np.linspace(-np.pi / 2, np.pi / 2, 70))  # dense near the rim
    for ang in np.linspace(0, np.pi, 7)[:-1]:
        pts = P(s * np.cos(ang), s * np.sin(ang))
        g.add(curve(pts, color=WHITE_, width=1.1, opacity=0.55))
    for rho in (0.6, 0.9):
        pts = P(rho * np.cos(th), rho * np.sin(th))
        g.add(curve(pts, color=ACC, width=1.3, opacity=0.9, closed=True))
    # silhouette of the dome (front profile along x1)
    g.add(curve(P(s, 0 * s), color=ACC, width=2.0))
    form = tex(r"(1-|\xi|^2)_+^{\,\delta}", 26, GREY_).next_to(g, RIGHT, buff=0.25)
    return VGroup(g, form)


# ================================================================ 079 local smoothing
def icon_local_smoothing():
    x_a, x_e, R_e = -1.25, 1.3, 0.46
    rad = lambda x: R_e * (x - x_a) / (x_e - x_a)  # noqa: E731
    axis = Arrow([-1.45, 0, 0], [1.5, 0, 0], buff=0, stroke_width=1.4, color=DIM, tip_length=0.1,
                 max_tip_length_to_length_ratio=0.1)
    cone = VGroup(Line([x_a, 0, 0], [x_e, R_e, 0]), Line([x_a, 0, 0], [x_e, -R_e, 0]))
    cone.set_stroke(GREY_, 1.4)
    rim = Ellipse(width=0.16, height=2 * R_e, stroke_color=GREY_, stroke_width=1.2).move_to([x_e, 0, 0])
    x1, x2 = 0.05, 0.75
    r1, r2 = rad(x1), rad(x2)
    slab = Polygon([x1, r1, 0], [x2, r2, 0], [x2, -r2, 0], [x1, -r1, 0], stroke_width=0,
                   fill_color=ACC, fill_opacity=0.28)
    e1 = Ellipse(width=0.1, height=2 * r1, stroke_color=ACC, stroke_width=1.8).move_to([x1, 0, 0])
    e2 = Ellipse(width=0.14, height=2 * r2, stroke_color=ACC, stroke_width=1.8).move_to([x2, 0, 0])
    # earlier wavefronts (circles of radius t at time t) in grey
    ws = VGroup(*[Ellipse(width=0.04 + 0.06 * rad(x) / R_e, height=2 * rad(x), stroke_color=GREY_,
                          stroke_width=1.0, stroke_opacity=0.6).move_to([x, 0, 0])
                  for x in (-0.75, -0.35)])
    l1 = tex("1", 22, GREY_).move_to([x1, -0.55, 0])
    l2 = tex("2", 22, GREY_).move_to([x2, -0.55, 0])
    lt = tex("t", 24, GREY_).move_to([1.55, -0.2, 0])
    return VGroup(axis, slab, cone, ws, rim, e1, e2, l1, l2, lt)


# ================================================================ 077 restriction
def icon_restriction():
    C = np.array([-2.05, 0, 0])
    R = 0.85
    angs = np.radians(np.linspace(-9, 9, 5))
    arc = Arc(radius=R, start_angle=np.radians(-30), angle=np.radians(60), arc_center=C,
              stroke_color=ACC, stroke_width=3.5)
    cap = AnnularSector(inner_radius=R - 0.12, outer_radius=R, start_angle=np.radians(-30),
                        angle=np.radians(60), arc_center=C, stroke_width=0, color=ACC, fill_opacity=0.25)
    g = VGroup(cap, arc)
    for a in angs:
        u = np.array([np.cos(a), np.sin(a), 0])
        n = np.array([-np.sin(a), np.cos(a), 0])
        p0 = C + R * u
        g.add(Dot(p0, radius=0.035, color=WHITE_))
        p1, p2 = p0 + 0.22 * u, C + 3.6 * u
        tube = Polygon(p1 + 0.075 * n, p2 + 0.075 * n, p2 - 0.075 * n, p1 - 0.075 * n,
                       stroke_width=0, fill_color=ACC, fill_opacity=0.16)
        g.add(tube)
        for s in np.linspace(0.4, 2.6, 6):   # wave crests across the packet
            q = C + (R + s) * u
            g.add(Line(q - 0.075 * n, q + 0.075 * n, stroke_color=ACC, stroke_width=1.3,
                       stroke_opacity=0.9))
    lab = tex(r"\Sigma", 26, GREY_).move_to(C + R * np.array([np.cos(0.62), np.sin(0.62), 0]) + UL * 0.12)
    g.add(lab)
    return g


# ================================================================ 076 Littlewood
def icon_littlewood():
    signs = [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]   # Barker sequence of length 13
    x0, dx, h = -1.45, 0.11, 0.34
    g = VGroup(Line([x0 - 0.06, 0, 0], [x0 + dx * 12 + 0.06, 0, 0], stroke_color=DIM, stroke_width=1.2))
    for i, s in enumerate(signs):
        x = x0 + i * dx
        g.add(Line([x, 0, 0], [x, s * h, 0], stroke_color=ACC, stroke_width=2.0))
        g.add(Dot([x, s * h, 0], radius=0.032, color=ACC if s > 0 else WHITE_))
    c = np.array([0.95, 0, 0])
    R0 = 0.44
    ref = Circle(radius=R0, stroke_color=GREY_, stroke_width=1.0, stroke_opacity=0.7).move_to(c)
    t = np.linspace(0, 2 * np.pi, 240, endpoint=False)
    r = R0 * (1 + 0.035 * np.sin(9 * t) + 0.025 * np.cos(15 * t + 0.7) + 0.015 * np.sin(23 * t + 2))
    mod = curve(np.c_[c[0] + r * np.cos(t), r * np.sin(t)], color=ACC, width=2.2, closed=True)
    band = Annulus(inner_radius=R0 * 0.92, outer_radius=R0 * 1.08, stroke_width=0, fill_color=ACC,
                   fill_opacity=0.12).move_to(c)
    arr = r_arrow(0.05, 0.38, 0.0, width=1.6)
    g.add(arr, band, ref, mod)
    return g


# ================================================================ 084 Erdos similarity
def icon_erdos_similarity():
    xl, xr, y = -1.42, 1.42, -0.25
    gaps = [(-1.12, -1.06), (-0.70, -0.66), (-0.17, -0.04), (0.28, 0.33), (0.74, 0.80), (1.10, 1.13)]
    g = VGroup()
    a = xl
    for lo, hi in gaps + [(xr, xr)]:
        g.add(Line([a, y, 0], [lo, y, 0], stroke_color=ACC, stroke_width=6))
        a = hi
    x0, tt, q = -0.92, 2.1, 0.62
    xs = [x0 + tt * q ** n for n in range(0, 9)]
    bad = 2   # x0 + t q^2 falls in the gap (-0.17, -0.04)
    yd = 0.3
    for n, x in enumerate(xs):
        col = RED_ if n == bad else WHITE_
        g.add(Dot([x, yd, 0], radius=0.036 * 0.9 ** n, color=col))
    xb = xs[bad]
    g.add(DashedLine([xb, yd - 0.07, 0], [xb, y + 0.02, 0], stroke_color=RED_, stroke_width=1.6,
                     dash_length=0.05))
    cr = VGroup(Line([-0.07, -0.07, 0], [0.07, 0.07, 0]), Line([-0.07, 0.07, 0], [0.07, -0.07, 0]))
    cr.set_stroke(RED_, 2.2).move_to([xb, y - 0.2, 0])
    g.add(cr)
    return g


# ================================================================ 090 triangular lattice
def icon_lattice():
    a = 0.29
    rows = 4
    hgt = a * np.sqrt(3) / 2
    pts = []
    for j in range(rows):
        for i in range(-6, 7):
            x = i * a + (a / 2 if j % 2 else 0)
            yy = (j - (rows - 1) / 2) * hgt
            if abs(x) <= 1.45:
                pts.append(np.array([x, yy, 0]))
    ctr = min(pts, key=lambda p: np.linalg.norm(p - np.array([0.0, hgt / 2, 0])))
    g = VGroup()
    hexagon = Polygon(*[ctr + a * np.array([np.cos(k * np.pi / 3), np.sin(k * np.pi / 3), 0])
                        for k in range(6)], stroke_color=ACC, stroke_width=1.8, fill_color=ACC,
                      fill_opacity=0.12)
    spokes = VGroup(*[Line(ctr, ctr + a * np.array([np.cos(k * np.pi / 3), np.sin(k * np.pi / 3), 0]),
                           stroke_color=ACC, stroke_width=1.0, stroke_opacity=0.6) for k in range(6)])
    g.add(hexagon, spokes)
    for p in pts:
        d = np.linalg.norm(p - ctr)
        if d < 1e-6:
            g.add(Dot(p, radius=0.045, color=ACC))
        elif d < a * 1.01:
            g.add(Dot(p, radius=0.04, color=WHITE_))
        else:
            g.add(Dot(p, radius=0.034, color=GREY_, fill_opacity=max(0.25, 1 - 0.45 * d)))
    return g


# ================================================================ 091 log Brunn-Minkowski
def _wulff(h, n=720, box=3.0):
    """Wulff shape {x : <x,u> <= h(u) for all u}, by clipping a square."""
    poly = [np.array(p) for p in ([-box, -box], [box, -box], [box, box], [-box, box])]
    for th in np.linspace(0, 2 * np.pi, n, endpoint=False):
        u = np.array([np.cos(th), np.sin(th)])
        c = h(u)
        out = []
        for i in range(len(poly)):
            P, Q = poly[i], poly[(i + 1) % len(poly)]
            fp, fq = P @ u - c, Q @ u - c
            if fp <= 0:
                out.append(P)
            if fp * fq < 0:
                out.append(P + (Q - P) * fp / (fp - fq))
        poly = out
    return np.array(poly)


def icon_log_bm():
    K = np.array([[-0.48, -0.2], [0.48, -0.2], [0.48, 0.2], [-0.48, 0.2]])
    Lv = np.array([[0.0, -0.46], [0.3, 0.0], [0.0, 0.46], [-0.3, 0.0]])
    hK = lambda u: np.max(K @ u)  # noqa: E731
    hL = lambda u: np.max(Lv @ u)  # noqa: E731
    M = _wulff(lambda u: np.sqrt(hK(u) * hL(u)))

    def shape(pts, x, col=ACC, fo=FILL, w=2.0):
        p = Polygon(*[[a + x, b, 0] for a, b in pts], stroke_color=col, stroke_width=w,
                    fill_color=ACC, fill_opacity=fo)
        return VGroup(p, Dot([x, 0, 0], radius=0.028, color=WHITE_))

    k = shape(K, 0)
    plus = tex(r"+_0", 30, GREY_)
    l = shape(Lv, 0)
    eq = tex(r"=", 30, GREY_)
    m = shape(M, 0, col=WHITE_, fo=0.3)
    return VGroup(k, plus, l, eq, m).arrange(RIGHT, buff=0.17)


# ================================================================ 096 Gaussian propeller
def icon_propeller():
    sig = 0.3
    g = VGroup()
    for i, rr in enumerate(np.linspace(0.55, 0.1, 6)):
        g.add(Circle(radius=rr, stroke_width=0, fill_color=ACC, fill_opacity=0.09))
    for k in range(3):
        a = np.pi / 2 + k * 2 * np.pi / 3
        g.add(Line(ORIGIN, 0.56 * np.array([np.cos(a), np.sin(a), 0]), stroke_color=WHITE_,
                   stroke_width=1.8))
    # Gaussian barycentre of each 120-degree sector: |E[X | sector]| = 3 sin(60)/sqrt(2 pi) sigma
    rb = 3 * np.sin(np.pi / 3) / np.sqrt(2 * np.pi) * sig
    for k in range(3):
        a = np.pi / 6 + k * 2 * np.pi / 3
        e = rb * np.array([np.cos(a), np.sin(a), 0])
        g.add(Arrow(ORIGIN, e * 1.0, buff=0, stroke_width=2.4, color=YELLOW_, tip_length=0.09,
                    max_tip_length_to_length_ratio=0.45, max_stroke_width_to_length_ratio=12))
    g.add(Dot(ORIGIN, radius=0.025, color=WHITE_))
    g.move_to(LEFT * 0.8)
    form = tex(r"\sum_i |m_i|^2 \le \dfrac{9}{8\pi}", 30, GREY_).next_to(g, RIGHT, buff=0.3)
    return VGroup(g, form)


# ================================================================ tiles
ICONS = {
    "073": icon_falconer,
    "071": icon_koebe,
    "072": icon_brennan,
    "075": icon_llogl,
    "078": icon_bochner_riesz,
    "079": icon_local_smoothing,
    "077": icon_restriction,
    "076": icon_littlewood,
    "084": icon_erdos_similarity,
    "090": icon_lattice,
    "091": icon_log_bm,
    "096": icon_propeller,
}
FEATURES = {
    "073": dict(big=falconer_big, animate=falconer_animate),
    "071": dict(big=koebe_big, animate=koebe_animate),
}


def _tiles():
    spec = json.loads((VIDEO / "data" / "grids.json").read_text())["c3_grid"]
    out = []
    for d in spec:
        t = dict(num=d["num"], name=d["name"], verdict=d["verdict"], icon=ICONS[d["num"]])
        if d.get("caption"):
            t["feature"] = dict(caption=d["caption"], **FEATURES.get(d["num"], {}))
        out.append(t)
    return out


class C3Grid(GridScene):
    CHAPTER = "an"
    TILES = _tiles()
    THREE_D = ("078", "079", "077")   # "... all three in three dimensions"

    def wait_until(self, t, **kw):
        # Hook into the template's idle stretch between {t077} and {t076}: when the
        # narration says "all three in three dimensions", light the three 3D tiles
        # together (Bochner-Riesz, local smoothing, restriction).
        target = self.cue(t)
        if not getattr(self, "_did_3d", False) and self.has_cue("t077") and self.has_cue("t076"):
            s = max(self.cue("t077") + 1.0, self.cue("t076") - 1.5)
            if self.now <= s + 0.05 and target >= s + 1.15:
                self._did_3d = True
                super().wait_until(s)
                self._three_d(target)
        super().wait_until(t, **kw)

    def _three_d(self, until):
        color = CHAPTER_COLOR[self.CHAPTER]
        group = [t for t in self.tiles if t.num in self.THREE_D]
        if len(group) != 3:
            return
        lit = []
        for t in group:
            lit += t.lit() + [Indicate(t.label, color=color, scale_factor=1.05),
                              t.icon.animate(rate_func=there_and_back).scale(1.08)]
        self.play(*lit, run_time=0.5)
        back = min(0.4, max(0.2, until - self.now - 0.45))
        self.wait_until(max(self.now, until - back - 0.05))
        self.play(*[a for t in group for a in t.visited()], run_time=back)
