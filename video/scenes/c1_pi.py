import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import math

import mpmath as mp

# ======================================================================
# True numbers (all computed here)
# ======================================================================
ACC = BLUE_          # family accent / pi
FR = GOLD_           # fractions p/q

mp.mp.dps = 60
PI = mp.pi
PI_F = float(PI)


def cf_convergents(x, n):
    a, y = [], x
    for _ in range(n):
        ai = int(mp.floor(y))
        a.append(ai)
        y = 1 / (y - ai)
    p0, q0, p1, q1 = 1, 0, a[0], 1
    out = [(p1, q1)]
    for ai in a[1:]:
        p0, q0, p1, q1 = p1, q1, ai * p1 + p0, ai * q1 + q0
        out.append((p1, q1))
    return out


def pi_err(p, q):
    return abs(PI - mp.mpf(p) / q)


CONV = [(p, q) for p, q in cf_convergents(PI, 18) if q <= 10 ** 6]
# (p, q, log10 q, log10 |pi - p/q|)
PTS = [(p, q, float(mp.log10(q)), float(mp.log10(pi_err(p, q)))) for p, q in CONV]
assert all(le < -2 * lq for _, _, lq, le in PTS)          # every convergent beats 1/q^2


def trunc_digits(x, n):
    """Truncated decimal expansion of x with n decimals (string)."""
    k = int(mp.floor(x * mp.mpf(10) ** n))
    s = str(k)
    return s[:-n] + "." + s[-n:]


def common_prefix(a, b):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return i


ND = 14
DIG_PI = trunc_digits(PI, ND)
DIG_22 = trunc_digits(mp.mpf(22) / 7, ND)
DIG_355 = trunc_digits(mp.mpf(355) / 113, ND)
M22 = common_prefix(DIG_PI, DIG_22)        # "3.14"     -> 4 chars
M355 = common_prefix(DIG_PI, DIG_355)      # "3.141592" -> 8 chars
assert M355 - 2 == 6                       # six decimal places
V22, V355 = 22 / 7, 355 / 113
E355 = pi_err(355, 113)
E355_EXP = int(mp.floor(mp.log10(E355)))
E355_MANT = float(E355 / mp.mpf(10) ** E355_EXP)
E355_TEX = rf"\approx {E355_MANT:.1f}\times 10^{{{E355_EXP}}}"

# proven upper bounds on mu(pi) (research notes, family 017)
RECORDS = [("Mahler", "1953", 42, "42"),
           ("Mignotte", "1974", 20, "20"),
           ("Hata", "1993", 8.01604539, "8.016"),
           ("Salikhov", "2008", 7.606308, "7.606"),
           ("Zeilberger–Zudilin", "2020", 7.103205334137, "7.103")]

# Flint Hills partial sums S_N = sum_{n<=N} 1/(n^3 sin^2 n)
FH_N = 1000
FH_S = []
_s = 0.0
for _n in range(1, FH_N + 1):
    _s += 1.0 / (_n ** 3 * math.sin(_n) ** 2)
    FH_S.append(_s)
FH_JUMP = max(range(1, FH_N), key=lambda i: FH_S[i] - FH_S[i - 1]) + 1   # = 355
assert FH_JUMP == 355


def clip01(v):
    return max(0.0, min(1.0, v))


# ======================================================================
# Zoomable number line centred on pi
# ======================================================================
NL_Y = -1.55
HALF = 6.2
UNIT = 10 ** 10                   # positions as integers in units of 1e-10
C_INT = PI_F * UNIT
LEVELS = []                       # (spacing in 1e-10 units, decimals)
for e in range(0, -10, -1):
    LEVELS.append((10 ** (e + 10), max(0, -e)))
    LEVELS.append((5 * 10 ** (e + 9), -(e - 1)))


def fmt_pos(P, dec):
    ip, fp = divmod(P, UNIT)
    if dec == 0:
        return str(ip)
    return f"{ip}." + f"{fp:010d}"[:dec]


class ZoomTicks(VGroup):
    """Tick marks + labels of a number line zooming in on pi.

    Children are never removed (a grow-only pool of lines and labels whose
    opacity is switched off when unused): the Cairo renderer draws the family
    flattened at the start of each play, so replacing children mid-play would
    leave ghosts behind."""

    def __init__(self, lw, alpha, grow):
        super().__init__()
        self.lw, self.alpha, self.grow = lw, alpha, grow
        self.cache = {}
        self.lines = []
        self.add_updater(lambda m: m.rebuild())
        self.rebuild()

    def label(self, s):
        if s not in self.cache:
            t = Text(s, font=SANS, font_size=22, color=GREY_)
            self.cache[s] = t
            self.add(t)
        return self.cache[s]

    def line(self, k):
        while len(self.lines) <= k:
            ln = Line(UP * 0.1, DOWN * 0.1, stroke_color=GREY_, stroke_width=2)
            self.lines.append(ln)
            self.add(ln)
        return self.lines[k]

    def rebuild(self):
        w = 10 ** self.lw.get_value()
        A = self.alpha.get_value()
        ext = (HALF + 0.25) * self.grow.get_value()      # visible half-length of the axis
        sp = [(D / UNIT) / w * HALF for D, _ in LEVELS]
        vis = [i for i in range(len(LEVELS)) if sp[i] >= 0.2]
        al = [clip01((s - 1.75) / 0.8) for s in sp]       # label alpha per level
        # All labels share one number of decimals (3.140, 3.145 rather than 3.14,
        # 3.145). When a finer level brings in an extra decimal, the old labels
        # cross-fade into the padded ones (common prefix kept in place).
        lab = [i for i in range(len(LEVELS)) if al[i] > 0]
        d_lo = d_hi = 0
        wgt = 1.0
        if lab:
            d_hi = LEVELS[lab[-1]][1]
            full = [i for i in lab if al[i] >= 1]
            d_lo = LEVELS[full[-1]][1] if full else LEVELS[lab[0]][1]
            if d_hi > d_lo:
                wgt = max(al[i] for i in lab if LEVELS[i][1] == d_hi)
        used, shown = 0, set()
        if A > 0.003 and vis:
            fi = vis[-1]
            Df = LEVELS[fi][0]
            lo = math.ceil((C_INT - w * 1.03 * UNIT) / Df)
            hi = math.floor((C_INT + w * 1.03 * UNIT) / Df)
            ly = NL_Y - 0.36
            for K in range(lo, hi + 1):
                P = K * Df
                i = next(j for j in vis if P % LEVELS[j][0] == 0)
                x = (P - C_INT) / UNIT / w * HALF
                edge = clip01((HALF - abs(x)) / 0.6) * clip01((ext - abs(x)) / 0.3)
                if edge <= 0:
                    continue
                a_t = clip01((sp[i] - 0.2) / 0.45)
                a_l = al[i]
                h = 0.05 + 0.09 * clip01((sp[i] - 0.5) / 1.5) + 0.07 * a_l
                op = a_t * edge * A
                if op > 0.01:
                    ln = self.line(used)
                    used += 1
                    ln.put_start_and_end_on(np.array([x, NL_Y - h, 0.0]), np.array([x, NL_Y + h, 0.0]))
                    ln.set_stroke(GREY_, width=2, opacity=op)
                lo_ = a_l * edge * A
                if lo_ > 0.01:
                    if LEVELS[i][1] >= d_hi or wgt >= 1.0:
                        s = fmt_pos(P, d_hi)
                        t = self.label(s)
                        t.move_to([x, ly, 0]).set_opacity(lo_)
                        shown.add(s)
                    else:
                        s0, s1 = fmt_pos(P, d_lo), fmt_pos(P, d_hi)
                        t0, t1 = self.label(s0), self.label(s1)
                        left = (x - t0.width / 2) * (1 - wgt) + (x - t1.width / 2) * wgt
                        t0.move_to([left + t0.width / 2, ly, 0]).set_opacity(lo_ * (1 - wgt))
                        t1.move_to([left + t1.width / 2, ly, 0]).set_opacity(lo_ * wgt)
                        shown.update((s0, s1))
        for ln in self.lines[used:]:
            ln.set_stroke(opacity=0)
        for s, t in self.cache.items():
            if s not in shown:
                t.set_opacity(0)
        return self


class Odometer(VGroup):
    """Fixed-width decimal readout whose glyph slots are re-shaped in place
    (DecimalNumber replaces its children, which ghosts under Cairo)."""

    def __init__(self, fmt, value, size=40, color=WHITE_):
        super().__init__()
        self.fmt = fmt
        allg = MathTex("0123456789.", font_size=size, color=color)[0]
        self.tpl = {c: allg[k] for k, c in enumerate("0123456789.")}
        base = allg[1].get_bottom()[1]
        self.off = {c: self.tpl[c].get_bottom()[1] - base for c in self.tpl}
        s0 = fmt.format(value)
        ref = MathTex(s0, font_size=size, color=color)[0]
        self.anchor = VectorizedPoint(ref.get_center())
        ax, ay = self.anchor.get_center()[:2]
        self.slots = [g.copy() for g in ref]
        self.pos = [(g.get_x() - ax, g.get_bottom()[1] - self.off[c] - ay) for g, c in zip(ref, s0)]
        self.add(self.anchor, *self.slots)
        self.set_value(value)

    def set_value(self, v):
        s = self.fmt.format(v)
        ax, ay = self.anchor.get_center()[:2]
        for slot, c, (x, by) in zip(self.slots, s, self.pos):
            slot.become(self.tpl[c])
            slot.move_to([ax + x, 0, 0]).shift(UP * (ay + by + self.off[c] - slot.get_bottom()[1]))
        return self


# ======================================================================
# Convergent plot (log-log)
# ======================================================================
PX0, SX = -4.55, 1.13            # x = PX0 + SX * log10 q      (q = 1 .. 10^6)
PY0, SY = 2.2, 0.405             # y = PY0 + SY * log10 err    (err = 1 .. 10^-12)
LX_MAX, LE_MIN = 6.0, -12.0


def c2p(lq, le):
    return np.array([PX0 + SX * lq, PY0 + SY * le, 0.0])


# ======================================================================
class C1Pi(VoiceScene):
    def construct(self):
        self.act_number_line()
        self.act_plot()
        self.act_records()
        self.act_flint()
        self.finish()

    # ------------------------------------------------------------------
    def act_number_line(self):
        # ---- hook: big pi
        big_pi = tex(r"\pi", 200, ACC).move_to(UP * 0.35)
        self.play_at("pi", Write(big_pi), run_time=0.7)

        # ---- decimal rows
        def row(lhs, digs, m, lhs_col, rest_col):
            r = MathTex(lhs, "=", digs[:m], digs[m:] + r"\ldots", font_size=44)
            r[0].set_color(lhs_col)
            r[2].set_color(WHITE_)
            r[3].set_color(rest_col)
            return r

        r_pi = row(r"\pi", DIG_PI, M355, ACC, WHITE_)
        r_22 = row(r"\frac{22}{7}", DIG_22, M22, FR, GREY_)
        r_355 = row(r"\frac{355}{113}", DIG_355, M355, FR, GREY_)
        rows = [r_pi, r_22, r_355]
        for r, y in zip(rows, (3.12, 2.0, 0.88)):
            r.shift(-r[1].get_center() + UP * y)
        blk = VGroup(*rows)
        dx = -blk.get_center()[0] + 0.0
        for r in rows:
            r.shift(RIGHT * dx)

        # ---- zoomable number line
        lw = ValueTracker(math.log10(0.32))
        nl_a = ValueTracker(0.0)
        nl_g = ValueTracker(0.0)      # axis growth: ticks never stick out past the line
        axis = Line([-HALF - 0.25, NL_Y, 0], [HALF + 0.25, NL_Y, 0], color=GREY_, stroke_width=2.5)
        ticks = ZoomTicks(lw, nl_a, nl_g)

        def xval(v):
            x = (v - PI_F) / (10 ** lw.get_value()) * HALF
            return max(-30.0, min(30.0, x))

        pi_stem = Line([0, NL_Y, 0], [0, NL_Y + 0.42, 0], color=ACC, stroke_width=3)
        pi_dot = Dot([0, NL_Y, 0], radius=0.075, color=ACC)
        pi_lab = tex(r"\pi", 40, ACC).next_to(pi_stem, UP, buff=0.04).shift(LEFT * 0.24)
        pi_mark = VGroup(pi_stem, pi_dot, pi_lab)

        def frac_marker(v, s):
            stem = Line([0, NL_Y, 0], [0, NL_Y + 1.0, 0], color=FR, stroke_width=2.5)
            dot = Dot([0, NL_Y, 0], radius=0.07, color=FR)
            lab = tex(s, 34, FR).next_to(stem, UP, buff=0.08)
            g = VGroup(stem, dot, lab)
            g.add_updater(lambda m: m.move_to([xval(v), m.get_center()[1], 0]))
            g.update()
            return g

        self.play_at(self.cue("pi") + 0.75,
                     ReplacementTransform(big_pi, r_pi[0]),
                     run_time=0.65)
        self.play(Write(r_pi[1:]), run_time=0.85)
        self.add(ticks)
        self.play(GrowFromCenter(axis), nl_g.animate(rate_func=smooth).set_value(1.0),
                  nl_a.animate(rate_func=lambda t: smooth(clip01(2 * t - 0.6))).set_value(1.0),
                  GrowFromEdge(pi_mark, DOWN), run_time=0.8)
        # first zoom: pi among 3.0 .. 3.4  ->  pi +- 0.0045
        self.play_until("f22", lw.animate.set_value(math.log10(0.0045)),
                        rate_func=smooth)

        # ---- 22/7
        m22 = frac_marker(V22, r"\frac{22}{7}")
        src22 = r_22[0].copy()
        self.play(FadeIn(r_22[1:], shift=RIGHT * 0.15), FadeIn(r_22[0]),
                  FadeIn(m22[0]), FadeIn(m22[1]), ReplacementTransform(src22, m22[2]),
                  run_time=max(0.4, min(0.9, self.cue("f355") - self.now - 0.05)))
        self.remove(*m22)
        self.add(m22)
        self.wait_until("f355")

        # ---- 355/113
        m355 = frac_marker(V355, r"\frac{355}{113}")
        src355 = r_355[0].copy()
        self.play(FadeIn(r_355[1:], shift=RIGHT * 0.15), FadeIn(r_355[0]),
                  FadeIn(m355[0]), FadeIn(m355[1]), ReplacementTransform(src355, m355[2]),
                  run_time=0.9)
        self.remove(*m355)
        self.add(m355)
        # second zoom: until 355/113 separates from pi
        w_final = float(E355) / 2.35 * HALF
        self.play_until(self.cue("L0_end") - 1.65, lw.animate.set_value(math.log10(w_final)),
                        rate_func=smooth)
        m22.clear_updaters()
        self.remove(m22)

        # ---- six decimal places + error brace
        x355 = xval(V355)
        boxes = VGroup(*[SurroundingRectangle(r[2][2:], color=YELLOW_, buff=0.07,
                                              stroke_width=2.5, corner_radius=0.05)
                         for r in (r_pi, r_355)])
        brace = BraceBetweenPoints([0, NL_Y - 0.62, 0], [x355, NL_Y - 0.62, 0],
                                   direction=DOWN, color=YELLOW_)
        elab = tex(E355_TEX, 36, YELLOW_).next_to(brace, DOWN, buff=0.12)
        self.play(Create(boxes), GrowFromCenter(brace), FadeIn(elab, shift=DOWN * 0.1),
                  run_time=0.8)
        self.play_until("measure", Indicate(r_pi[2][2:], color=YELLOW_, scale_factor=1.06),
                        Indicate(r_355[2][2:], color=YELLOW_, scale_factor=1.06))

        self.nl = dict(rows=rows, axis=axis, ticks=ticks, nl_a=nl_a, pi_mark=pi_mark,
                       m355=m355, boxes=boxes, brace=brace, elab=elab)

    # ------------------------------------------------------------------
    def act_plot(self):
        nl = self.nl
        r_pi, r_22, r_355 = nl["rows"]

        # ---- axes (log-log)
        x_ax = Line(c2p(0, LE_MIN), c2p(LX_MAX, LE_MIN), color=GREY_, stroke_width=2.5)
        y_ax = Line(c2p(0, LE_MIN), c2p(0, 0) + UP * 0.15, color=GREY_, stroke_width=2.5)
        xt = VGroup()
        for k in range(0, 7):
            p = c2p(k, LE_MIN)
            xt.add(Line(p, p + UP * 0.1, color=GREY_, stroke_width=2))
            xt.add(tex("1" if k == 0 else ("10" if k == 1 else f"10^{{{k}}}"), 26, GREY_)
                   .next_to(p, DOWN, buff=0.14))
        yt = VGroup()
        for k in range(0, 13, 3):
            p = c2p(0, -k)
            yt.add(Line(p, p + RIGHT * 0.1, color=GREY_, stroke_width=2))
            yt.add(tex("1" if k == 0 else f"10^{{-{k}}}", 26, GREY_).next_to(p, LEFT, buff=0.14))
        x_title = VGroup(txt("denominator", 26, GREY_), tex("q", 34, GREY_)).arrange(RIGHT, buff=0.12)
        x_title[1].align_to(x_title[0], DOWN).shift(DOWN * 0.075)
        x_title.next_to(xt, DOWN, buff=0.16).set_x(c2p(3, 0)[0])
        y_title = VGroup(txt("error", 26, GREY_), tex(r"\left|\pi-\tfrac{p}{q}\right|", 34, WHITE_)
                         ).arrange(RIGHT, buff=0.14)
        y_title.next_to(c2p(0, 0), UP, buff=0.32).align_to(c2p(0, 0) + LEFT * 0.75, LEFT)
        axes = VGroup(x_ax, y_ax, xt, yt)

        # ---- points
        dots = {}
        for p, q, lq, le in PTS:
            dots[(p, q)] = Dot(c2p(lq, le), radius=0.07, color=FR)
        d22, d355 = dots[(22, 7)], dots[(355, 113)]
        lab22 = tex(r"\frac{22}{7}", 30, FR).next_to(d22, LEFT, buff=0.12)
        lab355 = tex(r"\frac{355}{113}", 30, FR).next_to(d355, DL, buff=0.06)

        # ---- transition
        t0 = self.now
        fade_out = [FadeOut(VGroup(r_pi, r_22[1:], r_355[1:], nl["boxes"]), shift=UP * 0.3),
                    FadeOut(VGroup(nl["axis"], nl["pi_mark"], nl["m355"], nl["brace"], nl["elab"])),
                    nl["nl_a"].animate.set_value(0.0)]
        nl["m355"].clear_updaters()
        self.play(*fade_out, run_time=0.5)
        nl["ticks"].clear_updaters()
        self.remove(nl["ticks"])
        self.play(Create(axes), Write(y_title),
                  ReplacementTransform(r_22[0], lab22), ReplacementTransform(r_355[0], lab355),
                  LaggedStart(Wait(run_time=0.6), GrowFromCenter(d22), GrowFromCenter(d355),
                              lag_ratio=1.0),
                  run_time=1.3)
        # "... compared to the size of the denominator"
        self.play_at(self.cue("measure") + 2.3, FadeIn(x_title, shift=UP * 0.1),
                     ShowPassingFlash(x_ax.copy().set_stroke(ACC, width=6), time_width=0.5),
                     run_time=max(0.5, min(1.0, self.cue("dirichlet") - self.now - 0.2)))

        # ---- Dirichlet: the 1/q^2 line
        mu = ValueTracker(2.0)

        def line_end():
            m = mu.get_value()
            return (min(LX_MAX, -LE_MIN / m), max(LE_MIN, -LX_MAX * m))

        def mk_line():
            lx, le = line_end()
            return Line(c2p(0, 0), c2p(lx, le), color=ACC, stroke_width=4)

        def mk_shade():
            lx, le = line_end()
            pts = [c2p(0, 0), c2p(lx, le), c2p(lx, LE_MIN), c2p(0, LE_MIN)]
            return Polygon(*pts, stroke_width=0, fill_color=ACC, fill_opacity=0.10)

        mu_line = mk_line()
        shade = mk_shade()
        rhs2 = tex(r"\frac{1}{q^{2}}", 34, ACC)
        rhsmu = tex(r"\frac{1}{q^{\mu}}", 34, ACC)
        rhsmu[0][max(range(len(rhsmu[0])), key=lambda i: rhsmu[0][i].get_x())].set_color(YELLOW_)

        def place_line_label(m):
            m.move_to(c2p(0.55, -0.55 * mu.get_value()) + UR * 0.3 + RIGHT * 0.12)
            return m
        place_line_label(rhs2)

        # right column
        CX = 4.45
        cap1 = caps("true for every irrational", 18, GREY_, spacing=0.03).move_to([CX, 2.55, 0])
        if cap1.get_right()[0] > 6.55:
            cap1.shift(LEFT * (cap1.get_right()[0] - 6.55))
        f_lhs = tex(r"\left|\pi-\frac{p}{q}\right|\;<", 46)
        f_r2 = tex(r"\frac{1}{q^{2}}", 46)
        f_rmu = tex(r"\frac{1}{q^{\mu}}", 46)
        f_rmu[0][max(range(len(f_rmu[0])), key=lambda i: f_rmu[0][i].get_x())].set_color(YELLOW_)
        form = VGroup(f_lhs, f_r2).arrange(RIGHT, buff=0.18).move_to([CX, 1.55, 0])
        f_rmu.move_to(f_r2, aligned_edge=LEFT)
        cap2 = txt("for infinitely many p/q", 26, GREY_).move_to([CX, 0.55, 0])

        self.play(Create(mu_line), FadeIn(shade), FadeIn(cap1, shift=DOWN * 0.1),
                  run_time=1.2)
        self.play(FadeIn(rhs2, shift=UP * 0.1), run_time=0.4)

        rest = [dots[(p, q)] for p, q, _, _ in PTS if (p, q) not in ((22, 7), (355, 113))]
        self.play_at(self.cue("dirichlet") + 1.75,
                     LaggedStart(*[GrowFromCenter(d) for d in rest], lag_ratio=0.28),
                     run_time=2.0)
        self.play(Write(form), run_time=1.0)
        self.play(FadeIn(cap2, shift=UP * 0.1), run_time=0.6)
        # gentle emphasis while "within about one over q squared" is spoken
        self.play_until("exponent", Indicate(f_r2, color=ACC, scale_factor=1.12),
                        mu_line.animate.set_stroke(width=5.5), rate_func=there_and_back)

        # ---- irrationality exponent: rotate the line to 1/q^3
        cap1b = caps("irrationality exponent", 18, ACC, spacing=0.03).move_to([CX, 2.55, 0])
        cap2b = txt("for infinitely many p/q?", 26, WHITE_).move_to(cap2)
        mu_lab = VGroup(tex(r"\mu =", 44, YELLOW_), Odometer("{:.2f}", 2.0, 44, YELLOW_))
        mu_lab.arrange(RIGHT, buff=0.15).move_to([CX, -0.45, 0])
        mu_lab[1].add_updater(lambda m: m.set_value(mu.get_value()))
        place_line_label(rhsmu)
        self.play(ReplacementTransform(cap1, cap1b), ReplacementTransform(f_r2, f_rmu),
                  ReplacementTransform(cap2, cap2b), ReplacementTransform(rhs2, rhsmu),
                  FadeIn(mu_lab, shift=UP * 0.1), run_time=1.0)

        mu_line.add_updater(lambda m: m.become(mk_line()))
        shade.add_updater(lambda m: m.become(mk_shade()))
        rhsmu.add_updater(place_line_label)

        def dim_updater(d, lq, le):
            def f(m):
                margin = (-mu.get_value() * lq) - le       # >0: below the line
                a = clip01((margin + 0.18) / 0.18)
                m.set_color(interpolate_color(ManimColor(DIM), ManimColor(FR), a))
            return f
        for p, q, lq, le in PTS:
            dots[(p, q)].add_updater(dim_updater(dots[(p, q)], lq, le))

        self.play_between(self.cue("exponent") + 1.3, self.cue("record") - 1.15,
                          mu.animate.set_value(3.0), rate_func=smooth)
        for d in dots.values():
            d.clear_updaters()
        mu_lab[1].clear_updaters()
        rhsmu.clear_updaters()
        mu_line.clear_updaters()
        shade.clear_updaters()
        self.play(Indicate(d22, color=YELLOW_, scale_factor=1.8),
                  Indicate(d355, color=YELLOW_, scale_factor=1.8),
                  Indicate(lab22, color=YELLOW_), Indicate(lab355, color=YELLOW_),
                  run_time=max(0.5, min(0.9, self.cue("record") - self.now - 0.05)))

        self.plot = VGroup(axes, x_title, y_title, mu_line, shade, rhsmu, lab22, lab355,
                           *dots.values(), cap1b, f_lhs, f_rmu, cap2b, mu_lab)

    # ------------------------------------------------------------------
    def act_records(self):
        self.wait_until("record")

        # ---- ladder of proven upper bounds (horizontal bars)
        X0 = -2.75
        S = 5.25 / 42
        ROW_Y = [1.85, 1.07, 0.29, -0.49, -1.27, -2.05]
        BH = 0.42

        title = VGroup(txt("Best proven upper bound on", 30, GREY_), tex(r"\mu(\pi)", 42, WHITE_))
        title.arrange(RIGHT, buff=0.18).to_edge(UP, buff=0.42).set_x(-6.25, direction=LEFT)
        title[1].align_to(title[0], DOWN).shift(DOWN * 0.08)
        base = Line([X0, ROW_Y[0] + 0.45, 0], [X0, ROW_Y[-1] - 0.4, 0], color=GREY_, stroke_width=2)

        def row_label(name, year, col=WHITE_, ycol=GREY_):
            n = txt(name, 24, col)
            y = txt(year, 22, ycol)
            g = VGroup(n, y).arrange(DOWN, aligned_edge=RIGHT, buff=0.08)
            return g

        def mk_bar(v, y, col=ACC, op=0.55):
            return Rectangle(width=max(v * S, 1e-3), height=BH, stroke_color=col, stroke_width=2,
                             fill_color=col, fill_opacity=op).move_to([X0 + v * S / 2, y, 0])

        rows, grows = [], []
        for (name, year, val, vs), y in zip(RECORDS, ROW_Y):
            lab = row_label(name, year).next_to([X0, y, 0], LEFT, buff=0.22)
            bar = mk_bar(val, y)
            num = tex(vs, 34, WHITE_).next_to(bar, RIGHT, buff=0.14)
            rows.append(VGroup(lab, bar, num))

            def grow(m, a, bar=bar, num=num, val=val, y=y):
                bar.become(mk_bar(val * a, y)).set_opacity(clip01(a * 10))
                bar.set_fill(opacity=0.55 * clip01(a * 10))
                num.next_to(bar, RIGHT, buff=0.14).set_opacity(clip01(a * 2.5))
            grows.append(AnimationGroup(FadeIn(lab, shift=RIGHT * 0.15),
                                        UpdateFromAlphaFunc(VGroup(bar, num), grow)))

        self.play(FadeOut(self.plot), FadeIn(title, shift=DOWN * 0.1), Create(base), run_time=0.6)
        self.play(LaggedStart(*grows, lag_ratio=0.33),
                  run_time=max(1.5, min(2.6, self.cue("L2_end") - 1.0 - self.now)))
        # "... about seven point one"
        zz = rows[-1]
        hl = SurroundingRectangle(VGroup(zz[1], zz[2]), color=WHITE_, buff=0.1,
                                  stroke_width=2.5, corner_radius=0.08)
        self.play_at(self.cue("L2_end") - 0.95, Create(hl), Indicate(zz[2], color=WHITE_),
                     run_time=0.8)

        # ---- the claim: a new bar drops to 2
        self.wait_until("claim")
        bar6 = zz[1].copy()
        num6 = Odometer("{:.3f}", RECORDS[-1][2], 34, YELLOW_)
        num6.next_to(bar6, RIGHT, buff=0.14)
        lab6 = row_label("This paper", "2026 · claimed", YELLOW_, YELLOW_)
        lab6.next_to([X0, ROW_Y[-1], 0], LEFT, buff=0.22)
        tr = ValueTracker(0.0)
        y5, y6 = ROW_Y[-2], ROW_Y[-1]
        v5 = RECORDS[-1][2]

        def upd_bar(m):
            t = tr.get_value()
            ty = smooth(clip01(t * 2.2))
            tv = smooth(clip01((t - 0.25) / 0.75))
            v = v5 + (2.0 - v5) * tv
            y = y5 + (y6 - y5) * ty
            m.become(Rectangle(width=v * S, height=BH, stroke_color=interpolate_color(
                ManimColor(ACC), ManimColor(YELLOW_), ty), stroke_width=2,
                fill_color=interpolate_color(ManimColor(ACC), ManimColor(YELLOW_), ty),
                fill_opacity=0.55 + 0.35 * ty).move_to([X0 + v * S / 2, y, 0]))

        bar6.add_updater(upd_bar)
        num6.add_updater(lambda m: m.set_value(v5 + (2.0 - v5) * smooth(clip01((tr.get_value() - 0.25) / 0.75)))
                         .next_to(bar6, RIGHT, buff=0.14))
        self.add(bar6, num6)

        card = paper_card("017", width=2.95).move_to([5.05, 0.0, 0])
        tag = paper_tag("017", color=ACC)
        self.play(tr.animate.set_value(1.0), FadeOut(hl), FadeIn(lab6, shift=DOWN * 0.15),
                  FadeIn(card, shift=LEFT * 1.6), run_time=1.3)
        bar6.clear_updaters()
        num6.clear_updaters()
        two = tex("2", 36, YELLOW_).move_to(num6, aligned_edge=LEFT)

        # big statement in the free space
        COLX = 1.2
        claim = tex(r"\mu(\pi) = 2", 72, YELLOW_).move_to([COLX, -0.2, 0])
        self.play(Write(claim), FadeIn(tag, shift=RIGHT * 0.2), ReplacementTransform(num6, two),
                  run_time=0.8)

        # floor at mu = 2: "the smallest possible"
        fx = X0 + 2 * S
        floor = DashedLine([fx, ROW_Y[0] + 0.45, 0], [fx, ROW_Y[-1] - 0.38, 0],
                           color=WHITE_, stroke_width=2.5, dash_length=0.1,
                           dashed_ratio=0.55).set_opacity(0.8)
        floor_lab = txt("smallest possible", 24, WHITE_).next_to(floor, UP, buff=0.1)
        floor_lab.align_to([fx - 0.1, 0, 0], LEFT)
        self.play_until("typical", Create(floor), FadeIn(floor_lab, shift=DOWN * 0.1))

        # ---- typical number
        hist = VGroup(*[VGroup(r[1], r[2]) for r in rows], base)
        self.play(hist.animate.set_opacity(0.3),
                  VGroup(*[r[0] for r in rows]).animate.set_opacity(0.45),
                  ShowPassingFlash(Line(floor.get_top(), floor.get_bottom(), color=YELLOW_,
                                        stroke_width=7), time_width=0.6),
                  run_time=1.2)
        card.add_updater(lambda m, dt: m.shift(UP * 0.018 * dt))
        glow6 = SurroundingRectangle(bar6, color=YELLOW_, buff=0.06, stroke_width=3,
                                     corner_radius=0.04)
        self.play_at(self.cue("typical") + 1.4, ShowPassingFlash(glow6, time_width=0.5),
                     Indicate(claim, color=YELLOW_, scale_factor=1.05), run_time=1.2)
        typ = VGroup(txt("same as almost every", 26, WHITE_),
                     txt("real number", 26, WHITE_)).arrange(DOWN, buff=0.12)
        typ.next_to(claim, DOWN, buff=0.45)
        self.play_at(self.cue("L3_end") - 1.8, FadeIn(typ, shift=UP * 0.15), run_time=0.9)
        self.wait_until("flint")
        card.clear_updaters()

        self.rec = dict(title=title, base=base, rows=rows, bar6=bar6, two=two, lab6=lab6,
                        floor=floor, floor_lab=floor_lab, typ=typ, claim=claim, card=card,
                        tag=tag)

    # ------------------------------------------------------------------
    def act_flint(self):
        R = self.rec
        banner = result_banner(r"\mu(\pi)=2", lean=CATALOG["017"]["lean"], is_tex=True, size=50)
        banner.move_to([0, 2.72, 0])
        banner[0].set_z_index(2)
        banner[1].set_z_index(3)
        R["claim"].set_z_index(3)
        others = VGroup(R["title"], R["base"], *R["rows"], R["bar6"], R["two"], R["lab6"],
                        R["floor"], R["floor_lab"], R["typ"])
        self.play(FadeOut(others), FadeOut(R["card"], shift=RIGHT * 1.2),
                  ReplacementTransform(R["claim"], banner[1][1]), run_time=0.7)
        self.play(FadeIn(banner[0], scale=1.04), FadeIn(banner[1][0], shift=DOWN * 0.08),
                  run_time=0.45)

        # ---- Flint Hills series (left)
        LX = -3.55
        fh_title = bold("Flint Hills series", 32, WHITE_).move_to([LX, 1.15, 0])
        series = tex(r"\sum_{n\ge 1}\frac{1}{n^{3}\sin^{2} n}", 60, WHITE_).move_to([LX, -0.15, 0])
        conv = VGroup(check_mark(GREEN_, size=0.32, width=5), bold("converges", 36, GREEN_))
        conv.arrange(RIGHT, buff=0.18).move_to([LX, -1.55, 0])

        # ---- partial sums plot (right)
        AX0, AX1 = 0.85, 6.15
        AY0, AY1 = -2.35, 1.2
        smax = 32.0

        def sp(n, s):
            return np.array([AX0 + (AX1 - AX0) * n / FH_N, AY0 + (AY1 - AY0) * s / smax, 0])

        fx_ax = Line(sp(0, 0), sp(FH_N, 0) + RIGHT * 0.1, color=GREY_, stroke_width=2.5)
        fy_ax = Line(sp(0, 0), sp(0, smax), color=GREY_, stroke_width=2.5)
        xlab = tex("N", 32, GREY_).next_to(fx_ax, RIGHT, buff=0.12)
        xticks = VGroup()
        for n in (500, 1000):
            p = sp(n, 0)
            xticks.add(Line(p, p + DOWN * 0.1, color=GREY_, stroke_width=2),
                       tex(str(n), 24, GREY_).next_to(p, DOWN, buff=0.16))
        ylab = VGroup(txt("partial sums", 22, GREY_)).next_to(fy_ax, UP, buff=0.12).align_to(fy_ax, LEFT)
        pts = [sp(n, FH_S[n - 1]) for n in range(1, FH_N + 1)]
        curve = VMobject(stroke_color=ACC, stroke_width=4).set_points_as_corners(pts)
        jx = sp(FH_JUMP, 0)
        jline = DashedLine(jx, sp(FH_JUMP, FH_S[FH_JUMP - 1]), color=FR, stroke_width=2,
                           dash_length=0.08)
        jtick = tex(str(FH_JUMP), 24, FR).next_to(jx, DOWN, buff=0.16)
        jlab = tex(r"355 \approx 113\,\pi", 32, FR).next_to(sp(FH_JUMP, FH_S[FH_JUMP - 1]), RIGHT,
                                                           buff=0.25).shift(UP * 0.35)

        # sin^2 n glyphs (denominator, after "n^3")
        gl = list(series[0])
        bar_g = max(gl, key=lambda g: g.width / max(g.height, 1e-3))
        den = sorted([g for g in gl if g.get_y() < bar_g.get_y() - 0.05
                      and g.get_x() > bar_g.get_left()[0]], key=lambda g: g.get_x())
        sin_part = VGroup(*den[2:])

        self.play(Write(series), run_time=1.1)
        self.wait_until(self.cue("flint") + 2.7)
        self.play(FadeIn(fh_title, shift=DOWN * 0.1), Create(VGroup(fx_ax, fy_ax)), FadeIn(xlab),
                  FadeIn(xticks), FadeIn(ylab), run_time=0.6)
        self.play_until(self.cue("L4_end") - 1.5, Create(curve, rate_func=linear),
                        Succession(Wait(run_time=1.0),
                                   Indicate(sin_part, color=FR, scale_factor=1.15, run_time=1.0)))
        self.play(Create(jline), FadeIn(jtick), FadeIn(jlab, shift=LEFT * 0.1), run_time=0.5)
        self.play_at(self.cue("L4_end") - 0.7, Create(conv[0]), FadeIn(conv[1], shift=RIGHT * 0.1),
                     run_time=0.55)
