import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
from lib.grid import GridScene

# Rapid-fire grid: Algebraic & Complex Geometry.
# Every icon is a small vector diagram: accent PURPLE_ for the "object", WHITE_/GREY_ for
# ambient structure, RED_ only on the three counterexample tiles.

ACC = PURPLE_
D_EXT = np.array([1.0, 0.55, 0.0]) / np.linalg.norm([1.0, 0.55])   # oblique "depth" direction
BIG_W, BIG_H = 5.2, 4.4                                              # big-card visual box


# ============================================================== shared drawing helpers
def _closed_smooth(pts, **kw):
    m = VMobject(**kw)
    pts = [np.array(p, dtype=float) for p in pts]
    m.set_points_smoothly([*pts, pts[0]])
    return m


def _poly(pts, **kw):
    m = VMobject(**kw)
    pts = [np.array(p, dtype=float) for p in pts]
    m.set_points_as_corners([*pts, pts[0]])
    return m


def _resample_closed(pts, N=96):
    """Closed polyline -> N points equally spaced by arclength, counter-clockwise, starting at
    the bottom-left-most point (so two outlines morph point-to-point without crumpling)."""
    P = np.array([np.array(p, float) for p in pts])
    if np.allclose(P[0], P[-1]):
        P = P[:-1]
    area = np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area < 0:
        P = P[::-1]
    i0 = int(np.argmin(P[:, 0] + P[:, 1]))
    P = np.roll(P, -i0, axis=0)
    Q = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    out = []
    for t in np.linspace(0, cum[-1], N, endpoint=False):
        j = min(int(np.searchsorted(cum, t, side="right")) - 1, len(seg) - 1)
        u = (t - cum[j]) / max(seg[j], 1e-9)
        out.append(Q[j] * (1 - u) + Q[j + 1] * u)
    return [*out, out[0]]


def _blob_pts(r=0.5, n=64):
    """A lumpy closed 'shape X' (deliberately not a disc or a square)."""
    th = np.linspace(0, TAU, n, endpoint=False)
    rr = 1 + 0.12 * np.sin(2 * th + 0.6) + 0.08 * np.cos(3 * th - 0.3) + 0.045 * np.sin(5 * th + 1.1)
    return np.stack([1.08 * r * rr * np.cos(th), 0.94 * r * rr * np.sin(th), 0 * th], axis=1)


def _blob(r=0.5, width=2.4, fo=0.26, pts=None):
    P = _blob_pts(r) if pts is None else pts
    return _closed_smooth(P, stroke_color=ACC, stroke_width=width, fill_color=ACC, fill_opacity=fo)


def _cyl_arcs(P, d=D_EXT):
    """Split a closed outline at its two extreme points across direction d.
    Returns (F, G): index runs of the arc facing away from d (front outer side)
    and the complementary arc (which, translated by L*d, is the back outer side)."""
    nrm = np.array([-d[1], d[0], 0.0])
    proj = P @ nrm
    imax, imin = int(np.argmax(proj)), int(np.argmin(proj))
    N = len(P)

    def run(i, j):
        idx = [i]
        while idx[-1] != j:
            idx.append((idx[-1] + 1) % N)
        return idx

    A, B = run(imax, imin), run(imin, imax)
    mid = lambda I: P[I[len(I) // 2]] @ d
    return (A, B) if mid(A) < mid(B) else (B, A)


def _sweep_pts(P, F, G, L, d=D_EXT):
    """Outline of the region swept by outline P translated along d by length L."""
    pts = np.vstack([P[F], P[G] + L * d])
    return [*pts, pts[0]]


def _cylinder(r=0.5, L=0.6, width=2.2, axis=True):
    """'X x line': the blob X extruded along a line (oblique view)."""
    P = _blob_pts(r)
    F, G = _cyl_arcs(P)
    body = VMobject(stroke_color=ACC, stroke_width=width, fill_color=ACC, fill_opacity=0.14)
    body.set_points_as_corners(_sweep_pts(P, F, G, L))
    back = _closed_smooth(P + L * D_EXT, stroke_color=ACC, stroke_width=width * 0.7,
                          stroke_opacity=0.45, fill_opacity=0)
    front = _blob(pts=P, width=width, fo=0.3)
    g = VGroup()
    if axis:
        g.add(Line(-1.45 * r * D_EXT, (L + 1.5 * r) * D_EXT, stroke_color=GREY_, stroke_width=width * 0.6))
    g.add(body, back, front)
    return g


def _grid_cube(s=1.0, depth=0.5, n=3, width=2.0):
    """'Ordinary space': a cube ruled by a coordinate grid."""
    o = D_EXT * depth
    h = s / 2
    BL, BR, TR, TL = (np.array([-h, -h, 0]), np.array([h, -h, 0]),
                      np.array([h, h, 0]), np.array([-h, h, 0]))
    hull = _poly([BL, BR, BR + o, TR + o, TL + o, TL], stroke_color=WHITE_, stroke_width=width,
                 fill_color=WHITE_, fill_opacity=0.05)
    tint = _poly([TL, TR, TR + o, TL + o], stroke_width=0, fill_color=WHITE_, fill_opacity=0.07)
    inner = VGroup(Line(TL, TR), Line(TR, BR), Line(TR, TR + o)).set_stroke(WHITE_, width)
    grid = VGroup()
    for i in range(1, n):
        f = i / n
        grid.add(Line(BL + RIGHT * s * f, TL + RIGHT * s * f), Line(BL + UP * s * f, BR + UP * s * f),
                 Line(TL + RIGHT * s * f, TL + RIGHT * s * f + o), Line(TL + o * f, TR + o * f),
                 Line(BR + UP * s * f, BR + UP * s * f + o), Line(BR + o * f, TR + o * f))
    grid.set_stroke(GREY_, width * 0.55, opacity=0.8)
    g = VGroup(hull, tint, grid, inner)
    g.move_to(ORIGIN)
    g.hull, g.tint, g.grid, g.inner = hull, tint, grid, inner
    return g


def _grid_square(s=1.0, n=4, width=2.0):
    sq = Square(s, stroke_color=WHITE_, stroke_width=width, fill_color=WHITE_, fill_opacity=0.05)
    grid = VGroup()
    for i in range(1, n):
        f = -s / 2 + s * i / n
        grid.add(Line([f, -s / 2, 0], [f, s / 2, 0]), Line([-s / 2, f, 0], [s / 2, f, 0]))
    grid.set_stroke(GREY_, width * 0.55, opacity=0.8)
    return VGroup(sq, grid)


def _torus_hole(cx=0.0, cy=0.0, w=1.0, color=WHITE_, width=2.0):
    """The classic smile + frown for the hole of a drawn torus."""
    smile = ArcBetweenPoints([cx - w / 2, cy + 0.06 * w, 0], [cx + w / 2, cy + 0.06 * w, 0], angle=1.4)
    # frown endpoints sit on the smile
    sm_R = (w / 2) / np.sin(0.7)
    sm_c = np.array([cx, cy + 0.06 * w + sm_R * np.cos(0.7), 0])
    fx = 0.36 * w
    fy = sm_c[1] - np.sqrt(sm_R ** 2 - fx ** 2)
    frown = ArcBetweenPoints([cx - fx, fy, 0], [cx + fx, fy, 0], angle=-1.2)
    return VGroup(smile, frown).set_stroke(color, width)


# ============================================================== icons
def icon_047():
    """Zariski cancellation: (X x line) = 5-space (cube), yet X != 4-space (square)."""
    cyl = _cylinder(r=0.3, L=0.42, width=2.0, axis=False)
    cong = tex(r"\cong", 42, GREY_)
    cube = _grid_cube(0.56, 0.3, n=3, width=1.8)
    blob = _blob(0.29, width=2.0)
    ncong = tex(r"\ncong", 42, RED_)
    sq = _grid_square(0.56, n=3, width=1.8)
    left = VGroup(cyl, cong, cube).arrange(RIGHT, buff=0.08)
    right = VGroup(blob, ncong, sq).arrange(RIGHT, buff=0.08)
    return VGroup(left, right).arrange(RIGHT, buff=0.3)


def icon_039():
    """Nagata: a sextic curve y^2=(1-x^2)(4x^2-1)^2 (sheared) forced through 10 points,
    two of them double points (the nodes)."""
    M = np.array([[1.0, 0.16], [0.06, 1.0]])

    def f(t):
        x, y = 1.2 * np.cos(t), 0.4 * np.sin(3 * t)
        return np.array([M[0, 0] * x + M[0, 1] * y, M[1, 0] * x + M[1, 1] * y, 0.0])

    ts = np.linspace(0, TAU, 181)[:-1]
    curve = _closed_smooth([f(t) for t in ts], stroke_color=ACC, stroke_width=2.6)
    nodes = [PI / 3, 2 * PI / 3]
    simple = [0.15, 0.75, 1.45, 2.5, 3.3, 3.95, 4.6, 5.6]
    params = sorted(nodes + simple)
    dots = VGroup(*[
        Dot(f(t), radius=0.062 if t in nodes else 0.046, color=WHITE_) for t in params])
    return VGroup(curve, dots)


def icon_038():
    """Fujita freeness: sections of K_X+mL over X with no common zero (globally generated)."""
    by, X0, X1 = -0.1, -1.25, 1.25
    base = Line([X0, by, 0], [X1, by, 0], stroke_color=WHITE_, stroke_width=2.2)
    g = VGroup(base)
    zeros = VGroup()
    for a, k, ph, col, op in [(0.36, 2.3, 0.4, ACC, 1.0), (0.3, 1.7, 2.1, WHITE_, 0.75),
                              (0.25, 3.1, -1.0, GREY_, 1.0)]:
        xs = np.linspace(X0, X1, 60)
        c = VMobject(stroke_color=col, stroke_width=2.2, stroke_opacity=op)
        c.set_points_smoothly([[x, by + a * np.sin(k * x + ph), 0] for x in xs])
        g.add(c)
        for m in range(-3, 4):
            z = (m * PI - ph) / k
            if X0 + 0.08 < z < X1 - 0.08:
                zeros.add(Dot([z, by, 0], radius=0.045, color=col).set_opacity(op))
    lab = tex(r"K_X+mL", 22, GREY_).move_to([X1 - 0.3, 0.5, 0])
    g.add(zeros, lab)
    return g


def _patch(corners, bulges, n=14):
    pts = []
    for i in range(4):
        a, b = np.array(corners[i], float), np.array(corners[(i + 1) % 4], float)
        d = b - a
        nrm = np.array([d[1], -d[0], 0]) / np.linalg.norm(d)
        for s in np.linspace(0, 1, n, endpoint=False):
            pts.append(a + s * d + bulges[i] * np.sin(PI * s) * nrm)
    return pts


def _plus(p, s=0.06, color=WHITE_):
    p = np.array(p, float)
    return VGroup(Line(p + LEFT * s, p + RIGHT * s), Line(p + DOWN * s, p + UP * s)).set_stroke(color, 1.8)


def _minus(p, s=0.06, color=WHITE_):
    p = np.array(p, float)
    return Line(p + LEFT * s, p + RIGHT * s).set_stroke(color, 1.8)


def icon_040():
    """Bloch: degree-0 zero-cycles on a surface S (p_g=0) map isomorphically to Alb(S)."""
    C = [(-1.3, -0.38, 0), (-0.28, -0.48, 0), (-0.1, 0.36, 0), (-1.12, 0.46, 0)]
    surf = _poly(_patch(C, [0.06, -0.08, 0.07, -0.06]), stroke_color=ACC, stroke_width=2.2,
                 fill_color=ACC, fill_opacity=0.16)
    fib = VGroup(
        VMobject().set_points_smoothly([[-1.21, -0.43, 0], [-0.98, 0.0, 0], [-0.62, 0.42, 0]]),
        VMobject().set_points_smoothly([[-0.79, -0.44, 0], [-0.55, -0.02, 0], [-0.2, 0.32, 0]]),
        VMobject().set_points_smoothly([[-1.2, 0.04, 0], [-0.7, -0.04, 0], [-0.19, -0.06, 0]]),
    ).set_stroke(ACC, 1.1, opacity=0.5)
    pts = VGroup()
    for p, sgn in [((-0.98, 0.2), 1), ((-0.42, 0.13), 1), ((-0.8, -0.24), -1), ((-0.38, -0.27), -1)]:
        q = np.array([p[0], p[1], 0])
        if sgn > 0:
            pts.add(Dot(q, radius=0.05, color=WHITE_), _plus(q + np.array([0.12, 0.09, 0])))
        else:
            pts.add(Circle(0.045, stroke_color=WHITE_, stroke_width=1.8).move_to(q),
                    _minus(q + np.array([0.12, 0.09, 0])))
    arrow = Arrow([0.0, 0, 0], [0.5, 0, 0], buff=0, stroke_width=2.2, color=GREY_,
                  max_tip_length_to_length_ratio=0.3, tip_length=0.13)
    iso = tex(r"\cong", 28, GREY_).next_to(arrow, UP, buff=0.04)
    torus = Ellipse(width=1.0, height=0.58, stroke_color=WHITE_, stroke_width=2.0,
                    fill_color=WHITE_, fill_opacity=0.05).move_to([1.12, 0, 0])
    hole = _torus_hole(1.12, -0.02, 0.44, WHITE_, 1.8)
    return VGroup(surf, fib, pts, arrow, iso, torus, hole)


def icon_050():
    """Griffiths: on the doubly ruled quadric P1 x P1, an ample bundle with no metric of
    Griffiths-positive curvature."""
    a, hz, tilt = 0.36, 0.48, 0.2

    def P(x, y, z):
        return np.array([x, hz * z + tilt * y, 0.0])

    fam1, fam2 = VGroup(), VGroup()
    for k in range(12):
        u = k * TAU / 12
        for s, grp in ((1, fam1), (-1, fam2)):
            e = [P(a * (np.cos(u) - s * v * np.sin(u)), a * (np.sin(u) + s * v * np.cos(u)), v)
                 for v in (-1, 1)]
            grp.add(Line(*e))
    fam1.set_stroke(ACC, 1.5, opacity=0.95)
    fam2.set_stroke(WHITE_, 1.2, opacity=0.45)
    rr = a * np.sqrt(2)
    rims = VGroup(*[Ellipse(width=2 * rr, height=2 * tilt * rr).move_to([0, sz * hz, 0])
                    for sz in (1, -1)]).set_stroke(WHITE_, 1.8)
    quad = VGroup(fam2, fam1, rims)
    theta = tex(r"\Theta_h>0", 40, RED_)
    strike = Line(theta.get_left() + LEFT * 0.08 + DOWN * 0.1, theta.get_right() + RIGHT * 0.08 + UP * 0.1,
                  stroke_color=RED_, stroke_width=2.6)
    neg = VGroup(theta, strike)
    return VGroup(quad, neg).arrange(RIGHT, buff=0.36)


def _cassini(scale_x=0.48, scale_y=0.5, a=1.0, b=1.08, n=120):
    pts = []
    for th in np.linspace(0, TAU, n, endpoint=False):
        r2 = a * a * np.cos(2 * th) + np.sqrt(b ** 4 - a ** 4 * np.sin(2 * th) ** 2)
        r = np.sqrt(max(r2, 0))
        pts.append([scale_x * r * np.cos(th), scale_y * r * np.sin(th), 0])
    return pts


def icon_051():
    """Kobayashi: no non-constant entire curve C -> X (X hyperbolic, genus>=2-like)."""
    o = np.array([0.22, 0.66, 0])
    BL = np.array([-0.4, -0.33, 0])
    ex = np.array([0.6, 0, 0])
    plane = VGroup(_poly([BL, BL + ex, BL + ex + o, BL + o], stroke_color=WHITE_, stroke_width=1.8,
                         fill_color=WHITE_, fill_opacity=0.05))
    gl = VGroup()
    for i in range(1, 4):
        f = i / 4
        gl.add(Line(BL + ex * f, BL + ex * f + o), Line(BL + o * f, BL + o * f + ex))
    plane.add(gl.set_stroke(GREY_, 1.0, opacity=0.8))
    plane.move_to([-1.15, 0, 0])
    arrow = Arrow([-0.68, 0, 0], [-0.18, 0, 0], buff=0, stroke_width=2.2, color=GREY_,
                  max_tip_length_to_length_ratio=0.3, tip_length=0.13)
    slash = Line([-0.51, -0.14, 0], [-0.35, 0.14, 0], stroke_color=WHITE_, stroke_width=2.4)
    surf = _closed_smooth(_cassini(scale_y=0.66), stroke_color=ACC, stroke_width=2.2, fill_color=ACC,
                          fill_opacity=0.18).move_to([0.78, 0, 0])
    holes = VGroup(_torus_hole(0.78 - 0.33, -0.02, 0.27, ACC, 1.8),
                   _torus_hole(0.78 + 0.33, -0.02, 0.27, ACC, 1.8))
    return VGroup(plane, arrow, slash, surf, holes)


def _globe(R=0.44, lump=0.0, outline=WHITE_, lat=WHITE_, mer=ACC, n=48):
    """Sphere with latitude/longitude lines; lump > 0 dents it radially (all curves alike)."""
    def bend(pts):
        out = []
        for p in pts:
            th = np.arctan2(p[1], p[0])
            f = 1 + lump * (0.6 * np.sin(3 * th + 0.5) + 0.4 * np.cos(2 * th - 0.3))
            out.append(np.array([p[0] * f, p[1] * f, 0.0]))
        return out

    ph = np.linspace(0, TAU, n, endpoint=False)

    def ell(cx, cy, rx, ry):
        return bend([[cx + rx * np.cos(t), cy + ry * np.sin(t), 0] for t in ph])

    g = VGroup(_closed_smooth(ell(0, 0, R, R), stroke_color=outline, stroke_width=2.0,
                              fill_color=outline, fill_opacity=0.05))
    for yy in (-0.5 * R, 0.0, 0.5 * R):
        rx = np.sqrt(R * R - yy * yy)
        g.add(_closed_smooth(ell(0, yy, rx, 0.24 * rx), stroke_color=lat, stroke_width=1.1,
                             stroke_opacity=0.55))
    for ww in (0.34 * R, 0.7 * R):
        g.add(_closed_smooth(ell(0, 0, ww, R), stroke_color=mer, stroke_width=1.3, stroke_opacity=0.9))
    return g


def icon_062():
    """LeBrun-Salamon: every positive quaternion-Kaehler manifold is a symmetric (Wolf)
    space -- no lumpy ones exist: lumpy => perfectly symmetric."""
    lumpy = _globe(0.44, lump=0.16, outline=GREY_, lat=GREY_, mer=GREY_)
    imp = tex(r"\Rightarrow", 34, GREY_)
    round_ = _globe(0.46)
    return VGroup(lumpy, imp, round_).arrange(RIGHT, buff=0.22)


def icon_063():
    """Generalized Mukai: rho(iota-1) <= n, equality only for (P^{iota-1})^rho; here the
    moment triangles of P^2 x P^2 x P^2."""
    def tri():
        return Polygon([0, 0, 0], [0.48, 0, 0], [0, 0.48, 0], stroke_color=ACC, stroke_width=2.2,
                       fill_color=ACC, fill_opacity=0.22)
    row = VGroup(tri(), tex(r"\times", 30, GREY_), tri(), tex(r"\times", 30, GREY_), tri())
    row.arrange(RIGHT, buff=0.14)
    formula = tex(r"\rho\,(\iota-1)\le n", 28, WHITE_).next_to(row, DOWN, buff=0.16)
    return VGroup(row, formula)


def _germ(hw):
    ball = Circle(0.42, stroke_color=GREY_, stroke_width=1.6, fill_color=WHITE_, fill_opacity=0.03)
    hh = 0.27
    cone = VGroup(Line([-hw, hh, 0], [hw, -hh, 0]), Line([hw, hh, 0], [-hw, -hh, 0])).set_stroke(ACC, 2.0)
    rims = VGroup(*[Ellipse(width=2 * hw, height=0.11).move_to([0, s * hh, 0]) for s in (1, -1)])
    rims.set_stroke(ACC, 1.8).set_fill(ACC, 0.2)
    pt = Dot(ORIGIN, radius=0.04, color=WHITE_)
    return VGroup(ball, cone, rims, pt)


def icon_059():
    """Zariski multiplicity: two hypersurface germs, ambiently homeomorphic (same cone over
    the same link) but with multiplicities 4 and 5."""
    g1, g2 = _germ(0.27), _germ(0.2)
    m4, m5 = tex(r"m=4", 28, RED_), tex(r"m=5", 28, RED_)
    eq = tex(r"\approx", 36, WHITE_)
    return VGroup(m4, g1, eq, g2, m5).arrange(RIGHT, buff=0.08)


def icon_060():
    """Global spherical shell: a class VII surface (drawn as S^1 x S^3) containing a shell
    around S^3 whose complement is connected."""
    tor = Ellipse(width=2.3, height=0.9, stroke_color=WHITE_, stroke_width=2.0,
                  fill_color=WHITE_, fill_opacity=0.04)
    hole = _torus_hole(0, -0.03, 0.95, WHITE_, 1.9)
    x0 = 0.8
    outer = Ellipse(width=0.27, height=0.62).move_to([x0, 0, 0])
    inner = Ellipse(width=0.12, height=0.42).move_to([x0, 0, 0])
    shell = Difference(outer, inner, stroke_color=ACC, stroke_width=1.6, fill_color=ACC, fill_opacity=0.5)
    lab = tex(r"S^3", 26, ACC).move_to([x0 + 0.42, 0.42, 0])
    return VGroup(tor, hole, shell, lab)


def _geodesic(R, a1, a2, n=20):
    """Hyperbolic geodesic in the Poincare disc of radius R between ideal angles a1, a2."""
    half = ((a2 - a1) % TAU) / 2
    mid = a1 + half
    dist, rad = R / np.cos(half), R * np.tan(half)
    C = dist * np.array([np.cos(mid), np.sin(mid), 0])
    p1 = R * np.array([np.cos(a1), np.sin(a1), 0])
    p2 = R * np.array([np.cos(a2), np.sin(a2), 0])
    f1 = np.arctan2(*(p1 - C)[1::-1])
    f2 = np.arctan2(*(p2 - C)[1::-1])
    df = (f2 - f1 + PI) % TAU - PI
    pts = [C + rad * np.array([np.cos(f1 + s * df), np.sin(f1 + s * df), 0]) for s in np.linspace(0, 1, n)]
    return VMobject().set_points_smoothly(pts)


def icon_058():
    """Kollar-Pardon: universal cover = (bounded symmetric domain) x C^m x (simply connected F)."""
    R = 0.42
    disc = VGroup(Circle(R, stroke_color=ACC, stroke_width=2.0, fill_color=ACC, fill_opacity=0.14))
    angs = [PI / 2 + k * TAU / 6 for k in range(6)]
    geo = VGroup(*[_geodesic(R, angs[k], angs[k + 1]) for k in range(5)],
                 _geodesic(R, angs[5], angs[0] + TAU),
                 _geodesic(R, angs[0], angs[2]), _geodesic(R, angs[2], angs[4]),
                 _geodesic(R, angs[4], angs[0] + TAU))
    disc.add(geo.set_stroke(ACC, 1.2, opacity=0.9))
    sq = _grid_square(0.74, n=4, width=1.8)
    sph = VGroup(Circle(0.38, stroke_color=WHITE_, stroke_width=1.9, fill_color=WHITE_, fill_opacity=0.05),
                 Ellipse(width=0.76, height=0.2).set_stroke(GREY_, 1.2))
    t1, t2 = tex(r"\times", 30, GREY_), tex(r"\times", 30, GREY_)
    return VGroup(disc, t1, sq, t2, sph).arrange(RIGHT, buff=0.12)


def icon_057():
    """Campana: special => pi_1 virtually abelian; the commutator loop closes up in Z^2."""
    sp = 0.32
    dots = VGroup(*[Dot([i * sp, j * sp, 0], radius=0.028, color=GREY_)
                    for i in range(6) for j in range(3)])
    p0 = np.array([sp, 0, 0])
    a = np.array([2 * sp, 0, 0])
    b = np.array([sp, 2 * sp, 0])
    kw = dict(buff=0.03, stroke_width=2.4, max_tip_length_to_length_ratio=0.25, tip_length=0.12)
    loop = VGroup(Arrow(p0, p0 + a, color=ACC, **kw), Arrow(p0 + a, p0 + a + b, color=WHITE_, **kw),
                  Arrow(p0 + a + b, p0 + b, color=ACC, **kw), Arrow(p0 + b, p0, color=WHITE_, **kw))
    lat = VGroup(dots, loop)
    form = tex(r"ab=ba", 32, WHITE_)
    return VGroup(lat, form).arrange(RIGHT, buff=0.24)


def _padded(fn, fx=1.1, fy=1.02):
    """Invisible margin around an icon, so the tile's 'lit' pulse (scale 1.12) never pushes a
    full-width icon past the tile frame."""
    def make():
        g = fn()
        box = Rectangle(width=g.width * fx, height=g.height * fy, stroke_opacity=0,
                        fill_opacity=0).move_to(g)
        return VGroup(box, g)
    return make


# ============================================================== featured: 047 big card
def big_047():
    """Left half of the 047 card. Initially only the shape X; animate_047 extrudes it."""
    frame = Rectangle(width=BIG_W, height=BIG_H, stroke_opacity=0, fill_opacity=0)
    r, L = 0.55, 1.0
    P0 = _blob_pts(r)
    F, G = _cyl_arcs(P0)
    full = np.array(_sweep_pts(P0, F, G, L))
    bb_c = (full.min(axis=0) + full.max(axis=0)) / 2
    c_f = np.array([-1.3, 1.08, 0]) - bb_c
    P = P0 + c_f
    body = VMobject(stroke_color=ACC, stroke_width=2.6, fill_color=ACC, fill_opacity=0.14)
    body.set_points_as_corners(_sweep_pts(P, F, G, 0.0))
    back = _closed_smooth(P, stroke_color=ACC, stroke_width=1.8, stroke_opacity=0.5, fill_opacity=0)
    front = _blob(pts=P, width=2.8, fo=0.3)
    lab_x = tex("X", 40, ACC)
    lab_x.move_to([c_f[0], P[:, 1].min() - 0.32, 0])
    vis = VGroup(frame, body, back, front, lab_x)
    vis.frame_rect, vis.body, vis.back, vis.front, vis.lab_x = frame, body, back, front, lab_x
    vis.geo = dict(r=r, L=L, P=P, F=F, G=G, c_f=c_f, cyl_cx=-1.3, lab_y=lab_x.get_y())
    return vis


def animate_047(scene, vis, run_time):
    R = run_time
    k = vis.frame_rect.width / BIG_W
    c = vis.frame_rect.get_center()
    z = vis.front.z_index
    g = vis.geo
    P, F, G, L, r, c_f = g["P"], g["F"], g["G"], g["L"], g["r"], g["c_f"]

    def T(m):   # build coordinates -> on-screen coordinates (vis may have been scaled/moved)
        m.scale(k, about_point=ORIGIN).shift(c)
        m.set_z_index(z)
        return m

    def Tp(pts):
        return [np.array(p) * k + c for p in pts]

    t0 = scene.now
    # ---------------------------------------------------------------- pieces (build coords)
    axis = Arrow(c_f - 1.45 * r * D_EXT, c_f + (L + 1.55 * r) * D_EXT, buff=0, color=GREY_,
                 stroke_width=2.4, tip_length=0.2, max_tip_length_to_length_ratio=0.2)
    lab_line = tex(r"\mathbb{C}", 34, GREY_).next_to(axis.get_end(), UR, buff=0.06)
    lab_xc = MathTex("X", r"\times", r"\mathbb{C}", font_size=40, color=WHITE_)
    lab_xc[0].set_color(ACC)
    lab_xc.move_to([g["cyl_cx"], g["lab_y"], 0])
    full_cyl = VMobject(stroke_color=ACC, stroke_width=2.6, fill_color=ACC, fill_opacity=0.14)
    full_cyl.set_points_as_corners(_resample_closed(_sweep_pts(P, F, G, L)))
    cube = _grid_cube(1.15, 0.55, n=3, width=2.4).move_to([1.62, 1.08, 0])
    cube.hull.set_points_as_corners(_resample_closed(cube.hull.get_anchors()))
    cong = tex(r"\cong", 60, WHITE_).move_to([0.3, 1.08, 0])
    lab_c5 = tex(r"\mathbb{C}^5", 40, WHITE_).move_to([1.62, g["lab_y"], 0])
    blob2 = _blob(pts=P - c_f + np.array([-1.3, -1.2, 0]), width=2.8, fo=0.3)
    lab_x2 = tex("X", 40, ACC).move_to([-1.3, -2.04, 0])
    sq = _grid_square(1.05, n=4, width=2.4).move_to([1.62, -1.2, 0])
    lab_c4 = tex(r"\mathbb{C}^4", 40, WHITE_).move_to([1.62, -2.04, 0])
    rel_q = tex(r"\overset{?}{\cong}", 60, GREY_).move_to([0.3, -1.16, 0])
    rel_no = tex(r"\ncong", 60, RED_).move_to(rel_q)
    for m in (axis, lab_line, lab_xc, full_cyl, cube, cong, lab_c5, blob2, lab_x2, sq, lab_c4,
              rel_q, rel_no):
        T(m)
    times_c = VGroup(lab_xc[1], lab_xc[2])

    def grow(m, a):
        m.set_points_as_corners(Tp(_sweep_pts(P, F, G, a * L)))

    # Parts join `vis` (so they collapse with the card) only right before they animate in.
    # 1) "if a shape, times a line": the line appears and X is swept along it.
    scene.wait(max(0.0, 0.12 * R - (scene.now - t0)))
    vis.add_to_back(axis)          # the line sits under the translucent solid
    vis.add(lab_line, times_c)
    scene.play(AnimationGroup(
        AnimationGroup(Create(axis), FadeIn(lab_line), run_time=0.6),
        AnimationGroup(UpdateFromAlphaFunc(vis.body, grow), vis.back.animate.shift(L * k * D_EXT),
                       Transform(vis.lab_x, lab_xc[0]), FadeIn(times_c, shift=RIGHT * 0.1), run_time=1.3),
        lag_ratio=0.75), run_time=0.19 * R, rate_func=linear)

    # 2) "...is ordinary five-dimensional space. Must the shape be ordinary four-space?"
    scene.wait(max(0.0, 0.32 * R - (scene.now - t0)))
    ghost = vis.front.copy().set_fill(opacity=0).set_stroke(opacity=0)
    vis.add(cube, cong, lab_c5, blob2, lab_x2, sq, lab_c4, rel_q)
    five = AnimationGroup(
        AnimationGroup(TransformFromCopy(full_cyl, cube.hull), FadeIn(lab_c5), run_time=1.0),
        AnimationGroup(Write(cong), Create(cube.grid, lag_ratio=0.1), Create(cube.inner), FadeIn(cube.tint),
                       run_time=0.7),
        lag_ratio=1.0)
    four = AnimationGroup(
        AnimationGroup(TransformFromCopy(ghost, blob2), FadeIn(lab_x2, shift=DOWN * 0.1),
                       FadeIn(sq, shift=DOWN * 0.1), FadeIn(lab_c4, shift=DOWN * 0.1), run_time=1.0),
        Write(rel_q, run_time=0.7), lag_ratio=0.6)
    scene.play(AnimationGroup(five, four, lag_ratio=1.0), run_time=0.38 * R, rate_func=linear)

    # 3) "...the paper's answer is no."
    scene.wait(max(0.0, 0.83 * R - (scene.now - t0)))
    scene.play(Transform(rel_q, rel_no),
               Indicate(blob2, color=RED_, scale_factor=1.06), run_time=0.1 * R)


class C2Grid(GridScene):
    CHAPTER = "ag"
    TILES = [
        dict(num="047", name="Zariski cancellation fails over ℂ", verdict="counterexample", icon=_padded(icon_047),
             feature=dict(caption="X × line ≅ 5-space, yet X is not 4-space.",
                          big=big_047, animate=animate_047)),
        dict(num="039", name="Nagata's conjecture", verdict="proved", icon=_padded(icon_039)),
        dict(num="038", name="Fujita's freeness conjecture", verdict="proved", icon=_padded(icon_038)),
        dict(num="040", name="Bloch's conjecture for surfaces", verdict="proved", icon=_padded(icon_040)),
        dict(num="050", name="Griffiths positivity conjecture", verdict="counterexample", icon=_padded(icon_050)),
        dict(num="051", name="Kobayashi's canonical-ampleness conjecture", verdict="proved", icon=_padded(icon_051)),
        dict(num="062", name="LeBrun–Salamon conjecture", verdict="proved", icon=_padded(icon_062)),
        dict(num="063", name="Generalized Mukai conjecture", verdict="proved", icon=_padded(icon_063)),
        dict(num="059", name="Zariski's multiplicity conjecture", verdict="counterexample", icon=_padded(icon_059)),
        dict(num="060", name="Global spherical shell conjecture", verdict="proved", icon=_padded(icon_060)),
        dict(num="058", name="Kollár–Pardon universal covers", verdict="proved", icon=_padded(icon_058)),
        dict(num="057", name="Campana's abelianity conjecture", verdict="proved", icon=_padded(icon_057)),
    ]
