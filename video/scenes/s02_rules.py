import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

# Ground rules: what the preprints are, Lean formalizations (the LEAN badge),
# caveats, and the plan of the video.

INTRO_PAPERS = ["102", "158", "017"]      # fixed-procedure papers for the opening fan
WAFFLE_COLS, WAFFLE_ROWS = 31, 12          # 31 x 12 = 372 families
SQ, PITCH, WAFFLE_Y = 0.28, 0.35, 0.05

LEAN_FILE = "lean/OAI/NumberTheory/DirichletL/Nonvanishing.lean"
# real statement + docstring from LEAN_FILE (docstring re-flowed onto two lines)
CODE_LINES = [
    ("/-- The Riemann zeta function does not vanish", "doc"),
    ("    to the right of `7 / 8`. -/", "doc"),
    ("theorem riemannZeta_ne_zero_of_seven_eighths_lt_re", "thm"),
    ("    {s : ℂ} (hs : (7 / 8 : ℝ) < s.re) :", "plain"),
    ("    riemannZeta s ≠ 0 :=", "plain"),
]


def win(a, b, f=smooth):
    """Rate function that runs f only within [a, b] of the animation's time.
    Used instead of LaggedStart where the animated mobjects already exist (a
    LaggedStart group would be re-added on top and change the z-order)."""
    return lambda t: f(min(1.0, max(0.0, (t - a) / (b - a))))


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def code_text(size=22):
    rows = []
    for s, kind in CODE_LINES:
        if kind == "doc":
            rows.append(f'<span foreground="{GREY_}">{_esc(s)}</span>')
        elif kind == "thm":
            kw, name = s.split(" ", 1)
            rows.append(f'<span foreground="{PINK_}">{kw}</span> '
                        f'<span foreground="{BLUE_}">{_esc(name)}</span>')
        else:
            rows.append(_esc(s))
    markup = f'<span font_features="calt=0,liga=0">' + "\n".join(rows) + "</span>"
    t = MarkupText(markup, font=MONO, font_size=size, color=WHITE_)
    # split glyphs into lines
    lines, i = VGroup(), 0
    for s, _ in CODE_LINES:
        n = sum(1 for ch in s if not ch.isspace())
        lines.add(VGroup(*t[i:i + n]))
        i += n
    return t, lines


class S02Rules(VoiceScene):

    # ------------------------------------------------------------ helpers
    def frac(self, a, b, f):
        """Time a fraction f of the way from cue a to cue b."""
        return self.cue(a) + f * (self.cue(b) - self.cue(a))

    def freeze(self, *mobs):
        """Stop ambient updaters before a fade-out. (Animation copies keep their
        updaters, which would otherwise fight the fade.) Drops empty drivers."""
        for m in mobs:
            for f in m.get_family():
                f.clear_updaters()
            if isinstance(m, VMobject) and not m.has_points() and not m.submobjects:
                self.remove(m)

    def drive(self, fn):
        """Run fn(dt) every frame (for groups that are not themselves in the scene)."""
        d = VMobject()
        d.add_updater(lambda m, dt: fn(dt))
        self.add(d)
        self.bring_to_back(d)   # z-order first => everything above is redrawn each frame
        return d

    def flow(self, pos, n=3, color=WHITE_, speed=0.45, radius=0.05):
        """Dots streaming along a path; pos(u) gives the point at u in [0,1]."""
        dots = VGroup(*[Dot(radius=radius, color=color) for _ in range(n)])
        dots.phase = 0.0

        def upd(m, dt):
            m.phase = (m.phase + dt * speed) % 1.0
            for k, d in enumerate(m):
                u = (m.phase + k / n) % 1.0
                d.move_to(pos(u))
                d.set_opacity(0.9 * np.sin(np.pi * u) ** 0.7)
        upd(dots, 0)
        dots.add_updater(upd)
        return dots

    # ------------------------------------------------------------ construct
    def construct(self):
        self.intro()
        self.pipeline()
        self.lean_waffle()
        self.code_panel()
        self.badge()
        self.rest()
        self.claims()
        self.plan()
        self.wait_until("end-0.5")
        self.freeze(*self.mobjects)
        self.finish()

    # ------------------------------------------------------------ 1. preprints
    def intro(self):
        F = lambda f: self.frac("preprint", "L0_end", f)
        title = serif("Ground rules", 84)
        self.wait_until("preprint")
        self.play_until(F(0.19), Write(title), rate_func=smooth, min_time=0.5)

        cards = [paper_card(n, width=2.45) for n in INTRO_PAPERS]
        for c, x, y, a in zip(cards, (-2.75, 0, 2.75), (0.35, 0.55, 0.35), (9, 0, -9)):
            c.rotate(a * DEGREES).move_to([x, y, 0])
            c.shift(DOWN * 7.5)
        self.add(cards[0], cards[2], cards[1])           # middle card on top
        hdr_pos = serif("Ground rules", 30).to_corner(UL, buff=0.42)
        self.play_between(F(0.21), F(0.4), title.animate.scale(30 / 84).move_to(hdr_pos),
                          LaggedStart(*[c.animate.shift(UP * 7.5) for c in (cards[0], cards[1], cards[2])],
                                      lag_ratio=0.12), min_time=0.5)
        self.header = title

        # stamp: "These are preprints"
        word = caps("Preprint", 40, ORANGE_, spacing=0.1)
        box = RoundedRectangle(width=word.width + 0.6, height=word.height + 0.42, corner_radius=0.1,
                               stroke_color=ORANGE_, stroke_width=5, fill_color=BG, fill_opacity=0.88)
        word.move_to(box)
        stamp = VGroup(box, word).rotate(11 * DEGREES).move_to([0.1, 0.35, 0])
        self.wait_until(F(0.41))
        self.play(FadeIn(stamp, scale=1.6), run_time=0.3, rate_func=rush_into)

        fan = Group(*cards, stamp)
        self.fan_drv = self.drive(lambda dt: fan.scale(1 + 0.012 * dt))   # slow push-in

        cap = txt("written by an internal OpenAI model", 32, GREY_,
                  t2c={"internal OpenAI model": WHITE_}).move_to(DOWN * 2.85)
        self.play_at(F(0.52), FadeIn(cap, shift=UP * 0.15), run_time=0.6)
        self.cards, self.stamp, self.fan, self.intro_caps = cards, stamp, fan, cap

    # ------------------------------------------------------------ 2. procedure / exceptions
    def pipeline(self):
        Y = 1.15
        cards, stamp, fan = self.cards, self.stamp, self.fan
        # nodes
        prob = Circle(radius=0.5, stroke_color=WHITE_, stroke_width=2.5, fill_color=CARD, fill_opacity=1)
        q = serif("?", 44).move_to(prob)
        prob_g = VGroup(prob, q).move_to([-4.6, Y, 0])
        prob_lbl = txt("problem", 24, GREY_).next_to(prob_g, DOWN, buff=0.16)

        m1 = bold("internal model", 28)
        m2 = txt("avg. 3 h of thinking", 22, GREY_)
        mtxt = VGroup(m1, m2).arrange(DOWN, buff=0.14)
        mbox = RoundedRectangle(width=mtxt.width + 0.6, height=mtxt.height + 0.5, corner_radius=0.18,
                                stroke_color=WHITE_, stroke_width=2, fill_color=CARD_HI, fill_opacity=1)
        model = VGroup(mbox, mtxt).move_to([-0.35, Y, 0])
        mtxt.move_to(mbox)

        px = 4.3
        targets = [np.array([px - 0.32, Y - 0.04, 0]), np.array([px, Y + 0.04, 0]),
                   np.array([px + 0.32, Y - 0.04, 0])]
        scale = 0.92 / 2.45
        paper_lbl = txt("preprints", 24, GREY_).move_to([px, Y - 1.0, 0])

        a1 = Arrow(prob_g.get_right(), mbox.get_left(), buff=0.15, stroke_width=3, color=GREY_,
                   max_tip_length_to_length_ratio=0.12)
        a2 = Arrow(mbox.get_right(), [px - 0.95, Y, 0], buff=0.15, stroke_width=3, color=GREY_,
                   max_tip_length_to_length_ratio=0.12)
        box = RoundedRectangle(width=12.1, height=2.95, corner_radius=0.25, stroke_color=GREY_,
                               stroke_width=1.5, stroke_opacity=0.5).move_to([-0.25, Y - 0.05, 0])
        box_lbl = caps("Most results:", 22, GREY_, spacing=0.07)
        most = caps("one fixed procedure", 22, WHITE_, spacing=0.07)
        VGroup(box_lbl, most).arrange(RIGHT, buff=0.28, aligned_edge=UP).next_to(
            box.get_corner(UL), DR, buff=0.25).shift(UP * 0.03)

        # --- transition from the fan
        self.wait_until("L0_end")
        self.remove(self.fan_drv)
        self.play_until(self.frac("procedure", "exceptions", 0.97),
                        FadeOut(stamp, scale=0.9, rate_func=win(0, 0.22)),
                        FadeOut(self.intro_caps, shift=DOWN * 0.2, rate_func=win(0, 0.22)),
                        *[c.animate(rate_func=win(0, 0.5)).scale(scale).move_to(t)
                          for c, t in zip(cards, targets)],
                        Create(box, rate_func=win(0.05, 0.5)),
                        FadeIn(box_lbl, rate_func=win(0.15, 0.5)), FadeIn(most, rate_func=win(0.2, 0.55)),
                        GrowFromCenter(prob_g, rate_func=win(0.3, 0.6)),
                        FadeIn(prob_lbl, rate_func=win(0.35, 0.62)),
                        GrowArrow(a1, rate_func=win(0.45, 0.7)),
                        FadeIn(model, scale=0.9, rate_func=win(0.52, 0.8)),
                        GrowArrow(a2, rate_func=win(0.66, 0.9)),
                        FadeIn(paper_lbl, rate_func=win(0.75, 1.0)),
                        min_time=0.8)
        f1 = self.flow(lambda u, a=a1: a.get_start() + u * (a.get_end() - a.get_start()), color=WHITE_)
        f2 = self.flow(lambda u, a=a2: a.get_start() + u * (a.get_end() - a.get_start()), color=WHITE_)
        self.add(f1, f2)
        self.wait_until("exceptions")

        # --- exceptions side path
        start = np.array(prob_lbl.get_bottom() + DOWN * 0.12)
        zone = RoundedRectangle(width=6.3, height=2.7, corner_radius=0.2).move_to([3.15, -2.15, 0])
        zone_d = DashedVMobject(zone.set_stroke(GOLD_, 1.6, opacity=0.8), num_dashes=70, dashed_ratio=0.55)
        yb = zone.get_center()[1]
        path = VMobject()
        path.start_new_path(start)
        path.add_line_to(np.array([start[0], yb + 0.4, 0]))
        path.add_quadratic_bezier_curve_to(np.array([start[0], yb, 0]), np.array([start[0] + 0.4, yb, 0]))
        path.add_line_to(np.array([zone.get_left()[0] - 0.12, yb, 0]))
        path.set_stroke(GOLD_, 2.5)
        path_d = DashedVMobject(path, num_dashes=34, dashed_ratio=0.55)
        tip = Triangle(stroke_width=0, fill_color=GOLD_, fill_opacity=1).scale(0.09)
        tip.rotate(-PI / 2).move_to([zone.get_left()[0] - 0.1, yb, 0])
        ex_chip = chip("EXCEPTIONS", GOLD_, size=20, fill_opacity=0.18)
        ex_back = ex_chip[0].copy().set_stroke(width=0).set_fill(BG, 1)
        ex = VGroup(ex_back, ex_chip).move_to([zone.get_center()[0], zone.get_top()[1], 0])

        z_card = paper_card("003", width=1.0).move_to([1.55, -1.82, 0])
        h_card = paper_card("032", width=1.0).move_to([4.65, -1.82, 0])

        def two(a, b):
            return VGroup(txt(a, 22, WHITE_), txt(b, 22, GREY_)).arrange(DOWN, buff=0.08)
        z_lbl = two("Riemann zeta", "zero-free region").next_to(z_card, DOWN, buff=0.14)
        h_lbl = two("Hodge conjecture", "CM abelian varieties").next_to(h_card, DOWN, buff=0.14)
        z_lbl.align_to(h_lbl, UP)

        self.play_until(self.frac("exceptions", "L1_end", 0.2),
                        Create(path_d), Create(zone_d), FadeIn(tip), FadeIn(ex, scale=0.8),
                        rate_func=smooth)
        f3 = self.flow(lambda u: path.point_from_proportion(u), n=2, color=GOLD_, speed=0.35)
        self.add(f3)
        self.play_at(self.frac("exceptions", "L1_end", 0.28),
                     FadeIn(z_card, shift=UP * 0.3), FadeIn(z_lbl, shift=UP * 0.15), run_time=0.6)
        self.play_at(self.frac("exceptions", "L1_end", 0.52),
                     FadeIn(h_card, shift=UP * 0.3), FadeIn(h_lbl, shift=UP * 0.15), run_time=0.6)
        self.play_at(self.frac("exceptions", "L1_end", 0.82),
                     Indicate(ex_chip, color=YELLOW_, scale_factor=1.12),
                     zone_d.animate.set_stroke(opacity=1.0, width=2.4), run_time=0.8)
        self.pipe = Group(*cards, prob_g, prob_lbl, model, a1, a2, box, box_lbl, most, paper_lbl,
                          f1, f2, f3, path_d, tip, zone_d, ex, z_card, h_card, z_lbl, h_lbl)

    # ------------------------------------------------------------ 3. 235 of 372
    def build_waffle(self):
        nums = sorted(CATALOG)
        assert len(nums) == WAFFLE_COLS * WAFFLE_ROWS
        x0 = -(WAFFLE_COLS - 1) * PITCH / 2
        y0 = (WAFFLE_ROWS - 1) * PITCH / 2 + WAFFLE_Y
        sqs, lean, rest = VGroup(), VGroup(), VGroup()
        for i, n in enumerate(nums):
            r, c = divmod(i, WAFFLE_COLS)
            sq = Square(SQ, stroke_width=0, fill_color=DIM, fill_opacity=0.55)
            sq.move_to([x0 + c * PITCH, y0 - r * PITCH, 0])
            sqs.add(sq)
            (lean if CATALOG[n]["lean"] else rest).add(sq)
        return sqs, lean, rest

    def lean_waffle(self):
        sqs, lean, rest = self.build_waffle()
        self.sqs, self.lean_sqs, self.rest_sqs = sqs, lean, rest
        assert len(lean) == 235 and len(rest) == 137

        ref = bold("235", 64, TEAL_)
        of = txt("/ 372 families", 34, GREY_)
        lab = bold("with Lean formalizations", 30, TEAL_)
        row = VGroup(ref, of, lab).arrange(RIGHT, buff=0.28, aligned_edge=DOWN).move_to([0, 2.7, 0])
        tr = ValueTracker(0)
        slide = (lab.width + 0.28) / 2
        ref.shift(RIGHT * slide)
        of.shift(RIGHT * slide)
        # fixed pool of digit glyphs (3 slots x 10 digits), shown/hidden in place:
        # no become()/re-parenting mid-play, so no ghosting
        vis = ValueTracker(0)
        num = VGroup()
        for k in range(3):
            slot = VGroup(*[bold(str(d), 64, TEAL_) for d in range(10)])
            for g in slot:
                g.move_to([ref[k].get_center()[0], 0, 0]).align_to(ref, DOWN)
            num.add(slot)

        def upd(m):
            v = int(round(tr.get_value()))
            digs = [v // 100, (v // 10) % 10, v % 10]
            show = [v >= 100, v >= 10, True]
            for slot, dgt, on in zip(m, digs, show):
                for d, g in enumerate(slot):
                    g.set_fill(opacity=vis.get_value() if (on and d == dgt) else 0.0)
        upd(num)
        num.add_updater(upd)

        self.wait_until("L1_end")
        self.freeze(self.pipe)
        self.play_until("lean+0.4", FadeOut(self.pipe, shift=UP * 0.3), min_time=0.3)
        self.add(num)
        self.play_until(self.frac("lean", "code", 0.24),
                        LaggedStart(*[FadeIn(s, scale=0.4) for s in sqs], lag_ratio=0.008),
                        vis.animate.set_value(1.0), FadeIn(of), rate_func=linear)
        self.play_until(self.frac("lean", "code", 0.6),
                        LaggedStart(*[s.animate.set_fill(TEAL_, 0.92) for s in lean], lag_ratio=0.03),
                        tr.animate.set_value(235), rate_func=linear)
        num.clear_updaters()
        self.play_until(self.frac("lean", "code", 0.8), FadeIn(lab, shift=LEFT * 0.2),
                        VGroup(num, of).animate.shift(LEFT * slide), min_time=0.3)
        self.counter = VGroup(num, of, lab)

    # ------------------------------------------------------------ 4. Lean code
    def code_panel(self):
        t, lines = code_text(22)
        pitch_bar = 0.27
        bars_w = [40, 31, 46, 24, 37]
        cw = 0.179  # mono advance at font_size 22
        panel = RoundedRectangle(width=10.5, height=4.05, corner_radius=0.18, stroke_color=DIM,
                                 stroke_width=1.5, fill_color=CARD, fill_opacity=0.96)
        panel.move_to([0, 0.35, 0])
        t.next_to(panel.get_corner(UL), DR, buff=0.0).shift(RIGHT * 0.62 + DOWN * 0.4)
        bars = VGroup()
        y = lines[-1].get_bottom()[1] - 0.38
        for k, w in enumerate(bars_w):
            b = RoundedRectangle(width=w * cw, height=0.075, corner_radius=0.03, stroke_width=0,
                                 fill_color=DIM, fill_opacity=0.75)
            b.move_to([0, y - k * pitch_bar, 0]).align_to(t, LEFT).shift(RIGHT * 2 * cw)
            bars.add(b)
        fname = mono(LEAN_FILE, 22, GREY_).next_to(panel, UP, buff=0.18).align_to(panel, LEFT)
        gx = panel.get_left()[0] + 0.3
        items = []
        for ln in lines:
            items.append((ln.get_center()[1], None))
        for b in bars:
            items.append((b.get_center()[1], b))
        checks = VGroup()
        for yy, bar in items:
            ck = check_mark(TEAL_, size=0.15, width=2.6).move_to([gx, yy, 0])
            ck.set_stroke(opacity=0)
            ck.is_bar = bar is not None
            checks.add(ck)

        early = lambda t: smooth(min(1.0, t / 0.3))
        late = lambda t: smooth(max(0.0, (t - 0.12) / 0.88))
        self.wait_until("code-0.1")
        self.play_until(self.frac("code", "L2_end", 0.34),
                        FadeOut(self.sqs, shift=DOWN * 0.25, rate_func=early),
                        FadeOut(self.counter, shift=UP * 0.2, rate_func=early),
                        FadeIn(panel, rate_func=late), FadeIn(fname, rate_func=late),
                        LaggedStart(*[FadeIn(ln, shift=RIGHT * 0.15) for ln in lines],
                                    LaggedStart(*[GrowFromEdge(b, LEFT) for b in bars], lag_ratio=0.15),
                                    lag_ratio=0.18, rate_func=late))
        self.add(checks)
        band = Rectangle(width=panel.width - 0.08, height=0.36, stroke_width=0,
                         fill_color=TEAL_, fill_opacity=0.12)
        ytop, ybot = items[0][0] + 0.25, items[-1][0] - 0.2

        def scan(m, a):
            yb = ytop + a * (ybot - ytop)
            m.move_to([panel.get_center()[0], yb, 0])
            for (yy, bar), ck in zip(items, checks):
                on = yb <= yy + 0.02
                ck.set_stroke(opacity=1.0 if (on and not ck.is_bar) else 0.0)
                if bar is not None:
                    bar.set_fill(TEAL_ if on else DIM, opacity=0.85 if on else 0.75)
        scan(band, 0)
        self.wait_until(self.frac("code", "L2_end", 0.36))
        self.add(band)
        self.play_until(self.frac("code", "L2_end", 0.8),
                        UpdateFromAlphaFunc(VGroup(band, checks, bars), lambda m, a: scan(band, a)),
                        rate_func=linear)
        ok_ck = check_mark(TEAL_, size=0.34, width=4)
        ok_t = bold("checked by computer", 30, TEAL_)
        ok = VGroup(ok_ck, ok_t).arrange(RIGHT, buff=0.22).next_to(panel, DOWN, buff=0.38)
        self.play_until(self.frac("code", "L2_end", 0.97), FadeOut(band), Create(ok_ck),
                        FadeIn(ok_t, shift=RIGHT * 0.2), min_time=0.3)
        self.code_grp = VGroup(panel, t, bars, fname, checks, ok)

    # ------------------------------------------------------------ 5. the badge
    def badge(self):
        big = lean_badge(14).scale(4.3).move_to([0, 0.25, 0])
        halo = glow(big[0], TEAL_, layers=8, width=36, opacity=0.05)
        halo.t = 0.0

        def pulse(m, dt):
            m.t += dt
            m.set_stroke(opacity=0.035 + 0.03 * np.sin(2.2 * m.t))
        c1 = txt("this family has a Lean formalization", 32, WHITE_).move_to([0, -0.9, 0])
        c2 = txt("covering at least part of the result", 30, GREY_,
                 t2c={"at least part": YELLOW_}).next_to(c1, DOWN, buff=0.3)

        self.play_between("L2_end", "badge+0.85",
                          FadeOut(self.code_grp, shift=LEFT * 0.4, rate_func=win(0, 0.45)),
                          GrowFromCenter(big, rate_func=win(0.3, 1.0)),
                          FadeIn(halo, scale=0.3, rate_func=win(0.3, 1.0)), min_time=0.5)
        halo.add_updater(pulse)
        halo.add_updater(lambda m: m.move_to(big))
        self.play_at(self.frac("badge", "L3_end", 0.3), big.animate.move_to([0, 0.8, 0]),
                     FadeIn(c1, shift=UP * 0.15), run_time=0.6)
        self.play_at(self.frac("badge", "L3_end", 0.56), FadeIn(c2, shift=UP * 0.15), run_time=0.6)
        self.big_badge, self.halo, self.badge_caps = big, halo, VGroup(c1, c2)

    # ------------------------------------------------------------ 6. the rest
    def rest(self):
        big, halo = self.big_badge, self.halo
        small = lean_badge(14).scale(1.45)
        l_txt = bold("235 with Lean", 30, TEAL_)
        g_sq = Square(0.3, stroke_width=0, fill_color=GREY_, fill_opacity=0.9)
        g_txt = bold("137 not yet formalized", 30, GREY_)
        legend = VGroup(VGroup(small, l_txt).arrange(RIGHT, buff=0.22),
                        VGroup(g_sq, g_txt).arrange(RIGHT, buff=0.22)).arrange(RIGHT, buff=0.9)
        legend.move_to([0, 2.68, 0])

        self.wait_until("L3_end-0.15")
        self.freeze(halo)
        early = lambda t: smooth(min(1.0, t / 0.45))
        late = lambda t: smooth(max(0.0, (t - 0.35) / 0.65))
        self.play_until("rest+0.6",
                        Transform(big, small, rate_func=smooth),
                        FadeOut(halo, rate_func=early),
                        FadeOut(self.badge_caps, shift=DOWN * 0.2, rate_func=early),
                        FadeIn(self.sqs, scale=0.94, rate_func=late),
                        FadeIn(l_txt, shift=LEFT * 0.2, rate_func=lambda t: smooth(max(0.0, (t - 0.7) / 0.3))),
                        min_time=0.5)
        self.remove(halo)
        self.play_until(self.frac("rest", "L4_end", 0.25),
                        self.lean_sqs.animate.set_fill(opacity=0.28),
                        self.rest_sqs.animate.set_fill(GREY_, 0.85),
                        FadeIn(VGroup(g_sq, g_txt), shift=LEFT * 0.2), min_time=0.4)

        # shimmer across the not-yet-formalized squares
        rs = self.rest_sqs
        rs.t = 0.0
        xs = [s.get_center()[0] for s in rs]

        def shimmer(m, dt):
            m.t += dt
            for s, x in zip(m, xs):
                s.set_fill(opacity=0.62 + 0.3 * np.sin(2.4 * m.t - 0.55 * x))
        self.shimmer_drv = self.drive(lambda dt: shimmer(rs, dt))

        # README warning
        src = mono("README.md", 22, GREY_)
        quote = txt("“Some of the unformalized results could have issues.”", 30, WHITE_,
                    slant=ITALIC, t2c={"could have issues.”": ORANGE_})
        qg = VGroup(src, quote).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        card = RoundedRectangle(width=qg.width + 0.8, height=qg.height + 0.4, corner_radius=0.14,
                                stroke_color=ORANGE_, stroke_width=1.6, stroke_opacity=0.7,
                                fill_color=CARD, fill_opacity=0.96)
        card.move_to([0, -3.05, 0])
        qg.move_to(card)
        bar = Line(card.get_corner(UL) + RIGHT * 0.22 + DOWN * 0.18,
                   card.get_corner(DL) + RIGHT * 0.22 + UP * 0.18, color=ORANGE_, stroke_width=3)
        qg.shift(RIGHT * 0.12)
        self.play_at(self.frac("rest", "L4_end", 0.53), FadeIn(card, shift=UP * 0.2),
                     FadeIn(src, shift=UP * 0.2), Create(bar), run_time=0.6)
        self.play_between(self.frac("rest", "L4_end", 0.68), self.frac("rest", "L4_end", 0.96),
                          Write(quote), rate_func=linear)
        self.rest_grp = VGroup(self.sqs, big, l_txt, g_sq, g_txt, card, src, quote, bar)

    # ------------------------------------------------------------ 7. claims
    def claims(self):
        small = txt("everything you're about to hear is", 32, GREY_).move_to([0, 0.95, 0])
        big = serif("what the papers claim", 76).move_to([0, -0.15, 0])
        word = big[-5:]
        ul = underline(word, color=YELLOW_, buff=0.16, width=4)
        self.wait_until("L4_end")
        self.play_until("claims+0.3", FadeOut(self.rest_grp, scale=0.97), min_time=0.4)
        self.remove(self.shimmer_drv)
        self.play(FadeIn(small, shift=UP * 0.15), run_time=0.5)
        self.play_between(self.frac("claims", "L5_end", 0.42), self.frac("claims", "L5_end", 0.8),
                          Write(big), rate_func=smooth)
        self.play_until(self.frac("claims", "L5_end", 1.0) + 0.15,
                        word.animate.set_color(YELLOW_), Create(ul), min_time=0.4)
        self.claim_grp = VGroup(small, big, ul)

    # ------------------------------------------------------------ 8. plan
    def plan(self):
        rows = VGroup()
        for i, (k, title, _, c) in enumerate(CHAPTERS):
            mk = RoundedRectangle(width=0.46, height=0.46, corner_radius=0.1, stroke_color=c,
                                  stroke_width=2, fill_color=c, fill_opacity=0.18)
            nm = bold(str(i + 1), 22, c).move_to(mk)
            if k == "oa":
                title = "Operator Algebras, Topology\n& Functional Analysis"
            tt = txt(title, 24, WHITE_, line_spacing=0.8)
            tt.next_to(mk, RIGHT, buff=0.24)
            rows.add(VGroup(mk, nm, tt))
        y = 2.45
        for r in rows:
            h = max(0.46, r[2].height)
            r.move_to([0, y - h / 2, 0]).align_to([-6.3, 0, 0], LEFT)
            y -= h + 0.13
        rows_c = (2.45 + y + 0.13) / 2
        rows.shift(DOWN * (rows_c - (-0.2)))

        hdr2 = serif("The plan", 30).to_corner(UL, buff=0.42)
        hdr2.align_to(self.header, LEFT).align_to(self.header, UP)

        self.play_until("plan+0.3", FadeOut(self.claim_grp, shift=UP * 0.4),
                        Transform(self.header, hdr2), min_time=0.35)
        self.play_until("big+0.3",
                        LaggedStart(*[FadeIn(r, shift=RIGHT * 0.3) for r in rows], lag_ratio=0.2),
                        min_time=0.6)

        # brace + two formats
        brace = Brace(rows, RIGHT, buff=0.22, color=GREY_)
        tipp = brace.get_tip()
        fx0, fw, fh = 0.6, 6.05, 2.25
        sp_frame = RoundedRectangle(width=fw, height=fh, corner_radius=0.16, stroke_color=YELLOW_,
                                    stroke_width=2, stroke_opacity=0.8, fill_color=CARD, fill_opacity=0.9)
        sp_frame.move_to([fx0 + fw / 2, 1.2, 0])
        rf_frame = sp_frame.copy().set_stroke(WHITE_, opacity=0.55)
        rf_frame.move_to([fx0 + fw / 2, -1.6, 0])
        ar1 = Arrow(tipp, sp_frame.get_left(), buff=0.12, stroke_width=3, color=GREY_,
                    max_tip_length_to_length_ratio=0.15)
        ar2 = Arrow(tipp, rf_frame.get_left(), buff=0.12, stroke_width=3, color=GREY_,
                    max_tip_length_to_length_ratio=0.15)

        img = ImageMobject(thumb_path("003", True))
        img.height = 1.75
        img.move_to(sp_frame.get_left() + RIGHT * (0.35 + img.width / 2))
        img_b = Rectangle(width=img.width, height=img.height, stroke_color=GREY_, stroke_width=1.2,
                          stroke_opacity=0.6).move_to(img)
        lights = glow(img_b, YELLOW_, layers=7, width=26, opacity=0.07)
        lights.t = 0.0

        def breathe(m, dt):
            m.t += dt
            m.set_stroke(opacity=0.05 + 0.035 * np.sin(2.0 * m.t))
        sp_t1 = caps("Spotlight", 24, YELLOW_, spacing=0.06)
        sp_t2 = txt("biggest problems,\nproperly explained", 24, GREY_, line_spacing=0.8)
        sp_txt = VGroup(sp_t1, sp_t2).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        sp_txt.next_to(img, RIGHT, buff=0.5)

        tiles = VGroup()
        tw, th, gap = 0.38, 0.29, 0.06
        for i in range(12):
            r_, c_ = divmod(i, 4)
            col = CHAPTERS[i % 9][3]
            tl = RoundedRectangle(width=tw, height=th, corner_radius=0.05, stroke_color=col,
                                  stroke_width=1.5, stroke_opacity=0.5, fill_color=CARD, fill_opacity=1)
            tl.move_to([c_ * (tw + gap), -r_ * (th + gap), 0])
            tl.col = col
            tiles.add(tl)
        tiles.move_to(rf_frame.get_left() + RIGHT * (0.4 + tiles.width / 2))
        rf_t1 = caps("Rapid fire", 24, WHITE_, spacing=0.06)
        rf_t2 = txt("everything else", 24, GREY_)
        rf_txt = VGroup(rf_t1, rf_t2).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        rf_txt.next_to(tiles, RIGHT, buff=0.5)
        tx = max(img.get_right()[0], tiles.get_right()[0]) + 0.42
        sp_txt.shift(RIGHT * (tx - sp_txt.get_left()[0]))
        rf_txt.shift(RIGHT * (tx - rf_txt.get_left()[0]))

        B = lambda f: self.frac("big", "rapid", f)
        R = lambda f: self.frac("rapid", "L6_end", f)
        self.play_until(B(0.42), GrowFromCenter(brace), GrowArrow(ar1), Create(sp_frame), min_time=0.4)
        self.play_until(B(0.68), FadeIn(lights, rate_func=lambda t: smooth(max(0.0, (t - 0.6) / 0.4))),
                        FadeIn(img, shift=UP * 0.2), FadeIn(img_b, shift=UP * 0.2),
                        FadeIn(sp_t1, shift=LEFT * 0.2), min_time=0.4)
        lights.add_updater(breathe)
        self.play_until(B(0.88), FadeIn(sp_t2, shift=LEFT * 0.2), min_time=0.3)

        self.wait_until("rapid")
        self.play_until(R(0.25), GrowArrow(ar2), Create(rf_frame), min_time=0.4)
        self.play_until(R(0.55), LaggedStart(*[FadeIn(tl, scale=0.6) for tl in tiles], lag_ratio=0.08),
                        FadeIn(rf_t1, shift=LEFT * 0.2), min_time=0.4)
        tiles.t = 0.0
        order = [0, 5, 10, 3, 6, 9, 1, 11, 4, 2, 7, 8]

        def flick(m, dt):
            m.t += dt
            cur = order[int(m.t / 0.16) % 12]
            for i, tl in enumerate(m):
                if i == cur:
                    tl.set_stroke(tl.col, width=3, opacity=1.0).set_fill(tl.col, 0.45)
                else:
                    tl.set_stroke(tl.col, width=1.5, opacity=0.5).set_fill(CARD, 1)
        self.drive(lambda dt: flick(tiles, dt))
        self.play_until(R(0.78), FadeIn(rf_t2, shift=LEFT * 0.2), min_time=0.3)
