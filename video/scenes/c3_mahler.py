import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import numpy as np
from scipy.spatial import ConvexHull

# Mahler volume-product spotlight (family 087).
#
# Geometry is exact: every shape K is stored by its support points x_K(u_j) and
# support function h_K(u_j) at N = 360 equally spaced unit normals u_j.
#   * Linear interpolation of (x_K, h_K) between two shapes is exactly the
#     Minkowski combination (1-l)K + lL, so every morph stays convex.
#   * The polar body has radial function 1/h_K, i.e. boundary points u_j / h_K(u_j).
#     For the square, triangle, hexagon, pentagon the polar's vertices sit at
#     sampled directions, so areas are exact (8, 27/4, 9 ...); the disk is a
#     360-gon (product 9.8686 -> "9.87").
#   * Stretch M = R diag(t,1): K -> M K, K° -> M^{-T} K° = R diag(1/t,1) K°.

ACC = TEAL_
KC = TEAL_      # the body K
PC = PINK_      # its polar K°

N = 360
ANG = np.arange(N) * 2 * np.pi / N
U = np.stack([np.cos(ANG), np.sin(ANG)], 1)

P0 = np.array([-3.55, 0.35, 0.0])   # origin of the left plane (screen)
S = 1.45                            # screen units per plane unit


def _poly(verts):
    V = np.array(verts, float)
    d = U @ V.T
    return V[d.argmax(1)], d.max(1)


def _disk(r=1.0):
    return U * r, np.full(N, r)


def _reg(n, r, ph):
    return [(r * np.cos(ph + 2 * np.pi * k / n), r * np.sin(ph + 2 * np.pi * k / n)) for k in range(n)]


def _area(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


_irr = [(1.25, -0.3), (1.15, 0.75), (-0.6, 1.05)]
KEYFRAMES = [
    _poly([(1, 1), (-1, 1), (-1, -1), (1, -1)]),       # 0 square        -> 8
    _disk(1.0),                                         # 1 disk          -> pi^2
    _poly(_reg(6, 1.12, 0.0)),                          # 2 hexagon       -> 9
    _poly(_reg(5, 1.18, np.pi / 2)),                    # 3 pentagon      -> 8.64
    _poly(_irr + [(-a, -b) for a, b in _irr]),          # 4 sym. hexagon  -> 8.86
    _poly([(1, 1), (-1, 1), (-1, -1), (1, -1)]),       # 5 square        -> 8
    _poly(_reg(3, np.sqrt(2), np.pi / 2)),              # 6 triangle (centroid at 0) -> 27/4
]


def scr(p):
    p = np.atleast_2d(p)
    return np.c_[P0[0] + S * p[:, 0], P0[1] + S * p[:, 1], np.zeros(len(p))]


# ------------------------------------------------------------------ scale
SX = 1.05


def Y(v):
    return 0.15 + (v - 8.0) * 0.92


# ------------------------------------------------------------------ 3D icons
def _rot3(a, tilt):
    ca, sa, ct, st = np.cos(a), np.sin(a), np.cos(tilt), np.sin(tilt)
    Ry = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])
    Rx = np.array([[1, 0, 0], [0, ct, -st], [0, st, ct]])
    return Rx @ Ry


def _poly3(verts):
    V = np.array(verts, float)
    V = V / np.linalg.norm(V, axis=1).max()
    D = np.linalg.norm(V[:, None] - V[None], axis=2)
    dmin = D[D > 1e-9].min()
    E = [(i, j) for i in range(len(V)) for j in range(i + 1, len(V)) if abs(D[i, j] - dmin) < 1e-6]
    hull = ConvexHull(V)
    Nr = hull.equations[:, :3]
    adj = [[f for f, s in enumerate(hull.simplices) if i in s and j in s] for (i, j) in E]
    return V, E, Nr, adj


CUBE = _poly3([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])
OCTA = _poly3([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)])
def _apex_up(verts):
    # rotate so that the first vertex points straight up (+y)
    V = np.array(verts, float)
    n = V[0] / np.linalg.norm(V[0])
    ax = np.cross(n, [0, 1, 0]); s = np.linalg.norm(ax); c = n[1]
    k = ax / s
    Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    R = np.eye(3) + s * Kx + (1 - c) * Kx @ Kx
    return V @ R.T


TETRA = _poly3(_apex_up([(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]))


class Wire(VGroup):
    """Slowly turning wireframe of a convex polytope (hidden edges dimmed)."""

    def __init__(self, data, center, size=0.8, color=KC, width=2.6, tilt=0.42, angle=0.35, speed=0.55):
        self.V, self.E, self.Nr, self.adj = data
        self.c = np.array(center, float)
        self.r = size / 2
        self.w, self.tilt, self.angle, self.speed = width, tilt, angle, speed
        self.lines = [VMobject(stroke_color=color, stroke_width=width) for _ in self.E]
        super().__init__(*self.lines)
        self.redraw()

    def redraw(self):
        R = _rot3(self.angle, self.tilt)
        P = self.V @ R.T
        nz = (self.Nr @ R.T)[:, 2]
        for k, (i, j) in enumerate(self.E):
            vis = any(nz[f] > 1e-6 for f in self.adj[k])
            a = self.c + self.r * np.array([P[i, 0], P[i, 1], 0])
            b = self.c + self.r * np.array([P[j, 0], P[j, 1], 0])
            ln = self.lines[k]
            ln.set_points_as_corners([a, b])
            ln.set_stroke(width=self.w if vis else self.w * 0.6, opacity=1.0 if vis else 0.3)

    def spin(self):
        # Only the live object spins: animation copies (e.g. the faded target of
        # a FadeOut) inherit this updater but must not reset their opacity.
        self._live = id(self)

        def upd(m, dt):
            if id(m) != m._live:
                return
            m.angle += dt * m.speed
            m.redraw()
        self.add_updater(upd)
        return self


class Simplex4(VGroup):
    """4-simplex (5-cell): its 10 edges projected from 4D, the projection plane
    slowly turning inside 4D."""

    def __init__(self, center, size=0.8, color=KC, width=2.2, speed=0.5):
        k = np.arange(5)
        n = np.sqrt(5 / 2)
        self.a, self.b = np.cos(2 * np.pi * k / 5) / n, np.sin(2 * np.pi * k / 5) / n
        self.cc, self.d = np.cos(4 * np.pi * k / 5) / n, np.sin(4 * np.pi * k / 5) / n
        self.c = np.array(center, float)
        self.r = size / 2 / np.sqrt(2 / 5) * 0.98
        self.phi, self.speed = 0.0, speed
        self.E = [(i, j) for i in range(5) for j in range(i + 1, 5)]
        self.lines = [VMobject(stroke_color=color, stroke_width=width) for _ in self.E]
        super().__init__(*self.lines)
        self.redraw()

    def redraw(self):
        u = np.cos(self.phi) * self.a + np.sin(self.phi) * self.cc
        v = np.cos(0.6 * self.phi) * self.b + np.sin(0.6 * self.phi) * self.d
        for k, (i, j) in enumerate(self.E):
            p = self.c + self.r * np.array([u[i], v[i], 0])
            q = self.c + self.r * np.array([u[j], v[j], 0])
            self.lines[k].set_points_as_corners([p, q])

    def spin(self):
        self._live = id(self)

        def upd(m, dt):
            if id(m) != m._live:
                return
            m.phi += dt * m.speed
            m.redraw()
        self.add_updater(upd)
        return self


def delayed(a, b, f=smooth):
    def r(t):
        if t <= a:
            return 0.0
        if t >= b:
            return 1.0
        return f((t - a) / (b - a))
    return r


class C3Mahler(VoiceScene):
    # -------------------------------------------------------------- geometry
    def geom(self):
        key = (self.t.get_value(), self.m.get_value(), self.rot.get_value())
        if key == getattr(self, "_gkey", None):
            return self._g
        t, m, r = key
        i = int(np.clip(np.floor(m), 0, len(KEYFRAMES) - 2))
        lam = m - i
        X = (1 - lam) * KEYFRAMES[i][0] + lam * KEYFRAMES[i + 1][0]
        h = (1 - lam) * KEYFRAMES[i][1] + lam * KEYFRAMES[i + 1][1]
        P = U / h[:, None]
        c, s = np.cos(r), np.sin(r)
        R = np.array([[c, -s], [s, c]])
        Mk = R @ np.diag([t, 1.0])
        Mp = R @ np.diag([1.0 / t, 1.0])
        Xs, Ps = X @ Mk.T, P @ Mp.T
        self._g = dict(K=Xs, P=Ps, aK=_area(Xs), aP=_area(Ps), Mk=Mk, Mp=Mp)
        self._gkey = key
        return self._g

    def scr(self, p):
        q = scr(p)
        q[:, 0] += self.px.get_value()
        return q

    def fr(self, a, b, f):
        """Time at fraction f of the way from cue a to cue b (keeps word sync
        proportional if the narration is re-timed)."""
        ta, tb = self.cue(a), self.cue(b)
        return ta + f * (tb - ta)

    def closed(self, pts):
        q = self.scr(pts)
        return np.vstack([q, q[:1]])

    # -------------------------------------------------------------- build
    def construct(self):
        self.t = ValueTracker(1.0)     # horizontal stretch
        self.m = ValueTracker(0.0)     # keyframe index (Minkowski morph)
        self.rot = ValueTracker(0.0)   # slow rotation of the pair
        self.px = ValueTracker(-P0[0])  # plane starts centred, slides left later
        self.add(self.t, self.m, self.rot, self.px)

        # ---- plane -------------------------------------------------------
        axes = VGroup(
            Line(P0 + LEFT * 2.55, P0 + RIGHT * 2.55, stroke_color=DIM, stroke_width=1.6),
            Line(P0 + DOWN * 2.0, P0 + UP * 2.0, stroke_color=DIM, stroke_width=1.6),
        )
        origin = Dot(P0, radius=0.055, color=WHITE_)
        VGroup(axes, origin).shift(RIGHT * self.px.get_value())

        Kpoly = VMobject(stroke_color=KC, stroke_width=5.5, fill_color=KC, fill_opacity=0.18)
        Ppoly = VMobject(stroke_color=PC, stroke_width=3.0, fill_color=PC, fill_opacity=0.14)
        Kpoly.set_points_as_corners(self.closed(self.geom()["K"]))
        Ppoly.set_points_as_corners(self.closed(self.geom()["P"]))
        Kpoly.add_updater(lambda mob: mob.set_points_as_corners(self.closed(self.geom()["K"])))
        Ppoly.add_updater(lambda mob: mob.set_points_as_corners(self.closed(self.geom()["P"])))

        Klab = tex("K", 46, KC)
        Plab = tex(r"K^\circ", 38, PC)

        def place_K(mob):
            g = self.geom()
            mob.move_to(self.scr(g["Mk"] @ np.array([1.0, 1.0]))[0] + np.array([0.27, 0.27, 0]))

        def place_P(mob):
            g = self.geom()
            mob.move_to(self.scr(g["Mp"] @ np.array([0.33, 0.33]))[0])

        place_K(Klab); place_P(Plab)

        # dual-line construction: vertex v of K  ->  line {y : v.y = 1}
        verts = [np.array(v, float) for v in [(1, 1), (-1, 1), (-1, -1), (1, -1)]]
        vdots, vlines = VGroup(), VGroup()
        for v in verts:
            mid = v / np.dot(v, v)
            d = np.array([-v[1], v[0]]) / np.linalg.norm(v)
            a, b = scr(mid + 1.18 * d)[0], scr(mid - 1.18 * d)[0]
            vdots.add(Dot(scr(v)[0], radius=0.075, color=KC))
            vlines.add(Line(a, b, stroke_color=PC, stroke_width=3))

        # ---- right column ------------------------------------------------
        defn = MathTex(r"K^\circ", r"=\{\,y \,:\, x\cdot y\le 1\ \text{ for all } x\in ", "K", r"\,\}",
                       font_size=38, color=WHITE_)
        defn[0].set_color(PC); defn[2].set_color(KC)
        defn.move_to([3.5, 1.45, 0])

        lhs = MathTex(r"\text{vol}(", "K", r")\,\cdot\,\text{vol}(", r"K^\circ", r")\ =", font_size=42, color=WHITE_)
        lhs[1].set_color(KC); lhs[3].set_color(PC)
        pnum = DecimalNumber(8.0, num_decimal_places=2, font_size=42, color=YELLOW_)
        pnum.next_to(lhs, RIGHT, buff=0.2)
        pnum.align_to(lhs[1], DOWN)
        kpart = VGroup(lhs[0], lhs[1], lhs[2][0])
        ppart = VGroup(lhs[2][2:], lhs[3], lhs[4][0])
        knum = DecimalNumber(4.0, num_decimal_places=2, font_size=30, color=KC)
        pnn = DecimalNumber(2.0, num_decimal_places=2, font_size=30, color=PC)
        knum.next_to(kpart, DOWN, buff=0.16)
        pnn.next_to(ppart, DOWN, buff=0.16).align_to(knum, DOWN)
        readout = VGroup(lhs, pnum, knum, pnn)
        readout.move_to([3.5, 0.0, 0])
        knum.add_updater(lambda d: d.set_value(self.geom()["aK"]))
        pnn.add_updater(lambda d: d.set_value(self.geom()["aP"]))
        pnum.add_updater(lambda d: d.set_value(self.geom()["aK"] * self.geom()["aP"]))

        # volume-product scale
        scale_ax = Arrow([SX, Y(6.2), 0], [SX, Y(10.45), 0], buff=0, color=GREY_, stroke_width=2.5,
                         max_tip_length_to_length_ratio=0.045, max_stroke_width_to_length_ratio=10)
        scale = VGroup(scale_ax)
        ptr = VGroup(Circle(radius=0.17, stroke_color=YELLOW_, stroke_width=2, stroke_opacity=0.45),
                     Dot(radius=0.085, color=YELLOW_))
        ptr.add_updater(lambda p: p.move_to([SX, Y(self.geom()["aK"] * self.geom()["aP"]), 0]))
        ptr.move_to([SX, Y(8), 0])

        def row(v, value_tex, name, desc, desc_color):
            y = Y(v)
            tick = Line([SX - 0.16, y, 0], [SX + 0.16, y, 0], stroke_color=WHITE_, stroke_width=3)
            val = tex(value_tex, 30 if "frac" in value_tex else 34, WHITE_)
            val.next_to([SX - 0.36, y, 0], LEFT, buff=0)
            nm = bold(name, 28)
            ds = txt(desc, 22, desc_color, weight=MEDIUM)
            nm.move_to([0, y, 0]).align_to([SX + 0.42, 0, 0], LEFT)
            ds.next_to(nm, DOWN, buff=0.13, aligned_edge=LEFT)
            return VGroup(tick, val, nm, ds)

        R1 = row(np.pi ** 2, r"\pi^2", "ball", "maximum · Blaschke–Santaló", GREEN_)
        R2 = row(8.0, "8", "cube & relatives", "symmetric minimum", YELLOW_)
        R3 = row(6.75, r"\frac{27}{4}", "simplex", "general minimum", YELLOW_)

        KeqP = tex(r"K = K^\circ", 38)
        KeqP[0][0].set_color(KC); KeqP[0][2:].set_color(PC)
        KeqP.move_to(P0 + S * np.array([0.72, 0.72, 0]) + np.array([0.62, 0.32, 0]))

        mh1 = bold("Mahler, late 1930s", 28)
        mh2 = tex(r"\min = \,?", 48)
        mh2[0][-1].set_color(YELLOW_)
        mahler = VGroup(mh1, mh2).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        mahler.move_to([0, -0.55, 0]).align_to([SX + 0.42, 0, 0], LEFT)

        card = paper_card("087", width=3.3)
        card.move_to([4.45, -1.18, 0])
        tag = paper_tag("087", color=ACC)

        banner = result_banner(
            r"\text{vol}(K)\,\text{vol}(K^\circ)\ \ge\ \frac{4^n}{n!}\ (\text{symmetric}),\quad"
            r" \frac{(n+1)^{n+1}}{(n!)^2}\ (\text{general})",
            is_tex=True, lean=CATALOG["087"]["lean"], size=30)
        banner.move_to([0, 0, 0]).align_to([6.55, 0, 0], RIGHT).align_to([0, -3.62, 0], DOWN)

        # icons for the minimizer rows
        ix = [4.55, 5.4, 6.25]                              # three icon columns
        cube_ic = Wire(CUBE, [ix[1], Y(8.0) - 0.15, 0], size=0.86, color=KC, angle=0.5)
        octa_ic = Wire(OCTA, [ix[2], Y(8.0) - 0.15, 0], size=0.9, color=PC, angle=0.2)
        tri_ic = RegularPolygon(3, start_angle=PI / 2, stroke_color=KC, stroke_width=2.6,
                                fill_color=KC, fill_opacity=0.15).scale(0.40)
        tri_ic.move_to([ix[0], Y(6.75) - 0.15 - 0.08, 0])
        tet_ic = Wire(TETRA, [ix[1], Y(6.75) - 0.15, 0], size=0.9, color=KC, angle=0.3, tilt=0.3)
        s4_ic = Simplex4([ix[2], Y(6.75) - 0.15, 0], size=0.86, color=KC)

        # ================================================================ 0: shape
        self.play_until("shape", FadeIn(axes), FadeIn(origin))
        self.play_until(self.fr("shape", "stretch", 0.25), DrawBorderThenFill(Kpoly))
        self.play_until(self.fr("shape", "stretch", 0.32), FadeIn(Klab, scale=0.7))
        Klab.add_updater(place_K)
        # "centered at the origin"
        self.play_between(self.fr("shape", "stretch", 0.335), self.fr("shape", "stretch", 0.49),
                          Flash(origin, color=WHITE_, line_length=0.22, flash_radius=0.22, num_lines=10),
                          Indicate(origin, color=WHITE_, scale_factor=1.8))
        # make room for the dual
        self.play_until(self.fr("shape", "stretch", 0.63), self.px.animate.set_value(0.0),
                        VGroup(axes, origin).animate.shift(LEFT * self.px.get_value()))
        # "and build its dual": every vertex x of K gives a line x.y = 1
        self.play_until(self.fr("shape", "stretch", 0.88),
                        LaggedStart(*[AnimationGroup(FadeIn(d, scale=0.4), GrowFromCenter(l))
                                      for d, l in zip(vdots, vlines)], lag_ratio=0.28),
                        Write(defn, rate_func=delayed(0.05, 1.0)))
        # "the polar body"
        place_P(Plab)
        self.play_until("stretch", FadeIn(Ppoly), FadeOut(vlines), FadeOut(vdots), FadeIn(Plab, scale=0.7))
        Plab.add_updater(place_P)

        # ================================================================ 1: stretch
        self.play_until(self.fr("stretch", "max", 0.13), FadeIn(readout, shift=UP * 0.2))
        # the K° label rides along briefly, then leaves before the diamond gets too thin
        self.play_until(self.fr("stretch", "max", 0.43), self.t.animate.set_value(1.65),
                        FadeOut(Plab, rate_func=delayed(0.05, 0.4)))
        self.play_until(self.fr("stretch", "max", 0.72), self.t.animate.set_value(0.62))
        self.play_until(self.fr("stretch", "max", 0.93), self.t.animate.set_value(1.0),
                        Circumscribe(pnum, color=YELLOW_, buff=0.08, stroke_width=3,
                                     rate_func=delayed(0.1, 0.95, linear)))

        # ================================================================ 2: max (ball)
        Klab.clear_updaters()
        self.play_between("max", self.fr("max", "mahler", 0.23),
                          FadeOut(defn, shift=UP * 0.3),
                          readout.animate.move_to([3.5, 3.05, 0]),
                          FadeOut(Klab),
                          Create(scale), FadeIn(ptr))
        self.play_until(self.fr("max", "mahler", 0.61), self.m.animate.set_value(1.0))
        self.play_until(self.fr("max", "mahler", 0.78), FadeIn(R1[0]), FadeIn(R1[1], shift=RIGHT * 0.15),
                        FadeIn(R1[2], shift=LEFT * 0.15), FadeIn(KeqP, scale=0.8))
        self.play_until(self.fr("max", "mahler", 0.97), FadeIn(R1[3], shift=UP * 0.1))

        # ================================================================ 3: Mahler's question
        self.play_between("mahler", self.fr("mahler", "claim", 0.13), FadeOut(KeqP), FadeIn(mh1, shift=UP * 0.15))
        self.play_until(self.fr("mahler", "claim", 0.39), self.m.animate.set_value(2.0))
        self.play_until(self.fr("mahler", "claim", 0.66), self.m.animate.set_value(3.0))
        self.play_until(self.fr("mahler", "claim", 0.93), self.m.animate.set_value(4.0),
                        FadeIn(mh2, shift=UP * 0.15, rate_func=delayed(0.3, 0.75)))

        # ================================================================ 4: the papers
        spin = lambda m, dt: m.increment_value(dt * 0.10)
        self.rot.add_updater(spin)
        self.play_between("claim", "claim+0.75",
                          FadeIn(card, shift=LEFT * 2.0), FadeIn(tag, shift=RIGHT * 0.3),
                          FadeOut(mahler))
        self.play_until("cube-0.15", card.animate.scale(1.03, about_edge=DOWN), rate_func=linear)
        self.rot.clear_updaters()

        # ================================================================ 5: symmetric minimum
        self.play_until(self.fr("cube", "simplex", 0.34), FadeOut(card, shift=RIGHT * 2.0, rate_func=delayed(0, 0.5)),
                        self.m.animate.set_value(5.0), self.rot.animate.set_value(0.0))
        self.play_until(self.fr("cube", "simplex", 0.54), FadeIn(R2[0]), FadeIn(R2[1], shift=RIGHT * 0.15),
                        FadeIn(R2[2], shift=LEFT * 0.15), FadeIn(R2[3], shift=UP * 0.1))
        kc = Kpoly.copy().clear_updaters()
        self.play_between(self.fr("cube", "simplex", 0.57), self.fr("cube", "simplex", 0.755), FadeTransform(kc, cube_ic))
        cube_ic.spin()
        pc = Ppoly.copy().clear_updaters()
        self.play_until(self.fr("cube", "simplex", 0.955), FadeTransform(pc, octa_ic))
        octa_ic.spin()

        # ================================================================ 6: general minimum
        self.play_between("simplex", self.fr("simplex", "L2_end", 0.205), self.m.animate.set_value(6.0))
        self.rot.add_updater(spin)
        self.play_until(self.fr("simplex", "L2_end", 0.296), FadeIn(R3[0]), FadeIn(R3[1], shift=RIGHT * 0.15),
                        FadeIn(R3[2], shift=LEFT * 0.15), FadeIn(R3[3], shift=UP * 0.1))
        self.play_until(self.fr("simplex", "L2_end", 0.41), FadeIn(banner, shift=UP * 0.25))
        kc = Kpoly.copy().clear_updaters()
        self.play_between(self.fr("simplex", "L2_end", 0.427), self.fr("simplex", "L2_end", 0.534), FadeTransform(kc, tri_ic))
        self.play_between(self.fr("simplex", "L2_end", 0.575), self.fr("simplex", "L2_end", 0.673), FadeIn(tet_ic, scale=0.6))
        tet_ic.spin()
        self.play_between(self.fr("simplex", "L2_end", 0.731), self.fr("simplex", "L2_end", 0.829), FadeIn(s4_ic, scale=0.6))
        s4_ic.spin()
        self.finish()
