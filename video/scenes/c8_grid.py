import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
import json

import numpy as np

from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
from lib.grid import GridScene

# Rapid-fire grid: Operator Algebras, Topology & Functional Analysis (accent SKY_).
# Icons are designed in a ~2.9 x 1.0 box (Tile auto-fits them); big visuals are
# designed in an exact 5.2 x 4.4 box (an invisible reference rectangle), so the
# big card shows them at scale 1 and the animate callables can map design
# coordinates onto the card with _bring().

ACC = SKY_
BIG_W, BIG_H = 5.2, 4.4


# ====================================================================== helpers
def P(x, y):
    return np.array([x, y, 0.0])


def lin3(M):
    return np.array([[M[0][0], M[0][1], 0.0], [M[1][0], M[1][1], 0.0], [0.0, 0.0, 1.0]])


def xmark(c, r=0.1, color=RED_, width=3.0):
    c = np.array(c, dtype=float)
    return VGroup(Line(c + P(-r, r), c + P(r, -r)),
                  Line(c + P(-r, -r), c + P(r, r))).set_stroke(color, width)


def tick(c, size=0.2, color=GREEN_, width=3.0):
    return check_mark(color, size=size, width=width).move_to(c)


def arc_arrow(s, e, angle, color=WHITE_, width=2.0, tip=0.11):
    a = ArcBetweenPoints(np.array(s, float), np.array(e, float), angle=angle,
                         stroke_width=width, tip_length=tip)
    a.add_tip(tip_shape=ArrowTriangleFilledTip, tip_length=tip, tip_width=tip * 0.9)
    a.set_color(color)
    return a


def arrow(s, e, color=WHITE_, width=2.0, tip=0.12):
    return Arrow(np.array(s, float), np.array(e, float), buff=0, stroke_width=width,
                 tip_length=tip, color=color, max_tip_length_to_length_ratio=0.6,
                 max_stroke_width_to_length_ratio=40)


def dots_ellipsis(c, color=GREY_, r=0.022, gap=0.09):
    return VGroup(*[Dot(np.array(c, float) + P((i - 1) * gap, 0), radius=r, color=color)
                    for i in range(3)])


def _ref():
    return Rectangle(width=BIG_W, height=BIG_H).set_stroke(opacity=0).set_fill(opacity=0)


def _bring(mob, *items, below=False):
    """Map design-space mobjects onto the big card's current frame and attach them
    to it (so they collapse / disappear with the card)."""
    k = mob.ref.width / BIG_W
    off = mob.ref.get_center()
    for it in items:
        it.scale(k, about_point=ORIGIN).shift(off)
        it.set_z_index(mob.ref.z_index)
        if below:
            mob.insert(1, it)
        else:
            mob.add(it)
    return items[0] if len(items) == 1 else items


def _map(mob, p):
    k = mob.ref.width / BIG_W
    return mob.ref.get_center() + k * np.array(p, float)


# ====================================================================== 288 Kadison similarity
KAD_M = np.array([[1.0, 0.6], [0.12, 0.78]])       # the "skew" S^{-1}


def coord_frame(h, n, grid_w, border_w, grid_op=0.55):
    g = VGroup()
    for i in range(1, n):
        t = -h + 2 * h * i / n
        g.add(Line(P(t, -h), P(t, h)), Line(P(-h, t), P(h, t)))
    g.set_stroke(GREY_, grid_w, opacity=grid_op)
    border = Square(2 * h).set_stroke(WHITE_, border_w, opacity=0.9)
    return VGroup(g, border)


def icon_288():
    h, r, th = 0.42, 0.29, 1.0
    M = lin3(KAD_M)
    u = r * P(np.cos(th), np.sin(th))
    left = VGroup(coord_frame(h, 4, 1.0, 1.5), Circle(r).set_stroke(ACC, 2.2),
                  Line(ORIGIN, u).set_stroke(WHITE_, 1.5))
    left.apply_matrix(M, about_point=ORIGIN)
    left.add(Dot(lin3(KAD_M) @ u, radius=0.035, color=WHITE_))
    right = VGroup(coord_frame(h, 4, 1.0, 1.5), Circle(r).set_stroke(ACC, 2.2),
                   Line(ORIGIN, u).set_stroke(WHITE_, 1.5), Dot(u, radius=0.035, color=WHITE_))
    left.shift(P(-0.86, 0))
    right.shift(P(0.98, 0))
    ar = arrow(P(-0.1, 0), P(0.4, 0), WHITE_, 2.0, 0.11)
    lab = tex("S", 26, WHITE_).next_to(ar, UP, buff=0.06)
    return VGroup(left, ar, lab, right)


K288 = dict(h=1.3, r=0.95, th0=0.35, C=P(0, 0.12))


def big_288():
    h, r, th0, C = K288["h"], K288["r"], K288["th0"], K288["C"]
    M = lin3(KAD_M)
    vis = VGroup(_ref())
    vis.ref = vis[0]
    frame = coord_frame(h, 6, 1.5, 2.4).shift(C)
    frame.apply_matrix(M, about_point=C)
    p0 = C + M @ (r * P(np.cos(th0), np.sin(th0)))
    vline = Line(C, p0).set_stroke(WHITE_, 2.6)
    vdot = Dot(p0, radius=0.075, color=WHITE_)
    origin = Dot(C, radius=0.04, color=GREY_)
    top = txt("Kadison, 1955", 24, GREY_).move_to(P(0, 1.95))
    lab = tex(r"\pi(a^*)\ \ne\ \pi(a)^*", 36, WHITE_).move_to(P(0, -1.82))
    vis.add(frame, origin, vline, vdot, top, lab)
    vis.frame, vis.vline, vis.vdot, vis.lab = frame, vline, vdot, lab
    orbit = Circle(r).rotate(th0).set_stroke(ACC, 3.4).shift(C)
    orbit.apply_matrix(M, about_point=C)
    lab2 = tex(r"\rho(a) = S\,\pi(a)\,S^{-1}", 36, WHITE_).move_to(P(0, -1.82))
    lab3 = tex(r"\rho(a^*) = \rho(a)^*", 36, WHITE_).move_to(P(-0.2, -1.82))
    ck = tick(lab3.get_right() + P(0.32, 0.02), 0.26, GREEN_, 4)
    vis.later = dict(orbit=orbit, lab2=lab2, lab3=lab3, ck=ck)
    return vis


def anim_288(scene, mob, T):
    L = mob.later
    r, th0 = K288["r"], K288["th0"]
    k = mob.ref.width / BIG_W
    C = _map(mob, K288["C"])
    orbit = _bring(mob, L["orbit"], below=True)
    mob.remove(orbit)
    mob.insert(2, orbit)          # above the grid, below the vector
    M2 = KAD_M
    vline, vdot = mob.vline, mob.vdot

    def put(Mt, th):
        q = Mt @ np.array([np.cos(th), np.sin(th)])
        p = C + k * r * P(q[0], q[1])
        vline.put_start_and_end_on(C, p)
        vdot.move_to(p)

    # 1. the bounded (non-*) representation: the vector's orbit is a skewed ellipse
    scene.play(Create(orbit), UpdateFromAlphaFunc(vline, lambda m, a: put(M2, th0 + TAU * a)),
               run_time=0.36 * T)
    # 2. one change of coordinates S straightens everything
    Sinv = np.linalg.inv(M2)
    lab2 = _bring(mob, L["lab2"])
    scene.play(mob.frame.animate.apply_matrix(lin3(Sinv), about_point=C),
               orbit.animate.apply_matrix(lin3(Sinv), about_point=C),
               UpdateFromAlphaFunc(vline, lambda m, a: put((1 - a) * M2 + a * np.eye(2), th0)),
               *_swap(mob.lab, lab2), run_time=0.30 * T)
    # 3. now it is a *-representation: the orbit is a circle (rotations)
    lab3 = _bring(mob, L["lab3"])
    ck = _bring(mob, L["ck"])
    scene.play(UpdateFromAlphaFunc(vline, lambda m, a: put(np.eye(2), th0 + TAU * a)),
               *_swap(lab2, lab3), Create(ck, rate_func=_delayed(0.3, 0.6)), run_time=0.34 * T)


# ====================================================================== 293 hyperinvariant
def icon_293():
    """Mini version of the big card's ladder: the shift S (blue arcs) keeps every tail
    K_{>=h} (staircase of bars); a commuting V (white arcs) pushes each tail one rung
    down (red extension), so no tail is hyperinvariant (red X)."""
    Y, d = 0.3, 0.36
    X = {j: d * j for j in range(-2, 4)}
    g = VGroup()
    rungs = {1: -0.02, 0: -0.25}          # two rungs: wide enough for a 2-line tile name
    R = X[3] + 0.27
    for h, y in rungs.items():
        g.add(Rectangle(width=X[h] - X[h - 1], height=0.17).move_to(P((X[h - 1] + X[h]) / 2 - 0.13, y))
              .set_stroke(RED_, 1.4).set_fill(RED_, 0.3))
        g.add(Rectangle(width=R - X[h] + 0.13, height=0.17).move_to(P((X[h] - 0.13 + R) / 2, y))
              .set_stroke(ACC, 1.4).set_fill(ACC, 0.18))
        g.add(xmark(P(R - 0.14, y), 0.05, RED_, 2.6))
    g.add(*[Dot(P(X[j], Y), radius=0.045, color=WHITE_) for j in X])
    g.add(dots_ellipsis(P(X[-2] - 0.2, Y), r=0.018, gap=0.055), dots_ellipsis(P(X[3] + 0.2, Y), r=0.018, gap=0.055))
    g.add(*[arc_arrow(P(X[j] + 0.06, Y + 0.06), P(X[j + 1] - 0.06, Y + 0.06), -PI / 1.6, ACC, 1.8, 0.08)
            for j in range(-2, 3)])
    g.add(*[arc_arrow(P(X[j] - 0.06, Y - 0.06), P(X[j - 1] + 0.06, Y - 0.06), -PI / 1.6, WHITE_, 1.5, 0.07)
            for j in range(-1, 4)])
    g.add(tex("S", 30, ACC).move_to(P(X[-2] - 0.6, Y + 0.13)),
          tex("V", 30, WHITE_).move_to(P(X[-2] - 0.6, Y - 0.17)))
    return g


X293 = {j: 0.5 + 0.55 * j for j in range(-3, 4)}
Y293 = 1.62
LAD = {2: 0.72, 1: 0.27, 0: -0.18, -1: -0.63, -2: -1.08}
BAR_R = 2.55
YB293 = -1.62


def _bar(x0, x1, y, color, op):
    return Rectangle(width=x1 - x0, height=0.34).move_to(P((x0 + x1) / 2, y)) \
        .set_stroke(color, 1.8).set_fill(color, op)


def big_293():
    vis = VGroup(_ref())
    vis.ref = vis[0]
    dots = VGroup(*[Dot(P(X293[j], Y293), radius=0.065, color=WHITE_) for j in range(-3, 4)])
    ells = VGroup(dots_ellipsis(P(-1.52, Y293), r=0.03, gap=0.11),
                  dots_ellipsis(P(2.45, Y293), r=0.03, gap=0.11))
    s_arcs = VGroup(*[arc_arrow(P(X293[j] + 0.09, Y293 + 0.09), P(X293[j + 1] - 0.09, Y293 + 0.09),
                                -PI / 2, ACC, 2.6, 0.13) for j in range(-3, 3)])
    s_lab = tex("S", 40, ACC).move_to(P(-2.1, Y293 + 0.22))
    vis.add(s_arcs, dots, ells, s_lab)
    vis.s_arcs = s_arcs
    later = {}
    later["bars"] = [_bar(X293[h] - 0.22, BAR_R, LAD[h], ACC, 0.18) for h in LAD]
    later["labs"] = [tex(r"K_{\ge %d}" % h, 28, WHITE_).move_to(P(-1.95, LAD[h])) for h in LAD]
    for lb in later["labs"]:
        lb.align_to(P(-1.55, 0), RIGHT)
    later["checks"] = [tick(P(2.3, LAD[h]), 0.2, GREEN_, 3.4) for h in LAD]
    later["crosses"] = [xmark(P(2.3, LAD[h]), 0.1, RED_, 3.4) for h in LAD]
    later["segs"] = [_bar(X293[h - 1] - 0.22, X293[h] - 0.22, LAD[h], RED_, 0.3) for h in LAD]
    later["v_arcs"] = VGroup(*[arc_arrow(P(X293[j] - 0.09, Y293 - 0.09),
                                         P(X293[j - 1] + 0.09, Y293 - 0.09), -PI / 2,
                                         WHITE_, 2.2, 0.12) for j in range(-2, 4)])
    later["v_lab"] = tex("V", 40, WHITE_).move_to(P(-2.1, Y293 - 0.36))
    # faint drop lines: the tail K_{>=h} starts right under the basis vector e_h
    later["drops"] = VGroup(*[DashedLine(P(X293[h], Y293 - 0.36), P(X293[h], LAD[h] + 0.19),
                                         dash_length=0.06) for h in LAD]).set_stroke(GREY_, 1.3, opacity=0.5)
    later["b1"] = txt("every tail is S-invariant", 24, GREEN_).move_to(P(0.2, YB293))
    later["b2"] = tex(r"VS = SV,\quad V K_{\ge h} \not\subseteq K_{\ge h}", 32, WHITE_).move_to(P(0.2, YB293))
    # precise wording: only the trivial subspaces 0 and H are hyperinvariant
    later["b3"] = txt("no nontrivial hyperinvariant subspace", 22, RED_, weight=SEMIBOLD).move_to(P(0.1, YB293))
    later["b4"] = txt("invariant subspace problem: still open", 22, GREY_).move_to(P(0.1, YB293 - 0.42))
    vis.later = later
    return vis


def _swap(old, new):
    """Cross-fade two labels that both live inside the card (no remover animations)."""
    return [old.animate(rate_func=_delayed(0.0, 0.35)).set_opacity(0),
            FadeIn(new, shift=UP * 0.12, rate_func=_delayed(0.3, 0.75))]


def anim_293(scene, mob, T):
    L = mob.later
    bars = [_bring(mob, b, below=True) for b in L["bars"]]
    labs = [_bring(mob, b) for b in L["labs"]]
    checks = [_bring(mob, b) for b in L["checks"]]
    drops = _bring(mob, L["drops"], below=True)
    b1 = _bring(mob, L["b1"])
    flash = mob.s_arcs.copy().set_stroke(YELLOW_, 4)
    # 1. shift S moves e_j -> e_{j+1}: every tail K_{>=h} is invariant (a ladder)
    scene.play(ShowPassingFlash(flash, time_width=0.5),
               at(mob, Create(drops, lag_ratio=0.18), 0.0, 0.7),
               LaggedStart(*[AnimationGroup(GrowFromEdge(b, RIGHT), FadeIn(lb, shift=RIGHT * 0.1),
                                            group=mob)
                             for b, lb in zip(bars, labs)], lag_ratio=0.18, group=mob),
               LaggedStart(*[Create(c) for c in checks], lag_ratio=0.15, group=mob),
               FadeIn(b1, shift=UP * 0.1), run_time=0.34 * T)
    # 2. a commuting operator V pushes every tail one rung down
    v_arcs = _bring(mob, L["v_arcs"])
    v_lab = _bring(mob, L["v_lab"])
    segs = [_bring(mob, s, below=True) for s in L["segs"]]
    crosses = [_bring(mob, c) for c in L["crosses"]]
    for c in crosses:
        mob.remove(c)
    b2 = _bring(mob, L["b2"])
    scene.play(AnimationGroup(
        AnimationGroup(Create(v_arcs, lag_ratio=0.1), FadeIn(v_lab), group=mob),
        AnimationGroup(LaggedStart(*[GrowFromEdge(s, RIGHT) for s in segs], lag_ratio=0.12, group=mob),
                       *[Transform(ck, cr) for ck, cr in zip(checks, crosses)],
                       *_swap(b1, b2), group=mob),
        lag_ratio=0.45, group=mob), run_time=0.33 * T)
    # 3. no rung survives every commuting operator (the classical problem is untouched)
    b3 = _bring(mob, L["b3"])
    b4 = _bring(mob, L["b4"])
    flash2 = v_arcs.copy().set_stroke(RED_, 4)
    scene.play(*_swap(b2, b3), ShowPassingFlash(flash2, time_width=0.5),
               LaggedStart(*[Indicate(c, color=RED_, scale_factor=1.3) for c in checks],
                           lag_ratio=0.1, group=mob),
               FadeIn(b4, rate_func=_delayed(0.3, 0.6)),
               run_time=0.33 * T)


# ====================================================================== 304 Hilbert–Smith
def blob_points(c, rx, ry, n=90, a=0.08, b=0.06, ph=0.5, scale=1.0):
    t = np.linspace(0, TAU, n, endpoint=False)
    rr = 1 + a * np.sin(3 * t + ph) + b * np.cos(2 * t)
    return [np.array(c, float) + scale * P(rx * q * np.cos(s), ry * q * np.sin(s)) for q, s in zip(rr, t)]


def blob_at(c, rx, ry, t, scale, a=0.08, b=0.06, ph=0.5):
    q = 1 + a * np.sin(3 * t + ph) + b * np.cos(2 * t)
    return np.array(c, float) + scale * P(rx * q * np.cos(t), ry * q * np.sin(t))


def smooth_closed(pts):
    m = VMobject()
    m.set_points_smoothly([*pts, pts[0]])
    return m


def padic_tree(top, width, levels=3, dy=0.3, p=2, node_r=0.035, w=1.3):
    nb = p ** levels
    xs = [np.array([top[0] - width / 2 + i * width / (nb - 1)]) for i in range(nb)]
    layers = [[x[0] for x in xs]]
    for _ in range(levels):
        prev = layers[-1]
        layers.append([float(np.mean(prev[i * p:(i + 1) * p])) for i in range(len(prev) // p)])
    layers = layers[::-1]                       # root first
    edges, nodes = VGroup(), VGroup()
    for k, layer in enumerate(layers):
        y = top[1] - k * dy
        for i, x in enumerate(layer):
            nodes.add(Dot(P(x, y), radius=node_r * (1.25 if k == 0 else 1.0), color=WHITE_))
            if k > 0:
                px = layers[k - 1][i // p]
                edges.add(Line(P(px, y + dy), P(x, y)))
    edges.set_stroke(GREY_, w)
    return VGroup(edges, nodes)


def icon_304():
    c = P(-0.72, 0)
    blob = smooth_closed(blob_points(c, 0.62, 0.42)).set_stroke(ACC, 2.0).set_fill(ACC, 0.10)
    orbs = VGroup(*[smooth_closed(blob_points(c, 0.62, 0.42, scale=s)) for s in (0.66, 0.34)])
    orbs.set_stroke(WHITE_, 1.1, opacity=0.6)
    dts = VGroup(*[Dot(blob_at(c, 0.62, 0.42, t, s), radius=0.035, color=ACC)
                   for s, t0 in ((0.66, 0.3), (0.34, 1.9)) for t in (t0, t0 + PI)])
    fix = Dot(c, radius=0.03, color=WHITE_)
    tree = padic_tree(P(0.82, 0.36), 0.9, 3, 0.24, 2, 0.028, 1.1)
    zp = tex(r"\mathbb{Z}_p", 24, WHITE_).move_to(P(0.3, 0.36))
    x = xmark(P(0.82, 0.0), 0.3, RED_, 2.6)
    return VGroup(blob, orbs, dts, fix, tree, zp, x)


B304 = dict(c0=P(0.0, 0.3), c1=P(0.1, 1.08), rx=2.12, ry=0.92, orbits=(0.74, 0.5, 0.26))


def _clip01(x):
    return min(1.0, max(0.0, x))


def _delayed(t0, t1, f=smooth):
    return lambda t: f(_clip01((t - t0) / (t1 - t0)))


def at(mob, anim, t0, t1):
    """Run `anim` (keeping its own easing and lag) during the fraction [t0, t1] of the
    enclosing play. group=mob keeps the card intact in the scene list."""
    return AnimationGroup(anim, group=mob, rate_func=lambda t: _clip01((t - t0) / (t1 - t0)))


def big_304():
    vis = VGroup(_ref())
    vis.ref = vis[0]
    c, rx, ry = B304["c0"], B304["rx"], B304["ry"]
    blob = smooth_closed(blob_points(c, rx, ry, 120)).set_stroke(ACC, 3.0).set_fill(ACC, 0.10)
    orbs = VGroup(*[smooth_closed(blob_points(c, rx, ry, 120, scale=s)) for s in B304["orbits"]])
    orbs.set_stroke(WHITE_, 1.5, opacity=0.45)
    dts = VGroup(*[Dot(radius=0.065, color=ACC) for _ in range(9)])
    fix = Dot(c, radius=0.05, color=WHITE_)
    mlab = tex("M", 40, WHITE_).move_to(c + P(-2.35, 0.85))
    top = VGroup(blob, orbs, fix, mlab)
    vis.add(top, dts)
    vis.top, vis.orbs, vis.dts = top, orbs, dts
    _place_304(vis, 0.0, 0.0, design=True)
    later = {}
    lie = VGroup(txt("Lie group", 24, GREEN_, weight=SEMIBOLD), tick(ORIGIN, 0.22, GREEN_, 3.4))
    lie.arrange(RIGHT, buff=0.12).move_to(c + P(1.45, 1.06))
    later["lie"] = lie
    later["tree"] = padic_tree(P(-1.6, -0.62), 2.0, 3, 0.42, 2, 0.05, 2.0)
    later["zp"] = tex(r"\mathbb{Z}_p", 40, WHITE_).move_to(P(-2.35, -0.62))
    later["arr"] = arrow(P(-1.6, -0.45), P(-1.6, 0.36), WHITE_, 2.6, 0.18)
    later["x"] = xmark(P(-1.6, -0.06), 0.22, RED_, 5)
    later["no"] = txt("no faithful action", 24, RED_, weight=SEMIBOLD).move_to(P(-0.1, -0.3)) \
        .align_to(P(-1.22, 0), LEFT)
    later["every"] = txt("in every dimension", 24, GREY_).move_to(P(1.3, -1.02))
    dim = MathTex(r"n = ", r"1,2,3,", r"\,4,5,6,\dots", font_size=34)
    dim[0].set_color(WHITE_)
    dim[1].set_color(GREY_)
    dim[2].set_color(ACC)
    later["dim"] = dim.next_to(later["every"], DOWN, buff=0.22)
    later["known"] = txt("known", 22, GREY_).next_to(dim[1], DOWN, buff=0.12)
    later["new"] = txt("new claim", 22, ACC).next_to(dim[2], DOWN, buff=0.12)
    vis.later = later
    return vis


def _place_304(mob, phase, f, design=False):
    c = B304["c0"] + f * (B304["c1"] - B304["c0"])
    rx, ry = B304["rx"], B304["ry"]
    i = 0
    for oi, s in enumerate(B304["orbits"]):
        for j in range(3):
            t = phase + TAU * j / 3 + 0.7 * oi
            p = blob_at(c, rx, ry, t, s)
            mob.dts[i].move_to(p if design else _map(mob, p))
            i += 1


def anim_304(scene, mob, T):
    L = mob.later
    rate = 0.6                                    # radians per second of the circle action
    st = {"ph": 0.0}

    def flow(dur, ff=lambda a: 0.0):
        ph0 = st["ph"]
        st["ph"] = ph0 + rate * dur
        return UpdateFromAlphaFunc(mob.dts, lambda m, a: _place_304(mob, ph0 + rate * dur * a, ff(a)),
                                   rate_func=linear)

    # 1. a group acting faithfully on a manifold, smoothly, like rotations: a Lie group
    lie = _bring(mob, L["lie"])
    mob.remove(lie)
    mob.top.add(lie)                              # moves with the manifold
    d1 = 0.36 * T
    scene.play(flow(d1), LaggedStart(*[Indicate(o, color=ACC, scale_factor=1.0) for o in mob.orbs],
                                     lag_ratio=0.3, group=mob),
               FadeIn(lie, shift=UP * 0.1, rate_func=_delayed(0.35, 0.75)), run_time=d1)
    # 2. make room; the p-adic integers cannot act faithfully
    tree, zp, arr, x, no = [_bring(mob, L[k]) for k in ("tree", "zp", "arr", "x", "no")]
    d2 = 0.42 * T
    mv = _delayed(0.0, 0.3)
    k = mob.ref.width / BIG_W
    scene.play(flow(d2, mv), mob.top.animate(rate_func=mv).shift(k * (B304["c1"] - B304["c0"])),
               at(mob, Create(tree[0], lag_ratio=0.05), 0.25, 0.6),
               at(mob, FadeIn(tree[1], lag_ratio=0.05), 0.3, 0.62),
               FadeIn(zp, rate_func=_delayed(0.3, 0.55)),
               GrowArrow(arr, rate_func=_delayed(0.45, 0.68)),
               at(mob, Create(x), 0.7, 0.85),
               FadeIn(no, shift=RIGHT * 0.1, rate_func=_delayed(0.72, 0.95)), run_time=d2)
    # 3. claimed in every dimension (1-3 were already known)
    ev, dim, kn, nw = [_bring(mob, L[k]) for k in ("every", "dim", "known", "new")]
    d3 = 0.22 * T
    scene.play(flow(d3, lambda a: 1.0), FadeIn(ev, shift=UP * 0.1), Write(dim), FadeIn(kn), FadeIn(nw),
               run_time=d3)


# ====================================================================== 325 Crouzeix
# A 3x3 non-normal matrix; its numerical range W(A) is an egg-shaped convex region with a
# corner at the normal-ish eigenvalue 1.463-0.398i.  All numbers on screen are computed here.
CRZ_A = np.array([[0, 1.319, 0.278], [0, -0.227 - 0.068j, 0.385], [0, 0, 1.463 - 0.398j]])


def _wbound(A, n=720):
    pts = []
    for th in np.linspace(0, TAU, n, endpoint=False):
        H = (np.exp(-1j * th) * A + np.exp(1j * th) * A.conj().T) / 2
        _, v = np.linalg.eigh(H)
        x = v[:, -1]
        pts.append(x.conj() @ A @ x)
    return np.array(pts)


CRZ_B = _wbound(CRZ_A)
CRZ_EIG = np.linalg.eigvals(CRZ_A)
_I2 = np.eye(2)
_N = [np.array([[0, 0.45], [0, 0]]), np.array([[0, 0], [0, -0.6 + 0.5j]]), np.array([[0, 0], [0.5, 0]])]


def _crz_coefs(s):
    """Path of polynomials P_s(z) = B0 + B1 z + B2 z^2 with 2x2 matrix coefficients:
    first scalar ones (B_j = b_j I), then genuinely matrix-valued ones."""
    l3 = CRZ_A[2, 2]
    u = min(s / 0.5, 1.0)
    z0 = -0.25 + 0.35 * np.sin(np.pi * u) * np.exp(2j * np.pi * u)
    sc = [z0 * l3, -(z0 + l3), 1.0]
    w = 0.0 if s < 0.5 else np.sin(np.pi * (s - 0.5)) ** 2
    return [sc[j] * _I2 + w * _N[j] for j in range(3)]


def _crz_path(n=241):
    A2 = CRZ_A @ CRZ_A
    pw = [np.eye(3), CRZ_A, A2]
    S = np.linspace(0, 1, n)
    R = []
    for s in S:
        Bs = _crz_coefs(s)
        PA = sum(np.kron(pw[j], Bs[j]) for j in range(3))           # P[A] = sum A^j (x) B_j
        Z = Bs[0][None] + Bs[1][None] * CRZ_B[:, None, None] + Bs[2][None] * (CRZ_B ** 2)[:, None, None]
        # z -> ||P(z)|| is subharmonic, so its max over the convex set W(A) is on the boundary
        R.append(np.linalg.norm(PA, 2) / np.linalg.norm(Z, ord=2, axis=(1, 2)).max())
    return S, np.array(R)


CRZ_S, CRZ_R = _crz_path()
assert CRZ_R.max() <= 2.0


def crz_region(O, k, stroke=2.0, fill=0.16, every=4):
    pts = [np.array(O, float) + k * P(z.real, z.imag) for z in CRZ_B[::every]]
    return Polygon(*pts).set_stroke(ACC, stroke).set_fill(ACC, fill)


def icon_325():
    O, k = P(-0.95, 0.0), 0.52
    ax = VGroup(Line(P(-1.45, O[1]), P(-0.05, O[1])), Line(P(O[0], -0.45), P(O[0], 0.45)))
    ax.set_stroke(GREY_, 1.0, opacity=0.55)
    reg = crz_region(O, k, 2.0, 0.2)
    eig = VGroup(*[Dot(O + k * P(z.real, z.imag), radius=0.035, color=WHITE_) for z in CRZ_EIG])
    base = -0.42
    g1 = Rectangle(width=0.2, height=0.36).set_stroke(width=0).set_fill(GREY_, 0.9)
    g1.move_to(P(0.5, base + 0.18))
    g2 = Rectangle(width=0.2, height=0.58).set_stroke(width=0).set_fill(ACC, 0.95)
    g2.move_to(P(0.8, base + 0.29))
    bl = Line(P(0.3, base), P(1.0, base)).set_stroke(GREY_, 1.2)
    ceil = DashedLine(P(0.3, base + 0.72), P(1.0, base + 0.72), dash_length=0.06).set_stroke(WHITE_, 1.6)
    two = tex(r"2\times", 22, WHITE_).next_to(ceil, RIGHT, buff=0.06)
    return VGroup(ax, reg, eig, bl, g1, g2, ceil, two)


C325 = dict(O=P(-0.98, 1.07), k=1.15, x0=-0.55, L=1.3, y1=-1.2, y2=-1.75, bh=0.3)


def big_325():
    vis = VGroup(_ref())
    vis.ref = vis[0]
    O, k = C325["O"], C325["k"]
    ax = VGroup(Line(P(-2.3, O[1]), P(1.1, O[1])), Line(P(O[0], 0.0), P(O[0], 2.12)))
    ax.set_stroke(GREY_, 1.4, opacity=0.55)
    re_l = tex(r"\mathbb{C}", 30, GREY_).move_to(P(-2.3, 1.95))
    eig = VGroup(*[Dot(O + k * P(z.real, z.imag), radius=0.065, color=WHITE_) for z in CRZ_EIG])
    vis.add(ax, re_l, eig)
    later = {}
    rng = np.random.default_rng(7)
    Z = rng.normal(size=(150, 3)) + 1j * rng.normal(size=(150, 3))
    Z /= np.linalg.norm(Z, axis=1, keepdims=True)
    vals = np.einsum("ni,ij,nj->n", Z.conj(), CRZ_A, Z)               # x* A x with |x| = 1
    later["cloud"] = VGroup(*[Dot(O + k * P(z.real, z.imag), radius=0.022, color=ACC)
                              .set_opacity(0.75) for z in vals])
    later["reg"] = crz_region(O, k, 3.0, 0.16, every=3)
    later["wlab"] = tex("W(A)", 40, ACC).move_to(P(1.45, 1.62))
    elab = txt("eigenvalues", 22, GREY_).move_to(P(1.85, 0.38))
    src = elab.get_left() + P(-0.08, 0.03)
    leads = VGroup()
    for d in eig:
        v = d.get_center() - src
        leads.add(Line(src, src + v * (1 - 0.1 / np.linalg.norm(v))))
    leads.set_stroke(GREY_, 1.3, opacity=0.8)
    later["eiglab"] = VGroup(leads, elab)
    later["formula"] = tex(r"p(z) = B_0 + B_1 z + B_2 z^2,\quad B_j \in M_m(\mathbb{C})", 30, WHITE_) \
        .move_to(P(0.0, -0.3))
    x0, Lb, y1, y2, bh = C325["x0"], C325["L"], C325["y1"], C325["y2"], C325["bh"]
    r0 = float(CRZ_R[0])
    later["gbar"] = Rectangle(width=Lb, height=bh).set_stroke(width=0).set_fill(GREY_, 0.85) \
        .move_to(P(x0 + Lb / 2, y1))
    later["sbar"] = Rectangle(width=r0 * Lb, height=bh).set_stroke(width=0).set_fill(ACC, 0.95) \
        .move_to(P(x0 + r0 * Lb / 2, y2))
    later["glab"] = tex(r"\max_{W(A)} \|p\|", 30, GREY_)
    later["glab"].move_to(P(-1.5, y1 - 0.02)).align_to(P(x0 - 0.15, 0), RIGHT)
    later["slab"] = tex(r"\| p(A) \|", 32, WHITE_).move_to(P(-1.5, y2)).align_to(P(x0 - 0.15, 0), RIGHT)
    later["ceil"] = DashedLine(P(x0 + 2 * Lb, y1 + 0.3), P(x0 + 2 * Lb, y2 - 0.3),
                               dash_length=0.09).set_stroke(YELLOW_, 3)
    later["two"] = tex(r"2\times", 32, YELLOW_).next_to(later["ceil"], UP, buff=0.08)
    vis.later = later
    return vis


def anim_325(scene, mob, T):
    L = mob.later
    cloud = _bring(mob, L["cloud"], below=True)
    reg = _bring(mob, L["reg"], below=True)
    wlab = _bring(mob, L["wlab"])
    eiglab = _bring(mob, L["eiglab"])
    # 1. the numerical range: all values x*Ax with |x| = 1; it contains the eigenvalues
    scene.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in cloud], lag_ratio=0.012, group=mob),
               Create(reg, rate_func=_delayed(0.3, 1.0)),
               FadeIn(wlab, rate_func=_delayed(0.5, 1.0)),
               FadeIn(eiglab, rate_func=_delayed(0.6, 1.0)), run_time=0.27 * T)
    # 2. plug the matrix into a polynomial (coefficients may be matrices too)
    formula, sbar, slab, gbar, glab = [_bring(mob, L[n]) for n in ("formula", "sbar", "slab", "gbar", "glab")]
    scene.play(at(mob, Write(formula), 0.0, 0.45),
               GrowFromEdge(sbar, LEFT, rate_func=_delayed(0.35, 0.7)),
               FadeIn(slab, rate_func=_delayed(0.35, 0.6)),
               GrowFromEdge(gbar, LEFT, rate_func=_delayed(0.6, 0.95)),
               FadeIn(glab, rate_func=_delayed(0.6, 0.85)),
               cloud.animate.set_opacity(0.35), run_time=0.27 * T)
    # 3. at most twice the max over W(A): vary p, the blue bar never crosses 2x
    ceil, two = _bring(mob, L["ceil"]), _bring(mob, L["two"])
    Lb = C325["L"] * mob.ref.width / BIG_W
    left = sbar.get_left()

    def upd(m, a):
        r = float(np.interp(a, CRZ_S, CRZ_R))
        m.stretch_to_fit_width(r * Lb)
        m.move_to(left + RIGHT * r * Lb / 2)

    scene.play(at(mob, Create(ceil), 0.0, 0.18), FadeIn(two, rate_func=_delayed(0.05, 0.2)),
               UpdateFromAlphaFunc(sbar, upd, rate_func=_delayed(0.12, 1.0)), run_time=0.46 * T)


# ====================================================================== the 8 rapid-fire icons
def icon_289():
    """Strong Kadison–Kastler: two close algebras are conjugate by a unitary u ~ 1."""
    c = P(-0.62, 0)
    g1 = coord_frame(0.42, 3, 1.1, 1.8, 0.7)
    g1[1].set_stroke(ACC, 2.0, opacity=1)
    g1[0].set_stroke(ACC, 1.1, opacity=0.6)
    g1.move_to(c)
    g2 = coord_frame(0.42, 3, 1.0, 1.6, 0.5).rotate(0.16).move_to(c + P(0.05, 0.03))
    g2[1].set_stroke(WHITE_, 1.5, opacity=0.9)
    u_arr = arc_arrow(c + 0.68 * rotate_vector(RIGHT, 0.12), c + 0.68 * rotate_vector(RIGHT, 0.8), 0.6,
                      WHITE_, 1.6, 0.09)
    lab1 = tex(r"N = u\,M\,u^*", 26, WHITE_)
    lab2 = tex(r"u \approx 1", 26, ACC)
    labs = VGroup(lab1, lab2).arrange(DOWN, buff=0.14, aligned_edge=LEFT).move_to(P(0.92, 0))
    return VGroup(g1, g2, u_arr, labs)


def icon_290():
    """Connes' bicentralizer: B_phi(M) is trivial (= C) for type III_1 factors."""
    c = P(-0.75, 0)
    outer = Circle(0.46).move_to(c).set_stroke(ACC, 2.0).set_fill(ACC, 0.08)
    inner = DashedVMobject(Circle(0.25).move_to(c), num_dashes=14).set_stroke(GREY_, 1.4)
    arrs = VGroup(*[arrow(c + 0.25 * rotate_vector(RIGHT, a), c + 0.09 * rotate_vector(RIGHT, a),
                          WHITE_, 1.4, 0.06) for a in (PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4)])
    ctr = Dot(c, radius=0.04, color=WHITE_)
    mlab = tex("M", 24, ACC).move_to(c + P(-0.5, 0.36))
    flow = arc_arrow(c + 0.58 * rotate_vector(RIGHT, 0.35), c + 0.58 * rotate_vector(RIGHT, 1.25),
                     0.9, GREY_, 1.4, 0.07)
    eq = tex(r"B_\varphi = \mathbb{C}", 32, WHITE_).move_to(P(0.72, 0))
    return VGroup(outer, inner, arrs, ctr, mlab, flow, eq)


def icon_296():
    """Generator problem: one operator T generates the whole II_1 factor M."""
    tdot = Dot(P(-1.2, 0), radius=0.07, color=ACC)
    tl = tex("T", 24, ACC).next_to(tdot, UP, buff=0.07)
    frame = RoundedRectangle(width=1.5, height=0.86, corner_radius=0.1).move_to(P(0.6, 0))
    frame.set_stroke(GREY_, 1.4).set_fill(ACC, 0.06)
    pts = [P(0.05 + 0.275 * i, -0.24 + 0.24 * j) for j in range(3) for i in range(5)]
    nodes = VGroup(*[Dot(p, radius=0.032, color=WHITE_) for p in pts])
    fan = VGroup(*[Line(P(-1.13, 0), p) for p in pts]).set_stroke(ACC, 0.9, opacity=0.45)
    ml = tex("M", 24, WHITE_).next_to(frame, RIGHT, buff=0.08).shift(UP * 0.25)
    return VGroup(fan, frame, nodes, tdot, tl, ml)


def icon_285():
    """Baum–Connes: the assembly map mu is not an isomorphism (counterexample)."""
    vs = [P(-1.45, -0.32), P(-1.05, 0.38), P(-0.62, -0.3), P(-0.98, -0.02), P(-1.38, 0.18), P(-0.66, 0.3)]
    tris = [(0, 3, 4), (3, 1, 4), (0, 2, 3), (3, 2, 5), (3, 5, 1)]
    mesh = VGroup(*[Polygon(vs[a], vs[b], vs[c]) for a, b, c in tris])
    mesh.set_stroke(WHITE_, 1.3, opacity=0.85).set_fill(WHITE_, 0.05)
    mdots = VGroup(*[Dot(v, radius=0.03, color=WHITE_) for v in vs])
    ar = arrow(P(-0.42, 0), P(0.42, 0), GREY_, 2.0, 0.12)
    mu = tex(r"\mu", 26, WHITE_).next_to(ar, UP, buff=0.04)
    x = xmark(P(0.0, 0), 0.13, RED_, 3)
    grid = VGroup(*[Dot(P(0.78 + 0.22 * i, -0.22 + 0.22 * j), radius=0.035, color=ACC)
                    for i in range(3) for j in range(3)])
    brl = VMobject().set_points_as_corners([P(0.72, 0.36), P(0.62, 0.36), P(0.62, -0.36), P(0.72, -0.36)])
    brr = VMobject().set_points_as_corners([P(1.12, 0.36), P(1.22, 0.36), P(1.22, -0.36), P(1.12, -0.36)])
    br = VGroup(brl, brr).set_stroke(ACC, 1.6)
    return VGroup(mesh, mdots, ar, mu, x, grid, br)


def mini_globe(c, r=0.15, color=ACC, width=1.8):
    """A tiny sphere (outline + equator + meridian) used as a 'survives' mark."""
    c = np.array(c, float)
    out = Circle(r).move_to(c).set_stroke(color, width).set_fill(color, 0.22)
    eq = Ellipse(width=2 * r, height=0.55 * r).move_to(c).set_stroke(color, width * 0.6, opacity=0.9)
    mer = Ellipse(width=0.55 * r, height=2 * r).move_to(c).set_stroke(color, width * 0.6, opacity=0.9)
    return VGroup(out, eq, mer)


def icon_309():
    """Kervaire invariant at p = 3: classes j = 0, 2, 3 survive (stems 10, 106, 322);
    j = 1 (stem 34) and j >= 4 (970, ...) die.  Survivors are drawn as small spheres (these
    are elements of the stable homotopy groups of spheres); stems are readable numbers."""
    stems = [10, 34, 106, 322, 970]
    alive = [True, False, True, True, False]
    # lay the stem numbers out by their own widths (tile width is the binding constraint:
    # this keeps them at ~22pt on screen instead of ~13pt)
    labs = VGroup(*[txt(str(s), 24, WHITE_ if ok else GREY_, weight=MEDIUM if ok else NORMAL)
                    for s, ok in zip(stems, alive)]).arrange(RIGHT, buff=0.12)
    labs.move_to(P(0, -0.44), aligned_edge=DOWN)
    marks = VGroup()
    for lb, ok in zip(labs, alive):
        x = lb.get_center()[0]
        marks.add(mini_globe(P(x, 0.2), 0.16) if ok else xmark(P(x, 0.2), 0.1, RED_, 3.0))
    ell = dots_ellipsis(P(labs.get_right()[0] + 0.12, 0.2), r=0.024, gap=0.06)
    base = Line(P(labs.get_left()[0] - 0.06, -0.06), P(ell.get_right()[0], -0.06)) \
        .set_stroke(GREY_, 1.2, opacity=0.6)
    return VGroup(base, marks, labs, ell)


def _trefoil_pieces(n=720, gap=0.17):
    t = np.linspace(0, TAU, n, endpoint=False)
    X = np.stack([np.sin(t) + 2 * np.sin(2 * t), np.cos(t) - 2 * np.cos(2 * t)], 1)
    A, B = X, np.roll(X, -1, axis=0)
    hits = []
    for i in range(n):
        a, b = A[i], B[i]
        j = np.arange(i + 2, n)
        if i == 0:
            j = j[j != n - 1]
        c, d = A[j], B[j]
        r, s = b - a, d - c
        den = r[0] * s[:, 1] - r[1] * s[:, 0]
        ok = np.abs(den) > 1e-12
        qa = c - a
        u = np.where(ok, (qa[:, 0] * s[:, 1] - qa[:, 1] * s[:, 0]) / np.where(ok, den, 1), -1)
        v = np.where(ok, (qa[:, 0] * r[1] - qa[:, 1] * r[0]) / np.where(ok, den, 1), -1)
        for jj in np.nonzero((u >= 0) & (u < 1) & (v >= 0) & (v < 1))[0]:
            hits.append((t[i] + u[jj] * TAU / n, t[j[jj]] + v[jj] * TAU / n))
    params = sorted([p for h in hits for p in h])
    unders = params[1::2]                          # alternate over / under along the curve
    pieces = []
    for k in range(len(unders)):
        a = unders[k] + gap
        b = (unders[k + 1] if k + 1 < len(unders) else unders[0] + TAU) - gap
        pieces.append((a, b))
    return pieces


TREFOIL = _trefoil_pieces()


def trefoil(scale=0.15, color=ACC, width=2.2):
    g = VGroup()
    for a, b in TREFOIL:
        g.add(ParametricFunction(lambda s: P(np.sin(s) + 2 * np.sin(2 * s), np.cos(s) - 2 * np.cos(2 * s)),
                                 t_range=[a, b, 0.03]))
    g.set_stroke(color, width)
    g.scale(scale, about_point=ORIGIN)
    return g


def icon_306():
    """Purely cosmetic surgery: distinct slopes give non-homeomorphic manifolds."""
    k = trefoil(0.155, ACC, 2.4).move_to(P(-1.0, 0))
    kl = tex("K", 27, ACC).move_to(P(-1.64, 0.38))
    eq = tex(r"S^3_{r}(K)\ \not\cong\ S^3_{r'}(K)", 25, WHITE_).move_to(P(0.5, 0.12))
    sub = tex(r"r \ne r'", 26, GREY_).next_to(eq, DOWN, buff=0.14)
    return VGroup(k, kl, eq, sub)


def icon_315():
    """Singer conjecture in 4D: L^2-Betti numbers vanish outside the middle degree."""
    s = 0.2
    tiles = VGroup()
    for i in range(5):
        for j in range(4):
            sq = Square(s).move_to(P(-1.5 + s * i, -0.3 + s * j))
            tiles.add(sq)
    tiles.set_stroke(GREY_, 1.0, opacity=0.7)
    tiles[7].set_fill(ACC, 0.55).set_stroke(ACC, 1.4, opacity=1)
    base_y = -0.32
    bl = Line(P(-0.2, base_y), P(1.35, base_y)).set_stroke(GREY_, 1.2)
    xs = [-0.02 + 0.32 * i for i in range(5)]
    bars, labs = VGroup(), VGroup()
    for i, x in enumerate(xs):
        if i == 2:
            bars.add(Rectangle(width=0.2, height=0.6).set_stroke(ACC, 1.4).set_fill(ACC, 0.6)
                     .move_to(P(x, base_y + 0.3)))
        else:
            bars.add(Line(P(x - 0.1, base_y + 0.02), P(x + 0.1, base_y + 0.02)).set_stroke(WHITE_, 3))
        labs.add(txt(str(i), 23, WHITE_ if i == 2 else GREY_).move_to(P(x, base_y - 0.2)))
    bt = tex(r"b^{(2)}_k(\widetilde M^4)", 25, WHITE_).move_to(P(0.6, 0.44)).align_to(P(-0.12, 0), LEFT)
    return VGroup(tiles, bl, bars, labs, bt)


def icon_322():
    """Tingley: an isometry of unit spheres extends to a linear isometry."""
    hx = RegularPolygon(6, radius=0.44).rotate(PI / 6)
    left = hx.copy().move_to(P(-0.88, 0)).set_stroke(ACC, 2.0).set_fill(ACC, 0.08)
    A = lin3([[0.9, 0.32], [-0.18, 0.86]])
    right_pts = [A @ v for v in hx.get_vertices()]
    right = Polygon(*right_pts).shift(P(0.92, 0)).set_stroke(WHITE_, 1.8).set_fill(WHITE_, 0.05)
    verts = hx.get_vertices()

    def onhex(i, f):
        return verts[i] + f * (verts[(i + 1) % 6] - verts[i])

    picks = [(1, 0.0), (5, 0.5), (4, 0.0)]
    lp = [onhex(i, f) + P(-0.88, 0) for i, f in picks]
    rp = [A @ onhex(i, f) + P(0.92, 0) for i, f in picks]
    ldots = VGroup(*[Dot(p, radius=0.04, color=ACC) for p in lp])
    rdots = VGroup(*[Dot(p, radius=0.04, color=WHITE_) for p in rp])
    rays = VGroup(*[DashedLine(P(0.92, 0), p, dash_length=0.04) for p in rp]).set_stroke(GREY_, 1.0)
    a1 = arc_arrow(lp[0] + P(0.07, 0.03), rp[0] + P(-0.07, 0.03), -0.5, GREY_, 1.5, 0.09)
    a2 = arc_arrow(lp[2] + P(0.07, -0.03), rp[2] + P(-0.07, -0.03), 0.5, GREY_, 1.5, 0.09)
    tl = tex("T", 24, WHITE_).next_to(a1, UP, buff=0.04)
    return VGroup(left, right, rays, ldots, rdots, a1, a2, tl)


# ====================================================================== scene
ICONS = {"288": icon_288, "293": icon_293, "304": icon_304, "325": icon_325,
         "289": icon_289, "290": icon_290, "296": icon_296, "285": icon_285,
         "309": icon_309, "306": icon_306, "315": icon_315, "322": icon_322}
FEATURES = {"288": (big_288, anim_288), "293": (big_293, anim_293),
            "304": (big_304, anim_304), "325": (big_325, anim_325)}


def _tiles():
    spec = json.loads((VIDEO / "data" / "grids.json").read_text())["c8_grid"]
    out = []
    for d in spec:
        t = dict(num=d["num"], name=d["name"], verdict=d["verdict"], icon=ICONS[d["num"]])
        if d.get("caption"):
            big, anim = FEATURES[d["num"]]
            t["feature"] = dict(caption=d["caption"], big=big, animate=anim)
        out.append(t)
    return out


class C8Grid(GridScene):
    CHAPTER = "oa"
    TILES = _tiles()
