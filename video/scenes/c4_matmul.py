import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

# Matrix multiplication exponent spotlight (family 107): omega <= 9/4 over C.
ACC = GREEN_
NUM = "107"

# ---------------------------------------------------------------- the two matrices
A_VALS = [[2, 7, 1, 3], [4, 0, 6, 5], [8, 3, 2, 1], [1, 5, 9, 2]]
B_VALS = [[5, 2, 0, 3], [1, 6, 4, 2], [4, 1, 3, 7], [2, 8, 5, 1]]
C_VALS = (np.array(A_VALS) @ np.array(B_VALS)).tolist()     # c00 = 2*5+7*1+1*4+3*2 = 27
CELL = 0.6
MAT_Y = 1.05
ROW_Y = -1.35                  # counter / icon row
FORM_Y = -2.95                 # cost-formula row

# ---------------------------------------------------------------- omega number line
LY = 0.9                       # height of the main line
LX0, LX1 = -5.8, 5.8           # x of omega = 2 and omega = 3


def X(w):
    return LX0 + (w - 2.0) * (LX1 - LX0)


# zoom inset: omega in [2.370, 2.377]
IW0, IW1 = 2.3700, 2.3770
IX0, IX1 = -5.6, 1.1
IY = -1.55
BOX_C, BOX_W, BOX_H = np.array([-2.25, -1.45, 0]), 7.7, 2.0


def XI(w):
    return IX0 + (w - IW0) / (IW1 - IW0) * (IX1 - IX0)


STRASSEN = float(np.log2(7))                       # 2.80735...
# (exact value -> position, label as narrated, era)
RECORDS = [(2.375477, "2.376", "1990"),            # Coppersmith-Winograd
           (2.3728596, "2.373", "2010s"),          # Stothers / Vassilevska Williams / Le Gall
           (2.371177, "2.371", "2020s")]           # ... Dupont et al. 2026 (previous record)
NINE4 = 2.25
VAL = 36                       # value-label size on the main line
NAME = 24                      # name-label size


def v3(x, y):
    return np.array([x, y, 0.0])


def matrix(vals, size=26, color=WHITE_):
    nums = VGroup()
    for i in range(4):
        for j in range(4):
            t = txt(str(vals[i][j]), size, color)
            t.move_to(v3((j - 1.5) * CELL, (1.5 - i) * CELL))
            nums.add(t)
    h, w = 4 * CELL + 0.12, 4 * CELL + 0.22

    def bracket(s):
        x = s * w / 2
        return VMobject(stroke_color=GREY_, stroke_width=2.5).set_points_as_corners(
            [v3(x - s * 0.13, h / 2), v3(x, h / 2), v3(x, -h / 2), v3(x - s * 0.13, -h / 2)])
    return VGroup(nums, VGroup(bracket(-1), bracket(1)))


def mini(lit, s=0.24):
    g = VGroup()
    for r in range(2):
        for c in range(2):
            sq = Square(s, stroke_color=GREY_, stroke_width=1.6)
            sq.move_to(v3((c - 0.5) * s, (0.5 - r) * s))
            sq.set_fill(ACC if (r, c) in lit else CARD, opacity=0.9 if (r, c) in lit else 1.0)
            g.add(sq)
    return g


def icon(la, lb):
    return VGroup(mini(la), tex(r"\times", 28, GREY_), mini(lb)).arrange(RIGHT, buff=0.08)


# schoolbook: C_ik = A_i1 B_1k + A_i2 B_2k  (8 block products)
SCHOOL = [({(i, j)}, {(j, k)}) for i in range(2) for k in range(2) for j in range(2)]
# Strassen's seven products M1..M7 (which blocks enter each factor)
STRAS = [({(0, 0), (1, 1)}, {(0, 0), (1, 1)}),
         ({(1, 0), (1, 1)}, {(0, 0)}),
         ({(0, 0)}, {(0, 1), (1, 1)}),
         ({(1, 1)}, {(1, 0), (0, 0)}),
         ({(0, 0), (0, 1)}, {(1, 1)}),
         ({(1, 0), (0, 0)}, {(0, 0), (0, 1)}),
         ({(0, 1), (1, 1)}, {(1, 0), (1, 1)})]


def pointer(color, w=0.26):
    t = Triangle(fill_color=color, fill_opacity=1, stroke_width=0).rotate(PI)
    t.scale_to_fit_width(w)
    return t


def put_on(t, x, y):
    """Place a down-pointing triangle so its tip sits just above (x, y)."""
    t.move_to(v3(x, y + 0.03 + t.height / 2))
    return t


def note(label, color, size=24):
    """Quiet caveat pill (mixed case, thin outline)."""
    t = txt(label, size, color, weight=MEDIUM)
    box = RoundedRectangle(width=t.width + 0.4, height=t.height + 0.26, corner_radius=0.12,
                           stroke_color=color, stroke_width=1.6, stroke_opacity=0.85,
                           fill_color=color, fill_opacity=0.08)
    t.move_to(box)
    return VGroup(box, t)


class C4Matmul(VoiceScene):

    def T(self, a, b, f):
        """Time at fraction f between cues a and b."""
        ta, tb = self.cue(a), self.cue(b)
        return ta + f * (tb - ta)

    def tw(self, phrase, a, a_words, b, b_words, fallback, lag=0.0):
        """Estimated time of `phrase` in the segment that starts at cue a (text
        a_words...) and ends at cue b (text b_words...), char-proportional."""
        ta, tb = self.cue(a), self.cue(b)
        for ln in self.timing.get("lines", []):
            text = ln["text"]
            if a_words in text:
                i0 = text.index(a_words)
                ip = text.find(phrase, i0)
                i1 = text.find(b_words, i0) if b_words else len(text)
                if ip >= 0 and i1 > i0:
                    return min(tb - 0.3, ta + (ip - i0) / (i1 - i0) * (tb - ta) + lag)
        return ta + fallback * (tb - ta)

    def go(self, t0, t1, *anims, **kw):
        """Play anims from t0 (or now, if later) to t1 (at least 0.25 s)."""
        self.wait_until(max(self.now, self.cue(t0)))
        rt = max(0.25, self.cue(t1) - self.now)
        self.play(*anims, run_time=rt, **kw)

    def construct(self):
        M = lambda f: self.T("mat", "strassen", f)        # noqa: E731
        S = lambda f: self.T("strassen", "L0_end", f)     # noqa: E731

        # ============================================================ 1. schoolbook
        A = matrix(A_VALS)
        B = matrix(B_VALS)
        Cm = matrix(C_VALS, size=22, color=WHITE_)
        for t in Cm[0]:
            t.set_fill(opacity=0)
        Cdots = VGroup(*[Dot(t.get_center(), radius=0.035, color=DIM) for t in Cm[0]])
        Cgrp = VGroup(Cm, Cdots)
        times = tex(r"\times", 44, GREY_)
        eq = tex("=", 44, GREY_)
        VGroup(A, times, B, eq, Cgrp).arrange(RIGHT, buff=0.42).move_to(v3(0, MAT_Y))
        nlab = tex(r"n \times n", 32, GREY_).next_to(A, DOWN, buff=0.22)
        nlabB = tex(r"n \times n", 32, GREY_).next_to(B, DOWN, buff=0.22)

        ac, bc = A[0].get_center(), B[0].get_center()
        rowy = [A[0][4 * i].get_y() for i in range(4)]
        colx = [B[0][k].get_x() for k in range(4)]
        cpos = [t.get_center() for t in Cm[0]]
        hl = dict(stroke_color=ACC, stroke_width=2.5, fill_color=ACC, fill_opacity=0.16)
        rowrect = RoundedRectangle(width=4 * CELL + 0.06, height=CELL * 0.86, corner_radius=0.13, **hl)
        colrect = RoundedRectangle(width=CELL * 0.86, height=4 * CELL + 0.06, corner_radius=0.13, **hl)
        crect = RoundedRectangle(width=CELL * 0.92, height=CELL * 0.86, corner_radius=0.12, **hl)
        rowrect.move_to(v3(ac[0], rowy[0]))
        colrect.move_to(v3(colx[0], bc[1]))
        crect.move_to(cpos[0])

        self.play_until(M(0.15),
                        LaggedStart(FadeIn(A, shift=RIGHT * 0.2), FadeIn(times), FadeIn(B, shift=RIGHT * 0.2),
                                    FadeIn(eq), FadeIn(Cgrp, shift=RIGHT * 0.2), lag_ratio=0.18),
                        FadeIn(nlab, shift=UP * 0.1), FadeIn(nlabB, shift=UP * 0.1))

        # one row meets one column -> one entry
        parts = []
        for j in range(4):
            parts += [str(A_VALS[0][j]), r"\cdot", str(B_VALS[j][0])]
            parts += ["+"] if j < 3 else []
        parts += ["=", str(C_VALS[0][0])]
        expr = MathTex(*parts, font_size=44, color=WHITE_).move_to(v3(0, ROW_Y))
        expr[-1].set_color(ACC)
        a_ix = [4 * j for j in range(4)]
        b_ix = [4 * j + 2 for j in range(4)]
        ops = [k for k in range(len(parts) - 2) if k not in a_ix + b_ix]
        self.go(M(0.15), M(0.24),
                FadeIn(rowrect, scale=1.05), FadeIn(colrect, scale=1.05), FadeIn(crect, scale=1.05))
        self.go(M(0.24), M(0.43),
                LaggedStart(*[AnimationGroup(TransformFromCopy(A[0][j], expr[a_ix[j]]),
                                             TransformFromCopy(B[0][4 * j], expr[b_ix[j]]))
                              for j in range(4)], lag_ratio=0.25),
                LaggedStart(*[FadeIn(expr[k]) for k in ops], lag_ratio=0.15))
        self.go(M(0.43), M(0.52), FadeIn(expr[-2]), FadeIn(expr[-1], shift=LEFT * 0.1))
        self.remove(*expr)
        self.add(expr)
        c00 = Cm[0][0]
        c00_src = expr[-1].copy()
        self.add(c00_src)

        # counter (Inter digits, one Text per value) replaces the expression
        mult = txt("multiplications", 32, GREY_)
        cnt_eq = tex("=", 48, GREY_)
        n3 = tex("n^3", 56, ACC)
        slot = Rectangle(width=0.62, height=0.3, stroke_width=0)
        row_full = VGroup(slot, mult, cnt_eq, n3).arrange(RIGHT, buff=0.24).move_to(v3(0, ROW_Y))
        n3.align_to(mult[0], DOWN)
        cnt_eq.set_y(mult[0].get_y() + 0.03)
        counts = VGroup()
        for v in range(4, 65, 4):
            c = txt(str(v), 40, WHITE_, weight=SEMIBOLD)
            c.align_to(slot, RIGHT).align_to(mult[0], DOWN)
            c.set_fill(opacity=0)
            counts.add(c)
        counts[0].set_fill(opacity=1)
        left = VGroup(counts, mult)
        left_full = left.get_center()
        left.shift(v3(-VGroup(counts, mult).get_center()[0], 0))     # centred until "= n^3" arrives
        self.go(M(0.52), M(0.58),
                c00_src.animate.scale_to_fit_height(c00.height).move_to(c00), FadeOut(Cdots[0]),
                FadeOut(expr, shift=UP * 0.15), FadeIn(VGroup(counts[0], mult), shift=UP * 0.15))
        c00.set_fill(opacity=1)
        self.remove(c00_src)
        self.add(counts)

        sweep_grp = VGroup(rowrect, colrect, crect, Cm[0], Cdots, counts)

        def sweep(mob, alpha):
            s = alpha * 15
            m = min(int(s), 14)
            f = s - m
            if alpha >= 1:
                m, f = 14, 1.0
            g = smooth(min(1.0, f / 0.55))
            i0, k0 = divmod(m, 4)
            i1, k1 = divmod(m + 1, 4)
            rowrect.move_to(v3(ac[0], interpolate(rowy[i0], rowy[i1], g)))
            colrect.move_to(v3(interpolate(colx[k0], colx[k1], g), bc[1]))
            crect.move_to(interpolate(cpos[m], cpos[m + 1], g))
            shown = m + 1 + (1 if f >= 0.6 else 0)
            for q in range(16):
                Cm[0][q].set_fill(opacity=1.0 if q < shown else 0.0)
                Cdots[q].set_opacity(0.0 if q < shown else 1.0)
                counts[q].set_fill(opacity=1.0 if q == shown - 1 else 0.0)
            return mob

        self.go(M(0.58), M(0.81), UpdateFromAlphaFunc(sweep_grp, sweep, rate_func=linear))
        # "... about n cubed steps"
        cbox = RoundedRectangle(width=Cm[0].width + 0.24, height=Cm[0].height + 0.26, corner_radius=0.14,
                                stroke_color=ACC, stroke_width=2.5, fill_color=ACC,
                                fill_opacity=0.06).move_to(Cm[0])
        self.go(M(0.82), M(0.96),
                left.animate.move_to(left_full), FadeIn(cnt_eq), Write(n3),
                FadeOut(VGroup(rowrect, colrect)), ReplacementTransform(crect, cbox))

        # ============================================================ 2. Strassen
        cap = serif("Strassen, 1969", 48).move_to(v3(0, 3.15))
        blines = VGroup()
        for Mx in (A, B, Cm):
            c = Mx[0].get_center()
            blines.add(DashedLine(c + UP * 2 * CELL, c + DOWN * 2 * CELL, dash_length=0.08,
                                  stroke_color=ACC, stroke_width=2.5),
                       DashedLine(c + LEFT * 2 * CELL, c + RIGHT * 2 * CELL, dash_length=0.08,
                                  stroke_color=ACC, stroke_width=2.5))
        icons8 = VGroup(*[icon(a, b) for a, b in SCHOOL]).arrange(RIGHT, buff=0.3).move_to(v3(0, ROW_Y + 0.05))
        icons7 = VGroup(*[icon(a, b) for a, b in STRAS]).arrange(RIGHT, buff=0.3).move_to(v3(0, ROW_Y + 0.05))
        k8 = txt("8", 36, WHITE_, weight=BOLD)
        k7 = txt("7", 36, ACC, weight=BOLD)
        klab = txt("half-size multiplications", 30, GREY_)
        krow = VGroup(k8, klab).arrange(RIGHT, buff=0.16).move_to(v3(0, ROW_Y - 0.8))
        k8.align_to(klab[0], DOWN)
        k7.move_to(k8)
        # cost row:  n^3  ->  n^{log2 7} ~ n^{2.807}
        n3_t = tex("n^3", 48, WHITE_)
        arrow1 = Arrow(LEFT * 0.6, RIGHT * 0.6, buff=0, stroke_width=3, color=GREY_,
                       max_tip_length_to_length_ratio=0.25)
        sf = tex(r"n^{\log_2 7}\approx n^{2.807}", 48, WHITE_)
        VGroup(n3_t, arrow1, sf).arrange(RIGHT, buff=0.3).move_to(v3(0, FORM_Y))
        sf[0][8:].set_color(ACC)
        self.go(S(0.0), S(0.12),
                FadeOut(VGroup(counts, mult, cnt_eq, cbox, nlab, nlabB), shift=DOWN * 0.1),
                n3.animate.scale(48 / 56).move_to(n3_t),
                Cm[0].animate.set_fill(opacity=0.45))
        self.go(S(0.12), S(0.25), Write(cap), LaggedStart(*[Create(l) for l in blines], lag_ratio=0.1))
        self.go(S(0.25), S(0.37),
                LaggedStart(*[FadeIn(ic, shift=UP * 0.15) for ic in icons8], lag_ratio=0.1),
                FadeIn(krow, shift=UP * 0.1))
        # "... showed you can do better": 8 -> 7
        cross = Cross(icons8[7], stroke_color=RED_, stroke_width=5).scale(0.9)
        self.go(S(0.37), S(0.41), Create(cross))
        self.go(S(0.41), S(0.50),
                *[ReplacementTransform(icons8[q], icons7[q]) for q in range(7)],
                FadeOut(VGroup(icons8[7], cross), shift=DOWN * 0.3, scale=0.6),
                ReplacementTransform(k8, k7))
        self.go(S(0.50), S(0.58), GrowArrow(arrow1), Write(sf), n3[0][0].animate.set_color(WHITE_))

        # ============================================================ 3. the race for omega
        top_y = 3.1
        t_n3 = tex("n^3", 48, WHITE_)
        t_n3[0][1].set_color(ACC)
        t_ar = Arrow(LEFT * 0.6, RIGHT * 0.6, buff=0, stroke_width=3, color=GREY_,
                     max_tip_length_to_length_ratio=0.25)
        t_n2 = tex(r"n^{2.807}", 48, WHITE_)
        t_n2[0][1:].set_color(ACC)
        toprow = VGroup(t_n3, t_ar, t_n2).arrange(RIGHT, buff=0.3).move_to(v3(0, top_y))
        stage = VGroup(A, times, B, eq, Cm, Cdots, blines, icons7, k7, klab)

        # number line from 2 to 3
        line = Line(v3(LX0, LY), v3(LX1, LY), stroke_color=GREY_, stroke_width=2.5)
        ticks = VGroup()
        for k in range(11):
            w = 2 + 0.1 * k
            major = k in (0, 5, 10)
            h = 0.24 if major else 0.12
            ticks.add(Line(v3(X(w), LY - h / 2), v3(X(w), LY + h / 2),
                           stroke_color=GREY_ if major else DIM, stroke_width=2))
        TL_Y = LY - 0.4
        tl2 = tex("2", 34, GREY_).move_to(v3(X(2), TL_Y))
        tl25 = tex("2.5", 34, GREY_).move_to(v3(X(2.5), TL_Y)).align_to(tl2, UP)
        omega_ax = tex(r"\omega", 48, ACC).move_to(v3(LX0 - 0.5, LY + 0.03))

        g3 = put_on(pointer(GREY_), X(3), LY)
        v3l = tex("3", VAL, GREY_).next_to(g3, UP, buff=0.12)
        n3l = txt("schoolbook", NAME, GREY_).next_to(v3l, UP, buff=0.12)
        ptri = put_on(pointer(ACC), X(STRASSEN), LY)
        pval = tex("2.807", VAL, ACC).next_to(ptri, UP, buff=0.12)
        sname = txt("Strassen 1969", NAME, GREY_).next_to(pval, UP, buff=0.12)
        n3l.align_to(sname, DOWN)
        n3l.set_x(min(X(3), 6.62 - n3l.width / 2))
        sname.set_x(min(X(STRASSEN), n3l.get_left()[0] - 0.4 - sname.width / 2))
        self.go(S(0.58), S(0.65),
                FadeOut(stage, shift=UP * 0.3), FadeOut(cap, shift=UP * 0.3),
                ReplacementTransform(n3, t_n3), ReplacementTransform(arrow1, t_ar),
                ReplacementTransform(sf[0][7:], t_n2[0]), FadeOut(sf[0][:7], shift=UP * 0.5))
        self.remove(sf)
        self.go(S(0.65), S(0.725),
                Create(line), LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.06),
                FadeIn(tl2), FadeIn(tl25))
        self.go(S(0.725), S(0.785),
                TransformFromCopy(t_n3[0][1], v3l), FadeIn(g3, shift=DOWN * 0.2), FadeIn(n3l),
                TransformFromCopy(t_n2[0][1:], pval), FadeIn(ptri, shift=DOWN * 0.2), FadeIn(sname))

        # "... pin down omega: the true exponent"
        head = tex(r"\text{cost}\approx n^{\omega}", 52, WHITE_).move_to(v3(0, top_y))
        head[0][-1].set_color(ACC)
        self.go(S(0.785), S(0.85), FadeTransform(toprow, head))
        self.go(S(0.88), S(0.99), TransformFromCopy(head[0][-1], omega_ax),
                Circumscribe(head[0][-1], color=ACC, shape=Circle, buff=0.06, stroke_width=3))

        # ============================================================ 4. decades of records
        mag = Rectangle(width=X(2.3778) - X(2.3692), height=0.3, stroke_color=WHITE_,
                        stroke_width=1.5).move_to(v3((X(2.3778) + X(2.3692)) / 2, LY))
        box = Rectangle(width=BOX_W, height=BOX_H, stroke_color=GREY_, stroke_width=1.5,
                        fill_color=CARD, fill_opacity=0.92).move_to(BOX_C)
        conn = VGroup(Line(mag.get_corner(DL), box.get_corner(UL)),
                      Line(mag.get_corner(DR), box.get_corner(UR))).set_stroke(GREY_, 1.2, opacity=0.6)
        iax = Line(v3(IX0 - 0.3, IY), v3(IX1 + 0.3, IY), stroke_color=GREY_, stroke_width=2)
        iticks = VGroup(*[Line(v3(XI(IW0 + 0.001 * k), IY - 0.07), v3(XI(IW0 + 0.001 * k), IY + 0.07),
                               stroke_color=DIM, stroke_width=2) for k in range(8)])
        zoom = txt("zoom", 22, GREY_).next_to(box.get_corner(UR), DL, buff=0.14)
        inset = VGroup(box, iax, iticks, zoom)
        self.wait_until("timeline")
        self.play_until(self.T("timeline", "r1", 0.6),
                        Create(mag), Create(conn), FadeIn(inset, shift=DOWN * 0.1))

        # main pointer drops from 2.807 toward 2.376, leaving Strassen's marker behind
        ghost = VGroup(ptri.copy().set_fill(GREY_), pval.copy().set_color(GREY_))
        self.add(ghost, ptri, pval)
        ival, iera, itri = [], [], []
        for w, s, era in RECORDS:
            it = put_on(pointer(ACC), XI(w), IY)
            itri.append(it)
            ival.append(tex(s, VAL, ACC).next_to(it, UP, buff=0.12))
            iera.append(txt(era, NAME, GREY_).move_to(v3(XI(w), IY - 0.42)))
        w0, s0, _ = RECORDS[0]
        nv = tex(s0, VAL, ACC).move_to(v3(X(w0), pval.get_y()))
        self.go(self.T("timeline", "r1", 0.6), "r1+0.35",
                ptri.animate.move_to(v3(X(w0), ptri.get_y())), Transform(pval, nv))
        self.go("r1+0.35", "r1+1.0",
                FadeIn(itri[0], shift=DOWN * 0.2), FadeIn(ival[0], shift=DOWN * 0.1),
                FadeIn(iera[0], shift=UP * 0.1), Flash(mag.get_center(), color=ACC, flash_radius=0.3))

        def step(k, cue):
            w, s, _ = RECORDS[k]
            nv = tex(s, VAL, ACC).move_to(v3(X(w), pval.get_y()))
            self.go(cue, f"{cue}+0.9",
                    ptri.animate.move_to(v3(X(w), ptri.get_y())), Transform(pval, nv),
                    TransformFromCopy(itri[k - 1], itri[k]),
                    itri[k - 1].animate.set_fill(GREY_), ival[k - 1].animate.set_color(GREY_),
                    FadeIn(ival[k], shift=LEFT * 0.4), FadeIn(iera[k], shift=UP * 0.1))

        step(1, "r2")
        step(2, "r3")
        # keep the eye on the newest record while the line finishes
        self.go("r3+0.9", self.T("r3", "claim", 0.95),
                Indicate(ival[2], color=ACC, scale_factor=1.12), Indicate(pval, color=ACC, scale_factor=1.12))

        # ============================================================ 5. the claim: 9/4
        card = paper_card(NUM, width=2.9).move_to(v3(4.95, -1.6))
        tag = paper_tag(NUM, color=ACC)
        old_t = tag[1][1]          # catalog title has raw LaTeX ("\mathbb C"); re-set it
        new_t = Text("Exponent at most 9/4 over ℂ", font=SANS, font_size=17, color=WHITE_, slant=ITALIC)
        new_t.move_to(old_t, aligned_edge=LEFT)
        tag[1].submobjects[1] = new_t

        seg = ("This paper", "It's a")
        t_94 = self.tw("nine fourths", "claim", seg[0], "caveat", seg[1], 0.33, lag=-0.15)
        t_225 = self.tw("two point", "claim", seg[0], "caveat", seg[1], 0.52, lag=0.2)
        t_C = self.tw("over the complex", "claim", seg[0], "caveat", seg[1], 0.75, lag=0.25)

        self.wait_until("claim")
        self.play_until(min(self.cue("claim+1.0"), t_94 - 0.05),
                        FadeOut(VGroup(inset, conn, mag, *itri, *ival, *iera)),
                        FadeIn(card, shift=LEFT * 0.8), FadeIn(tag, shift=RIGHT * 0.2))

        # the leap: 2.371 -> 2.25
        x_old, x_new = X(RECORDS[2][0]), X(NINE4)
        y_t = ptri.get_y()
        ghost2 = ptri.copy().set_fill(GREY_)
        self.add(ghost2, ptri)
        arc = ArcBetweenPoints(v3(x_old, y_t), v3(x_new, y_t), angle=PI * 0.9)
        trail = TracedPath(ptri.get_center, stroke_color=YELLOW_, stroke_width=3, dissipating_time=0.5)
        self.add(trail)

        def fly(m, a):
            m.move_to(arc.point_from_proportion(a))
            m.set_fill(interpolate_color(ManimColor(ACC), ManimColor(YELLOW_), a))
            return m

        l94 = tex(r"9/4", 42, YELLOW_)
        l94.next_to(put_on(pointer(YELLOW_), x_new, LY), UP, buff=0.12)
        t225 = tex("2.25", 34, YELLOW_).move_to(v3(x_new, TL_Y)).align_to(tl2, UP)
        glow_dot = Dot(v3(x_new, y_t), radius=0.2, color=YELLOW_, fill_opacity=0.0)
        old_lab = pval.copy().scale(30 / VAL).set_color(GREY_).next_to(ghost2, UP, buff=0.12)
        self.go(t_94, max(t_94 + 0.9, self.now + 0.9),
                UpdateFromAlphaFunc(ptri, fly, rate_func=smooth),
                Transform(pval, old_lab))
        self.remove(trail)
        self.play(FadeIn(l94, shift=DOWN * 0.15), Flash(ptri.get_center(), color=YELLOW_, flash_radius=0.35),
                  run_time=0.5)
        self.add(glow_dot)
        self.bring_to_front(ptri)
        clock = {"t": 0.0}

        def breathe(m, dt):
            clock["t"] += dt
            m.set_fill(opacity=0.12 + 0.08 * np.sin(2 * PI * clock["t"] / 1.6))
        glow_dot.add_updater(breathe)
        self.go(t_225, t_225 + 0.6, FadeIn(t225, shift=UP * 0.15))

        banner = result_banner(r"\omega \le \tfrac{9}{4}\;\;\text{over } \mathbb{C}", color=YELLOW_,
                               label="CLAIMED RESULT", lean=CATALOG[NUM]["lean"], size=52, is_tex=True)
        banner.move_to(v3(-1.45, -1.25))
        self.go(t_C, min(t_C + 0.9, self.cue("caveat") + 0.4), FadeIn(banner, shift=UP * 0.2))

        # ============================================================ 6. caveat
        ch1 = note("asymptotic: n → ∞", BLUE_)
        ch2 = note("not a practical algorithm", ORANGE_)
        chips = VGroup(ch1, ch2).arrange(RIGHT, buff=0.3).move_to(v3(banner.get_x(), -2.52))
        t_not = self.tw("not a faster", "caveat", "It's a", "jump", "But as", 0.6, lag=0.1)
        t_cost = self.tw("cost grows", "caveat", "It's a", "jump", "But as", 0.25, lag=0.0)
        t_big = self.tw("enormous", "caveat", "It's a", "jump", "But as", 0.4, lag=0.0)
        self.go(t_cost - 0.2, t_cost + 0.8, Indicate(head, color=YELLOW_, scale_factor=1.08))
        self.go(t_big, t_big + 0.7, FadeIn(ch1, shift=UP * 0.15))
        self.go(t_not, t_not + 0.7, FadeIn(ch2, shift=UP * 0.15))

        # ============================================================ 7. the size of the jump
        a0 = v3(x_old, pval.get_top()[1] + 0.12)
        a1 = v3(x_new + 0.05, l94.get_top()[1] + 0.12)
        jarc = CurvedArrow(a0, a1, angle=PI * 0.55, color=YELLOW_, stroke_width=4, tip_length=0.2)
        jlab = tex(r"-0.12", 38, YELLOW_).next_to(jarc, UP, buff=0.08)
        sliver = Line(v3(X(RECORDS[2][0]), LY), v3(X(RECORDS[0][0]), LY), stroke_color=ACC, stroke_width=10)
        sl = VGroup(txt("1990–2026:", 26, GREY_), tex(r"-0.004", 34, ACC)).arrange(RIGHT, buff=0.14)
        sl[0].align_to(sl[1], DOWN).shift(DOWN * 0.02)
        sl.move_to(v3(X(2.3734), 0.02))
        slead = Line(v3(X(2.3734), LY - 0.1), v3(X(2.3734), sl.get_top()[1] + 0.06),
                     stroke_color=ACC, stroke_width=1.5, stroke_opacity=0.8)
        self.go("jump", "jump+0.8", Create(jarc), FadeIn(jlab, shift=DOWN * 0.1))
        self.go("jump+0.8", "jump+1.4", Create(sliver), Create(slead), FadeIn(sl, shift=UP * 0.1))
        self.wait_until(max(self.now, self.narr_end - 0.5))
        glow_dot.clear_updaters()
        self.finish()
