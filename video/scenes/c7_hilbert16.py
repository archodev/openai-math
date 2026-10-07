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


