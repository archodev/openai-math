import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import re

ACC = ORANGE_
NUM = "362"
E_COL = BLUE_
B_COL = PURPLE_

# ======================================================================
# word-level timing estimate (syllable model, anchored on inline cues)
# ======================================================================
_ANCHORS = {1: [("q", "do"), ("open", "in")], 2: [("details", "global")]}


def _norm(tok):
    return re.sub(r"[^a-z0-9]", "", tok.lower())


def _syl(tok):
    w = tok.lower()
    if re.search(r"\d", w):
        return 5
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee", "ye")):
        n -= 1
    return max(1, n)


def _pause(tok):
    if tok.endswith((",", ";", ":")):
        return 1.5
    if tok.endswith((".", "?", "!")):
        return 2.5
    return 0.0


# ======================================================================
# graph curves (max |p| versus t)
# ======================================================================
TB, TSTAR, YMAX, XMAX, TEND = 2.4, 5.0, 6.0, 10.0, 9.55


def P_ok(t):
    """Largest momentum on the 'smooth' branch: grows, stays finite (no uniform bound
    is claimed, so it is NOT drawn levelling off)."""
    return 0.75 + 0.2 * t + 0.12 * np.sin(1.6 * t)


_C = 0.55


def P_bad(t):
    return P_ok(TB) + _C * (1.0 / (TSTAR - t) - 1.0 / (TSTAR - TB))


# ======================================================================
# the plasma: precomputed analytic trajectories, drawn as a few big VMobjects
# ======================================================================
N = 150
UNIT_CIRCLE = Circle(radius=1, num_components=5).points.copy()   # 4 cubic arcs


def _seg_pts(A, B):
    D = B - A
    return np.stack([A, A + D / 3, A + 2 * D / 3, B], axis=1).reshape(-1, 3)


def _tri_pts_ordered(tip, u, size):
    nrm = np.stack([-u[:, 1], u[:, 0], np.zeros(len(u))], axis=1)
    base = tip - u * size
    a, b = base + nrm * size * 0.55, base - nrm * size * 0.55
    out = []
    for i in range(len(u)):
        out += [_seg_pts(tip[i:i + 1], a[i:i + 1]), _seg_pts(a[i:i + 1], b[i:i + 1]),
                _seg_pts(b[i:i + 1], tip[i:i + 1])]
    return np.concatenate(out) if out else np.zeros((0, 3))


class Plasma(VGroup):
    """~150 one-species charged particles in a slowly swirling 3D cloud (differential
    rotation + clockwise gyration), its own radial E field and dipole B loops.
    All geometry is driven by ValueTrackers; one updater rebuilds the points."""

    def __init__(self, seed=362):
        super().__init__()
        rng = np.random.default_rng(seed)
        u = rng.random(N)
        self.R = 0.16 + 0.84 * np.sqrt(u)
        self.phi0 = rng.random(N) * TAU
        self.Om = 0.55 / (0.45 + self.R)
        self.h0 = rng.normal(0, 1, N) * 0.11 * (1.25 - 0.7 * self.R)
        self.hb = rng.uniform(0.015, 0.05, N)
        self.wb = rng.uniform(0.5, 1.1, N)
        self.pb = rng.random(N) * TAU
        self.rg = rng.uniform(0.025, 0.07, N)
        self.wg = rng.uniform(3.2, 5.5, N)
        self.pg = rng.random(N) * TAU
        # solar-wind mode (screen coordinates)
        self.S = np.array([-8.55, 0.2])
        self.Rs = 2.2
        self.thw = rng.uniform(-0.34, 0.34, N)
        self.vw = rng.uniform(1.4, 2.4, N)
        self.sw0 = rng.random(N) * 14.0
        self.Lw = 14.0
        self.dw = rng.uniform(-0.8, 0.8, N)
        self.t_lap = 1e9          # wrap-around frozen after this time (set at the morph)

        self.trk = {k: ValueTracker(v) for k, v in dict(
            cx=0.0, cy=0.05, sc=2.5, inc=60 * DEGREES, tilt=-10 * DEGREES, w=0.0,
            alpha=0.0, e0=0.0, e1=0.0, e2=0.0, b=0.0, bdraw=0.0, pulse=0.0, ripple=-1.0,
            clipx=6.9, clipy=3.65, kick=0.0, kalpha=0.0).items()}
        self.clock = 0.0
        self.tweens = []          # background tracker tweens: (key, t0, t1, v0, v1, rate_func)
        self.alive = np.ones(N, bool)
        self.kidx = None

        # E grid (local, screen-aligned)
        xs = np.arange(-2.6, 2.61, 0.34)
        ys = np.arange(-1.7, 1.71, 0.34)
        G = np.array([(x, y) for x in xs for y in ys])
        ell = np.sqrt((G[:, 0] / 1.15) ** 2 + (G[:, 1] / 0.95) ** 2)
        self.grid = []
        for lo, hi in ((1.0, 1.38), (1.38, 1.76), (1.76, 2.15)):
            sel = (ell >= lo) & (ell < hi)
            self.grid.append(G[sel])
        # B loops (local 3D, in the plane of screen-x and the rotation axis)
        # (right edge: clockwise in the (a,h) plane, so B points up inside the ring;
        #  the left edge is the mirror image)
        th = np.linspace(0, -TAU, 73)
        self.loops = []
        for r0 in (0.34, 0.6):
            for sgn in (1, -1):
                self.loops.append(np.stack([sgn * (0.92 + r0 * np.cos(th)), r0 * np.sin(th)], axis=1))

        def vm(**kw):
            m = VMobject(**kw)
            m.set_points(np.zeros((0, 3)))
            return m

        self.b_lines = vm(stroke_color=B_COL, stroke_width=2.2, fill_opacity=0)
        self.b_heads = vm(stroke_width=0, fill_color=B_COL, fill_opacity=0.8)
        self.e_lines = [vm(stroke_color=E_COL, stroke_width=2.2, fill_opacity=0) for _ in range(3)]
        self.e_heads = [vm(stroke_width=0, fill_color=E_COL, fill_opacity=0.8) for _ in range(3)]
        self.trA = vm(stroke_color=ACC, stroke_width=1.8, fill_opacity=0)
        self.trB = vm(stroke_color=ACC, stroke_width=1.4, fill_opacity=0)
        self.halo = vm(stroke_width=0, fill_color=ACC, fill_opacity=0.1)
        cols = [interpolate_color(ManimColor(ACC), ManimColor(BG), 0.45), ManimColor(ACC),
                interpolate_color(ManimColor(ACC), ManimColor(WHITE), 0.25)]
        self.cols = cols
        self.layers = [vm(stroke_width=0, fill_color=c, fill_opacity=1) for c in cols]
        # the hypothetical "kicked" particle
        self.k_trail = vm(stroke_color=RED_, stroke_width=2.5, fill_opacity=0)
        self.k_dot = Dot(radius=0.06, color=RED_)
        self.k_ring = Circle(radius=0.15, stroke_color=RED_, stroke_width=2.5)
        self.k_arrow = Arrow(ORIGIN, RIGHT, buff=0, color=RED_, stroke_width=5,
                             max_tip_length_to_length_ratio=0.2, tip_length=0.22)
        self.k_lab = MathTex("p", font_size=36, color=RED_)
        self.add(self.b_lines, self.b_heads, *self.e_lines, *self.e_heads, self.trA, self.trB,
                 self.halo, *self.layers, self.k_trail, self.k_ring, self.k_dot,
                 self.k_arrow, self.k_lab)
        self.add_updater(lambda m, dt: m.step(dt))

    # -------------------------------------------------------------- helpers
    def v(self, k):
        return self.trk[k].get_value()

    def to(self, **kw):
        return [self.trk[k].animate.set_value(v) for k, v in kw.items()]

    def project(self, a, b, h):
        inc, tl = self.v("inc"), self.v("tilt")
        ys = b * np.cos(inc) + h * np.sin(inc)
        dep = -b * np.sin(inc) + h * np.cos(inc)
        ct, st = np.cos(tl), np.sin(tl)
        return a * ct - ys * st, a * st + ys * ct, dep

    def cloud_local(self, t):
        ph = self.phi0 + self.Om * t
        ga = -(self.wg * t + self.pg)          # one species: all gyrate the same way
        a = self.R * np.cos(ph) + self.rg * np.cos(ga)
        b = self.R * np.sin(ph) + self.rg * np.sin(ga)
        h = self.h0 + self.hb * np.sin(self.wb * t + self.pb)
        return self.project(a, b, h)

    def wind(self, t):
        lap = np.floor((self.sw0 + self.vw * min(t, self.t_lap)) / self.Lw)
        s = self.sw0 + self.vw * t - lap * self.Lw
        r = self.Rs + s
        c, sn = np.cos(self.thw), np.sin(self.thw)
        wig = 0.07 * np.sin(5.0 * t + self.pg)
        x = self.S[0] + r * c - wig * sn
        y = self.S[1] + r * sn + wig * c
        return x, y, s

    def screen(self, t):
        """(N,3) screen positions + depth (N,) at time t (current trackers)."""
        cx, cy, sc, w = self.v("cx"), self.v("cy"), self.v("sc"), self.v("w")
        lx, ly, dep = self.cloud_local(t)
        X = cx + sc * lx
        Y = cy + sc * ly
        s = None
        if w < 1.0:
            ws = smooth(w)
            wx, wy, s = self.wind(t)
            X = (1 - ws) * wx + ws * X
            Y = (1 - ws) * wy + ws * Y
            dep = (1 - ws) * self.dw + ws * dep
        return np.stack([X, Y, np.zeros(N)], axis=1), dep, s

    def kicked_local(self, t):
        tau = max(0.0, t - self.k_t0)
        v0, vm, t0 = 0.25, 0.55, 0.7
        s = vm * tau - (vm - v0) * t0 * (1 - np.exp(-tau / t0))
        return self.k_p0 + self.k_dir * s

    def start_kick(self):
        t = self.clock + 0.05
        lx, ly, dep = self.cloud_local(t)
        score = -0.6 * lx + ly + 2.0 * (dep > 0.05) + 1.5 * ((lx ** 2 + ly ** 2) > 0.3)
        k = int(np.argmax(score))
        self.kidx, self.k_t0 = k, t
        self.k_p0 = np.array([lx[k], ly[k]])
        d = np.array([-0.25, 1.0])
        self.k_dir = d / np.linalg.norm(d)
        self.alive[k] = False

    # -------------------------------------------------------------- per frame
    def tween(self, key, dur, v1, rate=smooth, delay=0.0, v0=None):
        """Animate a tracker in the background (non-blocking), driven by the clock.
        The start value is read when the tween begins (unless v0 is given)."""
        self.tweens.append([key, self.clock + delay, self.clock + delay + dur, v0, v1, rate])

    def step(self, dt):
        self.clock += dt
        t = self.clock
        for tw in list(self.tweens):
            key, t0, t1, v0, v1, rf = tw
            if t < t0:
                continue
            if v0 is None:
                v0 = tw[3] = self.v(key)
            a = float(np.clip((t - t0) / (t1 - t0), 0, 1))
            self.trk[key].set_value(v0 + (v1 - v0) * rf(a))
            if a >= 1:
                self.tweens.remove(tw)
        al = self.v("alpha")
        sc, cx, cy = self.v("sc"), self.v("cx"), self.v("cy")
        dsc = float(np.clip(0.55 + 0.45 * sc / 2.3, 0.5, 1.0))
        pos, dep, s_w = self.screen(t)
        m = self.alive
        # ---- trails
        K, dlt = 7, 0.045
        hist = [pos]
        for k in range(1, K + 1):
            p, _, s2 = self.screen(t - k * dlt)
            if s_w is not None:  # collapse across wrap-around jumps
                jump = s2 > s_w + 0.01
                p[jump] = hist[-1][jump]
            hist.append(p)
        for j, k in enumerate(range(K)):
            jump = np.linalg.norm(hist[k + 1] - hist[k], axis=1) > 1.0
            hist[k + 1][jump] = hist[k][jump]
        A = np.concatenate([_seg_pts(hist[k][m], hist[k + 1][m]) for k in range(0, 3)], axis=0)
        B = np.concatenate([_seg_pts(hist[k][m], hist[k + 1][m]) for k in range(3, K)], axis=0)
        # reorder so that consecutive segments of a particle form one subpath
        nm = int(m.sum())
        A = A.reshape(3, nm, 4, 3).transpose(1, 0, 2, 3).reshape(-1, 3)
        B = B.reshape(K - 3, nm, 4, 3).transpose(1, 0, 2, 3).reshape(-1, 3)
        self.trA.set_points(A).set_stroke(opacity=0.42 * al, width=1.8 * dsc)
        self.trB.set_points(B).set_stroke(opacity=0.16 * al, width=1.4 * dsc)
        # ---- dots, three depth layers
        pu = self.v("pulse")
        rads = np.array([0.03, 0.037, 0.045]) * dsc * (1 + 0.3 * pu)
        bins = [(dep < -0.22), (dep >= -0.22) & (dep <= 0.22), (dep > 0.22)]
        for lay, sel, r in zip(self.layers, bins, rads):
            sel = sel & m
            P = pos[sel]
            lay.set_points((P[:, None, :] + r * UNIT_CIRCLE[None]).reshape(-1, 3))
            lay.set_fill(opacity=al)
        hs = (dep > -0.22) & m
        P = pos[hs]
        self.halo.set_points((P[:, None, :] + rads[2] * 2.3 * UNIT_CIRCLE[None]).reshape(-1, 3))
        self.halo.set_fill(opacity=(0.09 + 0.07 * pu) * al)
        for lay, c in zip(self.layers, self.cols):
            lay.set_fill(interpolate_color(c, ManimColor(WHITE), 0.35 * pu) if pu > 0.01 else c)
        # ---- E field (computed from the particles' projected positions)
        lx, ly, _ = self.cloud_local(t)
        Pl = np.stack([lx, ly], axis=1)
        rip = self.v("ripple")
        cxv = self.v("clipx")
        for i in range(3):
            ea = self.v(f"e{i}") * al
            g = self.grid[i]
            if ea < 1e-3 or len(g) == 0:
                self.e_lines[i].set_points(np.zeros((0, 3)))
                self.e_heads[i].set_points(np.zeros((0, 3)))
                continue
            d = g[:, None, :] - Pl[None, :, :]
            r2 = (d ** 2).sum(-1) + 0.2 ** 2
            E = (d / r2[..., None] ** 1.5).sum(1)
            u = E / np.linalg.norm(E, axis=1, keepdims=True)
            gs = np.stack([cx + sc * g[:, 0], cy + sc * g[:, 1]], axis=1)
            keep = (gs[:, 0] > -6.85) & (gs[:, 0] < cxv) & (gs[:, 1] < self.v("clipy")) & (gs[:, 1] > -3.65)
            gs, u = gs[keep], u[keep]
            L = 0.19 * sc
            u3 = np.concatenate([u, np.zeros((len(u), 1))], axis=1)
            g3 = np.concatenate([gs, np.zeros((len(gs), 1))], axis=1)
            tail, tip = g3 - u3 * L / 2, g3 + u3 * L / 2
            hsz = 0.075 * sc
            self.e_lines[i].set_points(_seg_pts(tail, tip - u3 * hsz * 0.6))
            self.e_heads[i].set_points(_tri_pts_ordered(tip, u3, hsz))
            boost = 1.0 + 1.3 * np.exp(-((rip * 3.6 - i) ** 2) / 0.5)
            op = [0.62, 0.42, 0.24][i] * ea * boost
            self.e_lines[i].set_stroke(opacity=min(1, op), width=2.2 * dsc)
            self.e_heads[i].set_fill(opacity=min(1, op))
        # ---- B loops (dipole of the rotating charge) with flowing arrowheads
        ba = self.v("b") * al
        bd = self.v("bdraw")
        if ba > 1e-3 and bd > 1e-3:
            pts, heads, dirs = [], [], []
            for lp in self.loops:
                n = max(2, int(len(lp) * bd))
                a = lp[:n, 0]
                h = lp[:n, 1]
                X, Y, _ = self.project(a, np.zeros_like(a), h)
                Q = np.stack([cx + sc * X, cy + sc * Y, np.zeros_like(X)], axis=1)
                pts.append(_seg_pts(Q[:-1], Q[1:]))
                if bd > 0.98:
                    for s0 in (0.1, 0.6):
                        f = ((s0 + 0.11 * t) % 1.0) * (len(Q) - 2)
                        j = int(f)
                        heads.append(Q[j + 1])
                        dv = Q[j + 1] - Q[j]
                        dirs.append(dv / (np.linalg.norm(dv) + 1e-9))
            self.b_lines.set_points(np.concatenate(pts)).set_stroke(opacity=0.55 * ba, width=2.0 * dsc)
            if heads:
                self.b_heads.set_points(_tri_pts_ordered(np.array(heads), np.array(dirs), 0.085 * sc))
            else:
                self.b_heads.set_points(np.zeros((0, 3)))
            self.b_heads.set_fill(opacity=0.75 * ba)
        else:
            self.b_lines.set_points(np.zeros((0, 3)))
            self.b_heads.set_points(np.zeros((0, 3)))
        # ---- kicked particle
        ka = self.v("kalpha") * al
        if self.kidx is not None and ka > 1e-3:
            p = self.kicked_local(t)
            P0 = np.array([cx + sc * p[0], cy + sc * p[1], 0])
            pp = self.kicked_local(t - 0.35)
            P1 = np.array([cx + sc * pp[0], cy + sc * pp[1], 0])
            self.k_trail.set_points(_seg_pts(P1[None], P0[None])).set_stroke(opacity=0.6 * ka)
            self.k_dot.move_to(P0).set_fill(opacity=ka)
            self.k_ring.move_to(P0).set_stroke(opacity=0.8 * ka)
            d3 = np.array([self.k_dir[0], self.k_dir[1], 0])
            ln_max = max(0.5, (3.5 - P0[1]) / d3[1] - 0.1)
            ln = 0.35 + (ln_max - 0.35) * self.v("kick")
            self.k_arrow.become(Arrow(P0 + d3 * 0.1, P0 + d3 * (0.1 + ln), buff=0, color=RED_,
                                      stroke_width=5, max_tip_length_to_length_ratio=0.35,
                                      tip_length=0.22))
            self.k_arrow.set_opacity(ka)
            self.k_lab.next_to(P0 + d3 * (0.1 + ln * 0.5), LEFT, buff=0.14)
            self.k_lab.set_opacity(ka)
        else:
            self.k_trail.set_points(np.zeros((0, 3)))
            for mob in (self.k_dot, self.k_ring, self.k_arrow, self.k_lab):
                mob.set_opacity(0)
                mob.move_to([20, 20, 0])
        return self

    def local_to_screen(self, p):
        return np.array([self.v("cx") + self.v("sc") * p[0], self.v("cy") + self.v("sc") * p[1], 0])


# ======================================================================
class C9Vlasov(VoiceScene):

    # -------------------------------------------------------------- timing
    def wt(self, li, word, nth=1, frac=0.0, fb=0.5):
        """Estimated start time of the nth occurrence of `word` in line li
        (falls back to fraction `fb` of the line if the word is gone)."""
        L = self.timing["lines"][li]
        toks = L["text"].replace("–", " ").replace("—", " ").split()
        cum, dur = [0.0], []
        for tk in toks:
            dur.append(_syl(tk) + 0.35)
            cum.append(cum[-1] + dur[-1] + _pause(tk))
        W = cum[-1] - _pause(toks[-1])
        anchors = [(0.0, L["start"])]
        for cue, w in _ANCHORS.get(li, []):
            if self.has_cue(cue):
                ks = [k for k, tk in enumerate(toks) if _norm(tk) == w]
                if ks:
                    k = ks[0]
                    lead = 0.55 if k > 0 and toks[k - 1].endswith((".", "?", "!", ":")) else 0.05
                    anchors.append((cum[k], self.cue(cue) + lead))
        anchors.append((W, L["end"]))
        anchors.sort()
        xs, ys = zip(*anchors)
        ks = [k for k, tk in enumerate(toks) if _norm(tk) == _norm(word)]
        if len(ks) < nth:
            print(f"[c9_vlasov] WARNING: word {word!r} not in line {li}; using fallback")
            return L["start"] + fb * (L["end"] - L["start"])
        k = ks[nth - 1]
        return float(np.interp(cum[k] + frac * dur[k], xs, ys))

    def wait_until(self, t, **kw):
        """Like VoiceScene.wait_until, but skips sub-frame waits (no 'too short' warnings)."""
        dt = self.cue(t) - self.now
        if dt > 1.0 / config.frame_rate - 1e-6:
            self.wait(dt, **kw)

    def span(self, t0, t1, *anims, min_rt=0.3, **kw):
        self.wait_until(t0)
        rt = max(min_rt, self.cue(t1) - self.now)
        self.play(*anims, run_time=rt, **kw)

    # -------------------------------------------------------------- build
    def construct(self):
        wt, cue = self.wt, self.cue
        pl = Plasma()
        self.pl = pl
        self.add(pl)

        # ================================================== the Sun + solar wind
        S = np.array([*pl.S, 0])
        sun = VGroup()
        for i in range(8, 0, -1):
            sun.add(Circle(radius=pl.Rs + 0.15 * i, stroke_width=0, fill_color=GOLD_,
                           fill_opacity=0.06).move_to(S))
        sun.add(Circle(radius=pl.Rs, stroke_width=0, fill_color=ORANGE_, fill_opacity=1).move_to(S))
        sun.add(Circle(radius=pl.Rs * 0.9, stroke_width=0, fill_color=GOLD_, fill_opacity=0.6).move_to(S))
        sun.add(Circle(radius=pl.Rs * 0.72, stroke_width=0, fill_color=YELLOW_, fill_opacity=0.5).move_to(S))
        wind_lab = txt("solar wind", 28, GREY_).move_to([-2.4, 2.35, 0])

        self.wait_until("plasma")
        self.play(FadeIn(sun, shift=RIGHT * 0.5), *pl.to(alpha=1.0), run_time=0.45)
        self.span(wt(0, "like") - 0.1, wt(0, "wind", frac=1.0), FadeIn(wind_lab, shift=UP * 0.1))

        # ---- 'is a swarm of charged particles': the wind gathers into a swirling cloud
        pl.t_lap = pl.clock + 0.2
        self.span(wt(0, "is") - 0.15, wt(0, "particles", frac=0.6),
                  *pl.to(w=1.0), sun.animate.shift(LEFT * 3.2).set_opacity(0),
                  FadeOut(wind_lab), rate_func=linear)
        self.remove(sun)
        pl.tween("pulse", 0.8, 1.0, rate=there_and_back)
        cap = caps("collisionless plasma", 22, GREY_).move_to([0, 3.42, 0])
        pl.trk["clipy"].set_value(2.95)
        self.span(wt(0, "rarely") - 0.1, wt(0, "collide", frac=0.9), FadeIn(cap, shift=DOWN * 0.1))

        # ---- fields
        e_lab = MathTex("E", font_size=40, color=E_COL)
        b_lab = MathTex("B", font_size=40, color=B_COL)
        e_lab.add_updater(lambda m: m.move_to(pl.local_to_screen((1.55, 1.12)))
                          .set_opacity(min(1, pl.v("e0")) * pl.v("alpha")))
        b_lab.add_updater(lambda m: m.move_to(pl.local_to_screen((1.78, -0.55)))
                          .set_opacity(pl.v("b") * pl.v("alpha")))
        self.add(e_lab, b_lab)
        self.wait_until(wt(0, "electric") - 0.1)
        for i in range(3):     # the E field appears band by band, outward
            pl.tween(f"e{i}", 0.6, 1.0, delay=0.22 * i)
        self.wait_until(wt(0, "magnetic") - 0.1)
        pl.tween("b", 0.9, 1.0)
        pl.tween("bdraw", 0.9, 1.0)
        # 'they create themselves': a ripple runs outward from the particles
        self.wait_until(wt(0, "create") - 0.2)
        pl.tween("pulse", 1.3, 0.8, rate=there_and_back)
        pl.tween("ripple", 1.3, 1.2, rate=linear, v0=-1.0)

        # ================================================== EQUATIONS + feedback loop
        FS = 36
        vl = MathTex(r"\partial_t", "f", r"+\hat v\cdot\nabla_x", "f", r"+\big(", "E", r"+\hat v\times", "B",
                     r"\big)\cdot\nabla_p", "f", "=0", font_size=FS, color=WHITE_)
        for i in (1, 3, 9):
            vl[i].set_color(ACC)
        vl[5].set_color(E_COL)
        vl[7].set_color(B_COL)
        mx = MathTex(r"\partial_t", "E", "=", r"\nabla\times", "B", "-", "j", r",\qquad\partial_t", "B",
                     r"=-\nabla\times", "E", font_size=FS, color=WHITE_)
        for i in (1, 10):
            mx[i].set_color(E_COL)
        for i in (4, 8):
            mx[i].set_color(B_COL)
        mx[6].set_color(ACC)
        EX = 2.5
        vl.move_to([EX, 1.2, 0])
        mx.move_to([EX, -0.55, 0])
        for m in (vl, mx):
            if m.width > 5.4:
                m.scale_to_fit_width(5.4)
        vh = MathTex(r"\hat v=\frac{p}{\sqrt{1+|p|^2}}", font_size=32, color=GREY_)
        vh_note = txt("relativistic velocity: always below c", 22, GREY_)
        vrow = VGroup(vh, vh_note).arrange(RIGHT, buff=0.3).move_to([EX, -2.2, 0])
        lab_f = bold("particles", 24, ACC).next_to(vl, UP, buff=0.26).align_to(vl, LEFT)
        lab_F = bold("fields", 24, E_COL).next_to(mx, UP, buff=0.26).align_to(mx, LEFT)
        xr = max(vl.get_right()[0], mx.get_right()[0]) + 0.3
        xl = min(vl.get_left()[0], mx.get_left()[0]) - 0.3
        arcR = CurvedArrow([xr, vl.get_y(), 0], [xr, mx.get_y(), 0], angle=-TAU / 4, color=ACC,
                           stroke_width=3, tip_length=0.2)
        arcL = CurvedArrow([xl, mx.get_y(), 0], [xl, vl.get_y(), 0], angle=-TAU / 4, color=E_COL,
                           stroke_width=3, tip_length=0.2)
        labR = MathTex(r"\rho,\,j", font_size=34, color=ACC).next_to(arcR, RIGHT, buff=0.1)
        labL = MathTex("E", ",\\,", "B", font_size=34).next_to(arcL, LEFT, buff=0.1)
        labL[0].set_color(E_COL)
        labL[2].set_color(B_COL)
        eqs = VGroup(lab_f, vl, lab_F, mx, vrow, arcR, arcL, labR, labL)

        self.wait_until("eq")
        self.play(*pl.to(cx=-4.6, cy=0.1, sc=1.1, clipx=-1.85, clipy=3.65), FadeOut(cap), run_time=0.9)
        self.span(self.now, max(self.now + 0.7, wt(1, "maxwell")), FadeIn(lab_f), Write(vl))
        self.play(FadeIn(lab_F), Write(mx), FadeIn(vrow, shift=UP * 0.1), run_time=0.95)
        self.wait_until(wt(1, "describe") - 0.15)
        self.play(LaggedStart(AnimationGroup(Create(arcR), FadeIn(labR)),
                              AnimationGroup(Create(arcL), FadeIn(labL)), lag_ratio=0.5), run_time=0.6)
        # a pulse travels round the loop; the plasma answers with a ripple
        path = VMobject().set_points(np.concatenate([arcR.points, arcL.points]))
        pdot = Dot(radius=0.07, color=YELLOW_).move_to(path.get_start())
        self.add(pdot)
        pl.trk["ripple"].set_value(-1.0)
        self.span(self.now, cue("q") - 0.3, MoveAlongPath(pdot, path, rate_func=linear),
                  pl.trk["ripple"].animate(rate_func=linear).set_value(1.2),
                  vl[5].animate(rate_func=there_and_back).scale(1.3),
                  vl[7].animate(rate_func=there_and_back).scale(1.3), min_rt=0.4)
        pl.trk["ripple"].set_value(-1.0)

        # ================================================== QUESTION: max |p| over time
        axes = Axes(x_range=[0, XMAX, 1], y_range=[0, YMAX, 1], x_length=6.4, y_length=4.2, tips=True,
                    axis_config=dict(color=GREY_, stroke_width=2.2, include_ticks=False,
                                     tip_width=0.16, tip_height=0.16))
        O = np.array([-0.55, -2.1, 0])
        axes.shift(O - axes.c2p(0, 0))
        ylab = VGroup(MathTex(r"\max|p|", font_size=36, color=WHITE_),
                      txt("largest momentum", 22, GREY_)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        xlab = txt("time", 24, GREY_)
        tlab = MathTex("T^*", font_size=34, color=RED_)
        inf_lab = VGroup(MathTex(r"\infty", font_size=50, color=RED_), txt("?", 34, RED_, weight=BOLD))
        inf_lab.arrange(RIGHT, buff=0.05, aligned_edge=DOWN)
        q_lab = txt("forever?", 24, GREY_)
        fin_lab = txt("finite for every t", 24, ACC)

        def lab_pos(ax):
            """target centres of the graph labels for a given axes placement"""
            top = ax.c2p(0, YMAX)
            return {
                ylab: top + RIGHT * (0.28 + ylab.width / 2) + DOWN * (ylab.height / 2 - 0.05),
                xlab: ax.c2p(XMAX, 0) + DOWN * (0.18 + xlab.height / 2) + LEFT * xlab.width / 2,
                tlab: ax.c2p(TSTAR, 0) + DOWN * (0.18 + tlab.height / 2),
                inf_lab: ax.c2p(TSTAR, YMAX) + UP * (0.12 + inf_lab.height / 2),
                q_lab: ax.c2p(TEND, P_ok(TEND)) + UP * (0.3 + q_lab.height / 2) + LEFT * 0.2,
                fin_lab: ax.c2p(8.0, P_ok(8.0)) + DOWN * (0.42 + fin_lab.height / 2),
            }
        for m, p in lab_pos(axes).items():
            m.move_to(p)

        tt = ValueTracker(0.02)
        curve = always_redraw(lambda: axes.plot(P_ok, x_range=[0, max(tt.get_value(), 0.03), 0.05],
                                                color=ACC, stroke_width=4.5))
        tip = always_redraw(lambda: Dot(axes.c2p(tt.get_value(), P_ok(tt.get_value())), radius=0.08,
                                        color=ACC))
        cont = DashedVMobject(axes.plot(P_ok, x_range=[TB, TEND, 0.05]), num_dashes=30, dashed_ratio=0.5)
        cont.set_stroke(GREY_, 3, opacity=0.9)
        lo, hi = TB, TSTAR - 1e-6
        for _ in range(80):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if P_bad(mid) < YMAX else (lo, mid)
        tsamp = TSTAR - (TSTAR - TB) * ((TSTAR - lo) / (TSTAR - TB)) ** np.linspace(0, 1, 90)
        bad = VMobject().set_points_smoothly(np.array([axes.c2p(t, P_bad(t)) for t in tsamp]))
        bad = DashedVMobject(bad, num_dashes=26, dashed_ratio=0.55).set_stroke(RED_, 4)
        tline = DashedLine(axes.c2p(TSTAR, 0), axes.c2p(TSTAR, YMAX), dash_length=0.09,
                           color=RED_, stroke_width=2).set_stroke(opacity=0.55)

        self.wait_until(cue("q") - 0.3)
        self.play(FadeOut(eqs, shift=UP * 0.3), FadeOut(pdot), run_time=0.45)
        self.play(Create(axes, lag_ratio=0), FadeIn(ylab), FadeIn(xlab), run_time=0.7)
        self.add(curve, tip)
        self.span(self.now, wt(1, "forever", frac=0.6), tt.animate.set_value(TB), rate_func=smooth, min_rt=0.8)
        self.play(Create(cont), FadeIn(q_lab), run_time=0.7)
        # '...or can particles get kicked to infinite momentum?'
        self.wait_until(wt(1, "kicked") - 0.25)
        pl.start_kick()
        pl.tween("kalpha", 0.3, 1.0)
        self.span(self.now, max(self.now + 1.0, wt(1, "momentum", frac=1.0)),
                  Create(bad, rate_func=linear),
                  pl.trk["kick"].animate(rate_func=rush_into).set_value(1.0))
        self.play(FadeIn(inf_lab, scale=1.4), Create(tline), FadeIn(tlab), run_time=0.4)

        # ================================================== OPEN since the 1980s, in 3D
        chip3 = chip("3D", ACC, size=22).move_to([-4.6, -2.75, 0])
        self.wait_until(wt(1, "three") - 0.3)
        pl.tween("kalpha", 0.6, 0.0)
        self.play(FadeIn(chip3, shift=UP * 0.1), run_time=0.5)
        pl.tween("inc", max(1.6, wt(1, "since") + 0.3 - self.now), 26 * DEGREES, rate=there_and_back)
        openchip = chip("OPEN SINCE THE 1980s", ACC, size=22).move_to([2.65, 3.3, 0])
        gs = VGroup(bold("Glassey–Strauss (1986):", 24, WHITE_), txt("bounded momentum", 24, GREY_),
                    MathTex(r"\Rightarrow", font_size=32, color=GREY_), txt("stays smooth", 24, GREY_))
        gs.arrange(RIGHT, buff=0.15).move_to([2.65, -3.05, 0])
        if gs.width > 7.4:
            gs.scale_to_fit_width(7.4)
        self.wait_until(wt(1, "open") - 0.25)
        self.play(FadeIn(openchip, shift=DOWN * 0.15), run_time=0.6)
        self.wait_until(wt(1, "since") - 0.1)
        self.play(FadeIn(gs, shift=UP * 0.1), run_time=0.7)
        self.span(self.now, cue("claim") - 0.05, Indicate(inf_lab, color=RED_, scale_factor=1.2), min_rt=0.4)

        # ================================================== CLAIM: the paper
        card = paper_card(NUM, width=2.75).move_to([5.1, 0.15, 0])
        tag = paper_tag(NUM, color=ACC)
        k, about = 0.72, axes.c2p(0, 0)
        shift = np.array([-1.5, -1.5, 0]) - about
        ax_t = axes.copy().scale(k, about_point=about).shift(shift)
        tgt = lab_pos(ax_t)
        self.wait_until("claim")
        self.play(VGroup(axes, cont).animate.scale(k, about_point=about).shift(shift),
                  *[m.animate.move_to(tgt[m]) for m in (ylab, xlab, q_lab)],
                  Uncreate(bad), FadeOut(tline), FadeOut(tlab), FadeOut(inf_lab),
                  FadeOut(openchip), FadeOut(gs), FadeOut(chip3),
                  FadeIn(card, shift=LEFT * 2.5), FadeIn(tag), run_time=0.75)
        fin_lab.move_to(lab_pos(axes)[fin_lab])
        title = serif("smooth forever", 50, YELLOW_).move_to([0.8, 3.0, 0])
        self.wait_until(wt(2, "smooth") - 0.45)
        self.play(tt.animate.set_value(TEND), cont.animate.set_stroke(opacity=0.0),
                  FadeOut(q_lab), FadeIn(fin_lab, shift=UP * 0.1), Write(title), run_time=1.1)

        # ================================================== DETAILS
        banner = result_banner("Global smooth solutions for 3D relativistic Vlasov–Maxwell",
                               lean=CATALOG[NUM]["lean"], size=30)
        banner.move_to([0, -0.72, 0])
        chips_ = [chip(s, ACC, size=18) for s in ("GLOBAL EXISTENCE", "UNIQUENESS", "NO SMALLNESS", "NO SYMMETRY")]
        crow = VGroup(*chips_).arrange(RIGHT, buff=0.3).move_to([0, -1.97, 0])
        fine = txt("one species  ·  compactly supported particles  ·  finite-energy fields", 22, GREY_)
        fine.move_to([0, -2.52, 0])
        k2 = 0.6 / 0.72
        about2 = axes.c2p(0, 0)
        shift2 = np.array([1.05, 0.78, 0]) - about2
        ax_t2 = axes.copy().scale(k2, about_point=about2).shift(shift2)
        tgt2 = lab_pos(ax_t2)
        self.wait_until(max(self.now + 0.3, wt(2, "global") - 0.5))
        self.play(FadeOut(card, shift=RIGHT * 2.5), FadeOut(title, shift=UP * 0.2),
                  VGroup(axes, cont).animate.scale(k2, about_point=about2).shift(shift2),
                  *[m.animate.move_to(tgt2[m]) for m in (ylab, xlab, fin_lab)],
                  *pl.to(cx=-4.0, cy=1.95, sc=0.8, clipx=0.3), run_time=0.8)
        self.play(FadeIn(banner, shift=UP * 0.15), FadeIn(chips_[0], shift=UP * 0.1), run_time=0.6)
        self.wait_until(wt(2, "uniqueness") - 0.1)
        self.play(FadeIn(chips_[1], shift=UP * 0.1), run_time=0.45)
        self.wait_until(wt(2, "made") - 0.1)
        pl.tween("pulse", 1.0, 1.0, rate=there_and_back)
        self.play(FadeIn(fine, shift=UP * 0.1), run_time=0.7)
        for word, ch in (("smallness", chips_[2]), ("symmetry", chips_[3])):
            self.wait_until(wt(2, word) - 0.15)
            self.play(FadeIn(ch, shift=UP * 0.1, scale=1.15), run_time=0.45)

        # ================================================== OUT
        end = self.narr_end
        self.wait_until(end - 0.5)
        others = [m for m in self.mobjects if m is not pl and not isinstance(m, ValueTracker)]
        self.play(pl.trk["alpha"].animate.set_value(0.0), *[FadeOut(m) for m in others],
                  run_time=end - self.now)
        self.remove(*self.mobjects)
        self.finish()
