import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
from lib.grid import GridScene

import json

AC = ORANGE_          # chapter accent (Geometry & PDE)
SW = 2.0              # main stroke
SW2 = 1.2             # secondary stroke
Z_FEAT = 61           # above the feature card (z=60) and the dimmer (z=50)
ICON_W, ICON_H = 2.75, 0.95
S2 = np.sqrt(2.0)


# =====================================================================
# small helpers
# =====================================================================
def _P(pts):
    pts = np.asarray(pts, dtype=float)
    if pts.ndim == 1:
        pts = pts[None]
    if pts.shape[1] == 2:
        pts = np.c_[pts, np.zeros(len(pts))]
    return pts


def _line(pts, color=WHITE_, w=SW, op=1.0, closed=False):
    pts = _P(pts)
    if closed:
        pts = np.r_[pts, pts[:1]]
    m = VMobject().set_points_as_corners(pts)
    m.set_stroke(color, w, op).set_fill(opacity=0)
    return m


def _multi(polys, color=GREY_, w=SW2, op=1.0, closed=False):
    """Many polylines in ONE VMobject (keeps submobject counts low)."""
    vm = VMobject()
    for pl in polys:
        pts = _P(pl)
        if closed:
            pts = np.r_[pts, pts[:1]]
        vm.start_new_path(pts[0])
        vm.add_points_as_corners(pts[1:])
    vm.set_stroke(color, w, op).set_fill(opacity=0)
    return vm


def _shape(pts, fill, fop=1.0, stroke=None, w=0.0, sop=1.0):
    pts = _P(pts)
    m = VMobject().set_points_as_corners(np.r_[pts, pts[:1]])
    m.set_fill(fill, fop)
    m.set_stroke(stroke or fill, w, sop if w > 0 else 0)
    return m


def _arrow(a, b, color=GREY_, w=1.6, tip=0.09):
    return Arrow(_P(a)[0], _P(b)[0], buff=0, color=color, stroke_width=w, tip_length=tip,
                 max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=40)


def _tri(center, direction, size=0.08, color=AC):
    d = np.asarray(direction, float)[:2]
    d = d / np.linalg.norm(d)
    n = np.array([-d[1], d[0]])
    c = np.asarray(center, float)[:2]
    pts = [c + d * size, c - d * size * 0.6 + n * size * 0.7, c - d * size * 0.6 - n * size * 0.7]
    return _shape(pts, color, 1.0)


def _fit(m, w=ICON_W, h=ICON_H, margin=0.94):
    """Normalise an icon; an invisible margin keeps it inside its tile even
    during the grid's 1.12x 'lit' pulse."""
    m.scale(min(w / m.width, h / m.height)).move_to(ORIGIN)
    pad = Rectangle(width=m.width / margin, height=m.height / margin)
    pad.set_stroke(opacity=0).set_fill(opacity=0)
    return VGroup(pad, m)


def _mark(vis):
    """Remember the design-space frame of a big visual (GridScene rescales it)."""
    vis._c0 = vis.get_center().copy()
    vis._w0 = vis.width
    return vis


def _mapper(vis):
    """Map design coordinates -> where the big visual actually sits now."""
    s = vis.width / vis._w0
    c1 = vis.get_center().copy()

    def f(m):
        m.shift(-vis._c0).scale(s, about_point=ORIGIN).shift(c1)
        return m
    f.s = s
    f.pts = lambda P: (np.asarray(P, float) - vis._c0) * s + c1
    return f


def _z(*mobs):
    """New mobjects created during a feature animation draw above the card."""
    for m in mobs:
        m.set_z_index(Z_FEAT)
    return mobs


def _keep(vis, *mobs):
    """...and, once they have been animated in, join the big card so they
    collapse with it."""
    vis.add(*mobs)


# =====================================================================
# 3D -> 2D orthographic view with visibility by ray marching
# =====================================================================
class _View:
    def __init__(self, az, el, scale=1.0):
        a, e = np.radians(az), np.radians(el)
        self.r = np.array([-np.sin(a), np.cos(a), 0.0])
        self.u = np.array([-np.sin(e) * np.cos(a), -np.sin(e) * np.sin(a), np.cos(e)])
        self.f = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
        self.s = scale

    def __call__(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        return self.s * np.stack([P @ self.r, P @ self.u, np.zeros(len(P))], 1)

    def visible(self, P, inside, step=0.025, n=90, off=0.03):
        P = np.atleast_2d(np.asarray(P, float))
        ts = off + step * np.arange(n)
        Q = P[:, None, :] + ts[None, :, None] * self.f[None, None, :]
        ins = inside(Q.reshape(-1, 3)).reshape(len(P), n)
        return ~ins.any(1)


def _runs(mask, closed=True):
    mask = np.asarray(mask, bool)
    n = len(mask)
    if closed and mask.any() and not mask.all():
        k = int(np.argmax(mask != np.roll(mask, 1)))
        idx = np.r_[np.arange(k, n), np.arange(k)]
    else:
        idx = np.arange(n)
    m = mask[idx]
    out, s = [], 0
    for i in range(1, n + 1):
        if i == n or m[i] != m[s]:
            seg = list(idx[s:i])
            if i < n:
                seg.append(idx[i])
            elif closed:
                seg.append(idx[0])
            out.append((np.array(seg), bool(m[s])))
            s = i
    return out


def _vis_curve(P3, view, inside, color, w=SW, op=1.0, back_op=0.22, back_w=None,
               closed=True, mask=None, draw_back=True):
    """Curve on a surface: front pieces solid, hidden pieces faint (or omitted)."""
    if mask is None:
        mask = view.visible(P3, inside)
    Q = view(P3)
    g = VGroup()
    for seg, v in _runs(mask, closed):
        if len(seg) < 2 or (not v and not draw_back):
            continue
        g.add(_line(Q[seg], color, w if v else (back_w or w * 0.7), op if v else back_op))
    return g


def _outline(view, Rfun, nb=220):
    """Silhouette of a star-shaped surface r = R(u) (max projected radius per angle)."""
    th = np.linspace(0.0, np.pi, 140)
    ph = np.linspace(0, 2 * np.pi, 280, endpoint=False)
    T, F = np.meshgrid(th, ph)
    U = np.stack([np.sin(T) * np.cos(F), np.sin(T) * np.sin(F), np.cos(T)], -1).reshape(-1, 3)
    Q = view(Rfun(U)[:, None] * U)
    ang = np.arctan2(Q[:, 1], Q[:, 0])
    rad = np.hypot(Q[:, 0], Q[:, 1])
    b = np.floor((ang + np.pi) / (2 * np.pi) * nb).astype(int) % nb
    rmax = np.zeros(nb)
    np.maximum.at(rmax, b, rad)
    rmax = (np.roll(rmax, 1) + 2 * rmax + np.roll(rmax, -1)) / 4
    a = -np.pi + (np.arange(nb) + 0.5) * 2 * np.pi / nb
    return np.stack([rmax * np.cos(a), rmax * np.sin(a), 0 * a], 1)


# =====================================================================
# 375  De Giorgi: Allen-Cahn transition layer, level sets of tanh
# =====================================================================
PH_NEG = interpolate_color(ManimColor(CARD), ManimColor(GREY_), 0.32)
PH_POS = interpolate_color(ManimColor(CARD), ManimColor(ORANGE_), 0.62)
LEVELS = [-0.9, -0.7, -0.45, -0.2, 0.0, 0.2, 0.45, 0.7, 0.9]


def _phase_layer(x0, x1, y0, y1, k, g=None, n=40, line_w=1.0, mid_w=2.4):
    """Strips between the level sets {u = c} of u = tanh((x - g(y))/sqrt2):
    x = k*sqrt2*artanh(c) + g(y). Flat (g = 0) is the 1D tanh profile."""
    ys = np.linspace(y0, y1, n)
    gy = g(ys) if g is not None else 0 * ys
    xs_lv = [k * S2 * np.arctanh(u) + gy for u in LEVELS]
    bounds = [np.full(n, x0)] + xs_lv + [np.full(n, x1)]
    us = [-1.0] + LEVELS + [1.0]
    strips = VGroup()
    for i in range(len(bounds) - 1):
        um = (us[i] + us[i + 1]) / 2
        col = interpolate_color(PH_NEG, PH_POS, (um + 1) / 2)
        L = np.stack([bounds[i], ys], 1)
        R = np.stack([bounds[i + 1], ys], 1)[::-1]
        strips.add(_shape(np.r_[L, R], col, 1.0))
    lines = VGroup()
    for u, xs in zip(LEVELS, xs_lv):
        mid = abs(u) < 1e-9
        lines.add(_line(np.stack([xs, ys], 1), WHITE_, mid_w if mid else line_w,
                        0.95 if mid else 0.35))
    return strips, lines


def _tanh_graph(x0, x1, yc, amp, k, color=AC, w=SW, n=60):
    xs = np.linspace(x0, x1, n)
    ys = yc + amp * np.tanh(xs / k / S2)
    return _line(np.stack([xs, ys], 1), color, w)


def icon_degiorgi():
    hw, hh = 0.62, 0.47
    k = 0.45 / (S2 * np.arctanh(0.9))
    strips, lines = _phase_layer(-hw, hw, -hh, hh, k, n=2)
    box = Rectangle(width=2 * hw, height=2 * hh).set_stroke(GREY_, SW2, 0.9)
    sq = VGroup(strips, lines, box)
    # 1D profile: u = tanh(x / sqrt 2), with the asymptotes u = +-1
    amp = 0.36
    gx0, gx1 = -0.68, 0.68
    axis = _line([[gx0, 0], [gx1, 0]], GREY_, 1.0, 0.7)
    asym = VGroup(*[DashedLine([gx0, s * amp, 0], [gx1, s * amp, 0], dash_length=0.05,
                               dashed_ratio=0.5).set_stroke(GREY_, 1.0, 0.6) for s in (-1, 1)])
    curve = _tanh_graph(gx0, gx1, 0, amp, k)
    graph = VGroup(axis, asym, curve)
    return _fit(VGroup(sq, graph).arrange(RIGHT, buff=0.32))


def _wave(y0, y1):
    H = y1 - y0
    return lambda y: (0.30 * np.sin(2 * np.pi * 1.05 * (y - y0) / H + 0.5)
                      + 0.13 * np.sin(2 * np.pi * 2.2 * (y - y0) / H + 1.9))


# design-space layout of the big De Giorgi card
DG = dict(x0=-2.3, x1=2.3, y0=0.05, y1=2.1, k=1.4 / (S2 * np.arctanh(0.9)),
          gy=-0.8, amp=0.42, dy=-1.76)


def big_degiorgi():
    d = DG
    strips, lines = _phase_layer(d["x0"], d["x1"], d["y0"], d["y1"], d["k"],
                                 g=_wave(d["y0"], d["y1"]), n=48)
    box = Rectangle(width=d["x1"] - d["x0"], height=d["y1"] - d["y0"]).set_stroke(GREY_, 1.6, 0.9)
    box.move_to([(d["x0"] + d["x1"]) / 2, (d["y0"] + d["y1"]) / 2, 0])
    ym = (d["y0"] + d["y1"]) / 2
    lab_m = tex("-1", 30, WHITE_).move_to([d["x0"] + 0.36, ym, 0])
    lab_p = tex("+1", 30, WHITE_).move_to([d["x1"] - 0.38, ym, 0])
    # 1D profile axes (curve itself is drawn during the animation)
    gy, amp = d["gy"], d["amp"]
    axis = _arrow([d["x0"], gy], [d["x1"] + 0.05, gy], GREY_, 1.4, 0.1)
    asym = VGroup(*[DashedLine([d["x0"], gy + s * amp, 0], [d["x1"], gy + s * amp, 0],
                               dash_length=0.08, dashed_ratio=0.5).set_stroke(GREY_, 1.0, 0.55)
                    for s in (-1, 1)])
    x8 = tex("x_8", 26, GREY_).next_to(axis.get_end(), DOWN, buff=0.08).shift(LEFT * 0.12)
    ulab = tex("u", 28, GREY_).move_to([d["x0"] - 0.22, gy + amp, 0])
    # dimension strip: n = 2 .. 10
    cells, nums = VGroup(), VGroup()
    for i, n in enumerate(range(2, 11)):
        c = Square(0.46).set_stroke(DIM, 1.4, 1.0).set_fill(CARD, 0)
        c.move_to([-1.84 + i * 0.46, d["dy"], 0])
        cells.add(c)
        nums.add(txt(str(n), 22, GREY_).move_to(c))
    nlab = tex("n", 30, GREY_).next_to(cells, LEFT, buff=0.2)
    vis = VGroup(strips, lines, box, lab_m, lab_p, axis, asym, x8, ulab, cells, nums, nlab)
    vis.strips, vis.lines, vis.cells, vis.nums = strips, lines, cells, nums
    # invisible placeholder so the legend row under the strip is inside the frame
    ph = Rectangle(width=4.0, height=0.3).set_stroke(opacity=0).set_fill(opacity=0)
    ph.move_to([0.0, d["dy"] - 0.48, 0])
    vis.add(ph)
    return _mark(vis)


def anim_degiorgi(scene, vis, rt):
    d = DG
    mp = _mapper(vis)
    # 1. the wavy transition layer is forced flat (monotone => one-dimensional)
    fs, fl = _phase_layer(d["x0"], d["x1"], d["y0"], d["y1"], d["k"], g=None, n=48)
    mp(fs), mp(fl)
    t1 = 0.36 * rt
    scene.wait(0.05 * rt)
    scene.play(*[Transform(a, b) for a, b in zip(vis.strips, fs)],
               *[Transform(a, b) for a, b in zip(vis.lines, fl)],
               run_time=t1, rate_func=smooth)
    # 2. the cross-section is exactly the tanh profile
    curve = mp(_tanh_graph(d["x0"], d["x1"], d["gy"], d["amp"], d["k"], w=3.0, n=90))
    form = mp(tex(r"u=\tanh\!\big(x_8/\sqrt2\big)", 26, AC)
              .move_to([-1.2, d["gy"] + 0.46 * d["amp"], 0]))
    form.set_stroke(BG, 4, background=True)
    _z(curve, form)
    scene.play(Create(curve), FadeIn(form, shift=UP * 0.1), run_time=0.2 * rt)
    _keep(vis, curve, form)
    # 3. which dimensions: true up to 8 (the claimed endpoint), false from 9 on
    ok = VGroup(*vis.cells[:7])
    bad = VGroup(*vis.cells[7:])
    leg_ok = txt("always flat", 22, AC).scale(mp.s).next_to(ok, DOWN, buff=0.12 * mp.s)
    leg_bad = txt("not always", 22, RED_).scale(mp.s).next_to(bad, DOWN, buff=0.12 * mp.s)
    ring8 = vis.cells[6].copy().set_stroke(AC, 3.2, 1.0).set_fill(opacity=0)
    _z(leg_ok, leg_bad, ring8)
    scene.wait(0.04 * rt)
    scene.play(LaggedStart(*[c.animate.set_fill(AC, 0.22).set_stroke(AC, 1.4, 0.8) for c in ok],
                           lag_ratio=0.12, group=vis),
               LaggedStart(*[nm.animate.set_color(WHITE_) for nm in vis.nums[:7]], lag_ratio=0.12,
                           group=vis),
               FadeIn(leg_ok), run_time=0.14 * rt)
    scene.play(Create(ring8), vis.nums[6].animate.set_color(AC).scale(1.2),
               *[c.animate.set_stroke(RED_, 1.4, 0.9).set_fill(RED_, 0.12) for c in bad],
               *[nm.animate.set_color(RED_) for nm in vis.nums[7:]],
               FadeIn(leg_bad), run_time=0.14 * rt)
    _keep(vis, leg_ok, leg_bad, ring8)


# =====================================================================
# 376  Navier-Stokes computer: cellular flow on a flat torus, particle,
#      target region, Turing tape
# =====================================================================
def _cell_ring(c, n=64):
    """Streamline sin(pi x) sin(pi y) = c of the unit cell (bisection along rays)."""
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    d = np.stack([np.cos(a), np.sin(a)], 1)
    lo = np.zeros(n)
    hi = 0.5 / np.abs(d).max(1)
    for _ in range(36):
        mid = (lo + hi) / 2
        p = 0.5 + mid[:, None] * d
        val = np.sin(np.pi * p[:, 0]) * np.sin(np.pi * p[:, 1])
        lo = np.where(val > c, mid, lo)
        hi = np.where(val > c, hi, mid)
    return 0.5 + lo[:, None] * d


# particle route in torus coordinates [0,2]^2: rides the cells, takes the
# hyperbolic stagnation point at the centre as a switch, ends in the target
WAY = [(0.22, 0.24), (0.55, 0.13), (0.86, 0.3), (0.95, 0.74), (1.13, 0.98), (1.55, 1.09),
       (1.86, 1.42), (1.72, 1.84), (1.32, 1.86), (1.05, 1.58), (0.98, 1.2), (0.78, 1.03),
       (0.36, 0.98), (0.13, 1.3), (0.24, 1.66), (0.52, 1.73)]
TARGET = (0.55, 1.72)
TARGET_R = 0.17


def _route(side, n=320):
    m = VMobject().set_points_smoothly(_P([((x - 1) * side / 2, (y - 1) * side / 2) for x, y in WAY]))
    return np.array([m.point_from_proportion(a) for a in np.linspace(0, 1, n)])


def _flow_box(side, rings=(0.22, 0.6), w=SW2, op=0.5, heads=True, marks=True):
    cs = side / 2
    polys = []
    g = VGroup()
    for i in range(2):
        for j in range(2):
            for c in rings:
                p = _cell_ring(c)
                polys.append(np.c_[(i + p[:, 0]) * cs - side / 2, (j + p[:, 1]) * cs - side / 2])
            if heads:  # flow direction on the outer ring, at the top of the cell
                p = _cell_ring(rings[0], n=4)[1]           # angle pi/2: top of ring
                x, y = (i + p[0]) * cs - side / 2, (j + p[1]) * cs - side / 2
                ccw = (i + j) % 2 == 0
                g.add(_tri([x, y], [-1 if ccw else 1, 0], size=0.045 * side, color=GREY_))
    g.add(_multi(polys, GREY_, w, op, closed=True))
    border = Square(side).set_stroke(GREY_, 1.4, 0.9)
    g.add(border)
    if marks:  # flat torus: opposite sides identified
        e = 0.05 * side
        chev = []
        for sx in (-1, 1):
            cx = sx * side / 2
            chev.append([(cx - e * 0.6, e), (cx + e * 0.6, 0), (cx - e * 0.6, -e)])
        for sy in (-1, 1):
            cy = sy * side / 2
            for dx in (-0.6 * e, 0.6 * e):
                chev.append([(dx - e, cy - e * 0.6), (dx, cy + e * 0.6), (dx + e, cy - e * 0.6)])
        g.add(_multi(chev, GREY_, 1.4, 0.9))
    return g


def _target(side, w=1.6):
    cx, cy = (TARGET[0] - 1) * side / 2, (TARGET[1] - 1) * side / 2
    c = Circle(radius=TARGET_R * side / 2).move_to([cx, cy, 0])
    c.set_fill(AC, 0.12).set_stroke(opacity=0)
    ring = DashedVMobject(c.copy().set_stroke(AC, w, 1.0), num_dashes=14)
    return VGroup(c, ring)


def _particle(r=0.05):
    return VGroup(Dot(radius=r * 2.2, color=WHITE_).set_opacity(0.18),
                  Dot(radius=r, color=WHITE_))


def icon_fluid():
    side = 0.95
    box = _flow_box(side, rings=(0.22, 0.62), op=0.45, marks=False)
    route = _route(side)
    trail = _line(route[:250], AC, 1.8)
    tgt = _target(side, w=1.4)
    dot = _particle(0.032).move_to(route[249])
    fluid = VGroup(box, tgt, trail, dot)
    # Turing tape with head
    bits = [0, 1, 1, 0, 1, 0]
    cw = 0.27
    tape = VGroup()
    for i, b in enumerate(bits):
        cell = Square(cw).set_stroke(GREY_, 1.2, 0.9).move_to([i * cw, 0, 0])
        tape.add(cell)
        if b:
            tape.add(Square(cw * 0.42).set_fill(WHITE_, 0.9).set_stroke(opacity=0).move_to(cell))
        else:
            tape.add(Circle(radius=cw * 0.2).set_stroke(GREY_, 1.2, 0.8).move_to(cell))
    head = _tri([3 * cw, -cw * 0.95], [0, 1], size=0.075)
    tm = VGroup(tape, head)
    return _fit(VGroup(fluid, tm).arrange(RIGHT, buff=0.32))


NS = dict(side=2.9, cy=-0.15, tape_y=1.9, cw=0.42)
TAPE0 = [0, 1, 1, 0, 1, 0, 0]
HEAD0 = 2
STEPS = [(1, +1), (0, +1), (1, -1), (1, +1)]        # (write, move); then HALT


def big_fluid():
    d = NS
    side = d["side"]
    flow = _flow_box(side, rings=(0.12, 0.42, 0.78), op=0.5)
    tgt = _target(side, w=2.0)
    olab = tex("O", 30, AC).next_to(tgt, RIGHT, buff=0.06)
    olab.set_stroke(CARD, 5, background=True)
    route = _route(side)
    dot = _particle(0.06).move_to(route[0])
    fluid = VGroup(flow, tgt, olab, dot).shift(UP * d["cy"])
    # Turing tape
    cw = d["cw"]
    cells, syms = VGroup(), VGroup()
    x_start = -(len(TAPE0) - 1) * cw / 2 + 0.55
    for i, b in enumerate(TAPE0):
        c = Square(cw).set_stroke(GREY_, 1.4, 0.9).move_to([x_start + i * cw, d["tape_y"], 0])
        cells.add(c)
        syms.add(mono(str(b), 24, WHITE_).move_to(c))
    head = _tri([cells[HEAD0].get_x(), d["tape_y"] - cw * 0.5 - 0.13], [0, 1], size=0.1)
    prog = txt("program", 22, GREY_).next_to(cells, LEFT, buff=0.2)
    eq = tex(r"\text{particle}\in O\iff\text{program halts}", 28, WHITE_)
    eq.move_to([0, d["cy"] - side / 2 - 0.4, 0])
    vis = VGroup(fluid, cells, syms, head, prog, eq)
    vis.dot, vis.cells, vis.syms, vis.head, vis.tgt, vis.eq = dot, cells, syms, head, tgt, eq
    # placeholder for the HALT chip (appears at the end)
    ph = Rectangle(width=0.9, height=0.4).set_stroke(opacity=0).set_fill(opacity=0)
    ph.next_to(cells, RIGHT, buff=0.22)
    vis.add(ph)
    vis.ph = ph
    return _mark(vis)


def anim_fluid(scene, vis, rt):
    d = NS
    mp = _mapper(vis)
    route = _route(d["side"])
    route = route + np.array([0, d["cy"], 0])
    route = mp.pts(route)                                       # into card coords
    n = len(route)
    nseg = len(STEPS) + 1
    cut = np.linspace(0, n - 1, nseg + 1).astype(int)
    trail = VMobject().set_points_as_corners(route[:2]).set_stroke(AC, 2.6, 0.95)
    _z(trail)
    scene.add(trail)
    vis.dot.set_z_index(Z_FEAT + 1)
    step_t = min(0.95, 0.68 * rt / nseg)
    syms = list(vis.syms)
    head_i = HEAD0
    cw = vis.cells[1].get_x() - vis.cells[0].get_x()

    def mover(i0, i1):
        def upd(m, a):
            j = int(round(i0 + (i1 - i0) * a))
            vis.dot.move_to(route[j])
            m.set_points_as_corners(route[:max(j, 1) + 1])
        return upd

    for k, (wbit, mv) in enumerate(STEPS):
        new = mono(str(wbit), 24, AC if wbit else WHITE_).scale(mp.s).move_to(vis.cells[head_i])
        scene.play(UpdateFromAlphaFunc(trail, mover(cut[k], cut[k + 1]), rate_func=smooth),
                   Transform(syms[head_i], new),
                   vis.head.animate.shift(RIGHT * mv * cw),
                   run_time=step_t)
        head_i += mv
    # last pulse: HALT, and the particle slides into the target region
    halt = chip("HALT", AC, size=16).scale(mp.s).move_to(vis.ph)
    _z(halt)
    scene.play(UpdateFromAlphaFunc(trail, mover(cut[-2], cut[-1]), rate_func=smooth),
               FadeIn(halt, scale=0.8), vis.cells[head_i].animate.set_stroke(AC, 2.4, 1.0),
               run_time=step_t * 1.2)
    rest = max(0.4, rt - step_t * (nseg + 0.2))
    scene.play(vis.tgt[0].animate.set_fill(AC, 0.4), Indicate(vis.dot, color=AC, scale_factor=1.6),
               run_time=min(0.6, rest * 0.5))
    scene.play(Indicate(vis.eq, color=AC, scale_factor=1.06), run_time=min(0.9, rest * 0.5))
    _keep(vis, trail, halt)


# =====================================================================
# 345  closed geodesics on a lumpy sphere
#      r = 1 + eps (x^4 + y^4 + z^4 - 3/5) has the symmetries of a cube, so its
#      sections by the 9 mirror planes are genuine closed geodesics
#      (fixed sets of isometric reflections are totally geodesic).
# =====================================================================
LUMP4, LUMP6 = 0.1, 6.0
LUMP_VIEW = (35, 28)
# normals of 6 of the 9 mirror planes of the cube group
LOOP_N = [(0, 0, 1), (0, 1, 0), (1, 1, 0), (1, 0, -1), (1, 0, 0), (0, 1, -1)]


def _lump_R(U):
    x, y, z = U[:, 0], U[:, 1], U[:, 2]
    return 1 + LUMP4 * (x ** 4 + y ** 4 + z ** 4 - 0.6) + LUMP6 * (x * x * y * y * z * z - 1 / 105)


def _lump_inside(Q):
    r = np.linalg.norm(Q, axis=1) + 1e-12
    return r < _lump_R(Q / r[:, None]) - 2e-3


def _plane_loop(nrm, n=220, radial=None):
    nrm = np.asarray(nrm, float)
    nrm = nrm / np.linalg.norm(nrm)
    a = np.array([1.0, 0, 0]) if abs(nrm[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(nrm, a)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(nrm, e1)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    U = np.cos(t)[:, None] * e1 + np.sin(t)[:, None] * e2
    r = _lump_R(U)
    if radial is not None:
        r = r * radial(t)
    return r[:, None] * U


def _lumpy_body(view, w=SW):
    out = _outline(view, _lump_R, nb=300)
    body = VMobject().set_points_as_corners(np.r_[out, out[:1]])
    body.set_fill([ManimColor("#3A4558"), ManimColor("#151B24")], 1.0)
    body.set_sheen_direction(DR)
    body.set_stroke(WHITE_, w, 0.9)
    # soft highlight towards the upper left (stacked translucent shrunken copies)
    hi = VGroup()
    c = body.get_center() + np.array([-0.22 * body.width, 0.24 * body.height, 0])
    for k in (0.75, 0.55, 0.38, 0.22):
        hi.add(body.copy().set_stroke(opacity=0).set_fill(WHITE_, 0.035).scale(k, about_point=c))
    return VGroup(body, hi)


def _geo_loop(i, view, w=SW, back_op=0.25, color=AC):
    P = _plane_loop(LOOP_N[i])
    mask = view.visible(P, _lump_inside)
    return _vis_curve(P, view, _lump_inside, color, w, 1.0, back_op=back_op, mask=mask), mask


def icon_geodesics():
    v = _View(*LUMP_VIEW, scale=0.5)
    body = _lumpy_body(v, w=1.8)
    loops = VGroup(*[_geo_loop(i, v, w=1.6, back_op=0.25)[0] for i in (0, 1, 2)])
    blob = VGroup(body, loops)
    inf = tex(r"\#\{\gamma\}=\infty", 30, WHITE_)
    return _fit(VGroup(blob, inf).arrange(RIGHT, buff=0.3))


GEO_SCALE = 1.5
GEO_FIRST = (0, 1, 2, 3)      # drawn one by one
GEO_SNAP = 4                  # the rubber band that snaps tight at the end
GEO_Y = 0.22


def big_geodesics():
    v = _View(*LUMP_VIEW, scale=GEO_SCALE)
    body = _lumpy_body(v, w=2.4).shift(UP * GEO_Y)
    lab = txt("closed geodesics:", 26, GREY_)
    lab.move_to([-0.35, -2.05, 0])
    ph = Rectangle(width=4.6, height=0.2).set_stroke(opacity=0).set_fill(opacity=0).move_to([0, 2.0, 0])
    vis = VGroup(body, lab, ph)
    vis.lab = lab
    return _mark(vis)


def anim_geodesics(scene, vis, rt):
    mp = _mapper(vis)
    v = _View(*LUMP_VIEW, scale=GEO_SCALE)
    loops = []
    for i in GEO_FIRST:
        g, _ = _geo_loop(i, v, w=3.0, back_op=0.28)
        loops.append(mp(g.shift(UP * GEO_Y)))
    count = tex("1", 38, AC).next_to(vis.lab, RIGHT, buff=0.18)
    _z(*loops, count)
    t_loop = 0.11 * rt
    for k, g in enumerate(loops):
        anims = [Create(g)]
        if k == 0:
            anims.append(FadeIn(count, scale=0.6))
        else:
            new = tex(str(k + 1), 38, AC).scale(mp.s).move_to(count, aligned_edge=LEFT)
            anims.append(Transform(count, new))
        scene.play(*anims, run_time=t_loop)
    inf = tex(r"\infty", 44, AC).scale(mp.s).move_to(count, aligned_edge=LEFT)
    scene.play(Transform(count, inf), run_time=0.09 * rt)
    # rubber band, loose -> snapped tight onto a 6th closed geodesic
    P = _plane_loop(LOOP_N[GEO_SNAP])
    mask = v.visible(P, _lump_inside)
    loose = _plane_loop(LOOP_N[GEO_SNAP], radial=lambda t: 1.17 + 0.05 * np.sin(3 * t + 0.6)
                        + 0.035 * np.cos(5 * t))
    Qt, Ql = v(P), v(loose)
    band, taut = VGroup(), VGroup()
    for seg, vv in _runs(mask, True):
        band.add(_line(Ql[seg], WHITE_, 2.6, 0.95))
        taut.add(_line(Qt[seg], YELLOW_, 3.4 if vv else 2.0, 1.0 if vv else 0.3))
    mp(band.shift(UP * GEO_Y)), mp(taut.shift(UP * GEO_Y))
    _z(band)
    used = 4 * t_loop + 0.09 * rt                     # = 0.53 rt
    scene.wait(0.08 * rt)                             # band appears ~"think rubber bands"
    scene.play(Create(band), run_time=0.11 * rt)
    scene.play(Transform(band, taut), run_time=0.14 * rt, rate_func=rush_into)
    # held (snapped) for the remaining ~0.19 rt, with a brief glow
    scene.play(Indicate(band, color=YELLOW_, scale_factor=1.03), run_time=0.08 * rt)
    _keep(vis, *loops, count, band)


# =====================================================================
# non-featured icons
# =====================================================================
def icon_yau():
    v = _View(-60, 20, scale=0.55)
    t = np.linspace(0, 2 * np.pi, 90, endpoint=False)
    rings = VGroup()
    for r, op in zip([0.3, 0.6, 0.9, 1.2], [1.0, 0.85, 0.6, 0.3]):
        P = np.stack([r * np.cos(t), r * np.sin(t), 0 * t + 0.62 * r * r], 1)
        rings.add(_line(v(P), AC, 1.6, op, closed=True))
    mer = VGroup()
    for k in range(3):   # meridians fade out as the end of the (noncompact) manifold
        r0, r1 = 0.4 * k, 0.4 * (k + 1)
        polys = []
        for phi in np.linspace(0, 2 * np.pi, 10, endpoint=False):
            rr = np.linspace(r0, r1, 12)
            polys.append(v(np.stack([rr * np.cos(phi), rr * np.sin(phi), 0.62 * rr * rr], 1)))
        mer.add(_multi(polys, AC, SW2, [0.7, 0.45, 0.2][k]))
    bowl = VGroup(mer, rings)
    cong = tex(r"\cong", 48, WHITE_)
    vp = _View(-60, 28, scale=0.42)
    s = np.linspace(-1, 1, 5)
    polys = [vp(np.stack([np.full(2, a), [-1, 1], [0, 0]], 1)) for a in s]
    polys += [vp(np.stack([[-1, 1], np.full(2, a), [0, 0]], 1)) for a in s]
    plane = _multi(polys, GREY_, SW2, 0.8)
    cn = tex(r"\mathbb{C}^n", 34, WHITE_).next_to(plane, UP, buff=0.04)
    flat = VGroup(plane, cn)
    return _fit(VGroup(bowl, cong, flat).arrange(RIGHT, buff=0.28))


def _torus_inside(Q, R=1.0, r=0.42):
    return (np.hypot(Q[:, 0], Q[:, 1]) - R) ** 2 + Q[:, 2] ** 2 < r * r - 2e-3


def icon_immersion():
    R, r = 1.0, 0.42
    v = _View(-70, 34, scale=0.5)
    inside = lambda Q: _torus_inside(Q, R, r)

    def T(u, w):
        return np.stack([(R + r * np.cos(w)) * np.cos(u), (R + r * np.cos(w)) * np.sin(u),
                         r * np.sin(w)], -1)

    def N(u, w):
        return np.stack([np.cos(w) * np.cos(u), np.cos(w) * np.sin(u), np.sin(w)], -1)

    def curve(u, w, color, wd, op):
        P = T(u, w) + 0.012 * N(u, w)
        return _vis_curve(P, v, inside, color, wd, op, draw_back=False, closed=True)

    u = np.linspace(0, 2 * np.pi, 260, endpoint=False)
    f = v.f
    base = np.cos(u) * f[0] + np.sin(u) * f[1]
    w0 = np.arctan2(-base, f[2])
    outline = VGroup(curve(u, w0, WHITE_, 1.8, 0.95), curve(u, w0 + np.pi, WHITE_, 1.8, 0.95))
    ww = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    mer = VGroup(*[curve(np.full_like(ww, uu), ww, AC, 1.3, 0.85)
                   for uu in np.linspace(0, 2 * np.pi, 12, endpoint=False)])
    lon = VGroup(*[curve(u, np.full_like(u, w1), AC, 1.0, 0.5) for w1 in (np.pi / 2, np.pi / 4)])
    torus = VGroup(mer, lon, outline)
    hook = tex(r"\hookrightarrow", 40, GREY_)
    # tesseract (projection of a 4-cube)
    o = 0.8
    sq = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    back = np.array([0.32, 0.24])

    def cube(sz, c):
        F = (sq - 0.5) * sz + c
        B = F + back * sz
        return F, B
    F1, B1 = cube(o, np.array([0, 0]))
    F2, B2 = cube(o * 0.48, np.array([0.08, 0.06]))
    polys = []
    for F, B in ((F1, B1), (F2, B2)):
        polys += [np.r_[F, F[:1]], np.r_[B, B[:1]]] + [[F[i], B[i]] for i in range(4)]
    polys += [[F1[i], F2[i]] for i in range(4)] + [[B1[i], B2[i]] for i in range(4)]
    tess = _multi(polys, GREY_, 1.1, 0.85)
    r4 = tex(r"\mathbb{R}^4", 32, WHITE_).next_to(tess, RIGHT, buff=0.1).shift(UP * 0.2)
    return _fit(VGroup(torus, hook, VGroup(tess, r4)).arrange(RIGHT, buff=0.22))


def _ideal_geodesic(a, b, n=40):
    """Poincare-disk geodesic between ideal points e^{ia}, e^{ib}."""
    d = (b - a) % (2 * np.pi)
    if d > np.pi:
        a, b, d = b, a, 2 * np.pi - d
    if abs(d - np.pi) < 1e-6:
        return np.array([[np.cos(a), np.sin(a)], [np.cos(b), np.sin(b)]])
    m = a + d / 2
    c = np.array([np.cos(m), np.sin(m)]) / np.cos(d / 2)
    rad = np.tan(d / 2)
    p1 = np.array([np.cos(a), np.sin(a)]) - c
    p2 = np.array([np.cos(b), np.sin(b)]) - c
    t1, t2 = np.arctan2(p1[1], p1[0]), np.arctan2(p2[1], p2[0])
    dt = (t2 - t1 + np.pi) % (2 * np.pi) - np.pi
    ts = t1 + np.linspace(0, dt, n)
    return c + rad * np.stack([np.cos(ts), np.sin(ts)], 1)


def _farey(depth=2):
    """Edges of the Farey tessellation by ideal triangles (exact, via inversions)."""
    def inv(a, b, o):
        d = (b - a) % (2 * np.pi)
        if d > np.pi:
            a, b, d = b, a, 2 * np.pi - d
        m = a + d / 2
        c = np.array([np.cos(m), np.sin(m)]) / np.cos(d / 2)
        rad = np.tan(d / 2)
        p = np.array([np.cos(o), np.sin(o)]) - c
        q = c + rad * rad * p / (p @ p)
        return np.arctan2(q[1], q[0])
    v0 = [np.pi / 2, np.pi / 2 + 2 * np.pi / 3, np.pi / 2 + 4 * np.pi / 3]
    edges = [(v0[0], v0[1], v0[2]), (v0[1], v0[2], v0[0]), (v0[2], v0[0], v0[1])]
    out = [(a, b) for a, b, _ in edges]
    for _ in range(depth):
        nxt = []
        for a, b, o in edges:
            m = inv(a, b, o)
            nxt += [(a, m, b), (m, b, a)]
            out += [(a, m), (m, b)]
        edges = nxt
    return out


def _disk_fan(p=complex(-0.35, -0.18), angles=(0.25, 0.55, 0.85), n=50):
    """Geodesics through p: Mobius images of diameters."""
    polys = []
    for th in angles:
        z = np.linspace(-0.995, 0.995, n) * np.exp(1j * th)
        w = (z + p) / (1 + np.conj(p) * z)
        polys.append(np.stack([w.real, w.imag], 1))
    return polys


def _saddle_geodesic(p0, v0, c=0.5, h=0.004, box=1.0):
    """Geodesic on the graph z = c(x^2 - y^2): x'' = -grad f * Hess f(v,v) / (1+|grad f|^2), RK4."""
    def acc(s):
        x, y, vx, vy = s
        fx, fy = 2 * c * x, -2 * c * y
        k = (2 * c * vx * vx - 2 * c * vy * vy) / (1 + fx * fx + fy * fy)
        return np.array([vx, vy, -fx * k, -fy * k])
    s = np.array([*p0, *v0], float)
    out = [s[:2].copy()]
    for _ in range(4000):
        k1 = acc(s); k2 = acc(s + h / 2 * k1); k3 = acc(s + h / 2 * k2); k4 = acc(s + h * k3)
        s = s + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        if abs(s[0]) > box or abs(s[1]) > box:
            break
        out.append(s[:2].copy())
    return np.array(out)


def icon_katok():
    # negatively curved saddle z = c(x^2 - y^2); three geodesics that start parallel
    # and close together spread apart (exponential divergence = entropy)
    c = 0.5
    v = _View(-62, 26, scale=0.62)
    lift = lambda xy: np.c_[xy, c * (xy[:, 0] ** 2 - xy[:, 1] ** 2)]
    s = np.linspace(-1, 1, 7)
    tt = np.linspace(-1, 1, 24)
    polys = [v(lift(np.stack([np.full_like(tt, a), tt], 1))) for a in s[1:-1]]
    polys += [v(lift(np.stack([tt, np.full_like(tt, a)], 1))) for a in s[1:-1]]
    grid = _multi(polys, GREY_, 1.0, 0.55)
    rim = np.r_[np.stack([tt, -np.ones_like(tt)], 1), np.stack([np.ones_like(tt), tt], 1),
                np.stack([tt[::-1], np.ones_like(tt)], 1), np.stack([-np.ones_like(tt), tt[::-1]], 1)]
    edge = _line(v(lift(rim)), WHITE_, 1.6, 0.9, closed=True)
    geo = VGroup()
    for y0 in (-0.11, 0.0, 0.11):
        g = v(lift(_saddle_geodesic((-1.0, y0), (1.0, 0.0), c)))
        geo.add(_line(g[:-6], AC, 1.8, 1.0), _tri(g[-1], g[-1] - g[-6], size=0.05))
    sad = VGroup(grid, edge, geo)
    # Poincare disk: Farey tessellation + a fan of geodesics through one point
    rad = 0.47
    farey = _multi([_ideal_geodesic(a, b) * rad for a, b in _farey(2)], GREY_, 1.0, 0.55)
    fan = _multi([q * rad for q in _disk_fan()], AC, 1.6, 0.95)
    rim = Circle(radius=rad).set_stroke(WHITE_, 1.6, 0.9)
    p = complex(-0.35, -0.18)
    pdot = Dot([p.real * rad, p.imag * rad, 0], radius=0.03, color=WHITE_)
    disk = VGroup(farey, fan, rim, pdot)
    return _fit(VGroup(sad, disk).arrange(RIGHT, buff=0.35))


def icon_lagrangian():
    W, H = 1.9, 0.92
    box = Rectangle(width=W, height=H).set_stroke(GREY_, 1.0, 0.5)
    fib = _multi([[(x, -H / 2), (x, H / 2)] for x in np.linspace(-W / 2, W / 2, 9)[1:-1]],
                 DIM, 1.0, 0.9)
    zero = _line([[-W / 2, 0], [W / 2, 0]], WHITE_, 1.8, 0.9)
    # identification marks on the two vertical edges (T*S^1 cut open)
    marks = _multi([[(sx * W / 2 - 0.05, 0.27), (sx * W / 2, 0.33), (sx * W / 2 + 0.05, 0.27)]
                    for sx in (-1, 1)], GREY_, 1.2, 0.8)
    # exact, embedded, non-graphical closed curve: (q, p) = (t + 1.4 sin t, .45 sin t + .12 sin 2t)
    t = np.linspace(0, 2 * np.pi, 200)
    q = t + 1.4 * np.sin(t)
    p = 0.45 * np.sin(t) + 0.12 * np.sin(2 * t)
    L = _line(np.stack([(q / (2 * np.pi) - 0.5) * W, p * 0.8], 1), RED_, 2.2)
    strip = VGroup(fib, box, zero, marks, L)
    lab = tex(r"L\not\simeq 0_M", 32, WHITE_)
    lab[0][0].set_color(RED_)
    return _fit(VGroup(strip, lab).arrange(RIGHT, buff=0.25))


def _ball(c, r, color=AC, fop=0.2, w=1.4):
    b = Circle(radius=r).move_to([c[0], c[1], 0]).set_stroke(color, w, 1.0).set_fill(color, fop)
    eq = Ellipse(width=2 * r, height=0.5 * r).move_to(b).set_stroke(WHITE_, 0.8, 0.35)
    return VGroup(b, eq)


def icon_packing():
    big = Circle(radius=0.47).set_stroke(WHITE_, 1.8, 0.95).set_fill(WHITE_, 0.04)
    big_eq = DashedVMobject(Ellipse(width=0.94, height=0.2).set_stroke(GREY_, 0.9, 0.5), num_dashes=18)
    small = VGroup(*[_ball(c, r) for c, r in [((-0.19, 0.11), 0.2), ((0.21, 0.13), 0.17),
                                                ((0.04, -0.25), 0.16), ((-0.29, -0.2), 0.09),
                                                ((0.3, -0.17), 0.08)]])
    balls = VGroup(big, big_eq, small)
    conds = VGroup(tex(r"\textstyle\sum_i R_i^{\,n}<R^n", 27, WHITE_),
                   tex(r"R_i+R_j<R", 27, WHITE_)).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    return _fit(VGroup(balls, conds).arrange(RIGHT, buff=0.3))


def icon_blaschke():
    v = _View(-30, 18, scale=0.47)
    inside = lambda Q: np.linalg.norm(Q, axis=1) < 1 - 2e-3
    sph = Circle(radius=0.47).set_stroke(WHITE_, 1.8, 0.95).set_fill(WHITE_, 0.04)
    t = np.linspace(0, 2 * np.pi, 160, endpoint=False)
    eq = _vis_curve(np.stack([np.cos(t), np.sin(t), 0 * t], 1), v, inside, GREY_, 1.0, 0.6,
                    back_op=0.2)
    mer = VGroup()
    for phi in np.radians([0, 45, 90, 135]):
        P = np.stack([np.sin(t) * np.cos(phi), np.sin(t) * np.sin(phi), np.cos(t)], 1)
        mer.add(_vis_curve(P, v, inside, AC, 1.6, 1.0, back_op=0.25))
    N = v([0, 0, 1])[0]
    S = v([0, 0, -1])[0]
    pd = Dot(N, radius=0.035, color=WHITE_)
    qd = Dot(S, radius=0.03, color=WHITE_).set_opacity(0.45)
    sphere = VGroup(sph, eq, mer, pd, qd)
    lab = tex(r"\mathrm{inj}=\mathrm{diam}", 30, WHITE_)
    return _fit(VGroup(sphere, lab).arrange(RIGHT, buff=0.3))


def icon_donaldson():
    v = _View(-62, 32, scale=0.62)
    sq = v(np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]], float))
    plane = _shape(sq, WHITE_, 0.04, GREY_, 1.2, 0.8)
    p0 = np.array([-0.55, -0.55, 0])
    e1, e2 = np.array([1.25, 0, 0]), np.array([0, 1.25, 0])
    par = _shape(v(np.array([p0, p0 + e1, p0 + e1 + e2, p0 + e2])), AC, 0.18)
    pv = v(np.array([p0, p0 + e1, p0 + e2]))
    av = _arrow(pv[0], pv[1], WHITE_, 2.0, 0.1)
    aj = _arrow(pv[0], pv[2], AC, 2.0, 0.1)
    ts = np.linspace(0.18, np.pi / 2 - 0.25, 20)
    arc_pts = v(p0 + 0.45 * np.stack([np.cos(ts), np.sin(ts), 0 * ts], 1))
    arc = _line(arc_pts, GREY_, 1.2, 0.9)
    arc_tip = _tri(arc_pts[-1], arc_pts[-1] - arc_pts[-3], size=0.045, color=GREY_)
    lv = tex("v", 34, WHITE_).next_to(av.get_end(), RIGHT, buff=0.04)
    lj = tex("Jv", 34, AC).next_to(aj.get_end(), UP, buff=0.04)
    pic = VGroup(plane, par, arc, arc_tip, av, aj, lv, lj)
    words = VGroup(txt("tamed", 24, GREY_),
                   VGroup(tex(r"\Rightarrow", 30, WHITE_), txt("compatible", 24, AC)).arrange(RIGHT, buff=0.1)
                   ).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
    return _fit(VGroup(pic, words).arrange(RIGHT, buff=0.3))


def _dumbbell(a, x0=0.0, s=0.4, neck_color=WHITE_, n=70):
    """Rotationally symmetric profile rho(x) = sqrt(1-x^2) (1 - a e^{-x^2/0.08})."""
    x = np.linspace(-1, 1, n)
    rho = np.sqrt(np.clip(1 - x * x, 0, 1)) * (1 - a * np.exp(-x * x / 0.08))
    top = np.stack([x * s + x0, rho * s], 1)
    bot = np.stack([x * s + x0, -rho * s], 1)[::-1]
    out = _line(np.r_[top, bot], WHITE_, 1.6, 0.95, closed=True)
    rings = VGroup()
    for xr in (-0.55, 0.0, 0.55):
        r = np.sqrt(1 - xr * xr) * (1 - a * np.exp(-xr * xr / 0.08)) * s
        th = np.linspace(-np.pi / 2, np.pi / 2, 30)
        col = neck_color if xr == 0 else AC
        op = 0.9 if xr == 0 and neck_color == RED_ else 0.7
        rings.add(_line(np.stack([x0 + xr * s + 0.22 * r * np.cos(th), r * np.sin(th)], 1), col, 1.2, op))
        rings.add(_line(np.stack([x0 + xr * s - 0.22 * r * np.cos(th), r * np.sin(th)], 1), col, 1.0, 0.25))
    return VGroup(out, rings)


def icon_calabi():
    s0 = _dumbbell(0.0)
    s1 = _dumbbell(0.5)
    s2 = _dumbbell(0.93, neck_color=RED_)
    spark = _multi([[(0.07 * np.cos(a), 0.07 * np.sin(a)), (0.16 * np.cos(a), 0.16 * np.sin(a))]
                    for a in np.radians([60, 120, 240, 300])], RED_, 1.6, 1.0)
    neck = Dot(radius=0.035, color=RED_)
    s2.add(VGroup(spark, neck).move_to(s2.get_center()))
    a1 = _arrow([0, 0], [0.32, 0], GREY_, 1.4, 0.08)
    a2 = a1.copy()
    row = VGroup(s0, a1, s1, a2, s2).arrange(RIGHT, buff=0.1)
    tl = tex(r"t\to T", 26, RED_).next_to(s2, DOWN, buff=0.06)
    return _fit(VGroup(row, tl))


def icon_bernoulli():
    # one-homogeneous free boundary: a (double) cone with its vertex singular point
    hw, hh, ry = 0.36, 0.44, 0.085
    th = np.linspace(0, 2 * np.pi, 60, endpoint=False)
    top = np.stack([hw * np.cos(th), hh + ry * np.sin(th)], 1)
    botf = np.stack([hw * np.cos(th[30:]), -hh + ry * np.sin(th[30:])], 1)   # front half
    botb = np.stack([hw * np.cos(th[:31]), -hh + ry * np.sin(th[:31])], 1)   # back half
    fill_up = _shape([(-hw, hh), (0, 0), (hw, hh)] + [tuple(p) for p in top[:31]][::-1][1:-1],
                     AC, 0.22)
    fill_dn = _shape([(-hw, -hh), (0, 0), (hw, -hh)] + [tuple(p) for p in botf][::-1],
                     AC, 0.22)
    sides = _multi([[(-hw, hh), (hw, -hh)], [(hw, hh), (-hw, -hh)]], WHITE_, 1.6, 0.95)
    rims = VGroup(_line(top, AC, 1.6, 1.0, closed=True), _line(botf, AC, 1.6, 1.0),
                  _line(botb, AC, 1.1, 0.3))
    apex = Dot(radius=0.035, color=WHITE_)
    cone = VGroup(fill_up, fill_dn, sides, rims, apex)
    # dimensions 2..8: flat (smooth) up to 6, first singular cone in 7
    xs = {n: (n - 2) * 0.33 for n in range(2, 9)}
    nl = VGroup(_line([[xs[2], 0], [xs[6], 0]], WHITE_, 2.0, 0.9),
                _line([[xs[6], 0], [xs[8], 0]], GREY_, 1.2, 0.6))
    ticks = _multi([[(x, -0.05), (x, 0.05)] for n, x in xs.items() if n != 7], GREY_, 1.2, 0.9)
    nums = VGroup(*[txt(str(n), 22, AC if n == 7 else GREY_, weight=BOLD if n == 7 else NORMAL)
                    .move_to([x, -0.27, 0]) for n, x in xs.items()])
    seven = Dot([xs[7], 0, 0], radius=0.06, color=AC)
    halo = Circle(radius=0.095).move_to(seven).set_stroke(AC, 1.4, 0.8)
    dims = VGroup(nl, ticks, nums, seven, halo)
    return _fit(VGroup(cone, dims).arrange(RIGHT, buff=0.35))


# =====================================================================
# scene
# =====================================================================
ICONS = {"375": icon_degiorgi, "376": icon_fluid, "345": icon_geodesics, "338": icon_yau,
         "333": icon_immersion, "339": icon_katok, "340": icon_lagrangian,
         "343": icon_packing, "344": icon_blaschke, "342": icon_donaldson,
         "352": icon_calabi, "367": icon_bernoulli}
BIGS = {"375": (big_degiorgi, anim_degiorgi), "376": (big_fluid, anim_fluid),
        "345": (big_geodesics, anim_geodesics)}


def _tiles():
    data = json.loads((VIDEO / "data" / "grids.json").read_text())["c9_grid"]
    out = []
    for d in data:
        t = dict(num=d["num"], name=d["name"], verdict=d["verdict"], icon=ICONS[d["num"]])
        if d.get("caption"):
            b, a = BIGS[d["num"]]
            t["feature"] = dict(caption=d["caption"], big=b, animate=a)
        out.append(t)
    return out


class C9Grid(GridScene):
    CHAPTER = "gp"
    TILES = _tiles()
