import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import hashlib
from math import comb

import numpy as np

CACHE = BUILD / "cache" / "c7_hilbert16"
ATTR = YELLOW_      # attracting limit cycle
REPL = ORANGE_      # repelling limit cycle
FLOW = BLUE_        # particles


# =====================================================================
#  Genuinely polynomial planar vector fields
# =====================================================================
def swirl_field(P):
    """x' = x - 2y - (x+y)(x^2+y^2),  y' = 2x + y + (x-y)(x^2+y^2)   (degree 3).
    In polar form r' = r(1 - r^2), theta' = 2 + r^2: one attracting limit
    cycle, the unit circle, with twisted spiral arms around it."""
    x, y = P[..., 0], P[..., 1]
    r2 = x * x + y * y
    return np.stack([x - 2 * y - (x + y) * r2, 2 * x + y + (x - y) * r2], -1)


def lienard_coefs(roots_s, kappa, eps):
    """Odd F(x) = eps * sum a_k x^k whose averaged (Melnikov) function has
    simple zeros at r^2 = roots_s  ->  one limit cycle near each radius."""
    poly = np.poly1d([1.0])
    for s in roots_s:
        poly = poly * np.poly1d([1.0, -s])
    c = (poly * kappa).coeffs[::-1]
    return {2 * j + 1: eps * cj / (comb(2 * j + 2, j + 1) / 2 ** (2 * j + 2))
            for j, cj in enumerate(c)}


def lienard_field(coefs):
    """Lienard system x' = y - F(x), y' = -x  (polynomial of degree deg F)."""
    ks = sorted(coefs)

    def F(x):
        return sum(coefs[k] * x ** k for k in ks)

    def f(P):
        x, y = P[..., 0], P[..., 1]
        return np.stack([y - F(x), -x], -1)
    return f


# degree-7 Lienard with three nested cycles (attracting / repelling / attracting)
HIL_COEFS = lienard_coefs([1.0, 1.8 ** 2, 2.6 ** 2], 1.0, 0.008)
# quintic Lienard with exactly two cycles (inner repelling, outer attracting)
LIE_COEFS = lienard_coefs([1.1 ** 2, 2.2 ** 2], 1.0, 0.05)
hil_field = lienard_field(HIL_COEFS)
lie_field = lienard_field(LIE_COEFS)


def _key(*parts):
    return hashlib.md5(repr(parts).encode()).hexdigest()[:12]


def find_cycles(field, y_lo, y_hi, n=60):
    """Limit cycles crossing the section {x = 0, y > 0}: zeros of the
    displacement map d(y) = Pi(y) - y.  Returns [(points, stable), ...]."""
    from scipy.integrate import solve_ivp
    from scipy.optimize import brentq

    def rhs(t, p):
        return field(np.asarray(p)[None])[0]

    def disp(y0):
        ev = lambda t, p: p[0]
        ev.direction, ev.terminal = 1, True
        big = lambda t, p: abs(p[0]) + abs(p[1]) - 40
        big.terminal = True
        sol = solve_ivp(rhs, [0, 80], [1e-9, y0], events=[ev, big], rtol=1e-10,
                        atol=1e-12, max_step=0.01)
        return sol.y_events[0][0][1] - y0 if len(sol.t_events[0]) else np.inf

    ys = np.linspace(y_lo, y_hi, n)
    d = np.array([disp(y) for y in ys])
    out = []
    for i in range(n - 1):
        if np.isfinite(d[i]) and np.isfinite(d[i + 1]) and np.sign(d[i]) != np.sign(d[i + 1]):
            y0 = brentq(disp, ys[i], ys[i + 1], xtol=1e-11)
            ev = lambda t, p: p[0]
            ev.direction, ev.terminal = 1, True
            sol = solve_ivp(rhs, [0, 80], [1e-9, y0], events=[ev], rtol=1e-11,
                            atol=1e-12, max_step=0.005)
            pts = sol.y.T
            stable = d[i] > 0 > d[i + 1]
            out.append((pts, bool(stable)))
    return out


def cached_cycles(name, field_key, field, y_lo, y_hi):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"cyc_{name}_{_key(field_key, y_lo, y_hi)}.npz"
    if f.exists():
        z = np.load(f)
        return [(z[f"p{i}"], bool(z[f"s{i}"])) for i in range(int(z["n"]))]
    cyc = find_cycles(field, y_lo, y_hi)
    np.savez(f, n=len(cyc), **{f"p{i}": p for i, (p, _) in enumerate(cyc)},
             **{f"s{i}": s for i, (_, s) in enumerate(cyc)})
    return cyc


def display_field(field, smax):
    """Same orbits, speed softly capped (keeps far-field particles on screen)."""
    def w(P):
        v = field(P)
        s = np.linalg.norm(v, axis=-1, keepdims=True)
        return v / np.sqrt(1 + (s / smax) ** 2)
    return w


def rk4(w, P0, nsteps, h):
    out = np.empty((nsteps + 1,) + P0.shape)
    P = P0.copy()
    out[0] = P
    for i in range(nsteps):
        k1 = w(P)
        k2 = w(P + h / 2 * k1)
        k3 = w(P + h / 2 * k2)
        k4 = w(P + h * k3)
        P = np.clip(P + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4), -60, 60)
        out[i + 1] = P
    return out


def mt(*parts, size=40, color=WHITE_):
    """Multi-part MathTex in the house style."""
    return MathTex(*parts, font_size=size, color=color)


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# =====================================================================
#  Rendering helpers
# =====================================================================
class Trail(VMobject):
    """Particle trail; the stroke gradient runs from tail (transparent) to head."""

    def get_gradient_start_and_end_points(self):
        return self.points[0], self.points[-1]


class Flow(VGroup):
    """~100 particles with fading trails following a polynomial vector field.
    Trajectories are precomputed (RK4); the updater only interpolates.
    Opacity is driven by `self.op` (ValueTracker), time direction by `self.rate`."""

    def __init__(self, name, field, field_key, center, scale, seed_box, n=100,
                 life=3.2, K=9, lag=0.042, speed=1.4, smax=2.2, t0=0.0, t1=20.0,
                 mask=None, color=FLOW, width=2.4, max_op=0.9, seed=1):
        super().__init__()
        self.c = np.array(center, dtype=float)[:2]
        self.s = float(scale)
        self.L, self.K, self.lag = life, K, lag
        self.dts = 1 / 60
        self.mask = mask or (lambda X, Y: np.ones_like(X))
        self.max_op = max_op
        self.op = ValueTracker(0.0)
        self.rate = ValueTracker(1.0)
        self.tau = t0
        rng = np.random.default_rng(seed)
        self.phi = (np.arange(n) + rng.random(n)) / n * life
        self.kmin = int(np.floor((t0 - 3.0) / life)) - 1
        kmax = int(np.ceil((t1 + 3.0 + life) / life)) + 1
        nk = kmax - self.kmin + 1
        S = int(round(life / self.dts)) + 1
        CACHE.mkdir(parents=True, exist_ok=True)
        f = CACHE / f"flow_{name}_{_key(field_key, center, scale, seed_box, n, life, speed, smax, t0, t1, seed)}.npy"
        if f.exists():
            self.traj = np.load(f)
        else:
            starts = np.empty((n, nk, 2))
            for i in range(n):
                for k in range(nk):
                    tstart = (self.kmin + k) * life - self.phi[i]
                    x0, x1, y0, y1 = seed_box(tstart)
                    sx, sy = rng.uniform(x0, x1), rng.uniform(y0, y1)
                    starts[i, k] = (np.array([sx, sy]) - self.c) / self.s
            w = display_field(field, smax)
            tr = rk4(w, starts.reshape(-1, 2), S, speed * self.dts)  # (S+1, n*nk, 2)
            self.traj = np.ascontiguousarray(
                tr.transpose(1, 0, 2).reshape(n, nk, S + 1, 2)).astype(np.float32)
            np.save(f, self.traj)
        self.nk = nk
        self.S = S
        rgb = color_to_rgb(color)
        self.rgbas = np.zeros((n, 2, 4))
        self.rgbas[:, :, :3] = rgb
        for i in range(n):
            t = Trail(stroke_width=width)
            t.set_stroke(color, width=width, opacity=0)
            t.set_fill(opacity=0)
            t.set_points_as_corners([ORIGIN, RIGHT * 1e-3])
            self.add(t)
        self._idx = np.arange(n)[:, None]
        self._hidden = False
        self.add_updater(lambda m, dt: m.step(dt))
        self.step(0)

    def to_screen(self, P):
        return self.c + self.s * P

    def step(self, dt):
        r = self.rate.get_value()
        self.tau += r * dt
        op = self.op.get_value()
        if op <= 1e-3:
            if not self._hidden:
                for t in self.submobjects:
                    t.stroke_rgbas = np.array([[0, 0, 0, 0.0]])
                self._hidden = True
            return
        self._hidden = False
        L, K = self.L, self.K
        u = self.tau + self.phi
        k = np.floor(u / L)
        s = u - k * L
        ki = np.clip(k.astype(int) - self.kmin, 0, self.nk - 1)[:, None]
        sj = s[:, None] - np.arange(K)[None, :] * self.lag * r
        sj = np.clip(sj, 0, L - 1e-6)
        fi = sj / self.dts
        i0 = np.minimum(fi.astype(int), self.S - 1)
        fr = (fi - i0)[..., None]
        A = self.traj[self._idx, ki, i0]
        B = self.traj[self._idx, ki, i0 + 1]
        pts = self.to_screen(A + (B - A) * fr)          # (n, K, 2) head first
        env = smooth01(s / 0.35) * smooth01((L - s) / 0.7)
        alpha = env * self.mask(pts[:, 0, 0], pts[:, 0, 1]) * op * self.max_op
        P3 = np.zeros(pts.shape[:2] + (3,))
        P3[..., :2] = pts[:, ::-1]                       # tail -> head
        a, b = P3[:, :-1], P3[:, 1:]
        bez = np.stack([a, a + (b - a) / 3, a + 2 * (b - a) / 3, b], axis=2)
        bez = bez.reshape(len(pts), -1, 3)
        self.rgbas[:, 1, 3] = alpha
        for i, t in enumerate(self.submobjects):
            t.points = bez[i]
            t.stroke_rgbas = self.rgbas[i]


def arrow_field(field, center, scale, xs, ys, mask, color=GREY_, op=0.42,
                length=0.27, width=1.5):
    c = np.array(center, dtype=float)[:2]
    g = VGroup()
    for X in xs:
        for Y in ys:
            m = float(mask(np.array([X]), np.array([Y]))[0])
            p = (np.array([X, Y]) - c) / scale
            v = field(p[None])[0]
            sp = np.linalg.norm(v)
            if sp < 1e-9:
                continue
            d = np.array([v[0], v[1], 0.0]) / sp
            L = length * (0.55 + 0.45 * np.tanh(sp / 1.2))
            mid = np.array([X, Y, 0.0])
            tail, head = mid - d * L / 2, mid + d * L / 2
            tl, tw = 0.085, 0.055
            base = head - d * tl
            perp = np.array([-d[1], d[0], 0.0])
            a = VMobject()
            a.set_points_as_corners([tail, base])
            a.start_new_path(base + perp * tw)
            a.add_points_as_corners([head, base - perp * tw, base + perp * tw])
            a.set_stroke(color, width=width, opacity=op * m)
            a.set_fill(color, opacity=op * m)
            a.base_op = op * m
            g.add(a)
    return g


def arrows_level(arrows, lvl0, lvl1):
    """Animate all arrows' opacity between base*lvl0 and base*lvl1."""
    def upd(m, alpha):
        lv = lvl0 + (lvl1 - lvl0) * alpha
        for a in m:
            a.set_stroke(opacity=a.base_op * lv)
            a.set_fill(opacity=a.base_op * lv)
    return UpdateFromAlphaFunc(arrows, upd)


def resample_closed(pts, n=220):
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    sl = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, sl[-1], n)
    return np.stack([np.interp(t, sl, pts[:, 0]), np.interp(t, sl, pts[:, 1])], -1)


def cycle_curve(pts, center, scale, stable, width=4.5):
    P = resample_closed(pts)
    P = np.c_[np.array(center)[:2] + scale * P, np.zeros(len(P))]
    P[-1] = P[0]
    vm = VMobject().set_points_as_corners(P)
    if stable:
        vm.set_stroke(ATTR, width=width)
        return vm
    vm.set_stroke(REPL, width=width - 0.7)
    return DashedVMobject(vm, num_dashes=34, dashed_ratio=0.55).set_stroke(REPL, width=width - 0.7)


def trace_path(field, start, T, center, scale, smax=2.2, n=600):
    w = display_field(field, smax)
    tr = rk4(w, np.array([start], dtype=float), n, T / n)[:, 0]
    P = np.c_[np.array(center)[:2] + scale * tr, np.zeros(len(tr))]
    return VMobject().set_points_as_corners(P)


# =====================================================================
#  The scene
# =====================================================================
class C7Hilbert16(VoiceScene):
    def at(self, a, b, f):
        """Time a fraction f of the way from cue a to cue b."""
        return self.cue(a) + f * (self.cue(b) - self.cue(a))

    def until(self, t, *anims, **kw):
        """play_until with a numeric time (no-op guard for tiny gaps)."""
        self.play_until(t, *anims, **kw)

    def construct(self):
        C1 = np.array([-2.3, -0.15, 0.0])    # main phase-plane origin on screen
        SA, SB = 2.0, 1.0                     # scale: swirl field, Hilbert field
        C2, S2 = np.array([-3.35, -0.55, 0.0]), 0.8   # quintic Lienard plane

        # ---------------------------------------------------------- masks
        mx = ValueTracker(9.0)                             # right fade edge (hook)

        def mask_a(X, Y):
            return smooth01((mx.get_value() - X) / 1.1)

        def right_fade(X, Y):
            return smooth01((0.95 - X) / 1.1)

        def mask_b(X, Y):
            return smooth01((0.95 - X) / 1.1) * smooth01((X + 5.85) / 0.9)

        def lie_mask(X, Y):
            return (smooth01((X + 6.75) / 0.5) * smooth01((-0.3 - X) / 0.6)
                    * smooth01((Y + 2.95) / 0.45) * smooth01((1.95 - Y) / 0.45))

        t_close = self.at("L0", "L0_end", 0.66)

        def seed_a(t):
            return (-7.3, 7.3, -4.1, 4.1) if t < t_close else (-7.3, 1.2, -4.1, 4.1)

        # ---------------------------------------------------------- cycles
        th = np.linspace(0, 2 * PI, 400)
        swirl_cyc = np.stack([np.cos(th), np.sin(th)], -1)          # r = 1 exactly
        hil_cyc = cached_cycles("hil", HIL_COEFS, hil_field, 0.3, 3.5)
        lie_cyc = cached_cycles("lie", LIE_COEFS, lie_field, 0.3, 3.5)
        hil_cyc.sort(key=lambda c: np.abs(c[0]).max())
        lie_cyc.sort(key=lambda c: np.abs(c[0]).max())

        # ================================================================
        #  {flow}  Picture a fluid swirling on a tabletop ...
        # ================================================================
        f_a = Flow("swirl", swirl_field, "swirl-v1", C1, SA, seed_a, n=115, speed=0.7,
                   smax=2.5, t0=0.0, t1=self.cue("hilbert") + 2, mask=mask_a, seed=3)
        self.add(f_a.op, f_a.rate, mx, f_a)
        self.play(f_a.op.animate.set_value(1.0), run_time=max(0.3, self.cue("flow") + 0.3))

        gx = np.arange(-6.75, 1.6, 0.62)
        gy = np.arange(-3.45, 3.5, 0.62)
        arr = arrow_field(swirl_field, C1, SA, gx, gy, right_fade, op=0.38)
        arr_hil = arrow_field(hil_field, C1, SB, gx, gy, mask_b, op=0.38)

        # "... where the velocity at every point ..."
        self.wait_until(self.at("L0", "L0_end", 0.38))
        order = sorted(range(len(arr)), key=lambda i: np.linalg.norm(arr[i].get_center() - C1))
        self.play(LaggedStart(*[FadeIn(arr[i], scale=0.4) for i in order], lag_ratio=0.006),
                  run_time=1.4)
        self.remove(*arr)
        self.add(arr)
        self.bring_to_front(f_a)

        # "... is given by polynomials."
        e1 = mt(r"\dot x", "=", r"x-2y-(x+y)(x^2+y^2)", size=42)
        e2 = mt(r"\dot y", "=", r"2x+y+(x-y)(x^2+y^2)", size=42)
        e2.next_to(e1, DOWN, buff=0.26)
        e2.shift((e1[1].get_center()[0] - e2[1].get_center()[0]) * RIGHT)
        eq = VGroup(e1, e2).move_to([3.85, 2.25, 0])
        rhs = VGroup(e1[2], e2[2])
        br = Brace(rhs, DOWN, buff=0.16, color=GREY_)
        br_lab = txt("polynomials in x and y", 26, YELLOW_).next_to(br, DOWN, buff=0.12)
        self.wait_until(t_close)
        self.play(mx.animate.set_value(1.05), Write(eq), run_time=1.2)
        self.play_until("L0_end", rhs.animate.set_color(YELLOW_), GrowFromCenter(br),
                        FadeIn(br_lab, shift=UP * 0.1))

        # ================================================================
        #  {cycle}  Some paths settle into isolated loops ...
        # ================================================================
        v_cyc = cycle_curve(swirl_cyc, C1, SA, True, width=5)
        v_glow = glow(v_cyc, ATTR, layers=5, width=18, opacity=0.07)
        self.wait_until("cycle")
        self.play(Create(v_cyc), FadeIn(v_glow), f_a.op.animate.set_value(0.65),
                  arrows_level(arr, 1.0, 0.6), rate_func=smooth,
                  run_time=self.at("L1", "L1_end", 0.27) - self.now)

        # "... called limit cycles"
        ang = -0.62
        anchor = C1 + SA * np.array([np.cos(ang), np.sin(ang), 0])
        lab = bold("limit cycle", 36, ATTR).move_to([2.5, -1.35, 0])
        sub_a = txt("attracting", 26, WHITE_).next_to(lab, DOWN, buff=0.14, aligned_edge=LEFT)
        sub_r = txt("repelling  (flow reversed)", 26, REPL).next_to(lab, DOWN, buff=0.14, aligned_edge=LEFT)
        ptr = Line(lab.get_left() + LEFT * 0.12, anchor + (lab.get_left() - anchor) * 0.05,
                   stroke_width=2, color=ATTR)
        dot_a = Dot(anchor, radius=0.055, color=ATTR)
        self.wait_until(self.at("L1", "L1_end", 0.38))
        self.play(FadeIn(lab, shift=LEFT * 0.15), Create(ptr), FadeIn(dot_a), run_time=0.7)

        # "... nearby paths spiral toward them ..."
        tr_in = trace_path(swirl_field, (0.05, 0.03), 6.2, C1, SA, smax=2.5)
        tr_out = trace_path(swirl_field, (-1.95, 1.42), 2.6, C1, SA, smax=2.5)
        for tpath in (tr_in, tr_out):
            tpath.set_stroke(WHITE_, width=2.6, opacity=0.95)
        heads = VGroup(*[Dot(tp.get_start(), radius=0.065, color=WHITE_) for tp in (tr_in, tr_out)])
        for d_, tp in zip(heads, (tr_in, tr_out)):
            d_.add_updater(lambda m, tp=tp: m.move_to(tp.points[-1]))
        self.wait_until(self.at("L1", "L1_end", 0.58))
        self.add(heads)
        self.play_until(self.at("L1", "L1_end", 0.86),
                        Create(tr_in, rate_func=linear), Create(tr_out, rate_func=linear),
                        FadeIn(sub_a, shift=UP * 0.1))

        # "... or away."   (reverse time: the same loop now repels)
        v_dash = cycle_curve(swirl_cyc, C1, SA, False, width=5)
        self.play_until("hilbert",
                        f_a.rate.animate.set_value(-1.0),
                        Uncreate(tr_in, rate_func=linear), Uncreate(tr_out, rate_func=linear),
                        FadeOut(v_cyc), FadeOut(v_glow), FadeIn(v_dash),
                        FadeOut(sub_a, shift=UP * 0.1), FadeIn(sub_r, shift=UP * 0.1),
                        lab.animate.set_color(REPL), ptr.animate.set_color(REPL),
                        dot_a.animate.set_color(REPL))
        for d_ in heads:
            d_.clear_updaters()

        # ================================================================
        #  {hilbert}  In 1900, as part of his sixteenth problem ...
        # ================================================================
        f_b = Flow("hil", hil_field, HIL_COEFS, C1, SB, lambda t: (-6.0, 1.2, -4.1, 4.1),
                   n=110, t0=self.now, t1=self.cue("claim") + 2, mask=mask_b, seed=5)
        self.add(f_b.op, f_b.rate, f_b)
        head = serif("Hilbert, 1900", 54).move_to([3.75, 3.0, 0])
        prob = bold("Problem 16", 32, YELLOW_).next_to(head, DOWN, buff=0.16)
        g1 = mt(r"\dot x", "=", "P(x,y)", size=46)
        g2 = mt(r"\dot y", "=", "Q(x,y)", size=46)
        g2.next_to(g1, DOWN, buff=0.28)
        g2.shift((g1[1].get_center()[0] - g2[1].get_center()[0]) * RIGHT)
        geq = VGroup(g1, g2).move_to([3.75, 1.2, 0])
        gbr = Brace(geq, DOWN, buff=0.16, color=GREY_)
        gbr_lab = txt("polynomials of degree ≤ d", 26, YELLOW_).next_to(gbr, DOWN, buff=0.12)
        self.play(FadeOut(VGroup(lab, ptr, dot_a, sub_r, v_dash, heads)),
                  Transform(arr, arr_hil),
                  f_a.op.animate.set_value(0.0), f_b.op.animate.set_value(1.0),
                  FadeOut(eq, shift=DOWN * 0.3), FadeOut(br), FadeOut(br_lab),
                  Write(head), run_time=1.2)
        self.remove(f_a)
        self.wait_until(self.at("hilbert", "quad", 0.2))
        self.play(FadeIn(prob, shift=UP * 0.15), FadeIn(geq, shift=UP * 0.2),
                  GrowFromCenter(gbr), FadeIn(gbr_lab), run_time=1.0)

        # "... Hilbert asked how many limit cycles ..."
        hc = [cycle_curve(p, C1, SB, st, width=4.6) for p, st in hil_cyc]
        hglow = [glow(c_, ATTR, layers=4, width=14, opacity=0.06) if st else VGroup()
                 for c_, (_, st) in zip(hc, hil_cyc)]
        title_q = mt(r"\#\,\text{limit cycles}", r"\le", "?", size=44)
        title_q[2].set_color(YELLOW_)
        title_q.move_to([3.75, -1.2, 0])
        nums = [tex(r"=\," + str(i + 1), size=44).next_to(title_q[0], RIGHT, buff=0.2)
                for i in range(len(hc))]
        leg_a = VGroup(Line(ORIGIN, RIGHT * 0.5, color=ATTR, stroke_width=4.5),
                       txt("attracting", 24, GREY_)).arrange(RIGHT, buff=0.18)
        leg_r = VGroup(DashedLine(ORIGIN, RIGHT * 0.5, color=REPL, stroke_width=3.8, dash_length=0.09),
                       txt("repelling", 24, GREY_)).arrange(RIGHT, buff=0.18)
        legend = VGroup(leg_a, leg_r).arrange(RIGHT, buff=0.5).move_to([3.75, -2.6, 0])
        t_a, t_b = self.at("hilbert", "quad", 0.42), self.at("hilbert", "quad", 0.72)
        self.wait_until(t_a)
        step = (t_b - t_a) / len(hc)
        self.play(FadeIn(title_q[0]), FadeIn(nums[0]), Create(hc[0]), FadeIn(hglow[0]),
                  arrows_level(arr, 1.0, 0.65), FadeIn(legend), run_time=step)
        for i in range(1, len(hc)):
            self.play(Create(hc[i]), FadeIn(hglow[i]), ReplacementTransform(nums[i - 1], nums[i]),
                      run_time=step)
        # "... can such a flow have.  It's notoriously hard."
        self.until(self.at("hilbert", "quad", 0.84),
                   ReplacementTransform(nums[-1], VGroup(title_q[1], title_q[2])))
        self.add(title_q)
        self.until(self.at("hilbert", "quad", 0.98),
                   Indicate(title_q[2], color=YELLOW_, scale_factor=1.5))

        # ================================================================
        #  {quad}  Even for degree two, nobody knew whether one upper
        #          limit covers every such flow.
        # ================================================================
        AXY, AXX = -2.65, 1.3
        cols = [2.0, 2.9, 3.8, 4.7, 5.6]
        x_axis = Line([AXX - 0.05, AXY, 0], [6.6, AXY, 0], color=GREY_, stroke_width=2.2)
        y_axis = Line([AXX, AXY, 0], [AXX, 2.0, 0], color=GREY_, stroke_width=2.2)
        d_lab = tex("d=", size=34, color=GREY_)
        tick_lab = [tex(str(d), size=34, color=WHITE_ if d == 2 else GREY_).move_to([x, AXY - 0.33, 0])
                    for d, x in zip(range(2, 7), cols)]
        dots_lab = tex(r"\cdots", size=34, color=GREY_).move_to([6.3, AXY - 0.33, 0])
        d_lab.next_to(tick_lab[0], LEFT, buff=0.12)
        loops = VGroup(*[Ellipse(width=0.56, height=0.3, color=ATTR, stroke_width=3)
                         .move_to([cols[0], AXY + 0.3 + 0.4 * i, 0]) for i in range(4)])
        known = VGroup(txt("4 found", 28, WHITE_), txt("(1979–80)", 24, GREY_)).arrange(
            DOWN, buff=0.08, aligned_edge=LEFT)
        known.next_to(loops, RIGHT, buff=0.3)
        up = DashedLine([cols[0], loops.get_top()[1] + 0.12, 0], [cols[0], 1.7, 0], color=GREY_,
                        stroke_width=2.6, dash_length=0.12)
        up_tip = Triangle(color=GREY_, fill_opacity=1, stroke_width=0).scale(0.08).move_to([cols[0], 1.75, 0])
        qbig = tex("?", size=60, color=YELLOW_).move_to([cols[0], 2.2, 0])
        one = VGroup(txt("one bound for", 26, WHITE_), txt("every degree-2 flow?", 26, WHITE_)).arrange(
            DOWN, buff=0.1, aligned_edge=LEFT).move_to([cols[0] + 0.45, 1.05, 0], aligned_edge=LEFT)

        self.wait_until("quad")
        self.play(FadeOut(VGroup(head, prob, geq, gbr, gbr_lab, legend), shift=UP * 0.2),
                  title_q.animate.move_to([3.95, 3.05, 0]), run_time=0.8)
        self.until(self.at("quad", "L2_end", 0.2),
                   Create(x_axis), Create(y_axis), FadeIn(d_lab), FadeIn(tick_lab[0]))
        self.until(self.at("quad", "L2_end", 0.42),
                   LaggedStart(*[Create(l_) for l_ in loops], lag_ratio=0.35),
                   FadeIn(known, shift=LEFT * 0.1))
        # "... nobody knew whether one upper limit covers every such flow."
        self.until(self.at("quad", "L2_end", 0.6),
                   Create(up), FadeIn(up_tip, shift=UP * 0.6), rate_func=smooth)
        self.until(self.at("quad", "L2_end", 0.72), FadeIn(qbig, scale=0.5),
                   FadeIn(one, shift=RIGHT * 0.1))
        self.until(self.at("quad", "L2_end", 0.98),
                   Wiggle(qbig, scale_value=1.25), up.animate.set_opacity(0.5))

        # ================================================================
        #  {claim}  This paper claims that for every degree, there is a
        #           finite ceiling.
        # ================================================================
        card = paper_card("143", width=3.45).move_to([-3.35, 0.25, 0])
        tag = paper_tag("143", color=YELLOW_)
        if CATALOG["143"].get("lean"):
            tag[1].remove(tag[1][-1])          # Lean covers only the Lienard companion
        card.shift(LEFT * 6.5)
        hc_all = VGroup(*hc, *hglow)
        self.wait_until("claim")
        self.add(card)
        self.play(card.animate.shift(RIGHT * 6.5),
                  f_b.op.animate.set_value(0.0), FadeOut(arr), FadeOut(hc_all),
                  FadeIn(tag, shift=RIGHT * 0.3),
                  FadeOut(VGroup(qbig, one, known), shift=UP * 0.2), FadeOut(up_tip),
                  Uncreate(up), run_time=0.9)
        self.remove(f_b)

        heights = [-0.7, -0.25, 0.15, 0.5, 0.8]
        ceil, regions, clabs = VGroup(), VGroup(), VGroup()
        for x, h, d in zip(cols, heights, range(2, 7)):
            cl = Line([x - 0.36, h, 0], [x + 0.36, h, 0], color=YELLOW_, stroke_width=6)
            rg = Rectangle(width=0.72, height=h - AXY, stroke_width=0)
            rg.set_fill([YELLOW_, YELLOW_], opacity=[0.0, 0.2]).set_sheen_direction(UP)
            rg.move_to([x, (h + AXY) / 2, 0])
            lb = tex(f"B({d})", size=26, color=GREY_).next_to(cl, UP, buff=0.1)
            ceil.add(cl), regions.add(rg), clabs.add(lb)
        self.until(self.at("claim", "exists", 0.45),
                   LaggedStart(*[FadeIn(t_, shift=UP * 0.15) for t_ in tick_lab[1:] + [dots_lab]],
                               lag_ratio=0.2),
                   tick_lab[0].animate.set_color(GREY_))
        # "... there is a finite ceiling."
        title_c = mt(r"\#\,\text{limit cycles}", r"\le", r"B(d)", r"<\infty", size=44)
        title_c[2].set_color(YELLOW_)
        title_c.move_to([3.95, 3.05, 0])
        every = txt("for every degree d", 26, GREY_).move_to([3.95, 2.45, 0])
        drops = []
        for cl, rg, lb in zip(ceil, regions, clabs):
            g = VGroup(cl, lb)
            src = g.copy().shift(UP * 0.9).set_opacity(0)
            drops.append(AnimationGroup(ReplacementTransform(src, g, rate_func=rush_into), FadeIn(rg)))
        self.until(self.at("claim", "exists", 0.97),
                   LaggedStart(*drops, lag_ratio=0.18),
                   ReplacementTransform(title_q[0], title_c[0]),
                   ReplacementTransform(title_q[1], title_c[1]),
                   FadeTransform(title_q[2], VGroup(title_c[2], title_c[3])),
                   FadeIn(every, shift=DOWN * 0.1))
        self.add(regions, ceil, clabs, title_c)

        # ================================================================
        #  {exists}  It doesn't compute it, but it proves it exists.
        # ================================================================
        base_h = list(heights)
        phase = [0.0, 1.3, 2.4, 3.7, 4.9]
        clock = ValueTracker(0.0)
        bob_amp = ValueTracker(0.0)
        pulse = ValueTracker(0.0)

        def bob(i):
            def upd(m):
                h = base_h[i] + bob_amp.get_value() * np.sin(2 * PI * 0.45 * clock.get_value() + phase[i])
                m.set_y(h)
                m.set_stroke(width=6 + 5 * pulse.get_value())
                clabs[i].next_to(m, UP, buff=0.1)
                regions[i].stretch_to_fit_height(h - AXY).set_y((h + AXY) / 2)
            return upd
        clock.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(clock, bob_amp, pulse)
        for i in range(len(ceil)):
            ceil[i].add_updater(bob(i))
        not_comp = chip("value not computed", GREY_, size=22)
        exists = chip("exists", YELLOW_, size=22)
        chips_ = VGroup(exists, not_comp).arrange(RIGHT, buff=0.25).move_to([3.95, 1.8, 0])
        self.wait_until("exists")
        self.play(bob_amp.animate.set_value(0.16), FadeIn(not_comp, shift=UP * 0.1), run_time=0.8)
        self.wait_until(self.at("exists", "lienard", 0.5))
        self.until(min(self.now + 1.2, self.cue("lienard") - 0.05),
                   FadeIn(exists, shift=UP * 0.1),
                   pulse.animate(rate_func=there_and_back).set_value(1.0))

        # ================================================================
        #  {lienard}  A companion pins down one classic case exactly: a
        #             degree-five oscillator family has at most two limit cycles.
        # ================================================================
        banner = result_banner(
            r"\#\{\text{limit cycles}\}\ \le\ B(d)<\infty\quad\text{for every degree-}d\text{ polynomial field}",
            color=YELLOW_, is_tex=True, size=34)
        banner.move_to([0, 2.85, 0])
        banner[0].set_z_index(-1)
        chart = VGroup(x_axis, y_axis, d_lab, *tick_lab, dots_lab, loops, regions, ceil, clabs, every, chips_)
        self.wait_until("lienard")
        for c_ in ceil:
            c_.clear_updaters()
        self.play(FadeOut(chart, shift=DOWN * 0.3),
                  ReplacementTransform(title_c, banner[1][1]),
                  FadeIn(banner[0]), FadeIn(banner[1][0]),
                  card.animate.shift(LEFT * 6.5), run_time=1.0)
        self.remove(card, clock)

        f_lie = Flow("lie", lie_field, LIE_COEFS, C2, S2, lambda t: (-6.6, -0.4, -2.9, 2.0),
                     n=75, t0=self.now, t1=self.cue("end") + 1, mask=lie_mask, seed=9,
                     width=2.2)
        self.add(f_lie.op, f_lie.rate, f_lie)
        lgx = np.arange(-6.45, -0.2, 0.55)
        lgy = np.arange(-2.75, 1.95, 0.55)
        arr_lie = arrow_field(lie_field, C2, S2, lgx, lgy, lie_mask, length=0.24, op=0.38)
        comp = VGroup(caps("companion paper", size=22, color=GREY_, spacing=0.05), lean_badge(20)).arrange(
            RIGHT, buff=0.3)
        le1 = tex(r"\dot x = y - F(x),\qquad \dot y = -x", size=44)
        le2 = mt(r"\deg F \le 5", r"\ \Longrightarrow\ ", r"\text{at most } 2", r"\text{ limit cycles}", size=40)
        le2[2].set_color(YELLOW_)
        sharp = txt("and some have exactly 2", 24, GREY_)
        lblock = VGroup(comp, le1, le2, sharp).arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        lblock.move_to([3.4, -0.45, 0])
        self.until(self.at("lienard", "L3_end", 0.27),
                   f_lie.op.animate.set_value(1.0),
                   LaggedStart(*[FadeIn(a) for a in arr_lie], lag_ratio=0.004),
                   FadeIn(comp, shift=UP * 0.1))
        # "... one classic case exactly ..."
        self.until(self.at("lienard", "L3_end", 0.42), Write(le1))
        # "... a degree-five oscillator family ..."
        self.wait_until(self.at("lienard", "L3_end", 0.46))
        self.until(self.at("lienard", "L3_end", 0.62), Write(le2[0]))
        # "... has at most two limit cycles."
        lc = [cycle_curve(p, C2, S2, st, width=4.4) for p, st in lie_cyc]
        lglow = [glow(c_, ATTR, layers=4, width=14, opacity=0.06) if st else VGroup()
                 for c_, (_, st) in zip(lc, lie_cyc)]
        nums_l = VGroup(*[tex(str(i + 1), size=30, color=ATTR if st else REPL)
                          for i, (_, st) in enumerate(lie_cyc)])
        for i, (p, st) in enumerate(lie_cyc):
            j = np.argmax(p[:, 0] + p[:, 1])
            pt = C2 + S2 * np.array([p[j, 0], p[j, 1], 0])
            nums_l[i].move_to(pt + np.array([0.22, 0.22, 0]))
        self.wait_until(self.at("lienard", "L3_end", 0.74))
        self.until(self.at("lienard", "L3_end", 0.9),
                   LaggedStart(*[AnimationGroup(Create(c_), FadeIn(g_), FadeIn(n_))
                                 for c_, g_, n_ in zip(lc, lglow, nums_l)], lag_ratio=0.5),
                   arrows_level(arr_lie, 1.0, 0.6), f_lie.op.animate.set_value(0.7),
                   Write(le2[1:]))
        self.until(min(self.now + 0.6, self.cue("end-0.55")), FadeIn(sharp, shift=UP * 0.1))

        # ---------------------------------------------------------- out
        self.wait_until("end-0.5")
        rest = [m for m in self.mobjects if m not in (f_lie, f_lie.op, f_lie.rate)
                and not isinstance(m, ValueTracker)]
        self.play(*[FadeOut(m) for m in rest], f_lie.op.animate.set_value(0.0),
                  run_time=self.narr_end - self.now)
        self.remove(f_lie)
        self.finish()
