import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import json
import math

import numpy as np

# Quasi-Riemann hypothesis spotlight (family 003).
#
# One complex plane carries the whole story: critical strip, true zeta zeros,
# a hypothetical zero drifting to the edge (with a prime-count inset showing
# the error blowing up), the classical zero-free sliver 1 - c/log t thinning as
# we climb to t ~ 10^12, the quasi-RH "fixed wall", and finally the claimed
# zero-free band 7/8 < Re s < 1 holding for zeta and Dirichlet L-functions
# (true zero heights for chi mod 3, 4, 5).

ACC = BLUE_
CACHE = BUILD / "cache" / "c1_qrh"
DATA_PATH = CACHE / "data.json"

# ---------------------------------------------------------------- plane geometry
X0, KX = -4.5, 3.8          # x of sigma = 0; scene units per unit of sigma
Y0, SY = -2.35, 0.117       # y of t = tb (window base); scene units per unit of t
TOP, BOT = 4.3, -4.3        # extent of the "infinite" vertical objects
C_ZF = 1 / 5.573412         # zero-free region sigma > 1 - 1/(5.573 log t)  (Mossinghoff-Trudgian)
RC = 1.0                    # dash-scroll compression during the climb
CLIMB_TOP = 1e12            # how high we climb
RIGHT_X = 1.3               # left edge of the right-hand panel
# close-up of the right edge (right panel): sigma in [MB_S0, MB_S1], same t-window as the plane
MB_X0, MB_W, MB_Y0, MB_H = 1.6, 4.6, -2.7, 2.15
MB_S0, MB_S1, MB_T = 0.8, 1.004, 52.0
PANEL_CX = 4.0              # centre of the right-hand panel


def sx(sig):
    return X0 + KX * sig


def mbx(sig):
    return MB_X0 + (min(max(sig, MB_S0), MB_S1) - MB_S0) * MB_W / (MB_S1 - MB_S0)


# ---------------------------------------------------------------- data (cached)
def _compute_data():
    import mpmath as mp
    mp.mp.dps = 20
    out = {}
    zz, n = [], 1
    while True:
        g = float(mp.zetazero(n).imag)
        if g > 105:
            break
        zz.append(g)
        n += 1
    out["zeta"] = zz
    out["Z"] = [[float(t), float(mp.siegelz(t))] for t in np.linspace(0, 50, 801)]
    chars = {"3": ([0, 1, -1], 1), "4": ([0, 1, 0, -1], 1), "5": ([0, 1, -1, -1, 1], 0)}

    def zc(t, chi, a):
        s = mp.mpc(0.5, t)
        q = len(chi)
        g = mp.power(q / mp.pi, (s + a) / 2) * mp.gamma((s + a) / 2)
        return (mp.dirichlet(s, chi) * mp.exp(1j * mp.arg(g))).real

    out["L"] = {}
    for k, (chi, a) in chars.items():
        grid = np.arange(0.05, 52.0, 0.02)
        v = [float(zc(t, chi, a)) for t in grid]
        zs = []
        for i in range(len(grid) - 1):
            if v[i] * v[i + 1] < 0:
                zs.append(float(mp.findroot(lambda t: zc(t, chi, a), (grid[i], grid[i + 1]),
                                            solver="anderson")))
        out["L"][k] = zs
    out["R"] = [[float(x), float(mp.riemannr(x))] for x in np.linspace(2, 100, 300)]
    out["primes"] = [p for p in range(2, 101) if all(p % d for d in range(2, int(p ** 0.5) + 1))]
    return out


def load_data():
    if not DATA_PATH.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text(json.dumps(_compute_data()))
    return json.loads(DATA_PATH.read_text())


# ---------------------------------------------------------------- dashed vertical line
class VDash(VGroup):
    """Dashed vertical line at a given sigma whose dash pattern can scroll
    (so climbing the strip visibly moves it)."""

    def __init__(self, sigma, color, width=2.5, opacity=1.0, dash=0.17, gap=0.12):
        self.sigma, self.dash, self.P = sigma, dash, dash + gap
        n = int((TOP - BOT) / self.P) + 4
        super().__init__(*[VMobject() for _ in range(n)])
        for m in self.submobjects:
            m.set_points_as_corners([[0, TOP + 1, 0], [0, TOP + 1.001, 0]])
        self.set_stroke(color, width, opacity)

    def layout(self, base, phase):
        x = sx(self.sigma)
        A = Y0 - phase
        k = math.floor((base - A) / self.P) - 1
        segs = []
        while True:
            a = A + k * self.P
            if a >= TOP:
                break
            lo, hi = max(a, base), min(a + self.dash, TOP)
            if hi > lo + 1e-3:
                segs.append((lo, hi))
            k += 1
        for i, m in enumerate(self.submobjects):
            if i < len(segs):
                lo, hi = segs[i]
                m.set_points_as_corners([[x, lo, 0], [x, hi, 0]])
            else:
                m.set_points_as_corners([[x, TOP + 1, 0], [x, TOP + 1.001, 0]])
        return self


class C1Qrh(VoiceScene):

    # ============================================================ helpers
    def wait_until(self, t, **kw):
        dt = self.cue(t) - self.now
        if dt > 0.5 / config.frame_rate:
            self.wait(dt, **kw)

    def Y(self, t):
        return Y0 + (t - self.tb.get_value()) * SY

    @staticmethod
    def swap(old, new, **kw):
        """Fade `old` out in the first half, `new` in during the second half."""
        return [FadeOut(old, rate_func=lambda a: smooth(min(1.0, 2 * a))),
                FadeIn(new, rate_func=lambda a: smooth(max(0.0, 2 * a - 1)), **kw)]

    def phase(self):
        return RC * np.log1p(SY * self.tb.get_value() / RC)

    def rt(self, want, until, pad=0.05):
        """A run time of at most `want` that still ends before cue `until`."""
        return max(0.25, min(want, self.cue(until) - self.now - pad))

    def relayout(self):
        y0 = self.Y(0)
        base = max(y0, BOT)
        for m, t, dy in self.att:
            m.set_y(float(np.clip(self.Y(t) + dy, -7.0, 7.0)))
        for m, sig, below in self.vlines:
            x = sx(sig() if callable(sig) else sig)
            m.set_points_as_corners([[x, max(y0 - below, BOT), 0], [x, TOP, 0]])
        for m, sig, dx in self.xatt:
            m.set_x(sx(sig() if callable(sig) else sig) + dx)
        for d in self.dashes:
            d.layout(base, self.phase())
        for m, s0, s1, fr in self.rects:
            a = sx(s0() if callable(s0) else s0)
            b = sx(s1() if callable(s1) else s1)
            top = base + max(fr() if callable(fr) else fr, 1e-3) * (TOP - base)
            m.set_points_as_corners([[a, base, 0], [b, base, 0], [b, top, 0], [a, top, 0], [a, base, 0]])
        if self.mb_wall is not None:
            x = mbx(self.wsig)
            self.mb_wall.set_points_as_corners([[x, MB_Y0, 0], [x, MB_Y0 + MB_H, 0]])
        if self.sl_on:
            self.update_sliver()
        if self.counter is not None:
            self.update_counter()

    def drive(self, fn, **kw):
        """Animation calling fn(alpha) + relayout each frame. It animates self.tb,
        the first mobject in the scene, so every mobject is redrawn per frame."""
        def upd(m, a):
            fn(a)
            self.relayout()
        return UpdateFromAlphaFunc(self.tb, upd, **kw)

    # ---- classical zero-free sliver  sigma > 1 - c / log t   (t >= 2)
    def update_sliver(self):
        tb = self.tb.get_value()
        ylo = max(self.Y(2.0), BOT)
        top = ylo + (TOP - ylo) * self.sl_frac
        if top - ylo < 1e-3:
            top = ylo + 1e-3
        ys = ylo + (top - ylo) * np.linspace(0, 1, 70) ** 1.7
        ts = np.maximum(tb + (ys - Y0) / SY, 2.0)
        sig = 1 - C_ZF / np.log(ts)
        curve = [[sx(s), y, 0] for s, y in zip(sig, ys)]
        x1 = sx(1)
        self.sl_fill.set_points_as_corners(curve + [[x1, top, 0], [x1, ylo, 0], curve[0]])
        self.sl_edge.set_points_as_corners(curve)
        if self.mb_on:
            t_lo = max(2.0, tb)
            t_top = t_lo + (tb + MB_T - t_lo) * max(self.sl_frac, 1e-3)
            ts = t_lo + (t_top - t_lo) * np.linspace(0, 1, 60) ** 1.7
            ys = MB_Y0 + (ts - tb) * MB_H / MB_T
            sig = 1 - C_ZF / np.log(ts)
            curve = [[mbx(sg), y, 0] for sg, y in zip(sig, ys)]
            xr = mbx(1)
            self.mb_fill.set_points_as_corners(curve + [[xr, ys[-1], 0], [xr, ys[0], 0], curve[0]])
            self.mb_edge.set_points_as_corners(curve)

    # ---- height read-out while climbing
    def counter_tex(self, ttop):
        if ttop < 95:
            s = f"{int(round(ttop, -1))}"
        elif ttop < 950:
            s = f"{int(round(ttop, -2))}"
        else:
            s = f"10^{{{int(math.floor(math.log10(ttop) + 1e-9))}}}"
        if s not in self._ctex:
            self._ctex[s] = MathTex(r"t\approx " + s, font_size=38, color=WHITE_)
        return self._ctex[s]

    def update_counter(self):
        ttop = self.tb.get_value() + (3.75 - Y0) / SY
        new = self.counter_tex(ttop).copy()
        new.move_to(self.counter_anchor, aligned_edge=LEFT)
        self.counter.become(new)

    def zero_dot(self, t, color=WHITE_, r=0.07):
        return Dot([sx(0.5), self.Y(t), 0], radius=r, color=color).set_z_index(3)

    def arrow_to(self, start, end, color=GREY_):
        return Arrow(start, end, buff=0.08, stroke_width=3, color=color,
                     max_tip_length_to_length_ratio=0.08, tip_length=0.18)

    # ============================================================ construct
    def construct(self):
        self.D = load_data()
        self.tb = ValueTracker(0.0).set_z_index(-100)
        self.add(self.tb)          # must stay the first mobject in z-order (see drive())
        self.att, self.vlines, self.xatt, self.dashes, self.rects = [], [], [], [], []
        self.sl_on, self.sl_frac, self.counter, self._ctex = False, 1.0, None, {}
        self.mb_on, self.mb_wall, self.wsig = False, None, 0.93
        self.counter_anchor = np.array([sx(0) + 0.17, 3.42, 0])

        self.hook()
        self.plane()
        self.strip_and_line()
        self.edge_and_sliver()
        self.quasi_and_claim()
        self.cousins_and_close()
        self.finish()

    # ------------------------------------------------------------ 1. zeta & the sum
    def hook(self):
        Z = np.array(self.D["Z"])
        base = -1.95
        hx = lambda t: -6.3 + 12.6 * t / 50
        wave_ax = Line([-6.3, base, 0], [6.3, base, 0], stroke_color=DIM, stroke_width=2)
        wave = VMobject(stroke_color=ACC, stroke_width=3.5, stroke_opacity=0.9)
        wave.set_points_as_corners([[hx(t), base + 0.36 * z, 0] for t, z in Z])
        xdots = VGroup(*[Dot([hx(g), base, 0], radius=0.06, color=WHITE_)
                         for g in self.D["zeta"] if g < 50])

        # hook: the zeta function traced along its critical line, from frame 1
        self.play_until("zeta", Create(wave), FadeIn(wave_ax), rate_func=linear)

        big = MathTex(r"\zeta(s)", font_size=130, color=WHITE_).move_to(UP * 1.25)
        cap = txt("the Riemann zeta function", 32, GREY_).next_to(big, DOWN, buff=0.3)
        self.play(Write(big), LaggedStart(*[GrowFromCenter(d) for d in xdots], lag_ratio=0.15),
                  run_time=self.rt(1.0, "sum"))
        self.play(FadeIn(cap, shift=UP * 0.15), run_time=self.rt(0.5, "sum"))

        # {sum}: zeta(s) = sum 1/n^s = 1 + 1/2^s + ...
        full = MathTex(r"\zeta(s)", "=", r"\sum_{n\ge1}", r"\frac{1}{n^s}",
                       font_size=84, color=WHITE_).move_to(UP * 1.0)
        exp = MathTex("=", "1", "+", r"\frac{1}{2^s}", "+", r"\frac{1}{3^s}", "+",
                      r"\frac{1}{4^s}", "+", r"\frac{1}{5^s}", "+", r"\cdots",
                      font_size=62, color=WHITE_).move_to(DOWN * 1.0)
        rest = VGroup(*full[1:])
        self.play_at("sum", FadeOut(wave), FadeOut(wave_ax), FadeOut(xdots), FadeOut(cap),
                     ReplacementTransform(big, full[0]),
                     FadeIn(rest, shift=LEFT * 0.3), run_time=self.rt(1.1, "complex"))
        self.remove(full[0], rest)
        self.add(full)
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.15) for p in exp], lag_ratio=0.2),
                  Indicate(full[2], color=ACC, scale_factor=1.12),
                  run_time=self.rt(1.8, "complex"))
        self.full, self.exp = full, exp

    # ------------------------------------------------------------ 2. complex plane
    def plane(self):
        hdr = MathTex(r"\zeta(s)", "=", r"\sum_{n\ge1}", r"\frac{1}{n^s}", font_size=34, color=WHITE_)
        hdr.move_to([RIGHT_X, 3.22, 0], aligned_edge=LEFT)
        self.hdr = hdr

        # axes (sigma, t), only the upper half plane
        re_line = Line([sx(-0.32), Y0, 0], [sx(1.3), Y0, 0], stroke_color=GREY_, stroke_width=2.5)
        im_line = Line([sx(0), Y0 - 0.35, 0], [sx(0), TOP, 0], stroke_color=GREY_, stroke_width=2.5)
        re_line.set_z_index(-2)
        im_line.set_z_index(-2)
        sig_lab = MathTex(r"\sigma", font_size=38, color=GREY_).move_to([sx(1.3) + 0.3, Y0, 0])
        t_lab = MathTex("t", font_size=38, color=GREY_).move_to([sx(0) + 0.3, 3.5, 0])
        ticks = VGroup()
        for t in range(10, 101, 10):
            tk = Line(LEFT * 0.08, RIGHT * 0.08, stroke_color=GREY_, stroke_width=2).move_to([sx(0), self.Y(t), 0])
            lb = txt(str(t), 22, GREY_)
            lb.next_to(tk, LEFT, buff=0.1)
            g = VGroup(tk, lb) if t != 50 else VGroup(tk)
            ticks.add(g)
            self.att.append((g, t, 0.0))
        self.att += [(re_line, 0, 0.0), (sig_lab, 0, 0.0)]
        self.vlines.append((im_line, 0.0, 0.35))
        self.re_line, self.sig_lab, self.im_line, self.t_lab = re_line, sig_lab, im_line, t_lab

        self.play_at("complex", ReplacementTransform(self.full, hdr),
                     FadeOut(self.exp, shift=DOWN * 0.2), run_time=self.rt(0.9, "strip"))
        self.play(Create(re_line), Create(im_line), FadeIn(sig_lab), FadeIn(t_lab),
                  LaggedStart(*[FadeIn(g) for g in ticks[:5]], lag_ratio=0.15),
                  run_time=self.rt(1.0, "strip"))
        self.add(ticks[5:])  # off-screen for now; they scroll in when we climb

        # a complex input s wandering over the plane
        u = ValueTracker(0.0)
        pts = []
        for a in np.linspace(0, 1, 160):
            sg = 0.42 + 0.36 * math.sin(2 * math.pi * 0.85 * a - 1.0)
            tt = 11 + 24 * a + 5 * math.sin(2 * math.pi * 1.4 * a)
            pts.append([sx(sg), self.Y(tt), 0])
        path = VMobject().set_points_smoothly(pts)
        sdot = Dot(path.get_start(), radius=0.085, color=YELLOW_).set_z_index(4)
        slab = MathTex(r"s=\sigma+it", font_size=34, color=YELLOW_)
        sdot.add_updater(lambda m: m.move_to(path.point_from_proportion(u.get_value())))
        slab.add_updater(lambda m: m.next_to(sdot, UR, buff=0.05))
        self.add(u)
        self.play(FadeIn(sdot, scale=0.5), FadeIn(slab), run_time=self.rt(0.5, "strip"))

        # prime-counting inset: pi(x) hugging a smooth estimate
        ax = Axes(x_range=[0, 100, 25], y_range=[0, 30, 10], x_length=4.6, y_length=2.1, tips=False,
                  axis_config=dict(stroke_color=GREY_, stroke_width=2, include_ticks=False))
        ax.move_to([PANEL_CX, 1.0, 0])
        pr = self.D["primes"]
        corners = [ax.c2p(0, 0)]
        for i, p in enumerate(pr):
            corners += [ax.c2p(p, i), ax.c2p(p, i + 1)]
        corners.append(ax.c2p(100, len(pr)))
        stair = VMobject(stroke_color=WHITE_, stroke_width=2.5).set_points_as_corners(corners)
        R = np.array(self.D["R"])
        rcurve = VMobject(stroke_color=ACC, stroke_width=3).set_points_smoothly(
            [ax.c2p(x, y) for x, y in R[::6]] + [ax.c2p(*R[-1])])
        pi_lab = VGroup(MathTex(r"\pi(x)", font_size=32, color=WHITE_),
                        txt("primes up to x", 22, GREY_)).arrange(RIGHT, buff=0.18)
        pi_lab.next_to(ax, UP, buff=0.12, aligned_edge=LEFT)
        r_lab = txt("smooth estimate", 22, ACC).move_to(ax.c2p(70, 6))
        xl = MathTex("x", font_size=30, color=GREY_).next_to(ax.x_axis.get_end(), RIGHT, buff=0.1)
        stair.set_z_index(1)
        self.inset = VGroup(ax, rcurve, stair, pi_lab, r_lab, xl)
        self.ax, self.rdata = ax, R

        t_inset = max(self.cue("complex") + 2.4, self.cue("L1_end") - 3.9)
        t0, t1 = self.now, self.cue("strip")
        u_mid = float(np.clip((t_inset - t0) / max(t1 - t0, 1e-3), 0.05, 0.6))
        self.play(u.animate(rate_func=linear).set_value(u_mid), run_time=max(0.2, t_inset - self.now))
        rest = self.cue("strip") - self.now
        self.play(u.animate(rate_func=linear).set_value(1.0),
                  Succession(AnimationGroup(Create(ax), FadeIn(pi_lab), FadeIn(xl), run_time=0.7),
                             AnimationGroup(Create(stair, rate_func=linear), Create(rcurve), run_time=1.5),
                             FadeIn(r_lab, run_time=0.5),
                             Wait(max(0.01, rest - 2.7))),
                  run_time=max(0.3, rest))
        sdot.clear_updaters()
        slab.clear_updaters()
        self.sdot, self.slab, self.u = sdot, slab, u

    # ------------------------------------------------------------ 3. strip, line, RH
    def strip_and_line(self):
        strip = Polygon(*[[0, 0, 0]] * 4, stroke_width=0, fill_color=ACC, fill_opacity=0.13).set_z_index(-5)
        self.strip_f = 0.0
        self.rects.append((strip, 0.0, 1.0, lambda: self.strip_f))
        edge = Line(ORIGIN, UP, stroke_color=GREY_, stroke_width=2.5).set_z_index(-1)
        self.vlines.append((edge, 1.0, 0.0))
        self.relayout()
        lab0 = MathTex("0", font_size=32, color=GREY_).move_to([sx(0) - 0.17, Y0 - 0.3, 0])
        lab1 = MathTex("1", font_size=32, color=GREY_).move_to([sx(1), Y0 - 0.32, 0])
        self.att += [(lab0, 0, -0.3), (lab1, 0, -0.32)]
        cap = caps("critical strip", 20, ACC).move_to([sx(0.5), Y0 - 0.85, 0])
        self.strip, self.edge, self.lab0, self.lab1, self.cap = strip, edge, lab0, lab1, cap

        self.add(strip)

        def grow_strip(a):
            self.strip_f = a

        self.play_at("strip", FadeOut(self.sdot), FadeOut(self.slab),
                     self.drive(grow_strip), Create(edge), run_time=self.rt(1.2, "line"))
        self.remove(self.u)
        self.play(FadeIn(lab0), FadeIn(lab1), FadeIn(cap, shift=UP * 0.1), run_time=self.rt(0.6, "line"))
        # "between real part zero and one"
        span = DoubleArrow([sx(0) + 0.06, 2.7, 0], [sx(1) - 0.06, 2.7, 0], buff=0, stroke_width=3,
                           color=WHITE_, tip_length=0.18, max_tip_length_to_length_ratio=0.1)
        span_l = MathTex(r"0<\sigma<1", font_size=36, color=WHITE_).next_to(span, UP, buff=0.12)
        self.wait_until(max(self.now, min(self.cue("strip") + 2.3, self.cue("line") - 1.3)))
        self.play(GrowFromCenter(span), FadeIn(span_l, shift=DOWN * 0.1),
                  Indicate(lab0, color=WHITE_), Indicate(lab1, color=WHITE_), run_time=self.rt(0.9, "line"))

        # {line}: critical line, zeros at their true heights
        crit = VDash(0.5, WHITE_, width=2.5, opacity=0.85).set_z_index(-1)
        crit.layout(self.Y(0), 0.0)
        self.dashes.append(crit)
        half = MathTex(r"\tfrac12", font_size=32, color=GREY_).move_to([sx(0.5), Y0 - 0.34, 0])
        self.att.append((half, 0, -0.34))
        self.crit, self.half = crit, half
        self.play_at("line", FadeOut(span), FadeOut(span_l), Create(crit, lag_ratio=0.6), FadeIn(half),
                     run_time=self.rt(0.8, "open"))

        zz = self.D["zeta"]
        dots = VGroup(*[self.zero_dot(t) for t in zz])
        for d, t in zip(dots, zz):
            self.att.append((d, t, 0.0))
        vis = [i for i, t in enumerate(zz) if t < 52]
        for d in dots:
            d.set_opacity(0)
        self.add(dots)
        self.zdots = dots

        Z = np.array(self.D["Z"])
        vwave = VMobject(stroke_color=ACC, stroke_width=3, stroke_opacity=0.9).set_z_index(-3)
        vwave.set_points_as_corners([[sx(0.5) + 0.3 * z, self.Y(t), 0] for t, z in Z])
        r0 = dots[0].width / 2

        def grow(m, a):
            tip = 50 * a
            for i in vis:
                s = float(np.clip((tip - zz[i]) / 2.5, 0, 1))
                d = dots[i]
                d.set_opacity(s)
                d.set_width(2 * r0 * (0.2 + 0.8 * s) + 1e-4)
                d.move_to([sx(0.5), self.Y(zz[i]), 0])

        self.play(Create(vwave, rate_func=linear),
                  UpdateFromAlphaFunc(dots, grow, rate_func=lambda a: min(1, a * 1.06)),
                  run_time=self.rt(1.6, "open"))
        for i, d in enumerate(dots):
            if i not in vis:
                d.set_opacity(1)

        # RH label pointing at the line
        rh = VGroup(bold("Riemann Hypothesis", 30),
                    VGroup(txt("every zero on", 26, GREY_),
                           MathTex(r"\sigma=\tfrac12", font_size=36, color=WHITE_)).arrange(RIGHT, buff=0.15))
        rh.arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([RIGHT_X + 0.2, -0.5, 0], aligned_edge=UL)
        tgt = (zz[0] + zz[1]) / 2
        arr = self.arrow_to(rh.get_left() + LEFT * 0.1 + DOWN * 0.0, [sx(0.5) + 0.12, self.Y(tgt), 0])
        z1 = txt("t = 14.13…", 22, GREY_).next_to(dots[0], LEFT, buff=0.15)
        self.rh, self.rh_arr, self.z1 = rh, arr, z1
        self.play(FadeOut(vwave), FadeIn(rh, shift=LEFT * 0.2), GrowArrow(arr), FadeIn(z1),
                  run_time=self.rt(0.9, "open"))

        # {open}
        chip_open = chip("OPEN SINCE 1859", ORANGE_, size=18).next_to(rh, DOWN, buff=0.28, aligned_edge=LEFT)
        self.chip_open = chip_open
        self.play_at("open", FadeIn(chip_open, scale=1.2), run_time=self.rt(0.5, "edge"))
        self.play(Indicate(chip_open, color=ORANGE_, scale_factor=1.06), run_time=self.rt(0.8, "edge"))

    # ------------------------------------------------------------ 4. edge danger, classical sliver, climb
    def edge_and_sliver(self):
        glow_l = Line(ORIGIN, UP, stroke_color=RED_, stroke_width=16, stroke_opacity=0.16).set_z_index(-1)
        self.vlines.append((glow_l, 1.0, 0.0))
        self.relayout()
        self.play_at("edge", FadeOut(self.rh), FadeOut(self.rh_arr), FadeOut(self.chip_open),
                     FadeOut(self.z1), FadeOut(self.cap),
                     self.edge.animate.set_stroke(RED_, width=4), FadeIn(glow_l),
                     self.lab1.animate.set_color(RED_), run_time=self.rt(0.6, "sliver"))

        # a hypothetical zero beta + i gamma leaving the line (with its mirror 1 - beta)
        gam = 27.7
        beta = ValueTracker(0.5)
        hz = Dot([sx(0.5), self.Y(gam), 0], radius=0.085, color=RED_).set_z_index(4)
        hm = Dot([sx(0.5), self.Y(gam), 0], radius=0.085, color=RED_, fill_opacity=0.4).set_z_index(4)
        blab = MathTex(r"\beta", font_size=34, color=RED_).next_to(hz, UP, buff=0.1)
        ax, R = self.ax, self.rdata
        xs = np.linspace(2, 100, 90)
        Rx = np.interp(xs, R[:, 0], R[:, 1])
        band = Polygon(*[[0, 0, 0]] * 3, stroke_width=0, fill_opacity=0.28).set_z_index(-1)
        err = VGroup(txt("error ≈", 26, WHITE_), MathTex(r"x^{\beta}", font_size=40, color=WHITE_))
        err.arrange(RIGHT, buff=0.12).move_to([PANEL_CX, -0.45, 0])

        def set_beta(b):
            beta.set_value(b)
            hz.move_to([sx(b), self.Y(gam), 0])
            hm.move_to([sx(1 - b), self.Y(gam), 0])
            blab.next_to(hz, UP, buff=0.1)
            w = 0.3 * xs ** b
            up = np.minimum(Rx + w, 29)
            lo = np.maximum(Rx - w, 0)
            pts = [ax.c2p(x, y) for x, y in zip(xs, up)] + [ax.c2p(x, y) for x, y in zip(xs[::-1], lo[::-1])]
            band.set_points_as_corners(pts + [pts[0]])
            k = float(np.clip((b - 0.5) / 0.45, 0, 1))
            band.set_fill(interpolate_color(ManimColor(ACC), ManimColor(RED_), k), opacity=0.28)

        set_beta(0.5)
        self.play(GrowFromCenter(hz), GrowFromCenter(hm), FadeIn(blab), FadeIn(band), FadeIn(err),
                  run_time=self.rt(0.5, "sliver"))
        self.play(self.drive(lambda a: set_beta(0.5 + 0.465 * a)),
                  run_time=self.rt(2.4, "sliver", pad=0.1))

        # {sliver}: classical zero-free zone sigma > 1 - c/log t
        self.sl_fill = Polygon(*[[0, 0, 0]] * 3, stroke_width=0, fill_color=GREEN_,
                               fill_opacity=0.3).set_z_index(-4)
        self.sl_edge = VMobject(stroke_color=GREEN_, stroke_width=3).set_z_index(-1)
        self.sl_frac = 0.0
        self.sl_on = True
        # close-up of the edge, sigma in [0.8, 1]
        mb_frame = Rectangle(width=MB_W, height=MB_H, stroke_color=GREY_, stroke_width=1.5)
        mb_frame.move_to([MB_X0 + MB_W / 2, MB_Y0 + MB_H / 2, 0])
        mb_strip = Rectangle(width=mbx(1) - MB_X0, height=MB_H, stroke_width=0, fill_color=ACC,
                             fill_opacity=0.13).move_to(mb_frame, aligned_edge=LEFT).set_z_index(-5)
        mb_red = Line([mbx(1), MB_Y0, 0], [mbx(1), MB_Y0 + MB_H, 0], stroke_color=RED_, stroke_width=4)
        mb_ticks = VGroup()
        for v, lab in ((0.8, "0.8"), (0.9, "0.9"), (1.0, "1")):
            tk = Line([mbx(v), MB_Y0, 0], [mbx(v), MB_Y0 - 0.08, 0], stroke_color=GREY_, stroke_width=2)
            tl = MathTex(lab, font_size=28, color=RED_ if v == 1.0 else GREY_).next_to(tk, DOWN, buff=0.06)
            mb_ticks.add(tk, tl)
        mb_sig = MathTex(r"\sigma", font_size=30, color=GREY_).next_to(mb_ticks[-1], RIGHT, buff=0.25)
        mb_title = caps("close-up of the edge", 18, GREY_).next_to(mb_frame, UP, buff=0.14, aligned_edge=LEFT)
        self.mb_fill = Polygon(*[[0, 0, 0]] * 3, stroke_width=0, fill_color=GREEN_,
                               fill_opacity=0.3).set_z_index(-4)
        self.mb_edge = VMobject(stroke_color=GREEN_, stroke_width=3)
        self.mb_on = True
        self.update_sliver()
        self.add(self.sl_fill, self.sl_edge)
        self.mbox = VGroup(mb_strip, mb_frame, mb_red, mb_ticks, mb_sig, mb_title)

        def grow_sl(a):
            self.sl_frac = a

        self.play_at("sliver", FadeOut(hz), FadeOut(hm), FadeOut(blab), FadeOut(band), FadeOut(err),
                     FadeOut(self.inset), run_time=self.rt(0.5, "L3_end"))
        self.add(self.mb_fill, self.mb_edge)
        self.play(self.drive(grow_sl), FadeIn(self.mbox), run_time=self.rt(1.8, "L3_end"))

        cz = VGroup(bold("Classical zero-free zone", 28, color=GREEN_),
                    MathTex(r"\sigma>1-\frac{c}{\log t}", font_size=42, color=WHITE_),
                    txt("de la Vallée Poussin, 1899", 22, GREY_))
        cz.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([RIGHT_X + 0.2, 2.55, 0], aligned_edge=UL)
        cz_arr = self.arrow_to([RIGHT_X + 0.05, cz[1].get_y(), 0], [sx(1) - 0.03, cz[1].get_y(), 0], color=GREEN_)
        # the t-axis label becomes a height read-out while we climb
        self.counter = self.counter_tex(52).copy().move_to(self.counter_anchor, aligned_edge=LEFT)
        self.update_counter()
        self.cz, self.cz_arr = cz, cz_arr
        self.play(FadeIn(cz, shift=LEFT * 0.2), GrowArrow(cz_arr), *self.swap(self.t_lab, self.counter),
                  run_time=self.rt(0.8, "L3_end"))

        # climb: window base tb from 0 to 10^12 (exponential), sliver thins
        lam = 25.0
        A = CLIMB_TOP / (math.exp(lam) - 1)
        self.climbF = lambda a: A * (math.exp(lam * a) - 1)
        self.wait_until(max(self.now, self.cue("L3_end") - 3.4))
        self.play(self.drive(lambda a: self.tb.set_value(self.climbF(a))),
                  run_time=self.rt(5.6, "quasi", pad=0.3))

    # ------------------------------------------------------------ 5. quasi-RH wall, then the claim
    def quasi_and_claim(self):
        q = VGroup(bold("Quasi-Riemann hypothesis", 28, color=ACC),
                   VGroup(txt("some fixed wall", 26, WHITE_),
                          MathTex(r"\sigma_0<1", font_size=38, color=WHITE_)).arrange(RIGHT, buff=0.18),
                   VGroup(txt("no zero with", 26, GREY_),
                          MathTex(r"\sigma>\sigma_0", font_size=38, color=WHITE_)).arrange(RIGHT, buff=0.18))
        q.arrange(DOWN, aligned_edge=LEFT, buff=0.24).move_to([RIGHT_X + 0.2, 2.55, 0], aligned_edge=UL)
        self.wsig = 0.93
        wall = Line(ORIGIN, UP, stroke_color=WHITE_, stroke_width=5).set_z_index(1)
        self.vlines.append((wall, lambda: self.wsig, 0.0))
        wlab = MathTex(r"\sigma_0\,?", font_size=38, color=WHITE_).move_to([sx(self.wsig) - 0.4, 3.4, 0])
        self.xatt.append((wlab, lambda: self.wsig, -0.4))
        self.relayout()
        # draw the wall from the top down
        wall_draw = Line([sx(self.wsig), TOP, 0], [sx(self.wsig), BOT, 0], stroke_color=WHITE_,
                         stroke_width=5).set_z_index(1)

        self.play_at("quasi", FadeOut(self.cz), FadeOut(self.cz_arr), FadeIn(q, shift=LEFT * 0.2),
                     run_time=self.rt(0.8, "claim"))
        mb_wall = Line([mbx(self.wsig), MB_Y0 + MB_H, 0], [mbx(self.wsig), MB_Y0, 0],
                       stroke_color=WHITE_, stroke_width=4)
        q0, q1 = self.cue("quasi"), self.cue("L4_end")
        self.wait_until(max(self.now, q0 + 0.3 * (q1 - q0)))
        self.play(Create(wall_draw), Create(mb_wall), FadeIn(wlab, shift=DOWN * 0.15),
                  run_time=self.rt(0.7, "claim"))
        self.remove(wall_draw)
        self.add(wall)
        self.mb_wall = mb_wall

        # "anywhere short of the edge": the wall slides around
        keys = [0.93, 0.84, 0.96, 0.91]

        def wig(a):
            seg = min(int(a * 3), 2)
            f = smooth(a * 3 - seg)
            self.wsig = keys[seg] + (keys[seg + 1] - keys[seg]) * f

        self.wait_until(max(self.now, q0 + 0.44 * (q1 - q0)))
        self.play(self.drive(wig, rate_func=linear), run_time=max(0.5, q0 + 0.62 * (q1 - q0) - self.now))

        # descend back to the real axis: the wall is the same at every height,
        # the classical sliver is not; the zeros come back, all left of the wall
        self.play(self.drive(lambda a: self.tb.set_value(self.climbF(1 - a))),
                  run_time=max(0.5, q1 - 0.05 - self.now))
        self.tb.set_value(0.0)
        self.relayout()

        # {claim}: the wall is at 7/8
        s0 = self.wsig
        lab78 = MathTex(r"\tfrac78", font_size=44, color=YELLOW_).move_to([sx(7 / 8) - 0.4, 3.35, 0])
        card = paper_card("003", width=3.3).move_to([PANEL_CX, 0.12, 0]).set_z_index(6)
        card_target = card.get_center()
        card.shift(RIGHT * 6.5)
        tag = paper_tag("003", color=ACC)

        def to78(a):
            self.wsig = s0 + (7 / 8 - s0) * a
            wall.set_stroke(interpolate_color(ManimColor(WHITE_), ManimColor(YELLOW_), a))

        counter, self.counter = self.counter, None
        self.xatt = []
        self.mb_on, mb_wall, self.mb_wall = False, self.mb_wall, None
        self.play_at("claim", self.drive(to78), FadeOut(q), *self.swap(counter, self.t_lab),
                     *self.swap(wlab, lab78, shift=DOWN * 0.15),
                     FadeOut(VGroup(self.mbox, mb_wall, self.mb_fill, self.mb_edge)),
                     card.animate.move_to(card_target), run_time=self.rt(0.8, "cousins"))
        self.vlines = [v for v in self.vlines if v[0] is not wall]
        w78 = VDash(7 / 8, YELLOW_, width=4).set_z_index(1)
        w78.layout(self.Y(0), 0.0)
        band = Polygon(*[[0, 0, 0]] * 4, stroke_width=0, fill_color=YELLOW_, fill_opacity=0.2).set_z_index(-4)
        self.band_s1 = 7 / 8
        self.rects.append((band, 7 / 8, lambda: self.band_s1, 1.0))
        self.relayout()
        self.add(band)
        t78 = MathTex(r"\tfrac78", font_size=32, color=YELLOW_).move_to([sx(7 / 8), Y0 - 0.34, 0])
        self.sl_on = False

        def fill_band(a):
            self.band_s1 = 7 / 8 + a / 8

        self.play(self.drive(fill_band), ReplacementTransform(wall, w78),
                  FadeOut(self.sl_fill), FadeOut(self.sl_edge), FadeIn(t78), FadeIn(tag, shift=RIGHT * 0.2),
                  run_time=self.rt(0.8, "cousins"))
        zf = caps("zero-free", 20, YELLOW_).rotate(PI / 2).move_to([sx(15 / 16), 1.05, 0])
        self.play(FadeIn(zf, shift=UP * 0.2), run_time=self.rt(0.6, "cousins"))
        self.band, self.w78, self.lab78, self.card, self.zf = band, w78, lab78, card, zf

    # ------------------------------------------------------------ 6. cousins, not RH, margin, Siegel
    def cousins_and_close(self):
        zz = self.D["zeta"]
        Lz = self.D["L"]
        vis = VGroup(*[d for d, t in zip(self.zdots, zz) if t < 52])
        self.remove(self.zdots)
        self.add(vis)
        self.att = [a for a in self.att if a[0] not in self.zdots]

        hdrL = MathTex(r"L(s,\chi)", "=", r"\sum_{n\ge1}", r"\frac{\chi(n)}{n^s}", font_size=34, color=WHITE_)
        hdrL.next_to(self.hdr, RIGHT, buff=0.45)
        self.play_at("cousins", Write(hdrL), run_time=self.rt(0.9, "notrh"))

        c0 = self.cue("cousins")
        t_end = self.cue("L5_end")
        self.wait_until(max(self.now, min(c0 + 1.0, t_end - 5.4)))
        self.play(self.card.animate.shift(RIGHT * 6.5), run_time=0.6)
        self.remove(self.card)

        title = VGroup(txt("no zeros with", 24, GREY_),
                       MathTex(r"\sigma>\tfrac78", font_size=36, color=YELLOW_)).arrange(RIGHT, buff=0.15)
        title.move_to([RIGHT_X + 0.2, 2.25, 0], aligned_edge=LEFT)

        def row(mt):
            ck = check_mark(YELLOW_, size=0.26, width=4)
            r = VGroup(ck, mt).arrange(RIGHT, buff=0.22)
            return r

        rows = [row(MathTex(r"\zeta(s)", font_size=38, color=WHITE_))]
        for k in ("3", "4", "5"):
            rows.append(row(MathTex(r"L(s,\chi),\ \ \chi \bmod " + k, font_size=36, color=WHITE_)))
        last = txt("… and every Dirichlet L-function", 24, WHITE_)
        y = 1.5
        for r in rows:
            r.move_to([RIGHT_X + 0.25, y, 0], aligned_edge=LEFT)
            y -= 0.72
        last.move_to([RIGHT_X + 0.25, y - 0.05, 0], aligned_edge=LEFT)

        self.play(FadeIn(title, shift=LEFT * 0.2), FadeIn(rows[0], shift=LEFT * 0.2), run_time=0.6)

        # zeros morph: zeta -> L(s, chi mod 3) -> mod 4 -> mod 5, the band stays empty
        slots = np.linspace(self.now + 0.1, t_end - 1.4, 4)
        cur = vis
        for i, k in enumerate(("3", "4", "5")):
            new = VGroup(*[self.zero_dot(t) for t in Lz[k] if t < 52])
            self.wait_until(slots[i])
            self.play(ReplacementTransform(cur, new), FadeIn(rows[i + 1], shift=LEFT * 0.2),
                      self.band.animate(rate_func=there_and_back).set_fill(opacity=0.34), run_time=0.8)
            cur = new
        self.wait_until(slots[3])
        self.play(FadeIn(last, shift=LEFT * 0.2), run_time=self.rt(0.6, "notrh"))
        self.ldots = cur

        # {notrh}: the 1/2 line is still a question
        rh = VGroup(bold("Riemann Hypothesis", 30),
                    VGroup(txt("every zero on", 26, GREY_),
                           MathTex(r"\sigma=\tfrac12", font_size=36, color=WHITE_)).arrange(RIGHT, buff=0.15))
        rh.arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([RIGHT_X + 0.2, -0.5, 0], aligned_edge=UL)
        L5 = [t for t in Lz["5"] if t < 52]
        gaps = [(L5[i + 1] - L5[i], (L5[i + 1] + L5[i]) / 2) for i in range(len(L5) - 1) if 8 < L5[i] < 26]
        tgt = max(gaps)[1]
        arr = self.arrow_to(rh.get_left() + LEFT * 0.1, [sx(0.5) + 0.12, self.Y(tgt), 0])
        still = chip("STILL OPEN", ORANGE_, size=18).next_to(rh, DOWN, buff=0.28, aligned_edge=LEFT)
        self.play_at("notrh", FadeOut(VGroup(title, *rows, last)), FadeOut(self.hdr), FadeOut(hdrL),
                     FadeIn(rh, shift=LEFT * 0.2), GrowArrow(arr),
                     self.crit.animate.set_stroke(ACC, width=4, opacity=1.0),
                     run_time=self.rt(0.8, "margin"))
        self.play(FadeIn(still, scale=1.2), self.crit.animate.set_stroke(WHITE_, width=2.5, opacity=0.85),
                  run_time=self.rt(0.6, "margin"))

        # {margin}: a fixed margin of width 1/8, and the result banner
        br = Brace(Line([sx(7 / 8) + 0.03, 2.62, 0], [sx(1) - 0.03, 2.62, 0]), UP, buff=0.02,
                   color=WHITE_, sharpness=1.2)
        br_l = MathTex(r"\tfrac18", font_size=34, color=WHITE_).next_to(br, UP, buff=0.05)
        banner = result_banner(r"&\zeta(s)\neq0,\ \ L(s,\chi)\neq0\\ &\text{for } \operatorname{Re} s>\tfrac78",
                               lean=CATALOG["003"]["lean"], is_tex=True, size=34)
        banner.move_to([PANEL_CX, 2.35, 0]).set_z_index(5)
        self.play_at("margin", GrowFromCenter(br), FadeIn(br_l, shift=DOWN * 0.1),
                     self.band.animate.set_fill(opacity=0.34), run_time=self.rt(0.6, "siegel"))
        self.play(FadeIn(banner, shift=UP * 0.2), self.band.animate.set_fill(opacity=0.2),
                  run_time=self.rt(0.8, "siegel"))

        # {siegel}: a hypothetical real zero hugging s = 1 is ruled out
        sz = Dot([sx(0.94), Y0, 0], radius=0.075, color=RED_).set_z_index(5)
        sl = VGroup(bold("Landau–Siegel zero", 28, color=RED_),
                    txt("hypothetical real zero of L(s,χ)", 22, GREY_))
        sl.arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([RIGHT_X + 0.2, -0.8, 0], aligned_edge=UL)
        s_arr = Arrow(sl.get_left() + LEFT * 0.1, sz.get_center(), buff=0.22, stroke_width=3, color=RED_,
                      max_tip_length_to_length_ratio=0.08, tip_length=0.18)
        self.play_at("siegel", FadeOut(rh), FadeOut(arr), FadeOut(still),
                     GrowFromCenter(sz), FadeIn(sl, shift=LEFT * 0.2), GrowArrow(s_arr),
                     run_time=self.rt(0.7, "L6_end"))
        # "hypothetical rogue zeros hugging the edge"
        self.wait_until(max(self.now, self.cue("L6_end") - 3.9))
        self.play(sz.animate.move_to([sx(0.965), Y0, 0]), Flash(sz, color=RED_, line_length=0.15,
                                                                 flash_radius=0.2),
                  run_time=self.rt(0.8, "L6_end"))
        cross = VGroup(Line(UL, DR), Line(DL, UR)).scale(0.16).move_to([sx(0.965), Y0, 0])
        cross.set_stroke(RED_, width=7).set_z_index(6)
        self.wait_until(max(self.now, self.cue("L6_end") - 2.4))
        self.play(Create(cross), sz.animate.set_opacity(0.25), banner[0].animate(rate_func=there_and_back).set_stroke(width=5),
                  run_time=self.rt(0.6, "end", pad=0.6))
