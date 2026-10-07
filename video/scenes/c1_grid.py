import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
from lib.grid import GridScene

import json
import math

import numpy as np

# Rapid-fire grid for Number Theory.  Every icon is a small, true-to-the-maths
# diagram drawn at (roughly) the size it is shown in the tile, so stroke widths
# and dot radii stay consistent across tiles.

ACC = BLUE_            # chapter accent
SW = 2.2               # main stroke
SW_T = 1.4             # thin stroke
RD = 0.034             # standard dot radius


# ------------------------------------------------------------------ helpers
def _isprime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    f = 3
    while f * f <= n:
        if n % f == 0:
            return False
        f += 2
    return True


def _P(x, y):
    return np.array([x, y, 0.0])


def _polar(r, a):
    return np.array([r * math.cos(a), r * math.sin(a), 0.0])


def _dot(p, r=RD, c=ACC, op=1.0):
    return Dot(p, radius=r, color=c, fill_opacity=op, stroke_width=0)


def _merged_dots(points, r, color, op=1.0):
    """Many dots as ONE VMobject (cheap to render, counts as one submobject)."""
    m = VMobject(stroke_width=0, fill_color=color, fill_opacity=op)
    for p in points:
        m.append_vectorized_mobject(Circle(radius=r).move_to(p))
    return m


def _segments(pairs, color, width, op=1.0):
    """Many line segments as one VMobject."""
    m = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=op, fill_opacity=0)
    for a, b in pairs:
        m.start_new_path(a)
        m.add_line_to(b)
    return m


def _m(s, size=24, color=WHITE_):
    return MathTex(s, font_size=size, color=color)


def _arrow(a, b, color=GREY_, width=2.0, tip=0.1):
    return Arrow(a, b, buff=0, color=color, stroke_width=width, tip_length=tip,
                 max_tip_length_to_length_ratio=0.4, max_stroke_width_to_length_ratio=12)


def _cubic_roots(a, b):
    return sorted(r.real for r in np.roots([1, 0, a, b]) if abs(r.imag) < 1e-9)


def _elliptic(a, b, xmax, n=70, color=ACC, width=SW, op=1.0):
    """Real locus of y^2 = x^3 + a x + b as smooth closed/open curves (true shape)."""
    f = lambda x: x ** 3 + a * x + b
    roots = _cubic_roots(a, b)
    parts = VGroup()
    r = roots[-1]
    U = math.sqrt(xmax - r)
    pts = [_P(r + u * u, math.copysign(math.sqrt(max(0.0, f(r + u * u))), u))
           for u in np.linspace(-U, U, n)]
    parts.add(VMobject(stroke_color=color, stroke_width=width, stroke_opacity=op)
              .set_points_smoothly(pts))
    if len(roots) == 3:                       # the bounded "egg"
        r1, r2 = roots[0], roots[1]
        th = np.linspace(0, TAU, n)
        pts = []
        for t in th:
            x = (r1 + r2) / 2 - (r2 - r1) / 2 * math.cos(t)
            pts.append(_P(x, math.copysign(math.sqrt(max(0.0, f(x))), math.sin(t) + 1e-12)))
        parts.add(VMobject(stroke_color=color, stroke_width=width, stroke_opacity=op)
                  .set_points_smoothly(pts))
    return parts


def _gear(r=0.16, teeth=8, depth=0.055, color=GREY_, width=SW_T):
    pts = []
    w = TAU / teeth
    for i in range(teeth):
        a = w * i
        pts += [_polar(r, a), _polar(r + depth, a + 0.12 * w),
                _polar(r + depth, a + 0.40 * w), _polar(r, a + 0.52 * w)]
    body = Polygon(*pts, stroke_color=color, stroke_width=width, fill_opacity=0)
    hole = Circle(radius=r * 0.42, stroke_color=color, stroke_width=width)
    return VGroup(body, hole)


# ------------------------------------------------------------------ data
G_CAT = 0.91596559417721901505   # Catalan's constant


def _catalan_sums(n):
    s, out = 0.0, []
    for j in range(n):
        s += (-1) ** j / (2 * j + 1) ** 2
        out.append(s)
    return out


def _liouville(n):
    k, m, d = 0, n, 2
    while d * d <= m:
        while m % d == 0:
            m //= d
            k += 1
        d += 1
    if m > 1:
        k += 1
    return -1 if k % 2 else 1


def _gauss_prime(a, b):
    if a == 0:
        return _isprime(abs(b)) and abs(b) % 4 == 3
    if b == 0:
        return _isprime(abs(a)) and abs(a) % 4 == 3
    return _isprime(a * a + b * b)


# ================================================================== ICONS
def icon_catalan():
    """Partial sums 1, 1-1/9, 1-1/9+1/25, ... zig-zagging onto G (true values,
    vertical axis linear about G)."""
    S = _catalan_sums(14)
    xs = np.linspace(-1.22, 1.0, len(S))
    k = 0.52 / (S[0] - G_CAT)
    pts = [_P(x, (s - G_CAT) * k) for x, s in zip(xs, S)]
    gl = DashedLine(_P(-1.36, 0), _P(1.13, 0), dash_length=0.06, dashed_ratio=0.55,
                    stroke_width=1.6, color=GREY_)
    zig = VMobject(stroke_color=ACC, stroke_width=SW).set_points_as_corners(pts)
    dots = VGroup(*[_dot(p, 0.036) for p in pts])
    lab = _m("G", 30).next_to(gl, RIGHT, buff=0.08)
    return VGroup(gl, zig, dots, lab)


def icon_h10():
    """A polynomial curve with its rational points -> algorithm box -> '?'."""
    R = 0.37
    circ = Circle(radius=R, stroke_color=GREY_, stroke_width=SW_T)
    ts = [0, 1 / 3, 1 / 2, 2 / 3, 1, 3 / 2, 2, 4, -1 / 4, -1 / 2, -1, -2, -3 / 2, -5]
    rp = [_P(R * (1 - t * t) / (1 + t * t), R * 2 * t / (1 + t * t)) for t in ts] + [_P(-R, 0)]
    dots = VGroup(*[_dot(p, 0.03) for p in rp])
    curve = VGroup(circ, dots).move_to(_P(-1.02, 0))
    a1 = _arrow(_P(-0.56, 0), _P(-0.14, 0))
    box = RoundedRectangle(width=0.78, height=0.62, corner_radius=0.08, stroke_color=ACC,
                           stroke_width=SW, fill_color=ACC, fill_opacity=0.10).move_to(_P(0.3, 0))
    gear = _gear(0.15, 8, 0.05).move_to(box)
    a2 = _arrow(_P(0.74, 0), _P(1.12, 0))
    q = _m("?", 40).move_to(_P(1.3, 0.0))
    return VGroup(curve, a1, box, gear, a2, q)


def icon_bsd():
    """Elliptic curve with rational points (on the chord y=1)  <->  L(E,s) with
    its zero at s=1."""
    E = _elliptic(-1, 1, 1.32, n=80)              # y^2 = x^3 - x + 1
    chord = Line(_P(-1.3, 1), _P(1.45, 1), stroke_color=GREY_, stroke_width=SW_T)
    pts = VGroup(*[_dot(_P(x, 1), 0.12, WHITE_) for x in (-1, 0, 1)])
    left = VGroup(E, chord, pts).scale(0.29).move_to(_P(-0.88, 0))
    arr = DoubleArrow(_P(-0.36, 0), _P(0.06, 0), buff=0, stroke_width=1.8, color=GREY_,
                      tip_length=0.08, max_tip_length_to_length_ratio=0.3)
    # L(E,s) near s = 1: simple zero, sign change (rank one)
    x0, x1, sc = 0.25, 1.38, 0.62
    s_to_x = lambda s: x0 + (s - 0.35) * sc
    axis = Line(_P(x0 - 0.02, -0.08), _P(x1, -0.08), stroke_color=GREY_, stroke_width=SW_T)
    Lf = lambda s: 0.30 * math.tanh(1.9 * (s - 1)) + 0.05 * (s - 1)
    lpts = [_P(s_to_x(s), -0.08 + Lf(s)) for s in np.linspace(0.38, 2.05, 40)]
    lc = VMobject(stroke_color=ACC, stroke_width=SW).set_points_smoothly(lpts)
    z = _dot(_P(s_to_x(1), -0.08), 0.045, WHITE_)
    ll = _m("L(E,s)", 20, GREY_).next_to(lpts[-1], UP, buff=0.06).shift(LEFT * 0.12)
    return VGroup(left, arr, axis, lc, z, ll)


def icon_goldfeld():
    """Quadratic twists E_d: d*y^2 = x^3 - x (same curve, rescaled vertically;
    E drawn in full, two twists' branches fainter) and the rank distribution:
    rank 0 and rank 1 each one half, rank >= 2 density zero."""
    twists = VGroup(_elliptic(-1, 0, 1.42, n=60))
    for d, op in ((2.4, 0.55), (6.0, 0.3)):
        c = _elliptic(-1, 0, 1.42, n=60, op=op)[0]               # unbounded branch only
        c.stretch(1 / math.sqrt(d), 1, about_point=ORIGIN)
        twists.add(c)
    twists.scale(0.36).move_to(_P(-0.82, 0.02))
    arr = _arrow(_P(-0.18, 0.0), _P(0.2, 0.0), tip=0.09)
    base_y, bw, hh = -0.4, 0.3, 0.62
    xs = [0.45, 0.86, 1.27]
    base = Line(_P(0.25, base_y), _P(1.47, base_y), stroke_color=GREY_, stroke_width=SW_T)
    bars = VGroup(*[Rectangle(width=bw, height=hh, stroke_color=ACC, stroke_width=SW,
                              fill_color=ACC, fill_opacity=0.35)
                    .move_to(_P(x, base_y + hh / 2)) for x in xs[:2]])
    flat = Line(_P(xs[2] - bw / 2, base_y), _P(xs[2] + bw / 2, base_y), stroke_color=ACC,
                stroke_width=SW + 1)
    labs = VGroup(*[_m(s, 20, GREY_).move_to(_P(x, base_y - 0.15))
                    for s, x in zip(("0", "1", r"{\geq}2"), xs)])
    half = _m(r"\tfrac12", 20, WHITE_).next_to(bars[1], UP, buff=0.04).set_x((xs[0] + xs[1]) / 2)
    return VGroup(twists, arr, base, bars, flat, labs, half)


def _dome(cx, cy, r, color=ACC, width=SW):
    """Hemisphere over the complex plane seen in perspective: silhouette arc plus
    the front half of its base circle, filled so nearer domes hide farther ones."""
    b = 0.3 * r
    pts = [_P(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, PI, 28)]
    pts += [_P(cx + r * math.cos(t), cy + b * math.sin(t)) for t in np.linspace(PI, TAU, 22)]
    return Polygon(*pts, stroke_color=color, stroke_width=width, fill_color=CARD, fill_opacity=1)


def icon_modularity():
    """Elliptic curve over an imaginary quadratic field, i.e. a complex torus
    <->  the modular side: hemispheres over lattice points of C in hyperbolic
    3-space (Bianchi picture, the 3-D analogue of the Farey arcs)."""
    torus = VGroup(
        Ellipse(width=0.98, height=0.58, stroke_color=ACC, stroke_width=SW),
        ArcBetweenPoints(_P(-0.24, 0.04), _P(0.24, 0.04), angle=0.9 * PI / 2, stroke_color=ACC,
                         stroke_width=SW),
        ArcBetweenPoints(_P(0.16, -0.01), _P(-0.16, -0.01), angle=0.7 * PI / 2, stroke_color=ACC,
                         stroke_width=SW),
    ).move_to(_P(-0.95, 0))
    arr = DoubleArrow(_P(-0.36, 0), _P(0.06, 0), buff=0, stroke_width=1.8, color=GREY_,
                      tip_length=0.08, max_tip_length_to_length_ratio=0.3)
    yb, yf, r = -0.08, -0.3, 0.24
    plane = Polygon(_P(0.14, -0.42), _P(1.62, -0.42), _P(1.78, -0.02), _P(0.3, -0.02),
                    stroke_color=GREY_, stroke_width=1.1, stroke_opacity=0.6, fill_opacity=0)
    back = VGroup(*[_dome(x, yb, r * 0.88, width=1.6) for x in (0.68, 1.12, 1.56)])
    front = VGroup(*[_dome(x, yf, r) for x in (0.46, 0.94, 1.42)])
    return VGroup(torus, arr, plane, back, front)


def icon_egyptian():
    """4/5 = 1/2 + 1/4 + 1/20: a unit bar cut into distinct unit fractions."""
    W, h, x0, y = 2.25, 0.34, -0.85, 0.0
    parts = VGroup()
    x = x0
    for fr, op in ((1 / 2, 0.42), (1 / 4, 0.3), (1 / 20, 0.55)):
        r = Rectangle(width=W * fr, height=h, stroke_color=ACC, stroke_width=SW,
                      fill_color=ACC, fill_opacity=op).move_to(_P(x + W * fr / 2, y))
        parts.add(r)
        x += W * fr
    rest = DashedVMobject(Rectangle(width=W / 5, height=h, stroke_color=GREY_, stroke_width=SW_T)
                          .move_to(_P(x + W / 10, y)), num_dashes=16)
    l1 = _m(r"\tfrac12", 26).move_to(parts[0])
    l2 = _m(r"\tfrac14", 26).move_to(parts[1])
    l3 = _m(r"\tfrac1{20}", 19).next_to(parts[2], UP, buff=0.05)
    xa, xb, yb = x0, x0 + W * 4 / 5, y - h / 2 - 0.06
    brk = VMobject(stroke_color=GREY_, stroke_width=SW_T).set_points_as_corners(
        [_P(xa, yb), _P(xa, yb - 0.06), _P(xb, yb - 0.06), _P(xb, yb)])
    l4 = _m(r"\tfrac45 =", 30, WHITE_).next_to(parts[0], LEFT, buff=0.12)
    return VGroup(parts, rest, l1, l2, l3, brk, l4)


def icon_moat():
    """Gaussian primes in the upper half-plane; the island reachable from 1+i
    with steps <= sqrt(2) (true component), and the empty ring just outside it."""
    A, B = 16, 13
    P = [(a, b) for a in range(-A, A + 1) for b in range(0, B + 1) if _gauss_prime(a, b)]
    S = set(P)
    comp, st = {(1, 1)}, [(1, 1)]
    while st:
        x, y = st.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q in S and q not in comp:
                    comp.add(q)
                    st.append(q)
    sc = 0.084
    pt = lambda z: _P(z[0] * sc, z[1] * sc)
    edges = [(pt(p), pt(q)) for p in comp for q in comp
             if p < q and (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 <= 2]
    rmax = max(math.hypot(*p) for p in comp)
    rout = min(math.hypot(*p) for p in P if math.hypot(*p) > rmax + 1e-9)
    rr = (rmax + rout) / 2 * sc
    ring = DashedVMobject(Arc(radius=rr, start_angle=0, angle=PI, stroke_color=WHITE_,
                              stroke_width=1.6, stroke_opacity=0.75), num_dashes=34)
    axis = Line(_P(-A * sc - 0.05, 0), _P(A * sc + 0.05, 0), stroke_color=GREY_,
                stroke_width=1.0, stroke_opacity=0.5)
    others = _merged_dots([pt(p) for p in P if p not in comp], 0.022, GREY_)
    island = _merged_dots([pt(p) for p in comp], 0.03, ACC)
    eg = _segments(edges, ACC, 1.6, op=0.9)
    return VGroup(axis, ring, others, eg, island)


def icon_artin():
    """2 is a primitive root mod 5, 11, 13, ...: its powers visit every nonzero
    residue (points 1..p-1 around a circle) before returning to 1."""
    g = VGroup()
    for p, r in ((5, 0.22), (11, 0.33), (13, 0.38)):
        circ = Circle(radius=r, stroke_color=GREY_, stroke_width=1.1, stroke_opacity=0.55)
        pos = {k: _polar(r, PI / 2 - TAU * (k - 1) / (p - 1)) for k in range(1, p)}
        seq = [pow(2, i, p) for i in range(p)]
        path = VMobject(stroke_color=ACC, stroke_width=1.7).set_points_as_corners([pos[k] for k in seq])
        dots = VGroup(*[_dot(pos[k], 0.028 if k > 1 else 0.042, GREY_ if k > 1 else WHITE_)
                        for k in range(1, p)])
        g.add(VGroup(circ, path, dots))
    g.arrange(RIGHT, buff=0.24)
    more = _m(r"\cdots", 30, GREY_).next_to(g, RIGHT, buff=0.16)
    return VGroup(g, more)


def icon_ostmann():
    """Primes vs. a sumset A+B (A={0,2}, B={3,5,9,11,17,29}): they never match;
    mismatches (missing 2, 23; extra 9) in red."""
    N, sx, x0 = 31, 0.07, -1.0
    X = lambda n: x0 + n * sx
    primes = [n for n in range(N + 1) if _isprime(n)]
    Aset, Bset = (0, 2), (3, 5, 9, 11, 17, 29)
    sums = sorted({a + b for a in Aset for b in Bset})
    y1, y2 = 0.24, -0.24
    lines = _segments([(_P(X(0) - 0.05, y), _P(X(N) + 0.05, y)) for y in (y1, y2)], GREY_, 1.0, op=0.5)
    pd = VGroup(*[_dot(_P(X(n), y1), 0.04, ACC) for n in primes])
    sd = VGroup(*[_dot(_P(X(n), y2), 0.04, RED_ if not _isprime(n) else WHITE_) for n in sums])
    miss = VGroup(*[Circle(radius=0.048, stroke_color=RED_, stroke_width=1.8).move_to(_P(X(n), y2))
                    for n in primes if n not in sums])
    ls = _m(r"A{+}B", 24, GREY_).move_to(_P(x0 - 0.42, y2))
    lp = _m(r"\mathbb{P}", 26, GREY_).move_to(_P(x0 - 0.36, y1)).align_to(ls, RIGHT)
    return VGroup(lines, pd, sd, miss, lp, ls)


def icon_gaps():
    """Consecutive primes 1289..1471 as arcs over the number line, arc size ~ gap;
    gaps above 1.5 log p (dashed) in accent (incl. the famous gap 1327 -> 1361)."""
    ps = [n for n in range(1289, 1472) if _isprime(n)]
    sx, sy, x0, y0 = 2.7 / (ps[-1] - ps[0]), 0.021, -1.35, -0.3
    X = lambda n: x0 + (n - ps[0]) * sx
    thr = 1.5 * math.log((ps[0] + ps[-1]) / 2)
    arcs = VGroup()
    for a, b in zip(ps, ps[1:]):
        big = (b - a) > thr
        arc = Arc(radius=1, start_angle=0, angle=PI, stroke_color=ACC if big else GREY_,
                  stroke_width=SW if big else 1.3, stroke_opacity=1 if big else 0.8)
        arc.stretch_to_fit_width((b - a) * sx).stretch_to_fit_height((b - a) * sy)
        arc.move_to(_P((X(a) + X(b)) / 2, y0 + (b - a) * sy / 2))
        arcs.add(arc)
    base = Line(_P(x0 - 0.04, y0), _P(X(ps[-1]) + 0.04, y0), stroke_color=GREY_, stroke_width=SW_T)
    th = DashedLine(_P(x0 - 0.04, y0 + thr * sy), _P(X(ps[-1]) + 0.04, y0 + thr * sy),
                    dash_length=0.05, dashed_ratio=0.5, stroke_width=1.3, color=WHITE_,
                    stroke_opacity=0.7)
    return VGroup(base, arcs, th)


def icon_chowla():
    """Liouville lambda(n) (+1 accent, -1 grey) and its shift lambda(n+1);
    the running sum of lambda(n)lambda(n+1) wanders near 0."""
    N, cw, gap = 24, 0.084, 0.02
    lam = [_liouville(n) for n in range(1, N + 2)]
    x0 = -0.92
    rows = VGroup()
    for k, yy in ((0, 0.36), (1, 0.1)):
        pos = VMobject(stroke_width=0, fill_color=ACC, fill_opacity=0.9)
        neg = VMobject(stroke_width=0, fill_color=GREY_, fill_opacity=0.35)
        for i in range(N):
            (pos if lam[i + k] > 0 else neg).append_vectorized_mobject(
                Rectangle(width=cw, height=0.17).move_to(_P(x0 + i * (cw + gap), yy)))
        rows.add(VGroup(neg, pos))
    l1 = _m(r"\lambda(n)", 20, GREY_).next_to(rows[0], LEFT, buff=0.1)
    l2 = _m(r"\lambda(n{+}1)", 20, GREY_).next_to(rows[1], LEFT, buff=0.1)
    run, s = [], 0
    for i in range(N):
        s += lam[i] * lam[i + 1]
        run.append(s)
    yz, sy = -0.3, 0.075
    walk = VMobject(stroke_color=WHITE_, stroke_width=1.8).set_points_as_corners(
        [_P(x0 - cw / 2, yz)] + [_P(x0 + i * (cw + gap) + cw / 2, yz + v * sy) for i, v in enumerate(run)])
    zero = DashedLine(_P(x0 - cw / 2, yz), _P(x0 + N * (cw + gap), yz), dash_length=0.05,
                      stroke_width=1.2, color=GREY_)
    lz = _m(r"\Sigma", 20, GREY_).next_to(zero, LEFT, buff=0.1).align_to(l2, RIGHT)
    return VGroup(rows, l1, l2, zero, walk, lz)


def icon_dd():
    """Free Lie algebra: one generator sigma_3, sigma_5, ... in each odd weight
    (accent dots) and iterated brackets [.,.] built from them (hollow nodes)."""
    dx, dy, y0 = 0.44, 0.34, -0.3
    levels = []
    for lv in range(3):
        n = 5 - lv
        levels.append([_P((i - (n - 1) / 2) * dx, y0 + lv * dy) for i in range(n)])
    edges = [(levels[lv][i], levels[lv + 1][i]) for lv in range(2) for i in range(len(levels[lv + 1]))]
    edges += [(levels[lv][i + 1], levels[lv + 1][i]) for lv in range(2) for i in range(len(levels[lv + 1]))]
    eg = _segments(edges, GREY_, 1.3, op=0.7)
    br = VGroup(*[Circle(radius=0.048, stroke_color=WHITE_, stroke_width=1.6, fill_color=CARD,
                         fill_opacity=1).move_to(p) for lv in (1, 2) for p in levels[lv]])
    gd = VGroup(*[_dot(p, 0.058) for p in levels[0]])
    labs = VGroup(*[_m(r"\sigma_{%d}" % w, 20, WHITE_).next_to(p, DOWN, buff=0.08)
                    for w, p in zip((3, 5, 7, 9, 11), levels[0])])
    more = _m(r"\cdots", 26, GREY_).next_to(gd, RIGHT, buff=0.16)
    return VGroup(eg, br, gd, labs, more)


# ================================================================== FEATURES
BIG_W, BIG_H = 5.2, 4.4


def _frame():
    return Rectangle(width=BIG_W, height=BIG_H, stroke_width=0, stroke_opacity=0, fill_opacity=0)


def _seal(g):
    g._w0, g._c0 = g.width, g.get_center().copy()
    return g


def _late(mob, *parts, z=62):
    """Map parts built in the big visual's build coordinates onto where the big
    visual is now (it was scaled/moved onto the card)."""
    s = mob.width / mob._w0
    c = mob.get_center()
    for p in parts:
        p.scale(s, about_point=mob._c0)
        p.shift(c - mob._c0)
        p.set_z_index(z)
    return parts


def _adopt(scene, mob, *parts):
    """Hand top-level helper mobjects to the card so they collapse with it."""
    if mob not in scene.get_mobject_family_members():
        print("[c1_grid] WARNING: big card was dissolved; late parts stay top-level")
        return
    scene.remove(*parts)
    mob.add(*parts)


def _beats(scene, num):
    """u in [0, 1] along the feature's narration line (cue f<num> -> f<num>_end) ->
    absolute time, clamped to just before the grid template collapses the card
    (it starts at f<num>_end - 0.45).  The beats below were read off the voice
    track as fractions of the line, so they follow the words if it is re-timed."""
    c0, c1 = scene.cue(f"f{num}"), scene.cue(f"f{num}_end")
    stop = c1 - 0.5
    return (lambda u: min(c0 + u * (c1 - c0), stop)), stop


def _go(scene, t0, t1, *anims, filler=None, min_rt=0.2):
    """Start at t0 (or now, if later), end at t1.  `filler(dt)` returns an animation
    that keeps something moving while we wait for t0."""
    gap = t0 - scene.now
    if gap > 0.07:
        if filler is not None:
            scene.play(filler(gap), run_time=gap)
        else:
            scene.wait(gap)
    rt = max(min_rt, t1 - scene.now)
    extra = [filler(rt)] if filler is not None else []
    scene.play(*anims, *extra, run_time=rt)


# ---------------------------------------------------------------- 005 Catalan
def big_catalan():
    g = VGroup(_frame())
    f = MathTex("G", "=", "1", r"-\frac{1}{9}", r"+\frac{1}{25}", r"-\frac{1}{49}", r"+\cdots",
                font_size=42, color=WHITE_).move_to(UP * 1.74)
    ax = Axes(x_range=[0, 12.6, 1], y_range=[0.875, 1.0125, 0.025], x_length=4.25, y_length=2.45,
              tips=False, axis_config=dict(color=GREY_, stroke_width=1.6, include_ticks=False))
    ax.move_to(_P(-0.22, -0.12))
    gline = DashedLine(ax.c2p(0, G_CAT), ax.c2p(12.6, G_CAT), dash_length=0.1, dashed_ratio=0.55,
                       stroke_width=2, color=GREY_)
    gl = _m("G", 36).next_to(gline, RIGHT, buff=0.12)
    one = _m("1", 28, GREY_).next_to(ax.c2p(0, 1), LEFT, buff=0.12)
    tick = Line(ax.c2p(0, 1) + LEFT * 0.06, ax.c2p(0, 1) + RIGHT * 0.06, stroke_color=GREY_, stroke_width=1.6)
    g.add(f, ax, gline, gl, one, tick)
    g._gl, g._G = gl, f[0]
    S = _catalan_sums(13)
    g._pts = [ax.c2p(i, s) for i, s in enumerate(S)]
    g._terms = [f[2], f[3], f[4], f[5], f[6]]
    approx = _m(r"G = 0.9159655\ldots", 36)
    res = _m(r"G \notin \mathbb{Q}", 42, YELLOW_)
    row = VGroup(approx, res).arrange(RIGHT, buff=0.55).move_to(DOWN * 1.92)
    g._row = row
    return _seal(g)


def animate_catalan(scene, mob, rt):
    T, _ = _beats(scene, "005")
    pts = mob._pts
    dots = [_dot(p, 0.055) for p in pts]
    segs = [Line(pts[i - 1], pts[i], stroke_color=ACC, stroke_width=3) for i in range(1, len(pts))]
    approx, res = mob._row[0].copy(), mob._row[1].copy()
    _late(mob, *segs, *dots, approx, res)
    for d in dots:
        d.set_z_index(63)
    terms = mob._terms
    # "Catalan's constant": the G of the formula and the level it converges to
    _go(scene, T(0.07), T(0.21), Indicate(mob._G, color=ACC, scale_factor=1.25),
        Indicate(mob._gl, color=ACC, scale_factor=1.25))
    # "one, minus a ninth, plus a twenty-fifth, minus a forty-ninth": each term lights
    # up as it is spoken and adds its point to the partial-sum zig-zag
    for i, (u0, u1) in enumerate(((0.285, 0.335), (0.345, 0.42), (0.47, 0.55), (0.60, 0.67))):
        a = [FadeIn(dots[i], scale=0.3), terms[i].animate.set_color(ACC)]
        if i:
            a.append(Create(segs[i - 1]))
        _go(scene, T(u0), T(u1), *a)
    # "and so on": the rest of the partial sums home in on G as its decimals appear.
    # group=mob: a fresh Group holding card children would be added to the scene and
    # dissolve the card (Scene.add extracts families).
    rest = [AnimationGroup(Create(segs[i - 1]), FadeIn(dots[i], scale=0.3), group=mob)
            for i in range(4, len(pts))]
    _go(scene, T(0.68), T(0.79), terms[4].animate.set_color(ACC),
        LaggedStart(*rest, lag_ratio=0.55, group=mob), Write(approx))
    # "is irrational" (lands with the first syllable, so it holds before the collapse)
    _go(scene, T(0.80), T(0.86), FadeIn(res, scale=1.25),
        Indicate(mob._gl, color=YELLOW_, scale_factor=1.3))
    _adopt(scene, mob, *segs, *dots, approx, res)


# ---------------------------------------------------------------- 004 Hilbert 10
def big_h10():
    g = VGroup(_frame())
    eqs = VGroup()
    for s in (r"x^2+y^2=3", r"y^2=x^3-2", r"\cdots"):
        t = _m(s, 32)
        pill = RoundedRectangle(width=t.width + 0.34, height=0.56, corner_radius=0.14,
                                stroke_color=GREY_, stroke_width=1.4, fill_color=BG, fill_opacity=0.6)
        eqs.add(VGroup(pill, t.move_to(pill)))
    eqs.arrange(RIGHT, buff=0.22).move_to(UP * 1.8)
    # "ONE algorithm": the claim is that no single procedure handles every equation
    # (individual equations can of course be settled).
    box = RoundedRectangle(width=4.2, height=1.2, corner_radius=0.16, stroke_color=ACC, stroke_width=3,
                           fill_color=ACC, fill_opacity=0.08).move_to(UP * 0.28)
    gear = _gear(0.26, 9, 0.08, ACC, 2.2).move_to(box.get_left() + RIGHT * 0.62)
    lab = bold("ONE ALGORITHM", 24, WHITE_)
    lab.move_to(box).set_x((gear.get_right()[0] + box.get_right()[0]) / 2)
    ins = VGroup(*[_arrow(e.get_bottom() + DOWN * 0.06, box.get_top() + RIGHT * 0.6 * (i - 1) + UP * 0.04,
                          width=2, tip=0.12) for i, e in enumerate(eqs)])
    yes = chip("YES", GREEN_, size=20, fill_opacity=0.12).move_to(_P(-1.05, -1.42))
    no = chip("NO", RED_, size=20, fill_opacity=0.12).move_to(_P(1.05, -1.42))
    outs = VGroup(_arrow(box.get_bottom() + DOWN * 0.04 + LEFT * 0.35, yes.get_top() + UP * 0.08, width=2, tip=0.12),
                  _arrow(box.get_bottom() + DOWN * 0.04 + RIGHT * 0.35, no.get_top() + UP * 0.08, width=2, tip=0.12))
    ask = txt("rational solution?", 22, GREY_).move_to(DOWN * 2.0)
    g.add(eqs, ins, box, gear, lab, outs, yes, no, ask)
    g._eqs, g._box, g._gear, g._lab, g._outs = eqs, box, gear, lab, outs
    g._ins, g._ask = ins, ask
    q = _m("?", 64, YELLOW_).move_to(_P(0, -1.42))
    cross = VGroup(Line(box.get_corner(UL) + _P(0.25, -0.12), box.get_corner(DR) + _P(-0.25, 0.12)),
                   Line(box.get_corner(DL) + _P(0.25, 0.12), box.get_corner(UR) + _P(-0.25, -0.12)))
    cross.set_stroke(RED_, width=6)
    g._q, g._cross = q, cross
    return _seal(g)


def _flashes(mobs, color, width=4, lag=0.0):
    """ShowPassingFlash along copies of `mobs` (top-level helpers, removed afterwards)."""
    cps = [m.copy().set_stroke(color, width=width).set_z_index(63) for m in mobs]
    fl = [ShowPassingFlash(c, time_width=0.6) for c in cps]
    return LaggedStart(*fl, lag_ratio=lag, group=VGroup(*cps)) if lag else AnimationGroup(*fl, group=VGroup(*cps))


def animate_h10(scene, mob, rt):
    T, stop = _beats(scene, "004")
    box, gear, lab, eqs = mob._box, mob._gear, mob._lab, mob._eqs
    q, cross = mob._q.copy(), mob._cross.copy()
    _late(mob, q, cross)
    # the gear never stops turning: a search can run forever without settling anything
    spin = lambda dt: Rotate(gear, angle=-0.4 * PI * dt, about_point=gear.get_center(), rate_func=linear)
    go = lambda u0, u1, *a: _go(scene, T(u0), T(u1), *a, filler=spin)
    # group=mob on Lagged/AnimationGroups of card parts (else the card dissolves)
    # "Hilbert's tenth problem, for fractions": equations are fed to one algorithm
    go(0.06, 0.24, LaggedStart(*[e[1].animate(rate_func=there_and_back).set_color(ACC) for e in eqs],
                               lag_ratio=0.35, group=mob),
       _flashes(mob._ins, ACC, lag=0.35))
    # "no single algorithm": struck out
    go(0.295, 0.375, Create(cross, lag_ratio=0.4), box.animate.set_stroke(RED_),
       lab.animate.set_opacity(0.45))
    # "can tell": it cannot commit to YES or NO
    go(0.385, 0.47, _flashes(mob._outs, YELLOW_), FadeIn(q, scale=0.4))
    # "for every whole-number polynomial equation": all of them, the '...' included
    go(0.51, 0.70, LaggedStart(*[AnimationGroup(e[0].animate.set_stroke(ACC, width=2.2),
                                                e[1].animate.set_color(ACC), group=e) for e in eqs],
                               lag_ratio=0.5, group=mob))
    # "whether it has a solution in fractions"
    go(0.80, 0.90, Indicate(mob._ask, color=YELLOW_, scale_factor=1.12),
       Indicate(q, color=YELLOW_, scale_factor=1.25))
    if stop - scene.now > 0.1:
        scene.play(spin(stop - scene.now), run_time=stop - scene.now)
    _adopt(scene, mob, q, cross)


# ================================================================== SCENE
def _padded(fn, kx=1.02):
    """Small invisible side margins: with the grid's 1.06x 'lit' pulse, an icon that
    fills the tile's full width still stays well inside the tile frame (the tile
    already keeps a 0.13 inner pad)."""
    def make():
        ic = fn()
        pad = Rectangle(width=ic.width * kx, height=ic.height, stroke_width=0, fill_opacity=0)
        return VGroup(pad.move_to(ic), ic)
    make.__name__ = fn.__name__
    return make


ICONS = {k: _padded(f) for k, f in {
    "005": icon_catalan, "004": icon_h10, "002": icon_bsd, "006": icon_goldfeld,
    "030": icon_modularity, "025": icon_egyptian, "028": icon_moat, "029": icon_artin,
    "013": icon_ostmann, "026": icon_gaps, "007": icon_chowla, "008": icon_dd,
}.items()}
FEATURES = {
    "005": dict(big=big_catalan, animate=animate_catalan),
    "004": dict(big=big_h10, animate=animate_h10),
}


# Scene-level caption overrides.  004: the claim is that no SINGLE algorithm handles
# every equation (specific equations can be settled); "no algorithm decides whether
# a polynomial equation has ..." reads like the flagged overclaim.
CAPTIONS = {
    "004": "No single algorithm decides, for every polynomial equation, whether it has a rational solution.",
}


def _tiles():
    spec = json.loads((VIDEO / "data" / "grids.json").read_text())["c1_grid"]
    out = []
    for d in spec:
        t = dict(num=d["num"], name=d["name"], verdict=d["verdict"], icon=ICONS[d["num"]])
        if d.get("caption"):
            t["feature"] = dict(caption=CAPTIONS.get(d["num"], d["caption"]), **FEATURES.get(d["num"], {}))
        out.append(t)
    return out


class C1Grid(GridScene):
    CHAPTER = "nt"
    TILES = _tiles()
