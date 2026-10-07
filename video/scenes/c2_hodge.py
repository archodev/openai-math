import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import numpy as np

ACC = PURPLE_
NUM = "032"
LIGHT = np.array([-0.45, 0.65, 0.62])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


# =====================================================================  3D helpers
def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(b):
    c, s = np.cos(b), np.sin(b)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


class View:
    """Orthographic camera: rotate local frame about screen-x by alpha,
    scale, translate. Camera frame: x right, y up, z toward the viewer."""

    def __init__(self, alpha, scale, center, beta=0.0):
        self.alpha, self.scale, self.center = alpha, scale, np.array(center, float)
        self.M = rot_y(beta) @ rot_x(alpha)

    def apply(self, P):
        Q = P @ self.M.T * self.scale
        Q[..., 0] += self.center[0]
        Q[..., 1] += self.center[1]
        return Q

    def dir_local(self):
        return self.M.T @ np.array([0, 0, 1.0])


class Mesh(VGroup):
    """Quad mesh drawn with the painter's algorithm. `grid_fn()` returns an
    (ns+1, nt+1, 3) array of camera-frame points; refreshed every frame."""

    def __init__(self, ns, nt, front, back, grid_fn, levels=28, stroke=1.0, cull=True, opacity=0.0,
                 edges=None):
        super().__init__()
        self.ns, self.nt, self.grid_fn, self.cull = ns, nt, grid_fn, cull
        self.levels, self.sw = levels, stroke
        self.opacity = opacity
        n = ns * nt
        self.polys = []
        for _ in range(n):
            p = VMobject(stroke_width=stroke, fill_opacity=1.0)
            p.points = np.zeros((16, 3))
            self.polys.append(p)
        self.add(*self.polys)
        self._empty = np.zeros((4, 3))
        self._clear = np.zeros((1, 4))
        i, j = np.divmod(np.arange(n), nt)
        self.parity = ((i + j) % 2).astype(int)
        front, back = list(front), list(back)
        if edges:  # (colour for t-edges, colour for s-edges): glued sides of the square
            ct, cs = edges
            self.parity[(i == 0) | (i == ns - 1)] = 3
            self.parity[(j == 0) | (j == nt - 1)] = 2
            front += [ct, cs]
            back += [ct, cs]
        # colour table [side][kind][level] -> rgb
        tab = np.zeros((2, len(front), levels, 3))
        for side, pal in enumerate((front, back)):
            for par, c in enumerate(pal):
                base = hex_rgb(c)
                for l in range(levels):
                    k = l / (levels - 1)
                    rgb = base * (0.30 + 0.85 * k) + 0.22 * k ** 6
                    tab[side, par, l] = np.clip(rgb, 0, 1)
        self.tab = tab
        self.refresh()

    def refresh(self):
        P = self.grid_fn()
        A, B, C, D = P[:-1, :-1], P[1:, :-1], P[1:, 1:], P[:-1, 1:]
        q = np.stack([A, B, C, D], 2).reshape(-1, 4, 3)
        n = len(q)
        cen = q.mean(1)
        nrm = np.cross((C - A).reshape(-1, 3), (D - B).reshape(-1, 3))
        nrm /= (np.linalg.norm(nrm, axis=1) + 1e-12)[:, None]
        facing = nrm[:, 2] >= 0
        side = (~facing).astype(int)
        nrm[~facing] *= -1
        lam = np.clip(nrm @ LIGHT, 0, 1)
        lvl = np.minimum((lam * (self.levels - 1) + 0.5).astype(int), self.levels - 1)
        order = np.argsort(cen[:, 2], kind="stable")
        if self.cull:
            order = order[facing[order]]
        b = np.roll(q, -1, axis=1)
        pts = np.empty((n, 4, 4, 3))
        pts[:, :, 0] = q
        pts[:, :, 1] = q + (b - q) / 3
        pts[:, :, 2] = q + 2 * (b - q) / 3
        pts[:, :, 3] = b
        pts = pts.reshape(n, 16, 3)
        # A fixed pool of slots that never changes (the Cairo renderer snapshots a
        # group's children per play() call): slot m shows the m-th quad in depth order.
        op = self.opacity
        sw = self.sw if op > 0.98 else 0
        for slot, k in zip(self.polys, order):
            slot.points = pts[k]
            rgb = self.tab[side[k], self.parity[k], lvl[k]]
            rgba = np.array([[rgb[0], rgb[1], rgb[2], op]])
            slot.fill_rgbas = rgba
            slot.stroke_rgbas = rgba
            slot.stroke_width = sw
        for slot in self.polys[len(order):]:
            slot.points = self._empty
            slot.fill_rgbas = self._clear
            slot.stroke_rgbas = self._clear
            slot.stroke_width = 0
        return self


# ---------------------------------------------------------------- torus
def torus_pts(R, r, u, v):
    return np.stack([(R + r * np.cos(v)) * np.cos(u), (R + r * np.cos(v)) * np.sin(u), r * np.sin(v)], -1)


def torus_nrm(u, v):
    return np.stack([np.cos(v) * np.cos(u), np.cos(v) * np.sin(u), np.sin(v)], -1)


def torus_grid(R, r, ns, nt, spin=0.0, v0=0.0):
    s = (np.arange(ns + 1) / ns + spin) * TAU
    t = np.arange(nt + 1) / nt * TAU + v0
    S, T = np.meshgrid(s, t, indexing="ij")
    return torus_pts(R, r, S, T)


def occluded(P, d, R, r, steps=90, tmax=None):
    tmax = tmax or 3 * (R + r)
    ts = np.linspace(0.04, tmax, steps)
    Q = P[:, None, :] + ts[None, :, None] * d[None, None, :]
    f = (np.sqrt(Q[..., 0] ** 2 + Q[..., 1] ** 2) - R) ** 2 + Q[..., 2] ** 2 - (r * 0.995) ** 2
    return (f < 0).any(1)


def runs(mask):
    """Contiguous True runs of a cyclic boolean array, as index lists."""
    n = len(mask)
    if mask.all():
        return [list(range(n)) + [0]]
    if not mask.any():
        return []
    start = int(np.argmin(mask))  # a False index
    out, cur = [], []
    for k in range(1, n + 1):
        i = (start + k) % n
        if mask[i]:
            cur.append(i)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def path_vm(Q, idx_runs, **style):
    vm = VMobject(**style)
    if not any(len(r_) >= 2 for r_ in idx_runs):
        vm.set_points_as_corners([Q[0], Q[0] + 1e-4 * RIGHT])
        vm.set_stroke(opacity=0)
        return vm
    first = True
    for run in idx_runs:
        if len(run) < 2:
            continue
        pts = Q[run]
        if first:
            vm.set_points_as_corners(pts)
            first = False
        else:
            vm.start_new_path(pts[0])
            vm.add_points_as_corners(pts[1:])
    return vm


def torus_curve(R, r, u, v, view, color, width=6.5, eps=0.02):
    """A closed curve on the torus. Returns VGroup(shadow, hidden, visible)."""
    P = torus_pts(R, r + eps, u, v)
    N = torus_nrm(u, v)
    d = view.dir_local()
    vis = (N @ d > 0.02) & ~occluded(P, d, R, r)
    Q = view.apply(P)
    vis_runs, hid_runs = runs(vis), runs(~vis)
    solid = path_vm(Q, vis_runs, stroke_color=color, stroke_width=width)
    shadow = path_vm(Q, vis_runs, stroke_color=BG, stroke_width=width + 5, stroke_opacity=0.5)
    hidden = path_vm(Q, hid_runs, stroke_color=color, stroke_width=width * 0.45, stroke_opacity=0.32)
    full = VMobject(stroke_color=color, stroke_width=width).set_points_as_corners(Q)
    g = VGroup(shadow, hidden, solid)
    g.full = full
    return g


# ---------------------------------------------------------------- fold (square -> torus)
def fold_grid(ns, nt, a, b, R1, spin=0.0):
    """Unit square (s,t) rolled (a: 0->1) into a tube of circumference 1, then
    bent (b: 0->1) into a torus with major radius R1. Centred at the origin."""
    s = np.arange(ns + 1) / ns + spin
    t = np.arange(nt + 1) / nt
    S, T = np.meshgrid(s, t, indexing="ij")
    if a < 1e-4:
        wy, wz = (T - 0.5), np.zeros_like(T)
    else:
        rho = 1 / (TAU * a)
        phi = TAU * a * (T - 0.5)
        wy, wz = rho * np.sin(phi), -rho * (1 - np.cos(phi))
    Ls = 1 + (TAU * R1 - 1) * b
    if b < 1e-4:
        P = np.stack([Ls * (S - 0.5), wy, wz], -1)
    else:
        rb = Ls / (TAU * b)
        th = TAU * b * (S - 0.5)
        P = np.stack([(rb + wy) * np.sin(th), (rb + wy) * np.cos(th) - rb, wz], -1)
    c = P[:-1, :-1].reshape(-1, 3).mean(0)
    return P - c


# =====================================================================  the scene
class C2Hodge(VoiceScene):

    def tf(self, a, b, f):
        """Time at fraction f between cues a and b."""
        ta, tb = self.cue(a), self.cue(b)
        return ta + f * (tb - ta)

    def construct(self):
        tf = self.tf

        # ------------------------------------------------------------ 0. hook: the seven problems
        names = ["P vs NP", "Riemann\nHypothesis", "Yang–Mills", "Navier–Stokes",
                 "Birch &\nSwinnerton-Dyer", "Hodge\nConjecture", "Poincaré\nConjecture"]
        tiles = VGroup()
        for nm in names:
            box = RoundedRectangle(width=3.0, height=1.05, corner_radius=0.12, stroke_color=GREY_,
                                   stroke_width=1.4, stroke_opacity=0.55, fill_color=CARD, fill_opacity=1)
            t = VGroup(*[Text(ln, font=SANS, font_size=24, color=WHITE_, weight=MEDIUM)
                         for ln in nm.split("\n")]).arrange(DOWN, buff=0.1)
            t.move_to(box)
            tiles.add(VGroup(box, t))
        row1 = VGroup(*tiles[:4]).arrange(RIGHT, buff=0.18)
        row2 = VGroup(*tiles[4:]).arrange(RIGHT, buff=0.18)
        VGroup(row1, row2).arrange(DOWN, buff=0.2).move_to(DOWN * 0.35)
        hodge_tile, poinc_tile = tiles[5], tiles[6]
        mp_head = caps("THE SEVEN MILLENNIUM PRIZE PROBLEMS", size=22, color=GREY_, spacing=0.035)
        mp_head.next_to(row1, UP, buff=0.45)
        ck = check_mark(GREEN_, size=0.3, width=4).next_to(poinc_tile[0].get_corner(UR), DL, buff=0.12)

        self.play(LaggedStart(*[FadeIn(tl, shift=UP * 0.25) for tl in tiles], lag_ratio=0.12),
                  FadeIn(mp_head, shift=DOWN * 0.1), run_time=1.5)
        self.play_until(tf("L0", "L0_end", 0.45), Create(ck),
                        poinc_tile[1].animate.set_opacity(0.55))
        others = [tl for tl in tiles if tl is not hodge_tile]
        tgt = hodge_tile.copy()
        tgt[0].set_stroke(ACC, width=3.2, opacity=1).set_fill(CARD_HI)
        tgt.scale(1.08)
        self.play_until(tf("L0", "L0_end", 0.66),
                        *[tl.animate.set_opacity(0.22) for tl in others], ck.animate.set_opacity(0.22),
                        Transform(hodge_tile, tgt))
        title = serif("The Hodge Conjecture", 72).move_to(UP * 0.45)
        mp_chip = chip("MILLENNIUM PRIZE PROBLEM", ACC, size=20, pad_x=0.18, pad_y=0.1)
        mp_chip.next_to(title, DOWN, buff=0.45)
        early = lambda t: smooth(min(1.0, t / 0.45))
        self.play_until("L0_end",
                        FadeOut(hodge_tile, scale=1.6, shift=UP * 0.6, rate_func=early),
                        FadeIn(title, scale=0.55, shift=DOWN * 0.6, rate_func=lambda t: smooth(max(0.0, t - 0.15) / 0.85)),
                        *[FadeOut(tl, shift=DOWN * 0.4, rate_func=early) for tl in others],
                        FadeOut(ck, shift=DOWN * 0.4, rate_func=early),
                        FadeOut(mp_head, shift=UP * 0.3, rate_func=early),
                        FadeIn(mp_chip, shift=UP * 0.2, rate_func=lambda t: smooth(max(0.0, t - 0.35) / 0.65)))

        # ------------------------------------------------------------ 1. a shape with loops
        R, r = 1.72, 0.80
        EL = 0.56  # elevation (rad)
        TC = np.array([-3.15, -0.45, 0])
        tview = View(-(PI / 2 - EL), 1.0, TC)
        st = {"spin": 0.0, "scale": 0.8, "op": 0.0}

        def tgrid():
            v = View(tview.alpha, st["scale"], TC)
            return v.apply(torus_grid(R, r, 44, 22, spin=st["spin"]))

        torus = Mesh(44, 22, ("#4C5874", "#3C4660"), ("#2A3040", "#232838"), tgrid, stroke=1.0)

        def torus_upd(m, dt):
            st["spin"] += dt / 46.0
            m.opacity = st["op"]
            m.refresh()
        torus.add_updater(torus_upd)
        sc_tr, op_tr = ValueTracker(0.8), ValueTracker(0.0)

        def follow(m, dt):
            st["scale"], st["op"] = sc_tr.get_value(), op_tr.get_value()
        torus.add_updater(follow, index=0)
        self.add(torus)

        header = serif("The Hodge Conjecture", 44).to_edge(UP, buff=0.42)
        eqX = tex(r"X=\{\,f_1=\cdots=f_k=0\,\}", 40).move_to([3.55, 2.2, 0])
        eqX_cap = txt("polynomial equations", 24, GREY_).next_to(eqX, DOWN, buff=0.18)

        self.play(ReplacementTransform(title, header), FadeOut(mp_chip, shift=UP * 0.2),
                  sc_tr.animate.set_value(1.0), op_tr.animate.set_value(1.0),
                  run_time=1.3, rate_func=smooth)
        self.wait_until(tf("shape", "cycles", 0.17))
        self.play(Write(eqX), FadeIn(eqX_cap, shift=UP * 0.1), run_time=1.1)

        # loops (fixed in space; the checkerboard spins underneath)
        n = 260
        uu = np.linspace(0, TAU, n, endpoint=False)
        V60 = PI / 3
        UM = -0.95  # meridian angle (front right)
        loop_g = torus_curve(R, r, uu, np.full(n, V60), tview, GOLD_)
        loop_b = torus_curve(R, r, np.full(n, UM), uu, tview, BLUE_)
        loop_p = torus_curve(R, r, uu + 0.35, uu + 1.2, tview, PINK_)
        loops = [loop_g, loop_b, loop_p]
        self.wait_until(tf("shape", "cycles", 0.48))
        self.play(LaggedStart(*[Create(L) for L in loops], lag_ratio=0.3),
                  run_time=tf("shape", "cycles", 0.75) - self.now)

        # shelf of classes
        def icon(L, h=0.58, w=1.0):
            ic = VGroup(L.full.copy().set_stroke(width=5))
            ic.scale(min(h / max(ic.height, 1e-3), w / max(ic.width, 1e-3)))
            return ic
        slots = VGroup(*[RoundedRectangle(width=1.25, height=0.85, corner_radius=0.1, stroke_color=DIM,
                                          stroke_width=1.4, fill_color=CARD, fill_opacity=0.5)
                         for _ in range(3)]).arrange(RIGHT, buff=0.22)
        dots3 = tex(r"\cdots", 40, GREY_)
        shelf_row = VGroup(slots, dots3).arrange(RIGHT, buff=0.25).move_to([3.55, -0.15, 0])
        icons = [icon(L).move_to(s) for L, s in zip(loops, slots)]
        shelf_cap = VGroup(txt("topology:", 26, GREY_), tex(r"H^{*}(X;\mathbb{Q})", 38)).arrange(RIGHT, buff=0.2)
        shelf_cap.next_to(shelf_row, UP, buff=0.3)
        self.add(slots)
        self.play(FadeIn(shelf_cap, shift=UP * 0.1), FadeIn(slots), FadeIn(dots3),
                  *[TransformFromCopy(L.full, ic) for L, ic in zip(loops, icons)],
                  run_time=max(0.6, tf("shape", "cycles", 0.99) - self.now))
        self.add(*icons)

        # ------------------------------------------------------------ 2. algebraic pieces (plane slices)
        zp = ValueTracker(r + 1.15)

        def hplane():
            k = np.linspace(0, TAU, 72)
            P = np.stack([(R + r + 0.55) * np.cos(k), (R + r + 0.55) * np.sin(k), np.full_like(k, zp.get_value())], -1)
            Q = tview.apply(P)
            return Polygon(*Q, stroke_color=WHITE_, stroke_width=2, stroke_opacity=0.7,
                           fill_color=SKY_, fill_opacity=0.13)
        plane1 = always_redraw(hplane)
        g_lab = tex("g=0", 30, WHITE_)
        g_lab.add_updater(lambda m: m.move_to(tview.apply(np.array([[R + r + 0.55, 0, zp.get_value()]]))[0] + RIGHT * 0.55))
        z1_inner = torus_curve(R, r, uu, np.full(n, PI - V60), tview, GOLD_)
        z1_outer = torus_curve(R, r, uu, np.full(n, V60), tview, YELLOW_, width=6.5)
        self.play_until(tf("cycles", "L1_end", 0.07), FadeIn(plane1), FadeIn(g_lab))
        self.play_until(tf("cycles", "L1_end", 0.236), zp.animate.set_value(r * np.sin(V60)), rate_func=smooth)
        Z1 = tex("Z_1", 34, GOLD_).move_to(tview.apply(torus_pts(R, r, np.array([PI + 0.15]), np.array([V60])))[0] + LEFT * 0.62 + UP * 0.05)
        self.play_until(tf("cycles", "L1_end", 0.39),
                        Create(z1_outer), Create(z1_inner),
                        FadeIn(Z1, scale=0.8))
        g_lab.clear_updaters()
        self.play_until(tf("cycles", "L1_end", 0.47), FadeOut(plane1), FadeOut(g_lab), z1_outer.animate.set_opacity(0))
        self.remove(z1_outer)

        ang = ValueTracker(UM - 0.9)

        def vplane():
            a = ang.get_value()
            w = np.array([np.cos(a), np.sin(a), 0])
            ez = np.array([0, 0, 1.0])
            ext, hz = R + r + 0.45, r + 0.55
            P = np.array([-ext * w - hz * ez, ext * w - hz * ez, ext * w + hz * ez, -ext * w + hz * ez])
            Q = tview.apply(P)
            return Polygon(*Q, stroke_color=WHITE_, stroke_width=2, stroke_opacity=0.7,
                           fill_color=SKY_, fill_opacity=0.13)
        plane2 = always_redraw(vplane)
        h_lab = tex("h=0", 30, WHITE_)

        def hlab_upd(m):
            a = ang.get_value()
            p = np.array([[-(R + r + 0.45) * np.cos(a), -(R + r + 0.45) * np.sin(a), r + 0.55]])
            m.next_to(tview.apply(p)[0], UL, buff=0.08)
        h_lab.add_updater(hlab_upd)
        z2_back = torus_curve(R, r, np.full(n, UM + PI), uu, tview, BLUE_)
        self.play_until(tf("cycles", "L1_end", 0.534), FadeIn(plane2), FadeIn(h_lab))
        self.play_until(tf("cycles", "L1_end", 0.645), ang.animate.set_value(UM), rate_func=smooth)
        z2_hi = torus_curve(R, r, np.full(n, UM), uu, tview, SKY_, width=6.5)
        Z2 = tex("Z_2", 34, BLUE_).move_to(tview.apply(torus_pts(R, r, np.array([UM]), np.array([-0.35])))[0] + RIGHT * 0.55 + DOWN * 0.2)
        self.play_until(tf("cycles", "L1_end", 0.777),
                        Create(z2_hi), Create(z2_back),
                        FadeIn(Z2, scale=0.8))
        h_lab.clear_updaters()
        # algebraic marks on the shelf
        lab1 = tex("Z_1", 30, GOLD_).next_to(slots[0], DOWN, buff=0.15)
        lab2 = tex("Z_2", 30, BLUE_).next_to(slots[1], DOWN, buff=0.15)
        qm = tex("?", 34, PINK_).next_to(slots[2], DOWN, buff=0.13)
        br = Line(slots[0].get_corner(DL) + DOWN * 0.62, slots[1].get_corner(DR) + DOWN * 0.62,
                  stroke_color=GREEN_, stroke_width=3)
        alg = txt("algebraic", 24, GREEN_).next_to(br, DOWN, buff=0.12)
        self.play_until(tf("cycles", "L1_end", 0.887),
                        FadeOut(plane2), FadeOut(h_lab), z2_hi.animate.set_opacity(0),
                        FadeIn(lab1, shift=UP * 0.1), FadeIn(lab2, shift=UP * 0.1),
                        slots[0].animate.set_stroke(GREEN_, width=2.4, opacity=1),
                        slots[1].animate.set_stroke(GREEN_, width=2.4, opacity=1))
        self.remove(z2_hi)
        self.play_until(tf("cycles", "L1_end", 0.99), GrowFromCenter(br), FadeIn(alg, shift=UP * 0.1),
                        FadeIn(qm, scale=0.6))

        # ------------------------------------------------------------ 3. the conjecture
        pink_ic = icons[2]
        self.play(FadeOut(eqX), FadeOut(eqX_cap),
                  Indicate(loop_p[2], color=PINK_, scale_factor=1.0),
                  run_time=0.8)
        self.play_until(tf("conj", "L2_end", 0.2),
                        Indicate(pink_ic, color=PINK_, scale_factor=1.25),
                        Circumscribe(slots[2], color=PINK_, buff=0.04))
        # symmetry test
        tslots = VGroup(*[RoundedRectangle(width=1.15, height=0.82, corner_radius=0.1, stroke_color=GREY_,
                                           stroke_width=1.4, stroke_opacity=0.8, fill_color=CARD, fill_opacity=0.9)
                          for _ in range(3)]).arrange(RIGHT, buff=0.18).move_to([3.55, 1.45, 0])
        tlabs = VGroup(tex(r"H^{p,q}", 30, GREY_), tex(r"H^{p,p}", 30, WHITE_), tex(r"H^{q,p}", 30, GREY_))
        for tl, sl in zip(tlabs, tslots):
            tl.next_to(sl, DOWN, buff=0.14)
        mirror = DashedLine(tslots[1].get_top() + UP * 0.25, tlabs[1].get_bottom() + DOWN * 0.08,
                            dash_length=0.08, stroke_color=GREY_, stroke_width=2, stroke_opacity=0.7)
        test_cap = caps("SYMMETRY TEST", size=22, color=GREY_, spacing=0.035).next_to(tslots, UP, buff=0.42)
        old_shelf = VGroup(shelf_cap, slots, dots3, icons[0], icons[1], lab1, lab2, qm, br, alg)
        self.play(FadeOut(old_shelf, shift=DOWN * 0.3),
                  FadeIn(tslots, shift=UP * 0.15), FadeIn(tlabs, shift=UP * 0.15), FadeIn(test_cap),
                  run_time=0.7)
        self.add(pink_ic)
        self.play(Create(mirror), pink_ic.animate.move_to(tslots[1]).scale(0.95),
                  run_time=max(0.5, tf("conj", "L2_end", 0.43) - self.now - 0.45))
        self.play(tslots[1].animate.set_stroke(GREEN_, width=3, opacity=1).set_fill(CARD_HI),
                  Flash(tslots[1], color=GREEN_, line_length=0.18, flash_radius=0.75, num_lines=10),
                  run_time=0.45)
        tck = check_mark(GREEN_, size=0.3, width=4.5)
        hodge_lab = VGroup(tck, bold("Hodge class", 28, PINK_)).arrange(RIGHT, buff=0.14)
        hodge_lab.next_to(tlabs[1], DOWN, buff=0.2)
        self.play_at(tf("conj", "L2_end", 0.47), Create(tck), FadeIn(hodge_lab[1], shift=UP * 0.12), run_time=0.6)

        # built from pieces
        self.wait_until(tf("conj", "L2_end", 0.6))
        f_rest = MathTex(r"\overset{?}{=}", r"q_1", r"[Z_1]", r"+", r"q_2", r"[Z_2]", r"+\cdots",
                         font_size=46, color=WHITE_)
        f_rest[2].set_color(GOLD_)
        f_rest[5].set_color(BLUE_)
        f_ic = pink_ic.copy().scale(1.05)
        formula = VGroup(f_ic, f_rest).arrange(RIGHT, buff=0.22).move_to([3.55, -1.05, 0])
        qmark = max(f_rest[0], key=lambda m_: m_.get_center()[1])  # the question mark
        qmark.set_color(ORANGE_).scale(1.7, about_edge=DOWN)
        piece_g = loop_p.full.copy().set_stroke(PINK_, width=5)
        piece_b = loop_p.full.copy().set_stroke(PINK_, width=5)
        self.play(TransformFromCopy(pink_ic, f_ic), Write(f_rest),
                  Transform(piece_g, loop_g.full.copy().set_stroke(GOLD_, width=7)),
                  Transform(piece_b, loop_b.full.copy().set_stroke(BLUE_, width=7)),
                  run_time=max(0.6, tf("conj", "L2_end", 0.77) - self.now))
        # fractional amounts
        qrow = MathTex(r"q_i\in\mathbb{Q}:", r"\frac12,", r"-\frac23,", r"3,", r"\frac57,", r"\dots",
                       font_size=40, color=GREY_)
        qrow.arrange(RIGHT, buff=0.3)
        qrow[0].set_color(YELLOW_)
        qrow.next_to(formula, DOWN, buff=0.45)
        self.play(FadeOut(piece_g), FadeOut(piece_b),
                  f_rest[1].animate.set_color(YELLOW_), f_rest[4].animate.set_color(YELLOW_),
                  FadeIn(qrow[0], shift=UP * 0.1), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.12) for c in qrow[1:]], lag_ratio=0.2),
                  run_time=max(0.6, tf("conj", "L2_end", 1.0) - self.now))

        # ------------------------------------------------------------ 4. still open
        open_chip = chip("GENERAL CASE: STILL OPEN", ORANGE_, size=20, pad_x=0.18, pad_y=0.1)
        hdr_target = VGroup(header.copy(), open_chip).arrange(RIGHT, buff=0.4).to_edge(UP, buff=0.42)
        self.wait_until("open")
        self.play(header.animate.move_to(hdr_target[0]), FadeIn(open_chip, shift=LEFT * 0.3),
                  Indicate(f_rest[0], color=ORANGE_, scale_factor=1.35),
                  run_time=min(1.2, tf("open", "claim", 0.75) - self.now))

        # ------------------------------------------------------------ 5. the paper
        card = paper_card(NUM, width=3.3)
        card.move_to([4.15, 0.15, 0])
        tag = paper_tag(NUM, color=ACC)
        panel = VGroup(tslots, tlabs, mirror, test_cap, pink_ic, hodge_lab, formula, qrow)
        self.wait_until("claim")
        self.play(FadeOut(panel, shift=LEFT * 0.4), run_time=0.45)
        self.play(FadeIn(card, shift=LEFT * 2.2), FadeIn(tag, shift=RIGHT * 0.3), run_time=0.9)
        # highlight the title on the first page
        img = card[-2]
        k = img.height / 1430
        ttl_c = img.get_center() + UP * (715 - 222) * k
        hl = Rectangle(width=1.0 * img.width * 0.74, height=0.2, stroke_width=0,
                       fill_color=YELLOW_, fill_opacity=0.28).move_to(ttl_c)
        self.play_at(tf("claim", "cm", 0.42), GrowFromEdge(hl, LEFT), run_time=0.6)
        dims = MathTex(r"\dim =", r"1,", r"\ 2,", r"\ 3,", r"\ 4,", r"\ \dots", font_size=38, color=WHITE_)
        dims[0].set_color(GREY_)
        ev = bold("every dimension", 28, YELLOW_)
        dimrow = VGroup(ev, dims).arrange(RIGHT, buff=0.3)
        dimrow.next_to(card, DOWN, buff=0.28)
        if dimrow.get_right()[0] > 6.6:
            dimrow.shift(LEFT * (dimrow.get_right()[0] - 6.6))
        self.wait_until(tf("claim", "cm", 0.76))
        self.play(FadeIn(ev, shift=UP * 0.1), FadeIn(dims[0]),
                  LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in dims[1:]], lag_ratio=0.25),
                  run_time=max(0.6, self.cue("cm") - self.now + 0.2))

        # ------------------------------------------------------------ 6. CM: lattice with extra symmetry
        h2 = VGroup(txt("Abelian varieties with ", 34), txt("complex multiplication", 34, ACC, weight=SEMIBOLD))
        h2.arrange(RIGHT, buff=0.14).to_edge(UP, buff=0.45)
        h2[0].align_to(h2[1], DOWN)

        O = np.array([-3.55, -0.3, 0])
        hh = 0.72
        RL = 2.55
        dots = VGroup()
        for m in range(-4, 5):
            for nn_ in range(-4, 5):
                p = np.array([m * hh, nn_ * hh, 0])
                rr = np.linalg.norm(p)
                if rr <= RL:
                    o = 1.0 if rr < RL - 0.8 else max(0.25, (RL - rr) / 0.8)
                    dots.add(Dot(O + p, radius=0.055, color=WHITE_, fill_opacity=o))
        grid = VGroup()
        for kk in range(-3, 4):
            c = kk * hh
            half = np.sqrt(max(RL ** 2 - c ** 2, 0))
            grid.add(Line(O + np.array([c, -half, 0]), O + np.array([c, half, 0]), stroke_color=DIM, stroke_width=1.5, stroke_opacity=0.7))
            grid.add(Line(O + np.array([-half, c, 0]), O + np.array([half, c, 0]), stroke_color=DIM, stroke_width=1.5, stroke_opacity=0.7))
        cell = Square(side_length=hh, stroke_color=ACC, stroke_width=3, fill_color=ACC, fill_opacity=0.28)
        cell.move_to(O + np.array([hh / 2, hh / 2, 0]))
        one = Dot(O + RIGHT * hh, radius=0.085, color=YELLOW_)
        lat = VGroup(grid, cell, dots, one)
        lab0 = tex("0", 28, GREY_).next_to(O, DR, buff=0.08)
        lab1_ = tex("1", 28, YELLOW_).next_to(O + RIGHT * hh, DR, buff=0.08)
        labi = tex("i", 30, GREY_).next_to(O + UP * hh, UL, buff=0.08)
        zi = tex(r"\Lambda=\mathbb{Z}[i]", 36, WHITE_).move_to(O + np.array([0, RL + 0.35, 0]))
        if zi.get_top()[1] > 2.75:
            zi.shift(DOWN * (zi.get_top()[1] - 2.75))
        zi.move_to([O[0] - 1.9, 2.25, 0])

        late = lambda t: smooth(max(0.0, t - 0.4) / 0.6)
        self.play(FadeOut(VGroup(header, open_chip), shift=UP * 0.4, rate_func=lambda t: smooth(min(1.0, t / 0.6))),
                  FadeIn(h2, shift=UP * 0.3, rate_func=late),
                  op_tr.animate.set_value(0.0), sc_tr.animate.set_value(0.6),
                  *[FadeOut(L) for L in (loop_g, loop_b, loop_p, z1_inner, z2_back, Z1, Z2)],
                  FadeOut(Group(card, hl, dimrow), shift=RIGHT * 1.5),
                  Create(grid, lag_ratio=0.05, rate_func=late),
                  LaggedStart(*[GrowFromCenter(d) for d in sorted(dots, key=lambda d: np.linalg.norm(d.get_center() - O))],
                              lag_ratio=0.02, rate_func=late),
                  run_time=max(0.8, tf("cm", "L3_end", 0.16) - self.now))
        torus.clear_updaters()
        self.remove(torus)
        self.play_until(tf("cm", "L3_end", 0.21), FadeIn(cell), GrowFromCenter(one), FadeIn(lab0), FadeIn(lab1_),
                        FadeIn(labi), FadeIn(zi, shift=DOWN * 0.1))
        # multiplication by i: rotate the lattice a quarter turn, it lands on itself
        arc = Arc(radius=hh * 1.55, start_angle=0.12, angle=PI / 2 - 0.24, arc_center=O,
                  stroke_color=YELLOW_, stroke_width=4).add_tip(tip_length=0.18, tip_width=0.18)
        xi = tex(r"\times\, i", 38, YELLOW_).move_to(O + hh * 1.55 * 1.38 * np.array([np.cos(PI / 4), np.sin(PI / 4), 0]))
        self.play_until(tf("cm", "L3_end", 0.265), Create(arc), FadeIn(xi, scale=0.7))
        self.play_until(tf("cm", "L3_end", 0.44), Rotate(lat, PI / 2, about_point=O), rate_func=smooth)

        # fold the (rotated) cell into a donut
        fs = {"a": 0.0, "b": 0.0, "alpha": 0.0, "beta": 0.0, "S": hh, "cx": 0.0, "cy": 0.0, "spin": 0.0, "op": 0.0}
        cell_c = cell.get_center()
        fs["cx"], fs["cy"] = cell_c[0], cell_c[1]
        R1 = 2.3 / TAU
        trk = {k: ValueTracker(v) for k, v in fs.items()}

        def fgrid():
            P = fold_grid(NS, NT, trk["a"].get_value(), trk["b"].get_value(), R1, spin=fs["spin"])
            v = View(trk["alpha"].get_value(), trk["S"].get_value(), (trk["cx"].get_value(), trk["cy"].get_value(), 0),
                     beta=trk["beta"].get_value())
            return v.apply(P)
        NS, NT = 26, 12
        fmesh = Mesh(NS, NT, ("#8A6CCB", "#5A4390"), ("#3E2F66", "#2E2349"), fgrid, stroke=1.0, cull=False,
                     edges=(GOLD_, BLUE_))

        def fupd(m, dt):
            if trk["b"].get_value() > 0.999:
                fs["spin"] += dt / 30.0
            m.opacity = trk["op"].get_value()
            m.refresh()
        fmesh.add_updater(fupd)
        self.add(fmesh)
        FC = np.array([3.4, -0.55, 0])
        self.play_until(tf("cm", "L3_end", 0.49), trk["op"].animate.set_value(1.0), cell.animate.set_fill(opacity=0.1),
                        *[Indicate(d, color=ACC, scale_factor=1.6) for d in dots])
        self.play_until(tf("cm", "L3_end", 0.565), trk["S"].animate.set_value(2.1), trk["cx"].animate.set_value(FC[0]),
                        trk["cy"].animate.set_value(FC[1]), FadeOut(arc), FadeOut(xi), rate_func=smooth)
        self.play_until(tf("cm", "L3_end", 0.69), trk["a"].animate.set_value(1.0), trk["alpha"].animate.set_value(-0.42),
                        trk["beta"].animate.set_value(0.62), trk["S"].animate.set_value(2.7), rate_func=smooth)
        self.play_until(tf("cm", "L3_end", 0.86), trk["b"].animate.set_value(1.0), trk["beta"].animate.set_value(0.0),
                        trk["alpha"].animate.set_value(-(PI / 2 - 0.6)), trk["S"].animate.set_value(3.9),
                        trk["cy"].animate.set_value(FC[1] + 0.1), rate_func=smooth)
        cg = tex(r"\mathbb{C}^g/\Lambda", 40, WHITE_).move_to(FC + DOWN * 2.15 + RIGHT * 0.0)
        cg_cap = txt("many-dimensional donut", 24, GREY_).next_to(cg, RIGHT, buff=0.25)
        VGroup(cg, cg_cap).move_to([FC[0], FC[1] - 2.2, 0])
        xi2 = tex(r"\times\, i", 38, YELLOW_).move_to(O + hh * 1.55 * 1.38 * np.array([np.cos(PI / 4), np.sin(PI / 4), 0]))
        arc2 = Arc(radius=hh * 1.55, start_angle=0.12, angle=PI / 2 - 0.24, arc_center=O,
                   stroke_color=YELLOW_, stroke_width=4).add_tip(tip_length=0.18, tip_width=0.18)
        self.play_until(tf("cm", "L3_end", 0.9), FadeIn(VGroup(cg, cg_cap), shift=UP * 0.12))
        self.play_until(tf("cm", "L3_end", 0.965), Rotate(lat, PI / 2, about_point=O),
                        Create(arc2), FadeIn(xi2), rate_func=smooth)

        # ------------------------------------------------------------ 7. the claim & what it implies
        banner = result_banner("Rational Hodge conjecture for all CM abelian varieties", size=30, lean=False)
        banner.move_to([0, 2.45, 0])
        lat_all = VGroup(lat, lab0, lab1_, labi, zi, arc2, xi2, cg, cg_cap)
        self.play(FadeOut(lat_all, shift=LEFT * 0.4), FadeOut(h2, shift=UP * 0.3),
                  FadeIn(banner, shift=DOWN * 0.25, rate_func=late),
                  trk["op"].animate.set_value(0.0), trk["S"].animate.set_value(2.0),
                  trk["cy"].animate.set_value(1.6), run_time=0.7)
        fmesh.clear_updaters()
        self.remove(fmesh)

        # Tate box (left), via Milne
        boxL = RoundedRectangle(width=5.9, height=3.45, corner_radius=0.16, stroke_color=ACC, stroke_width=2,
                                fill_color=CARD, fill_opacity=0.85).move_to([0, -0.95, 0])
        tate_t = bold("Tate conjecture", 32, WHITE_)
        tate_s = txt("abelian varieties over finite fields", 24, GREY_)
        VGroup(tate_t, tate_s).arrange(DOWN, buff=0.12).next_to(boxL.get_top(), DOWN, buff=0.28)
        arrow = Arrow(np.array([0, banner.get_bottom()[1] - 0.04, 0]),
                      np.array([0, boxL.get_top()[1] + 0.04, 0]), buff=0,
                      stroke_color=WHITE_, stroke_width=5, max_tip_length_to_length_ratio=0.3)
        milne = txt("Milne (1999, 2002)", 24, WHITE_).next_to(arrow, RIGHT, buff=0.2)
        self.play(GrowArrow(arrow), FadeIn(milne, shift=LEFT * 0.15), run_time=0.8)
        self.play_until(tf("tate", "k3", 0.45), FadeIn(boxL), Write(tate_t))
        # points of y^2 = x^3 - x over F_17
        p_ = 17
        sp = 0.112
        g0 = boxL.get_center() + DOWN * 0.5
        fgrid_dots = VGroup()
        lit = VGroup()
        for x in range(p_):
            for y in range(p_):
                pos = g0 + np.array([(x - 8) * sp, (y - 8) * sp, 0])
                if (y * y - (x ** 3 - x)) % p_ == 0:
                    lit.add(Dot(pos, radius=0.055, color=YELLOW_))
                else:
                    fgrid_dots.add(Dot(pos, radius=0.02, color=GREY_, fill_opacity=0.5))
        fp_lab = VGroup(tex(r"y^2=x^3-x", 32, WHITE_), tex(r"\text{over }\mathbb{F}_{17}", 30, GREY_))
        fp_lab.arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        fp_lab.next_to(fgrid_dots, RIGHT, buff=0.4)
        fp_grp = VGroup(fgrid_dots, lit, fp_lab)
        fp_grp.move_to(g0)
        self.wait_until(tf("tate", "k3", 0.6))
        self.play(FadeIn(tate_s, shift=UP * 0.1), FadeIn(fgrid_dots), FadeIn(fp_lab), run_time=0.6)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in lit], lag_ratio=0.15),
                  run_time=max(0.6, tf("tate", "k3", 1.0) - self.now))
        tw = {"t": 0.0}
        phases = np.random.default_rng(3).uniform(0, TAU, len(lit))

        def twinkle(m, dt):
            tw["t"] += dt
            for d, ph in zip(m, phases):
                d.set_fill(opacity=0.65 + 0.35 * np.sin(2.2 * tw["t"] + ph))
        lit.add_updater(twinkle)

        # companion papers (right)
        boxR = RoundedRectangle(width=5.9, height=3.45, corner_radius=0.16, stroke_color=ACC, stroke_width=2,
                                fill_color=CARD, fill_opacity=0.85).move_to([3.45, -0.95, 0])
        comp = caps("COMPANION PAPERS", size=22, color=ACC, spacing=0.035)
        same = bold("same claim for", 28, WHITE_)
        prod = MathTex(r"S_1", r"\times", r"S_2", r"\times", r"\cdots", r"\times", r"S_n", font_size=50, color=WHITE_)
        k3c = txt("products of K3 surfaces", 26, GREY_)
        VGroup(comp, same, prod, k3c).arrange(DOWN, buff=0.28).move_to(boxR)
        tate_grp = VGroup(arrow, milne, boxL, tate_t, tate_s, fp_grp)
        self.wait_until("k3")
        self.play(tate_grp.animate.shift(LEFT * 3.45), FadeIn(boxR, shift=LEFT * 1.2),
                  FadeIn(comp, shift=LEFT * 1.2), run_time=0.8)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.5)
        self.wait_until(tf("k3", "L4_end", 0.38))
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in prod], lag_ratio=0.18),
                  FadeIn(k3c, shift=UP * 0.1), run_time=1.4)
        self.play(Circumscribe(banner[0], color=YELLOW_, buff=0.06, time_width=0.6), run_time=1.4)
        self.finish()
