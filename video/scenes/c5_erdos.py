import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import numpy as np

ACC = GOLD_
NUM = "159"

# ---------------------------------------------------------------- number grid
COLS, ROWS = 30, 6                 # 1..180; with 30 columns, step-30 APs are columns
CELL, GAP = 0.42, 0.022
PITCH = CELL + GAP
Y_TOP = 2.92                       # y of the first row once the grid is built
Y_INTRO = -0.4                     # y of the single intro row (1..30)

AP_INTRO = [5, 12, 19, 26]                 # step 7 (narration)
AP_PRIMES = [7, 37, 67, 97, 127, 157]      # six primes, step 30 (checked below)

# Word anchors (offsets from the nearest stable cue), measured on the narration.
W = dict(
    evenly="ap+1.7",
    five="L0_end-2.22", twelve="L0_end-1.70", nineteen="L0_end-1.30", twentysix="L0_end-0.70",
    wholeset="erdos+1.55", adding="erdos+3.6", infinity="erdos+4.85",
    must="primes-2.45", every="primes-1.25",
    thepr="primes+0.45", passt="primes+1.05", green="L1_end-4.55", arbit="L1_end-2.2",
    infull="claim+1.85", showing="claim+2.85",
    thin="prize-3.8", faster="prize-3.05", beyond="prize-0.75",
    cash="prize+1.75",
)


def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


assert all(is_prime(p) for p in AP_PRIMES) and not is_prime(187)
assert len({b - a for a, b in zip(AP_PRIMES, AP_PRIMES[1:])}) == 1
assert len({b - a for a, b in zip(AP_INTRO, AP_INTRO[1:])}) == 1


def prime_reciprocal_curve(xmax_exp=7):
    """(log10 x, sum_{p<=x} 1/p) as an honest step curve for x <= 1000,
    sampled log-uniformly above. Cached."""
    out = BUILD / "cache" / "c5_erdos" / "prime_recip.npy"
    if out.exists():
        return np.load(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 10 ** xmax_exp
    sieve = np.ones(n + 1, dtype=bool)
    sieve[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = False
    ps = np.nonzero(sieve)[0]
    cs = np.cumsum(1.0 / ps)
    pts = [(np.log10(2.0), 0.0)]
    prev = 0.0
    for p, s in zip(ps, cs):
        if p > 1000:
            break
        pts.append((np.log10(p), prev))
        pts.append((np.log10(p), s))
        prev = s
    for lx in np.linspace(3.0, xmax_exp, 240)[1:]:
        k = np.searchsorted(ps, 10 ** lx, side="right") - 1
        pts.append((lx, cs[k]))
    arr = np.array(pts)
    np.save(out, arr)
    return arr


def make_cell(n):
    sq = RoundedRectangle(width=CELL, height=CELL, corner_radius=0.05,
                          stroke_color=DIM, stroke_width=1.2, fill_color=CARD, fill_opacity=1.0)
    t = Text(str(n), font=SANS, font_size=20, color=WHITE_)
    if t.width > CELL * 0.82:
        t.scale_to_fit_width(CELL * 0.82)
    t.move_to(sq)
    g = VGroup(sq, t)
    g.sq, g.t, g.n = sq, t, n
    return g


def cell_pos(n, y0=Y_TOP):
    r, c = divmod(n - 1, COLS)
    return np.array([(c - (COLS - 1) / 2) * PITCH, y0 - r * PITCH, 0.0])


class C5Erdos(VoiceScene):

    # ------------------------------------------------------------ helpers
    def t(self, key):
        return self.cue(W.get(key, key))

    def at(self, key, *anims, rt=0.8, before=None, **kw):
        """Play anims starting at word `key`; never run past `before`."""
        self.wait_until(self.t(key))
        if before is not None:
            rt = max(0.25, min(rt, self.t(before) - self.now - 0.05))
        self.play(*anims, run_time=rt, **kw)

    def ripple(self, cell):
        r = cell.sq.copy().set_fill(opacity=0).set_stroke(ACC, width=4, opacity=1)
        return r

    def outs(self, *groups, **kw):
        """FadeOut for every top-level scene mobject that belongs to `groups`
        (members may have been added one by one)."""
        fam = set()
        for g in groups:
            fam.update(g.get_family())
        return [FadeOut(m, **kw) for m in list(self.mobjects)
                if m in fam or any(x in fam for x in m.get_family())]

    def gather(self, group):
        """Make `group` a single top-level mobject (its visible members were
        added one by one)."""
        fam = set(group.get_family())
        self.mobjects = [m for m in self.mobjects if m not in fam]
        self.add(group)
        return group

    # ------------------------------------------------------------ scene
    def construct(self):
        cells = {n: make_cell(n) for n in range(1, COLS * ROWS + 1)}
        for n, c in cells.items():
            c.move_to(cell_pos(n))
        row1 = VGroup(*[cells[n] for n in range(1, COLS + 1)])
        rest = VGroup(*[cells[n] for n in range(COLS + 1, COLS * ROWS + 1)])
        row1.shift(UP * (Y_INTRO - Y_TOP))

        # ============================================================ 1. {ap}
        title = serif("Arithmetic progression", 58).move_to(UP * 2.3)
        # general form a, a+d, a+2d, a+3d sitting under the example 5, 12, 19, 26
        terms = VGroup(*[tex(s_, 42, GREY_) for s_ in ("a", "a+d", "a+2d", "a+3d", r"\cdots")])
        for m, n in zip(terms, AP_INTRO + [AP_INTRO[-1] + 4]):
            m.move_to([cells[n].get_x(), Y_INTRO - 0.78, 0])
        terms[-1].set_x(cells[30].get_x() - 0.15)

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in row1], lag_ratio=0.04),
                  Write(title), run_time=1.25)
        self.at("evenly", LaggedStart(*[FadeIn(m, shift=UP * 0.12) for m in terms], lag_ratio=0.3),
                rt=1.3, before="five")

        arcs = VGroup()
        prev = None
        for i, (key, n) in enumerate(zip(["five", "twelve", "nineteen", "twentysix"], AP_INTRO)):
            c = cells[n]
            anims = [c.sq.animate.set_fill(ACC, 1.0).set_stroke(ACC, 2),
                     c.t.animate.set_color(BG), terms[i].animate.set_color(ACC)]
            if prev is not None:
                a = CurvedArrow(prev.get_top() + UP * 0.07, c.get_top() + UP * 0.07, angle=-PI / 2,
                                color=ACC, stroke_width=3, tip_length=0.16)
                lab = tex("+7", 34, ACC).next_to(a.point_from_proportion(0.5), UP, buff=0.1)
                arcs.add(VGroup(a, lab))
                anims += [Create(a), FadeIn(lab, shift=UP * 0.1)]
            self.wait_until(self.t(key) - 0.05)
            rp = self.ripple(c)
            self.add(rp)
            self.play(*anims, rp.animate.scale(1.8).set_stroke(opacity=0), run_time=0.45)
            self.remove(rp)
            prev = c

        # ============================================================ 2. {erdos}
        head = serif("Erdős's conjecture", 52, ACC).move_to(UP * 1.6)
        aset = tex(r"A\subseteq\{1,2,3,\dots\}", 42, GREY_).move_to(UP * 0.62)
        F = MathTex(r"\sum_{a\in A}\frac{1}{a}", r"=\infty", r"\;\Longrightarrow\;",
                    r"A\text{ has progressions of every length}", font_size=48, color=WHITE_)
        F.move_to(DOWN * 0.68)
        F[1][-1].set_color(ACC)

        minis = VGroup()
        for k in (3, 4, 5, 6):
            dots = VGroup(*[Dot(radius=0.085, color=ACC) for _ in range(k)]).arrange(RIGHT, buff=0.26)
            ln = Line(dots[0].get_center(), dots[-1].get_center(), color=ACC, stroke_width=2,
                      stroke_opacity=0.5)
            lab = tex(f"k={k}", 32, GREY_).next_to(dots, DOWN, buff=0.22)
            minis.add(VGroup(ln, dots, lab))
        dots_more = tex(r"\cdots", 40, GREY_)
        minis.add(dots_more)
        minis.arrange(RIGHT, buff=0.8, aligned_edge=UP).move_to(DOWN * 2.45)
        dots_more.match_y(minis[0][1])

        self.wait_until("erdos")
        lift = UP * (Y_TOP - Y_INTRO)
        self.play(FadeOut(title, shift=UP * 0.3), *self.outs(terms, arcs, shift=lift),
                  row1.animate.shift(UP * (Y_TOP - Y_INTRO)),
                  Succession(Wait(0.3), Write(head, run_time=0.9)), run_time=1.2)
        self.at("wholeset", FadeIn(aset, shift=DOWN * 0.15), rt=0.7)
        self.at("adding", Write(F[0]), rt=1.0, before="infinity")
        self.at("infinity", Write(F[1]), rt=0.5)
        self.play(Indicate(F[1][-1], color=ACC, scale_factor=1.35), run_time=0.45)
        self.at("must", Write(F[2]), Write(F[3]), rt=1.0, before="every")
        self.at("every", LaggedStart(*[FadeIn(m, shift=UP * 0.2) for m in minis], lag_ratio=0.25),
                *[Indicate(cells[n].sq, color=ACC, scale_factor=1.25) for n in AP_INTRO],
                rt=1.0, before="primes")

        # ============================================================ 3. {primes}
        # plot: partial sums of 1/p over primes p <= x (log-scale x)
        data = prime_reciprocal_curve()
        ax = Axes(x_range=[0, 7, 1], y_range=[0, 3.5, 1], x_length=4.3, y_length=2.15,
                  axis_config=dict(color=GREY_, stroke_width=2, include_tip=False,
                                   tick_size=0.05)).move_to([3.95, -2.05, 0])
        xt = VGroup(*[tex(s_, 26, GREY_).next_to(ax.c2p(v, 0), DOWN, buff=0.14)
                      for v, s_ in [(1, "10"), (3, "10^3"), (5, "10^5"), (7, "10^7")]])
        yt = VGroup(*[tex(str(v), 26, GREY_).next_to(ax.c2p(0, v), LEFT, buff=0.12) for v in (1, 2, 3)])
        xlab = tex("x", 30, GREY_).next_to(ax.c2p(7, 0), RIGHT, buff=0.12)
        hl = VGroup(*[DashedLine(ax.c2p(0, v), ax.c2p(7, v), color=DIM, stroke_width=1.2,
                                 dash_length=0.06) for v in (1, 2, 3)])
        curve = VMobject().set_points_as_corners([ax.c2p(x, y) for x, y in data])
        curve.set_stroke(ACC, width=3.5)
        ptitle = tex(r"\frac12+\frac13+\frac15+\frac17+\frac1{11}+\cdots=\infty", 32)
        ptitle.move_to([3.65, -0.33, 0])
        ptitle[0][-1].set_color(ACC)
        tick = check_mark(GREEN_, size=0.32, width=4).next_to(ptitle, RIGHT, buff=0.18)
        clab = tex(r"\sim\log\log x\to\infty", 30, GREY_).move_to(ax.c2p(4.75, 0.52))
        plot = VGroup(hl, ax, xt, yt, xlab, curve, clab)

        # Green–Tao column + the AP pulled out below the grid
        col = VGroup(*[cells[n] for n in AP_PRIMES])
        nums = VGroup(*[Text(str(n), font=SANS, font_size=36, weight=SEMIBOLD, color=WHITE_)
                        for n in AP_PRIMES])
        for i, m in enumerate(nums):
            m.move_to([-5.8 + 1.12 * i, -1.3, 0])
        gt_arcs = VGroup()
        for a_, b_ in zip(nums, nums[1:]):
            a = CurvedArrow(a_.get_top() + UP * 0.1, b_.get_top() + UP * 0.1, angle=-PI / 2,
                            color=ACC, stroke_width=2.5, tip_length=0.13)
            lab = tex("+30", 28, ACC).next_to(a.point_from_proportion(0.5), UP, buff=0.07)
            gt_arcs.add(VGroup(a, lab))
        gt_name = bold("Green–Tao (2008)", 28, ACC)
        gt_sub = txt("arbitrarily long progressions of primes", 24, GREY_)
        gt = VGroup(gt_name, gt_sub).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        gt.next_to(nums, DOWN, buff=0.45).align_to(nums, LEFT)

        self.wait_until("primes")
        lhs = self.gather(VGroup(F[0], F[1]))
        self.play(FadeOut(head, shift=UP * 0.2), FadeOut(aset, shift=UP * 0.2),
                  *self.outs(VGroup(F[2], F[3]), minis, shift=DOWN * 0.2),
                  ReplacementTransform(lhs, ptitle),
                  LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in rest], lag_ratio=0.006),
                  *[cells[n].sq.animate.set_fill(CARD, 1.0).set_stroke(DIM, 1.2) for n in AP_INTRO],
                  *[cells[n].t.animate.set_color(WHITE_) for n in AP_INTRO],
                  run_time=0.8)
        prime_anims = []
        for n in range(1, COLS * ROWS + 1):
            c = cells[n]
            if is_prime(n):
                prime_anims.append(AnimationGroup(c.sq.animate.set_fill(ACC, 0.24).set_stroke(ACC, 1.8),
                                                  c.t.animate.set_color(WHITE_)))
            else:
                prime_anims.append(c.t.animate.set_color(DIM))
        rt = float(np.clip(self.t("green") - 0.45 - self.now, 0.9, 1.6))
        self.play(LaggedStart(*prime_anims, lag_ratio=0.004),
                  FadeIn(VGroup(hl, ax, xt, yt, xlab)),
                  Succession(Wait(0.25 * rt), Create(curve, rate_func=linear, run_time=0.75 * rt)),
                  run_time=rt)
        self.play(FadeIn(tick, scale=0.5), FadeIn(clab, shift=UP * 0.1), run_time=0.35)
        self.wait_until(self.t("green") - 0.1)
        self.play(LaggedStart(*[AnimationGroup(c.sq.animate.set_fill(ACC, 1.0).set_stroke(ACC, 2),
                                               c.t.animate.set_color(BG)) for c in col], lag_ratio=0.25),
                  run_time=0.8)
        colbox = SurroundingRectangle(col, color=ACC, buff=0.06, corner_radius=0.08, stroke_width=3)
        self.play(Create(colbox),
                  LaggedStart(*[TransformFromCopy(c.t, m) for c, m in zip(col, nums)], lag_ratio=0.12),
                  run_time=1.0)
        self.play(LaggedStart(*[AnimationGroup(Create(a[0]), FadeIn(a[1], shift=UP * 0.08))
                                for a in gt_arcs], lag_ratio=0.3), run_time=0.9)
        self.at("arbit", FadeIn(gt_name, shift=UP * 0.12), FadeIn(gt_sub, shift=UP * 0.12), rt=0.7)
        self.play(Indicate(colbox, color=ACC, scale_factor=1.04), run_time=0.9)

        # ============================================================ 4. {claim}
        card = paper_card(NUM, width=3.0).move_to([4.62, 0.3, 0])
        tag = paper_tag(NUM, color=ACC)
        cap = caps("The paper claims", 20, ACC)
        chead = serif("Erdős's conjecture, in full", 46)
        hdr = VGroup(cap, chead).arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_edge(LEFT, buff=0.55)
        hdr.set_y(2.62)

        klab = tex("k =", 34, GREY_)
        ksq = VGroup()
        for k in range(3, 10):
            sq = RoundedRectangle(width=0.56, height=0.56, corner_radius=0.08, stroke_color=DIM,
                                  stroke_width=1.5, fill_color=CARD, fill_opacity=1.0)
            ksq.add(VGroup(sq, tex(str(k), 32, GREY_).move_to(sq)))
        ksq.arrange(RIGHT, buff=0.12)
        kmore = tex(r"\cdots", 36, GREY_)
        krow = VGroup(klab, ksq, kmore).arrange(RIGHT, buff=0.22)
        krow.align_to(hdr, LEFT).set_y(1.28)

        dfn = textex(r"If $A\subseteq\{1,\dots,N\}$ has no $k$-term progression:", 32, GREY_)
        dfn.align_to(hdr, LEFT).set_y(0.28)
        b_old = tex(r"|A|\le C_k\,N\exp\!\big(-(\log\log N)^{c_k}\big)", 42, GREY_)
        b_new = tex(r"|A|\le C_k\,N\exp\!\big(-c_k(\log N)^{\varepsilon_k}\big)", 42, WHITE_)
        assert len(b_old[0]) == 24 and len(b_new[0]) == 23
        x_old, x_new = b_old[0][12:23], b_new[0][12:22]      # (log log N)^c  vs  c(log N)^eps
        x_new.set_color(ACC)
        l_old = bold("before (k ≥ 5)", 24, GREY_)
        l_new = bold("this paper", 24, ACC)
        for lab, b, y in ((l_old, b_old, -0.72), (l_new, b_new, -1.75)):
            lab.align_to(hdr, LEFT).set_y(y)
            b.set_x(-3.62 + b.width / 2).set_y(y)
        ul_new = Underline(x_new, color=ACC, stroke_width=3, buff=0.06)

        self.wait_until("claim")
        beat3 = Group(*cells.values(), colbox, plot, ptitle, tick, nums, gt_arcs, gt)
        card.shift(RIGHT * 5.5)
        self.play(*self.outs(beat3, shift=LEFT * 0.4),
                  card.animate.shift(LEFT * 5.5), run_time=0.9)
        self.play(FadeIn(tag, shift=RIGHT * 0.2), FadeIn(cap, shift=RIGHT * 0.2),
                  Write(chead), FadeIn(krow, shift=UP * 0.1), run_time=0.9)
        self.at(self.t("infull") - 0.15,
                LaggedStart(*[AnimationGroup(s[0].animate.set_fill(ACC, 0.22).set_stroke(ACC, 2),
                                             s[1].animate.set_color(WHITE_)) for s in ksq]
                            + [kmore.animate.set_color(ACC)], lag_ratio=0.18),
                rt=1.0)
        self.at("showing", FadeIn(dfn, shift=UP * 0.12), rt=0.7)
        # the previous record for long progressions, as the baseline
        self.play(FadeIn(l_old, shift=RIGHT * 0.15), FadeIn(b_old, shift=UP * 0.12),
                  card.animate.shift(UP * 0.04), run_time=0.8)
        self.play(card.animate.shift(UP * 0.04), run_time=max(0.2, self.t("thin") - self.now - 0.1),
                  rate_func=linear)
        # ... and the paper's bound grows out of it: log log N  ->  log N
        self.at(self.t("thin") - 0.1, FadeIn(l_new, shift=RIGHT * 0.15),
                TransformFromCopy(b_old, b_new), rt=0.9)
        self.at("faster", Create(ul_new), Indicate(x_new, color=ACC, scale_factor=1.15), rt=0.8)
        self.play(Indicate(x_old, color=WHITE_, scale_factor=1.1), run_time=0.8)
        known = txt("known", 22, GREY_).next_to(ksq[0], DOWN, buff=0.12)
        self.at("beyond",
                ksq[0][0].animate.set_fill(CARD, 1.0).set_stroke(DIM, 1.5),
                ksq[0][1].animate.set_color(GREY_), FadeIn(known, shift=DOWN * 0.08),
                *[s.animate(rate_func=there_and_back).scale(1.12) for s in ksq[1:]],
                rt=0.6)

        # ============================================================ 5. {prize}
        banner = result_banner(
            r"\sum_{a\in A}\frac{1}{a}=\infty\;\Longrightarrow\;\text{arithmetic progressions of every length}",
            color=ACC, lean=CATALOG[NUM]["lean"], is_tex=True, size=32)
        banner.to_edge(LEFT, buff=0.55).set_y(-0.2)
        coin = VGroup(Circle(radius=0.3, stroke_color=ACC, stroke_width=3, fill_color=ACC,
                             fill_opacity=0.16),
                      bold("$", 30, ACC))
        coin[1].move_to(coin[0])
        plabel = bold("Erdős prize problem", 30, WHITE_)
        prize = VGroup(coin, plabel).arrange(RIGHT, buff=0.22)
        prize.align_to(banner, LEFT).shift(RIGHT * 0.1).set_y(1.38)

        self.wait_until("prize")
        self.play(*self.outs(VGroup(hdr, krow, known, dfn, l_old, l_new, b_old, b_new, ul_new),
                             shift=LEFT * 0.3), run_time=0.45)
        self.play(FadeIn(banner, shift=UP * 0.2), run_time=0.65)
        self.at(self.t("cash") - 0.35, GrowFromCenter(coin), FadeIn(plabel, shift=RIGHT * 0.15), rt=0.6)
        self.play(Indicate(coin, color=ACC, scale_factor=1.2), run_time=0.7)
        hold = self.narr_end - 0.5 - self.now
        if hold > 0.3:
            self.play(banner.animate.shift(UP * 0.06), card.animate.shift(UP * 0.06),
                      run_time=hold, rate_func=linear)
        self.finish()
