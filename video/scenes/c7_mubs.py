import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

ACCENT = YELLOW_
A_COL = BLUE_      # basis A ("position")
B_COL = PINK_      # basis B ("momentum")


def unit(a):
    return np.array([np.cos(a), np.sin(a), 0.0])


def dial(r, angle, color, sw=2.8):
    """A measurement basis as a glyph: a tiny copy of the cartoon -- a faint grey
    unit circle with two perpendicular basis arrows reaching its rim (arrows to
    the rim, equal length, no filled face: reads as 'unit vectors', not a clock)."""
    c = Circle(radius=r, stroke_color=GREY_, stroke_width=1.5, stroke_opacity=0.6)
    h1 = Arrow(ORIGIN, RIGHT * r, buff=0, color=color, stroke_width=sw,
               max_tip_length_to_length_ratio=0.4, max_stroke_width_to_length_ratio=100)
    h1.rotate(angle, about_point=ORIGIN)
    h2 = h1.copy().rotate(PI / 2, about_point=ORIGIN)
    return VGroup(c, h1, h2)


def ghost_dial(r, color=GREY_):
    c = DashedVMobject(Circle(radius=r, stroke_color=color, stroke_width=2.2),
                       num_dashes=10, dashed_ratio=0.55)
    return VGroup(c)


class C7Mubs(VoiceScene):
    def construct(self):
        self.part_cartoon()
        self.part_chart()
        self.part_claim()
        self.finish()

    # ------------------------------------------------------------------ L0
    def part_cartoon(self):
        O = np.array([-3.3, -0.25, 0.0])
        R = 2.05

        def vec(a, color):
            return Arrow(O, O + R * unit(a), buff=0, color=color, stroke_width=6,
                         max_tip_length_to_length_ratio=0.12,
                         max_stroke_width_to_length_ratio=10)

        circle = Circle(radius=R, stroke_color=GREY_, stroke_width=2,
                        stroke_opacity=0.55).move_to(O)
        a1, a2 = vec(0, A_COL), vec(PI / 2, A_COL)
        la1 = tex("a_1", 36, A_COL).move_to(O + (R + 0.36) * RIGHT)
        la2 = tex("a_2", 36, A_COL).move_to(O + (R + 0.36) * UP)

        theta = ValueTracker(0.0)   # angle of basis B relative to A
        bop = ValueTracker(0.0)     # opacity of basis B
        pop = ValueTracker(0.0)     # opacity of the projections
        bsc = ValueTracker(0.0)     # growth of the probability bars

        def make_B():
            t, o = theta.get_value(), bop.get_value()
            b1, b2 = vec(t, B_COL), vec(t + PI / 2, B_COL)
            lb1 = tex("b_1", 36, B_COL).move_to(O + (R + 0.4) * unit(t))
            lb2 = tex("b_2", 36, B_COL).move_to(O + (R + 0.4) * unit(t + PI / 2))
            g = VGroup(b1, b2, lb1, lb2)
            g.set_stroke(opacity=o).set_fill(opacity=o)
            return g

        def make_proj():
            # shadows of b1 on the two A-directions (drawn under the A arrows)
            t, o = theta.get_value(), pop.get_value()
            tip = O + R * unit(t)
            fx = O + R * np.cos(t) * RIGHT
            fy = O + R * np.sin(t) * UP
            s1 = Line(O, fx, stroke_color=ACCENT, stroke_width=6.5, stroke_opacity=o)
            s2 = Line(O, fy, stroke_color=ACCENT, stroke_width=6.5, stroke_opacity=o)
            # fixed dash count: the redraw keeps the same sub-mobject structure (no ghosts)
            d1 = DashedVMobject(Line(tip, fx, stroke_width=2.5, color=GREY_), num_dashes=9)
            d2 = DashedVMobject(Line(tip, fy, stroke_width=2.5, color=GREY_), num_dashes=9)
            d1.set_stroke(opacity=o)
            d2.set_stroke(opacity=o)
            return VGroup(s1, s2, d1, d2)

        # probability panel ------------------------------------------------
        base_y, H, bw = -1.2, 2.75, 1.0
        bx = [2.15, 4.25]

        def make_bars():
            t, s = theta.get_value(), bsc.get_value()
            ps = [np.cos(t) ** 2, np.sin(t) ** 2]
            g = VGroup()
            for x, p in zip(bx, ps):
                h = max(H * p * s, 1e-3)
                r = Rectangle(width=bw, height=h, stroke_width=0, fill_color=ACCENT,
                              fill_opacity=0.8)
                r.move_to([x, base_y + h / 2, 0])
                pct = txt(f"{round(100 * p)}%", 30, WHITE_)
                pct.next_to(r, UP, buff=0.14).set_opacity(s)
                g.add(r, pct)
            return g

        baseline = Line([bx[0] - 0.85, base_y, 0], [bx[1] + 0.85, base_y, 0],
                        stroke_color=GREY_, stroke_width=2)
        plabs = VGroup(tex("a_1", 36, A_COL).move_to([bx[0], base_y - 0.38, 0]),
                       tex("a_2", 36, A_COL).move_to([bx[1], base_y - 0.38, 0]))
        cap = VGroup(txt("measure", 26, GREY_), tex("b_1", 36, B_COL),
                     txt("in basis A", 26, GREY_)).arrange(RIGHT, buff=0.14)
        cap[1].shift(DOWN * 0.03)
        cap.move_to([sum(bx) / 2, 2.2, 0])

        formula = tex(r"|\langle a_i , b_j \rangle|^2 = \tfrac{1}{2}", 46)
        formula.move_to([sum(bx) / 2, -2.3, 0])
        formula[0][-3:].set_color(ACCENT)
        fcap = txt("every outcome equally likely", 24, GREY_).next_to(formula, DOWN, buff=0.22)

        head = serif("Mutually unbiased", 54).move_to([0, 3.15, 0])

        def leg(color, s):
            sw = Line(LEFT * 0.22, RIGHT * 0.22, stroke_color=color, stroke_width=6)
            t = txt(s, 28, color)
            return VGroup(sw, t).arrange(RIGHT, buff=0.16)

        legA, legB = leg(A_COL, "basis A"), leg(B_COL, "basis B")
        VGroup(legA, legB).arrange(RIGHT, buff=0.7).move_to([O[0], -2.95, 0])
        posA = txt("position", 28, A_COL).move_to(legA[1], aligned_edge=LEFT)
        momB = txt("momentum", 28, B_COL).move_to(legB[1], aligned_edge=LEFT)

        # ---------------------------------------------------- animation
        # "In quantum mechanics": one way of measuring = a pair of perpendicular directions
        self.play_until("measure+1.0",
                        Create(circle),
                        LaggedStart(GrowArrow(a1), GrowArrow(a2), lag_ratio=0.35),
                        LaggedStart(FadeIn(la1), FadeIn(la2), FadeIn(legA), lag_ratio=0.3))

        # "two ways of measuring": a second basis turns out of the first
        B = always_redraw(make_B)
        self.add(B)
        self.play_between("measure+1.45", "measure+2.6",
                          theta.animate.set_value(20 * DEGREES),
                          bop.animate.set_value(1.0), FadeIn(legB),
                          rate_func=smooth)
        # "are mutually unbiased"
        self.play_between("measure+2.6", "measure+3.8", Write(head))

        # "if knowing the result of one ...": shadows of b1 on A = outcome odds
        proj = always_redraw(make_proj)
        bars = always_redraw(make_bars)
        # shadows sit ON the A axes (yellow = probability, same as the bars), under B
        self.add(proj, bars)
        self.bring_to_front(B)
        self.play_between("measure+4.15", "measure+5.35",
                          pop.animate.set_value(1.0), bsc.animate.set_value(1.0),
                          Create(baseline), FadeIn(plabs), FadeIn(cap, shift=DOWN * 0.1))
        # "... tells you nothing about the other": turn B until A's odds are 50/50
        self.play_between("L0_end-2.95", "L0_end-2.05",
                          theta.animate.set_value(45 * DEGREES), rate_func=smooth)
        self.play_between("L0_end-2.05", "L0_end-1.45",
                          Write(formula), FadeIn(fcap, shift=UP * 0.1))
        # "like position and momentum"
        self.play_between("L0_end-1.45", "L0_end-0.95",
                          ReplacementTransform(legA[1], posA))
        self.play_between("L0_end-0.8", "L0_end-0.25",
                          ReplacementTransform(legB[1], momB))

        for m in (B, proj, bars):
            m.clear_updaters()
        self.cart = dict(circle=circle, a1=a1, a2=a2, la1=la1, la2=la2, B=B, proj=proj,
                         rest=VGroup(bars, baseline, plabs, cap, formula, fcap, head,
                                     legA[0], legB[0], posA, momB))

    # ------------------------------------------------------------------ L1
    def part_chart(self):
        ds = [2, 3, 4, 5, 6, 7, 8, 9]
        xs = {d: -5.25 + 1.5 * i for i, d in enumerate(ds)}
        y0, pitch, r = -2.05, 0.40, 0.175

        def row_col(k):
            return interpolate_color(ManimColor(BLUE_), ManimColor(PINK_), min(k, 9) / 9)

        cols = {}
        for d in ds:
            if d == 6:
                continue
            cols[d] = VGroup(*[dial(r, k * PI / 2 / (d + 1), row_col(k))
                               .move_to([xs[d], y0 + k * pitch, 0]) for k in range(d + 1)])
        counts = {d: tex(str(d + 1), 32, GREEN_).next_to(cols[d], UP, buff=0.14)
                  for d in cols}

        dlabs = {d: tex(str(d), 38, WHITE_).move_to([xs[d], -2.66, 0]) for d in ds}
        dname = tex("d", 38, GREY_).move_to([-6.35, -2.66, 0])
        facts = {4: "2^2", 8: "2^3", 9: "3^2"}
        flabs = {d: tex(s, 30, GREY_).move_to([xs[d], -3.15, 0]) for d, s in facts.items()}

        h1 = VGroup(tex("N(d)", 40), txt("= max number of mutually unbiased bases in", 27, GREY_),
                    tex(r"\mathbb{C}^d", 40, GREY_)).arrange(RIGHT, buff=0.17)
        h1[1].shift(DOWN * 0.02)
        h1.move_to([0, 3.25, 0])
        h2 = tex(r"d = p^k \;\Longrightarrow\; N(d) = d + 1", 40, GREEN_).move_to([0, 2.55, 0])

        # ---- the cartoon's two bases become the first two dials of d = 2
        c = self.cart
        self.play_between("L0_end", "prime+0.2",
                          FadeOut(c["rest"]), FadeOut(c["proj"]),
                          FadeOut(VGroup(c["la1"], c["la2"], c["B"][2], c["B"][3])))
        circ2 = c["circle"].copy()
        self.play_between(
            "prime+0.2", "prime+1.2",
            ReplacementTransform(VGroup(c["circle"], c["a1"], c["a2"]), cols[2][0]),
            ReplacementTransform(VGroup(circ2, c["B"][0], c["B"][1]), cols[2][1]),
            FadeIn(h1, shift=DOWN * 0.15),
            LaggedStart(FadeIn(dname), *[FadeIn(dlabs[d], shift=UP * 0.15) for d in ds],
                        lag_ratio=0.08))
        # "... that's a prime power"
        pp = [d for d in ds if d != 6]
        self.play_between("prime+1.2", "prime+1.85",
                          *[dlabs[d].animate.set_color(GREEN_) for d in pp],
                          dlabs[6].animate.set_color(DIM),
                          LaggedStart(*[FadeIn(flabs[d], shift=UP * 0.1) for d in (4, 8, 9)],
                                      lag_ratio=0.25))

        def grow_col(d):
            dials = [m for j, m in enumerate(cols[d]) if not (d == 2 and j < 2)]
            return AnimationGroup(LaggedStart(*[GrowFromCenter(m) for m in dials], lag_ratio=0.3),
                                  FadeIn(counts[d], shift=DOWN * 0.1),
                                  Indicate(dlabs[d], color=GREEN_, scale_factor=1.15))

        # "like two, three, four or five": each column fills as its number is spoken
        for d, (t0, t1) in zip((2, 3, 4, 5), (("prime+2.2", "prime+2.7"),
                                              ("prime+2.72", "prime+3.2"),
                                              ("prime+3.22", "prime+3.6"),
                                              ("prime+3.62", "prime+4.15"))):
            self.play_between(t0, t1, grow_col(d))
        # "you can fit d plus one such measurements"
        self.play_between("six-1.85", "six-0.45",
                          LaggedStart(*[grow_col(d) for d in (7, 8, 9)], lag_ratio=0.3),
                          Succession(Wait(0.3), Write(h2)))

        # ---- "Six is the first dimension that isn't"
        x6 = xs[6]
        band = RoundedRectangle(width=1.8, height=4.7, corner_radius=0.15,
                                stroke_color=ACCENT, stroke_width=2.4, stroke_opacity=0.9,
                                fill_color=ACCENT, fill_opacity=0.08)
        band.move_to([x6, -1.07, 0])
        f6 = tex(r"2\cdot 3", 30, ACCENT).move_to([x6, -3.15, 0])
        others = VGroup(*cols.values(), *counts.values(), *[dlabs[d] for d in pp],
                        *flabs.values(), h2)
        self.play_between("six+0.65", "six+1.5",
                          FadeIn(band), others.animate.fade(0.62),
                          dlabs[6].animate.set_color(ACCENT).scale(1.15))
        self.play_between("six+2.1", "six+2.7", FadeIn(f6, shift=UP * 0.12))

        # "and for thirty-five years"
        since = txt("open since 1991 (Zauner)", 26, GREY_).move_to([x6, 2.5, 0])
        self.play_between("six+3.1", "six+3.9", FadeOut(h2, shift=UP * 0.15),
                          FadeIn(since, shift=DOWN * 0.12))

        # "the maximum could have been anything from three to seven"
        solid = VGroup(*[dial(r, k * PI / 6, ACCENT).move_to([x6, y0 + k * pitch, 0])
                         for k in range(3)])
        ghosts = VGroup(*[ghost_dial(r).move_to([x6, y0 + k * pitch, 0]) for k in range(3, 7)])
        brace = Brace(ghosts, RIGHT, buff=0.08, color=GREY_, sharpness=1.2)
        qm = tex("?", 44, ACCENT).next_to(brace, RIGHT, buff=0.1)
        rng = MathTex("3", r"\le", "N(6)", r"\le", "7", font_size=40, color=WHITE_)
        rng.move_to([x6, band.get_top()[1] + 0.42, 0])
        rng[0].set_color(ACCENT)
        self.play_between("L1_end-2.6", "L1_end-1.95", Write(rng[2]))
        # "... from three" (the known construction) "... to seven" (the d+1 bound)
        self.play_between("L1_end-1.25", "L1_end-0.7",
                          LaggedStart(*[GrowFromCenter(m) for m in solid], lag_ratio=0.35),
                          FadeIn(rng[0:2], shift=RIGHT * 0.15))
        self.play_between("L1_end-0.66", "L1_end+0.1",
                          LaggedStart(*[Create(g) for g in ghosts], lag_ratio=0.3),
                          FadeIn(rng[3:5], shift=LEFT * 0.15),
                          Succession(Wait(0.3), AnimationGroup(GrowFromCenter(brace),
                                                               FadeIn(qm, scale=0.6))))

        self.chart = dict(cols=cols, counts=counts, dlabs=dlabs, dname=dname, flabs=flabs,
                          h1=h1, h2=h2, band=band, f6=f6, since=since)
        self.six = dict(solid=solid, ghosts=ghosts, brace=brace, qm=qm, rng=rng)

    # ------------------------------------------------------------------ L2
    def part_claim(self):
        ch, s = self.chart, self.six
        stack = VGroup(s["solid"], s["ghosts"], s["brace"], s["qm"])
        S1 = 1.35
        tgt = stack.copy().scale(S1)
        tgt.shift(np.array([-4.3, -0.95, 0]) - tgt[0][0].get_center())
        rtgt = s["rng"].copy().scale(1.25).shift(DOWN * 0.05)

        fade_out = VGroup(*ch["cols"].values(), *ch["counts"].values(), *ch["dlabs"].values(),
                          ch["dname"], *ch["flabs"].values(), ch["h1"], ch["band"],
                          ch["f6"], ch["since"])

        card = paper_card("266", width=2.8)
        card.move_to([4.75, 0.85, 0])
        tag = paper_tag("266", color=ACCENT)

        # "The paper claims"
        self.play_between("claim", "claim+0.9",
                          FadeOut(fade_out),
                          Transform(stack, tgt), Transform(s["rng"], rtgt),
                          FadeIn(card, shift=LEFT * 2.5),
                          FadeIn(tag, shift=RIGHT * 0.3))
        self.remove(stack)
        self.add(*stack)

        # "exactly three": slots 5..7 vanish, slot 4 is crossed out, range -> N(6) = 3
        ghosts = s["ghosts"]
        g4 = ghosts[0]
        rr = g4.width / 2
        cross = VGroup(Line(UL * rr * 0.62, DR * rr * 0.62), Line(DL * rr * 0.62, UR * rr * 0.62))
        cross.set_stroke(RED_, width=4).move_to(g4)
        rng = s["rng"]
        n63 = MathTex("N(6)", "=", "3", font_size=40 * 1.25, color=ACCENT).move_to(rng)
        # the upper bound 7 collapses onto the known lower bound 3
        self.play_between("claim+1.1", "claim+1.7",
                          *[FadeOut(g, scale=0.4) for g in ghosts[1:]],
                          FadeOut(s["brace"]), FadeOut(s["qm"]),
                          g4.animate.set_stroke(RED_),
                          Create(cross),
                          FadeOut(rng[0:2], shift=LEFT * 0.3),
                          ReplacementTransform(rng[2], n63[0]),
                          ReplacementTransform(rng[3], n63[1]),
                          ReplacementTransform(rng[4], n63[2]))

        # banner: the claim, with N(6) = 3 flowing into it; stack settles with labels
        ban = result_banner(r"N(6) = 3\text{:}\ \ \text{no four mutually unbiased bases in }\mathbb{C}^6",
                            color=ACCENT, lean=CATALOG["266"]["lean"], is_tex=True, size=36)
        ban.move_to([0.35, -2.13, 0])
        box, header, body = ban[0], ban[1][0], ban[1][1]
        glyphs = body[0]
        head_part, rest_part = glyphs[:6], glyphs[6:]

        final = VGroup(s["solid"], g4, cross)
        S2 = 1.8
        ftgt = final.copy().scale(S2 / S1)
        ftgt.shift(np.array([-4.0, 0.85, 0]) - VGroup(ftgt[0], ftgt[1]).get_center())
        kbr = Brace(ftgt[0], LEFT, buff=0.12, color=GREY_, sharpness=1.2)
        known = VGroup(kbr, txt("known", 26, GREY_).next_to(kbr, LEFT, buff=0.12))
        ruled = txt("ruled out", 26, RED_).next_to(ftgt[1], LEFT, buff=0.32)

        self.add(box)
        self.bring_to_front(*n63)
        box.set_opacity(0)
        n63_glyphs = VGroup(*[g for part in n63 for g in part])
        self.play_between("claim+1.85", "claim+2.6",
                          box.animate.set_fill(CARD, opacity=0.92).set_stroke(ACCENT, opacity=1),
                          Succession(Wait(0.6), FadeIn(header, shift=RIGHT * 0.15, run_time=0.4)),
                          ReplacementTransform(n63_glyphs, head_part),
                          FadeIn(rest_part, shift=LEFT * 0.2),
                          Transform(final, ftgt),
                          Succession(Wait(0.3), AnimationGroup(FadeIn(known, shift=RIGHT * 0.1),
                                                               FadeIn(ruled, shift=RIGHT * 0.1))))

        # "computer-assisted proof"
        comp = chip("COMPUTER-ASSISTED PROOF", ORANGE_, size=22, pad_x=0.2, pad_y=0.11)
        fp = txt("under stated floating-point assumptions", 22, GREY_)
        VGroup(comp, fp).arrange(DOWN, buff=0.2).move_to([-0.45, 0.85, 0])
        self.play_between("L2_end-1.25", "L2_end-0.7",
                          FadeIn(comp, scale=0.85), FadeIn(fp, shift=UP * 0.1))
        self.wait_until("L2_end")
