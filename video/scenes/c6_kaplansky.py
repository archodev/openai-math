import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
import re

from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

ACC = PINK_      # chapter accent, also the colour of alpha
BCOL = BLUE_     # beta
PCOL = YELLOW_   # products / emphasis

# first words after each mid-line cue (used to estimate word times inside a line)
ANCHORS = {"conj": "Kaplansky conj", "stood": "The zero-divisor", "companion": "A companion"}
PUNCT = {",": 4, ";": 4, ":": 6, ".": 7, "?": 7, "!": 7}

# Schematic product table: class of each cell (row r = term of beta, column c = term
# of alpha); cells of one class are the same group element.  Every class has an even
# number of cells and never repeats a row or a column, like the components of the
# paper's pairing graph.  Classes are listed in bin order with their colours.
CLASS_GRID = ["FABC", "DEFA", "ACDF", "BFAE"]
CLASSES = [("A", YELLOW_), ("F", SKY_), ("B", GREEN_), ("C", ORANGE_), ("D", PURPLE_), ("E", TEAL_)]


def early(t, k=1.8):
    """rate_func that finishes in the first 1/k of the animation"""
    return smooth(min(1.0, k * t))


def late(t, d=0.35):
    """rate_func that waits for the first fraction d, then runs"""
    return smooth(max(0.0, (t - d) / (1 - d)))


def deg(a):
    return a * DEGREES


def unit(a):
    return np.array([np.cos(deg(a)), np.sin(deg(a)), 0.0])


class C6Kaplansky(VoiceScene):

    # ------------------------------------------------------------ timing helpers
    def _pauses(self):
        """Silent gaps (start, end) in the narration audio, if it is available."""
        if hasattr(self, "_pz"):
            return self._pz
        self._pz = []
        try:
            import soundfile as sf
            x, sr = sf.read(str(BUILD / "audio" / f"{self.scene_id}.wav"))
            if abs(len(x) / sr - self.narr_end) > 0.3:
                return self._pz                      # audio and timing out of sync
            if x.ndim > 1:
                x = x.mean(1)
            hop = int(0.01 * sr)
            n = len(x) // hop
            e = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1))
            sil = e < 0.01 * e.max()
            i = 0
            while i < n:
                if sil[i]:
                    j = i
                    while j < n and sil[j]:
                        j += 1
                    if j - i >= 9:
                        self._pz.append((i * 0.01, j * 0.01))
                    i = j
                else:
                    i += 1
        except Exception:
            pass
        return self._pz

    def ph(self, phrase, fallback):
        """Estimated time at which `phrase` starts being spoken: punctuation-weighted
        character interpolation between cue / line boundaries, snapped to the end of
        the matching pause in the audio when the phrase follows punctuation."""
        for ln in self.timing.get("lines", []):
            T = re.sub(r"\d{4}s?", lambda m: "y" * 15, ln["text"])   # years are long to say
            p = T.find(phrase)
            if p < 0:
                continue
            w = np.cumsum([0] + [1 + PUNCT.get(ch, 0) for ch in T])
            pts = [(0, ln["start"] + 0.03)]
            for cue, a in ANCHORS.items():
                q = T.find(a)
                if q > 0 and self.has_cue(cue):
                    pts += [(q - 1, self.cue(cue) - 0.05), (q, self.cue(cue) + 0.45)]
            pts.append((len(T), ln["end"]))
            pts.sort()
            t = self.cue(fallback)
            for (c0, t0), (c1, t1) in zip(pts, pts[1:]):
                if c0 <= p <= c1 and c1 > c0:
                    t = t0 + (w[p] - w[c0]) / (w[c1] - w[c0]) * (t1 - t0)
                    break
            if (p >= 2 and T[p - 2] in PUNCT) or p in [q for q, _ in pts[1:-1]]:
                near = [b for _, b in self._pauses() if abs(b - t) < 0.7]
                if near:
                    t = min(near, key=lambda b: abs(b - t))
            return t
        return self.cue(fallback)

    def go(self, t_end, *anims, lo=0.3, **kw):
        """Play so the animation ends at t_end (but never shorter than lo)."""
        rt = max(lo, self.cue(t_end) - self.now)
        self.play(*anims, run_time=rt, **kw)

    def at(self, t, *anims, rt=0.8, limit=None, **kw):
        """Wait for t, then play for rt seconds (clipped to end by `limit`)."""
        self.wait_until(t)
        if limit is not None:
            rt = max(0.25, min(rt, self.cue(limit) - self.now))
        self.play(*anims, run_time=rt, **kw)

    def breathe(self, mob, until, color, peak=0.32, period=1.5):
        """Slow pulsing halo around `mob` until time `until` (keeps a hold alive)."""
        halo = mob.copy().set_fill(opacity=0).set_stroke(color, width=10, opacity=0)
        self.add(halo)
        while self.cue(until) - self.now > 0.7:
            rt = min(period, self.cue(until) - self.now - 0.05)
            self.play(halo.animate(rate_func=there_and_back).set_stroke(opacity=peak), run_time=rt)
        self.remove(halo)

    # ------------------------------------------------------------ scene
    def construct(self):
        self.beat_algebra()
        self.beat_torsion()
        self.beat_conjecture()
        self.beat_gardam()
        self.beat_claim()
        self.finish()

    # ============================================================ 1. group algebra
    def beat_algebra(self):
        O = np.array([-3.15, -0.45, 0.0])
        SP = 1.0
        dots, D = VGroup(), {}
        for i in range(-3, 4):
            for j in range(-3, 4):
                p = O + SP * (i * RIGHT + j * UP)
                r = np.hypot(i - 0.5, (j - 0.5) * 1.1)
                d = Dot(p, radius=0.065, color=GREY_)
                d.set_opacity(float(np.clip(1.05 - r / 4.3, 0.12, 0.95)))
                dots.add(d)
                D[(i, j)] = d
        D[(0, 0)].set_color(WHITE_).set_opacity(1).scale(1.35)
        self.D = D

        def P(i, j):
            return D[(i, j)].get_center()

        arr_g = Arrow(P(0, 0), P(1, 0), buff=0.14, stroke_width=4, tip_length=0.18, color=WHITE_)
        arr_h = Arrow(P(0, 0), P(0, 1), buff=0.14, stroke_width=4, tip_length=0.18, color=WHITE_)
        lab1 = tex("1", 36).move_to(P(0, 0) + np.array([-0.36, -0.36, 0]))
        labg = tex("g", 36).move_to(P(1, 0) + np.array([0.0, -0.45, 0]))
        labh = tex("h", 36).move_to(P(0, 1) + np.array([-0.45, 0.0, 0]))
        labgh = tex("gh", 36, color=PCOL).move_to(P(1, 1) + np.array([0.4, 0.36, 0]))
        Glab = tex("G", 50, color=GREY_).move_to(O + np.array([-2.55, 2.55, 0]))

        # right column: the algebra
        X = 3.6
        head = caps("group algebra", 20, ACC).move_to([X, 2.75, 0])
        kg = MathTex(r"K[G]", "=", r"\Big\{\sum c_g\, g\Big\}", font_size=46, color=WHITE_)
        kg.move_to([X, 1.75, 0])
        XE = 2.8  # x of the '=' signs
        a_eq = MathTex(r"\alpha", "=", r"1+g", font_size=54, color=WHITE_)
        b_eq = MathTex(r"\beta", "=", r"1+h", font_size=54, color=WHITE_)
        p_eq = MathTex(r"\alpha\beta", "=", r"1+g+h+gh", font_size=54, color=WHITE_)
        a_eq[0].set_color(ACC)
        b_eq[0].set_color(BCOL)
        p_eq[0].set_color(PCOL)
        for eq, y in ((a_eq, 0.45), (b_eq, -0.6), (p_eq, -1.85)):
            eq.move_to([0, y, 0])
            eq.shift((XE - eq[1].get_center()[0]) * RIGHT)

        ringA = VGroup(*[Circle(radius=0.21, color=ACC, stroke_width=4).move_to(P(*k)) for k in [(0, 0), (1, 0)]])
        ringB = VGroup(*[Circle(radius=0.31, color=BCOL, stroke_width=3.5).move_to(P(*k)) for k in [(0, 0), (0, 1)]])
        ringA2 = ringA.copy().shift(UP * SP)
        sq = Square(side_length=SP, stroke_color=PCOL, stroke_width=3,
                    fill_color=PCOL, fill_opacity=0.14).move_to((P(0, 0) + P(1, 1)) / 2)
        pdots = VGroup(*[Dot(P(*k), radius=0.13, color=PCOL) for k in [(0, 0), (1, 0), (0, 1), (1, 1)]])

        # --- "Take a group of symmetries"
        order = sorted(dots, key=lambda d: np.linalg.norm(d.get_center() - O))
        self.play(LaggedStart(*[GrowFromCenter(d) for d in order], lag_ratio=0.03),
                  FadeIn(Glab), run_time=1.1)
        t_build = self.ph("and build", "group+1.4")
        self.go(t_build, GrowArrow(arr_g), GrowArrow(arr_h),
                FadeIn(lab1), FadeIn(labg, shift=UP * 0.1), FadeIn(labh, shift=RIGHT * 0.1), lo=0.5)
        # --- "and build its group algebra:"
        self.play(FadeIn(head, shift=DOWN * 0.1), Write(kg), run_time=1.2)
        # --- "formal sums of group elements"
        self.at(self.ph("formal sums", "group+3.1"), Create(ringA), TransformFromCopy(VGroup(lab1, labg), a_eq[2]),
                FadeIn(a_eq[:2]), rt=0.9)
        self.play(Indicate(kg[2], color=ACC, scale_factor=1.06), run_time=0.7)
        # --- "which you add and multiply like polynomials"
        self.at(self.ph("which you add", "group+4.8"), Create(ringB),
                TransformFromCopy(VGroup(lab1, labh), b_eq[2]), FadeIn(b_eq[:2]), rt=0.7)
        self.at(self.ph("multiply", "group+5.6"), TransformFromCopy(ringA, ringA2), Write(p_eq), rt=0.9,
                limit="L0_end")
        self.go(max(self.now + 0.5, self.ph("polynomials", "L0_end-0.8") + 0.35),
                FadeIn(sq), FadeOut(VGroup(ringA, ringA2, ringB)), GrowFromCenter(pdots),
                FadeIn(labgh), lo=0.5)
        self.b1 = VGroup(arr_g, arr_h, lab1, labg, labh, labgh, Glab, head, kg, a_eq, b_eq, p_eq, sq, pdots)

    # ============================================================ 2. torsion
    def beat_torsion(self):
        D = self.D
        keep = [D[(0, 0)], D[(1, 0)], D[(2, 0)]]
        others = VGroup(*[d for k, d in D.items() if k not in [(0, 0), (1, 0), (2, 0)]])
        C = np.array([-3.5, 0.3, 0.0])
        R = 1.3
        angs = [210, 330, 90]
        pos = [C + R * unit(a) for a in angs]

        # the row 1, g, g^2 bends round into a cycle
        self.wait_until("torsion")
        labs = VGroup(*[tex(s, 38).move_to(C + (R + 0.42) * unit(a)) for s, a in zip(["1", "g", "g^2"], angs)])
        self.go(self.ph("returns to", "torsion+0.9") + 0.15, FadeOut(others), FadeOut(self.b1),
                *[d.animate.set_fill(WHITE_, 1).set(width=0.2).move_to(p) for d, p in zip(keep, pos)],
                lo=0.7)
        tri = RegularPolygon(3, radius=0.45, stroke_color=GREY_, stroke_width=3).move_to(C)
        mark = Dot(tri.get_vertices()[0], radius=0.07, color=ACC)
        icon = VGroup(tri, mark)
        marker = Dot(pos[0], radius=0.1, color=PCOL)
        mglow = glow(Circle(radius=0.12).move_to(pos[0]), color=PCOL, layers=4, width=14, opacity=0.12)
        mk = VGroup(mglow, marker)
        self.play(LaggedStart(*[FadeIn(l, scale=0.6) for l in labs], lag_ratio=0.2),
                  FadeIn(icon, scale=0.7), FadeIn(mk, scale=0.5), run_time=0.45)

        gap = 0.22
        arcs = VGroup()
        for k in range(3):
            arc = Arc(radius=R, start_angle=deg(angs[k]) + gap, angle=deg(120) - 2 * gap, arc_center=C,
                      color=(PCOL if k == 2 else WHITE_), stroke_width=4)
            arc.add_tip(tip_length=0.18, tip_width=0.18)
            arcs.add(arc)
        t_easy = self.ph("it's easy", "torsion+3.2")
        step = max(0.45, (t_easy - 0.45 - self.now) / 3)
        for k in range(3):
            path = Arc(radius=R, start_angle=deg(angs[k]), angle=deg(120), arc_center=C)
            self.play(Create(arcs[k]), MoveAlongPath(mk, path),
                      Rotate(icon, angle=deg(120), about_point=C), run_time=step)
        g3 = tex("g^3 = 1", 42, color=PCOL).move_to(C + DOWN * (R + 0.9))

        # (1-g)(1+g+g^2) = 1 - g^3 = 0
        XC = 2.75
        eq1 = MathTex(r"(1-g)", r"(1+g+g^2)", font_size=56, color=WHITE_).move_to([XC, 1.6, 0])
        eq1[0].set_color(ACC)
        eq1[1].set_color(BCOL)
        br = VGroup(*[Brace(m, DOWN, buff=0.1, color=GREY_) for m in eq1])
        nz = VGroup(*[tex(r"\neq 0", 34, color=GREY_).next_to(b, DOWN, buff=0.08) for b in br])
        eq2 = MathTex("=", "1", "+g", "+g^2", "-g", "-g^2", "-g^3", font_size=52, color=WHITE_)
        eq2.move_to([XC + 0.1, -0.3, 0])
        eq3 = MathTex("=", "1-g^3", "=", "0", font_size=56, color=WHITE_)
        eq3.next_to(eq2, DOWN, buff=0.5).align_to(eq2, LEFT)
        eq3[3].set_color(PCOL)
        t_two = self.ph("two nonzero", "torsion+4.4")
        self.go(max(t_easy + 0.5, self.now + 0.8), FadeIn(g3, shift=UP * 0.15),
                Flash(keep[0], color=PCOL, line_length=0.18, flash_radius=0.3), Write(eq1), lo=0.8)
        self.at(t_two - 0.2, GrowFromCenter(br[0]), GrowFromCenter(br[1]), FadeIn(nz, shift=UP * 0.1), rt=0.45)
        self.play(FadeIn(eq2[0]), TransformFromCopy(eq1[1], eq2[1:4]),
                  TransformFromCopy(eq1[1], eq2[4:7]), run_time=0.7)
        strikes = VGroup(*[Line(eq2[i].get_corner(DL) + LEFT * 0.03, eq2[i].get_corner(UR) + RIGHT * 0.03,
                                color=RED_, stroke_width=3) for i in (2, 4, 3, 5)])
        self.play(LaggedStart(*[Create(s) for s in strikes], lag_ratio=0.25),
                  eq2[2:6].animate.set_opacity(0.4), run_time=0.45)
        self.play(Write(eq3), run_time=0.5)
        if self.cue("conj") - self.now > 0.3:
            self.go("conj", Indicate(eq3[3], color=PCOL, scale_factor=1.35))
        self.cyc = dict(keep=keep, labs=labs, arcs=arcs, icon=icon, mk=mk, g3=g3, C=C, R=R)
        self.eqs = VGroup(eq1, br, nz, eq2, strikes, eq3)

    # ============================================================ 3. the conjecture
    def beat_conjecture(self):
        cy = self.cyc
        R = cy["R"]
        C2 = np.array([0.0, 0.0, 0.0])
        cyc_grp = VGroup(*cy["keep"], cy["labs"], cy["arcs"], cy["icon"], cy["mk"], cy["g3"])
        title = VGroup(serif("Kaplansky", 52), txt("1956", 32, GREY_)).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        title.move_to([0, 2.9, 0])
        # the cycle moves to centre stage while the name is said
        self.play(FadeOut(self.eqs, shift=RIGHT * 0.4), cyc_grp.animate.shift(C2 - cy["C"]),
                  Write(title[0]), FadeIn(title[1], shift=LEFT * 0.2), run_time=1.1)
        t_wo = self.ph("without such", "conj+2.3")
        self.go(t_wo - 0.35, Rotate(cy["icon"], angle=deg(120), about_point=C2),
                MoveAlongPath(cy["mk"], Arc(radius=R, start_angle=deg(210), angle=deg(120), arc_center=C2)),
                lo=0.6)

        # unroll the cycle into an infinite line: powers of g never come back to 1
        yL, sp, x0 = 0.55, 1.2, -1.2
        X = {k: x0 + sp * k for k in range(-4, 7)}

        def op(k):
            return float(np.clip(1.12 - abs(X[k]) / 6.2, 0.18, 1.0))

        ldots = {k: Dot([X[k], yL, 0], radius=0.1, color=WHITE_).set_opacity(op(k)) for k in X}
        larr = {k: Arrow([X[k], yL, 0], [X[k + 1], yL, 0], buff=0.17, stroke_width=3.5, tip_length=0.16,
                         color=GREY_).set_opacity(min(op(k), op(k + 1))) for k in range(-4, 6)}
        names = {-1: "g^{-1}", 0: "1", 1: "g", 2: "g^2", 3: "g^3"}
        llabs = {k: tex(s, 36).set_opacity(op(k)).next_to([X[k], yL, 0], DOWN, buff=0.24) for k, s in names.items()}
        keep, labs, arcs = cy["keep"], cy["labs"], cy["arcs"]
        new_dots = VGroup(*[ldots[k] for k in X if k not in (0, 1, 2)])
        new_arrs = VGroup(*[larr[k] for k in larr if k not in (0, 1, 2)])
        tgt_arcs = [larr[0].copy().set_color(WHITE_), larr[1].copy().set_color(WHITE_),
                    larr[2].copy().set_color(PCOL)]
        mk = cy["mk"]
        self.play(*[d.animate.move_to(ldots[k]) for d, k in zip(keep, (0, 1, 2))],
                  *[Transform(a, t) for a, t in zip(arcs, tgt_arcs)],
                  *[l.animate.move_to(llabs[k]) for l, k in zip(labs, (0, 1, 2))],
                  mk.animate.move_to(ldots[1]),
                  FadeOut(cy["icon"], scale=0.5), FadeOut(cy["g3"]),
                  run_time=1.1)
        self.play(FadeIn(new_dots, lag_ratio=0.05), FadeIn(new_arrs, lag_ratio=0.05),
                  FadeIn(llabs[-1]), FadeIn(llabs[3]),
                  arcs.animate.set_color(GREY_), run_time=0.6)

        speed = 1.05

        def drift(m, dt):
            m.shift(RIGHT * speed * dt)
            o = float(np.clip((6.2 - m.get_center()[0]) / 1.6, 0, 1))
            m[1].set_opacity(o)
            for g_ in m[0]:
                g_.set_stroke(opacity=0.12 * o)
        mk.add_updater(drift)

        # "called torsion" -> torsion-free
        tf = VGroup(chip("TORSION-FREE", GREEN_, size=18),
                    tex(r"g^n \neq 1\ \ (g\neq 1,\ n\neq 0)", 38, color=GREEN_)).arrange(RIGHT, buff=0.35)
        tf.move_to([0, 1.7, 0])
        self.at(self.ph("torsion,", "conj+4.0") - 0.2, FadeIn(tf, shift=DOWN * 0.15), rt=0.7)

        stmt = MathTex(r"\alpha", r"\neq 0,\ ", r"\beta", r"\neq 0", r"\;\Longrightarrow\;",
                       r"\alpha\beta", r"\neq 0", font_size=60, color=WHITE_).move_to([0, -1.05, 0])
        stmt[0].set_color(ACC)
        stmt[2].set_color(BCOL)
        self.at(self.ph("it can never", "conj+5.0"), Write(stmt), rt=1.0)
        nzd = bold("no zero divisors", 38, ACC).move_to([0, -2.25, 0])
        self.at(self.ph("no zero divisors", "L1_end-1.1"), FadeIn(nzd, shift=UP * 0.15),
                Indicate(stmt[5:], color=ACC, scale_factor=1.08), rt=0.9)
        self.line = VGroup(*keep, *labs, *arcs, new_dots, new_arrs, llabs[-1], llabs[3])
        self.k = dict(title=title, tf=tf, stmt=stmt, nzd=nzd, mk=mk)

    # ============================================================ 4. Gardam / unit conjecture
    def beat_gardam(self):
        k = self.k
        self.wait_until("gardam")
        k["mk"].clear_updaters()
        W, H = 5.8, 2.7
        zbox = RoundedRectangle(width=W, height=H, corner_radius=0.18, stroke_color=ACC, stroke_width=2.2,
                                fill_color=CARD, fill_opacity=0.95).move_to([0, -0.15, 0])
        ztitle = bold("Zero-divisor conjecture", 30).move_to(zbox.get_top() + DOWN * 0.5)
        zf = k["stmt"].copy().scale_to_fit_width(4.3).move_to(zbox.get_center() + DOWN * 0.05)
        # box goes *behind* the statement that morphs into it
        zbox_t = zbox.copy()
        zbox.set_fill(opacity=0).set_stroke(opacity=0)
        self.add(zbox)
        self.bring_to_back(zbox)
        quick = dict(rate_func=early)
        self.play(FadeOut(self.line, **quick), FadeOut(k["mk"], **quick), FadeOut(k["tf"], **quick),
                  FadeOut(k["title"], **quick),
                  ReplacementTransform(k["stmt"], zf), FadeTransform(k["nzd"], ztitle),
                  Transform(zbox, zbox_t), run_time=1.0)
        zcard = VGroup(zbox, ztitle, zf)

        ubox = zbox_t.copy().set_stroke(GREY_).move_to([-3.15, -0.15, 0])
        utitle = bold("Unit conjecture", 30).move_to(ubox.get_top() + DOWN * 0.5)
        uf = MathTex(r"u\ \text{invertible}", r"\;\Longrightarrow\;", r"u=\lambda g", font_size=40,
                     color=WHITE_).move_to(ubox.get_center() + DOWN * 0.05)
        ucard = VGroup(ubox, utitle, uf)
        self.at(self.ph("Giles", "gardam+1.2") - 0.15, zcard.animate.move_to([3.15, -0.15 + 0.0, 0]),
                FadeIn(ucard, shift=RIGHT * 0.8), rt=0.8)
        uchip = chip("DISPROVED · GARDAM 2021", RED_, size=18).move_to(ubox.get_bottom() + UP * 0.45)
        self.at(self.ph("disproved", "gardam+2.0"), FadeIn(uchip, scale=1.3),
                ubox.animate.set_stroke(RED_), uf.animate.set_opacity(0.55), rt=0.6)
        self.at(self.ph("Kaplansky's unit", "gardam+3.4"), Indicate(utitle, color=RED_, scale_factor=1.08),
                rt=0.9, limit="stood")
        zchip = chip("STILL OPEN", ACC, size=18).move_to(zbox.get_bottom() + UP * 0.45)
        self.at(self.ph("The zero-divisor", "stood+0.4"), FadeIn(zchip, scale=1.3),
                VGroup(ubox, utitle, uf, uchip).animate.set_opacity(0.5), rt=0.6)
        self.play(Circumscribe(zbox, color=ACC, buff=0.08, time_width=0.6), run_time=1.0)
        self.breathe(zbox, "claim", ACC)
        self.cards = dict(ubox=ubox, utitle=utitle, uf=uf, uchip=uchip,
                          zbox=zbox, ztitle=ztitle, zf=zf, zchip=zchip)

    # ============================================================ 5. the claim
    def small_card(self, title, x, color):
        box = RoundedRectangle(width=3.95, height=1.0, corner_radius=0.14, stroke_color=color,
                               stroke_width=1.8, fill_color=CARD, fill_opacity=0.95).move_to([x, 3.15, 0])
        t = bold(title, 22).move_to(box.get_top() + DOWN * 0.3)
        return box, t

    def beat_claim(self):
        c = self.cards
        self.wait_until("claim")
        # header: the two conjectures shrink to the top, then the paper slides in
        sub, sut = self.small_card("Unit conjecture", -2.05, RED_)
        szb, szt = self.small_card("Zero-divisor conjecture", 2.05, ACC)
        suc = chip("DISPROVED · GARDAM 2021", RED_, size=15).move_to(sub.get_bottom() + UP * 0.28)
        szc = chip("STILL OPEN", ACC, size=15).move_to(szb.get_bottom() + UP * 0.28)
        card = paper_card("196", width=3.3).move_to([0.3, -0.3, 0])
        tag = paper_tag("196", color=ACC)
        self.play(ReplacementTransform(c["ubox"], sub), ReplacementTransform(c["utitle"], sut),
                  ReplacementTransform(c["uchip"], suc), FadeOut(c["uf"], rate_func=lambda t: early(t, 3)),
                  ReplacementTransform(c["zbox"], szb), ReplacementTransform(c["ztitle"], szt),
                  ReplacementTransform(c["zchip"], szc), FadeOut(c["zf"], rate_func=lambda t: early(t, 3)),
                  run_time=0.6)
        card.shift(RIGHT * 7.5)
        self.play(card.animate.shift(LEFT * 7.5), FadeIn(tag, shift=UP * 0.2), run_time=0.7)
        szc2 = chip("COUNTEREXAMPLE · CLAIMED", RED_, size=15).move_to(szc)
        self.at(self.ph("counterexample", "claim+1.3"), ReplacementTransform(szc, szc2),
                szb.animate.set_stroke(RED_), rt=0.6)

        # "a torsion-free group" : paper slides aside, the group G appears
        grow = VGroup(tex("G", 54), chip("TORSION-FREE", GREEN_, size=17),
                      chip("FINITELY PRESENTED", GREY_, size=17)).arrange(RIGHT, buff=0.3)
        grow.move_to([1.6, 2.05, 0])
        self.at(self.ph("a torsion-free group", "claim+2.3") - 0.15,
                card.animate.scale(2.5 / 3.3).move_to([-4.75, -0.2, 0]),
                FadeIn(grow, shift=DOWN * 0.15, rate_func=late), rt=0.9)

        # "built with the help of random graphs"
        cA, cB = np.array([3.4, 0.3, 0]), np.array([-0.3, 0.3, 0])
        vA = [cA + np.array(v) for v in [(-1.0, 0.6, 0), (0.85, 0.8, 0), (1.0, -0.6, 0), (-0.75, -0.7, 0)]]
        vB = [cB + np.array(v) for v in [(-0.9, 0.7, 0), (0.95, 0.5, 0), (0.65, -0.75, 0), (-1.0, -0.5, 0)]]

        def edges(V, ctr, spec):
            g = VGroup()
            for i, j, a in spec:
                if i == j:
                    v = V[i] - ctr
                    v = v / np.linalg.norm(v)
                    e = Circle(radius=0.22).move_to(V[i] + v * 0.22)
                elif a == 0:
                    e = Line(V[i], V[j])
                else:
                    e = ArcBetweenPoints(V[i], V[j], angle=a)
                g.add(e.set_stroke(WHITE_, width=3, opacity=0.65))
            return g

        specA = [
            [(0, 1, 0), (0, 2, 0), (1, 3, 0.4), (2, 3, 0), (3, 3, 0), (1, 2, 0), (0, 3, -0.5)],
            [(0, 3, 0), (1, 2, 0), (0, 1, 0.5), (0, 1, -0.5), (2, 3, 0.3), (2, 2, 0), (1, 3, 0)],
            [(0, 1, 0), (1, 2, 0.45), (1, 2, -0.45), (2, 3, 0), (3, 0, 0.3), (0, 0, 0), (0, 2, 0)],
        ]
        specB = [
            [(0, 2, 0), (1, 3, 0), (0, 1, 0), (2, 3, 0.4), (1, 1, 0), (0, 3, 0), (1, 2, 0.4)],
            [(0, 1, 0.4), (0, 1, -0.4), (1, 2, 0), (2, 3, 0), (3, 3, 0), (0, 2, 0), (1, 3, 0.3)],
            [(0, 1, 0), (1, 2, 0), (2, 3, 0.45), (2, 3, -0.45), (3, 0, 0), (1, 1, 0), (0, 2, -0.3)],
        ]
        EA = [edges(vA, cA, s) for s in specA]
        EB = [edges(vB, cB, s) for s in specB]
        dA = VGroup(*[Dot(p, radius=0.12, color=ACC) for p in vA])
        dB = VGroup(*[Dot(p, radius=0.12, color=BCOL) for p in vB])
        eA, eB = EA[0], EB[0]
        rg = txt("random graphs", 26, GREY_).move_to([1.55, -1.25, 0])
        t_two = self.ph("where two", "claim+5.5")
        self.at(self.ph("built", "claim+3.4") - 0.1,
                Create(eA), Create(eB),
                LaggedStart(*[GrowFromCenter(d) for d in [*dB, *dA]], lag_ratio=0.08), rt=0.9)
        self.play(FadeIn(rg, shift=UP * 0.1), run_time=0.4)
        # re-sample twice, then settle on the chosen pair
        rt = max(0.35, min(0.7, (t_two - 0.1 - self.now) / 2))
        for s in (1, 2):
            self.play(Transform(eA, EA[s]), Transform(eB, EB[s]), run_time=rt)

        # "where two nonzero elements": the vertices become the terms of alpha and beta
        GX, GY, cs = 1.45, -0.6, 0.68
        colx = [GX + cs * (c_ - 1.5) for c_ in range(4)]
        rowy = [GY + cs * (1.5 - r_) for r_ in range(4)]
        ya, xb = rowy[0] + 0.83, colx[0] - 0.9
        la = tex(r"\alpha\neq 0", 44, color=ACC).next_to([colx[-1], ya, 0], RIGHT, buff=0.45)
        lb = tex(r"\beta\neq 0", 44, color=BCOL).next_to([xb, GY, 0], LEFT, buff=0.4)
        self.wait_until(t_two - 0.25)
        self.play(FadeOut(eA), FadeOut(eB), FadeOut(rg), run_time=0.3)
        self.play(*[d.animate.move_to([x, ya, 0]) for d, x in zip(dA, colx)],
                  *[d.animate.move_to([xb, y, 0]) for d, y in zip(dB, rowy)], run_time=0.75)
        self.play(FadeIn(la, shift=LEFT * 0.15), FadeIn(lb, shift=RIGHT * 0.15), run_time=0.5)

        # "with coefficients mod two": the product table; equal products pile up in pairs
        frame, cells = VGroup(), {}
        col_of = dict(CLASSES)
        for r_ in range(4):
            for c_ in range(4):
                p = np.array([colx[c_], rowy[r_], 0])
                frame.add(RoundedRectangle(width=0.58, height=0.58, corner_radius=0.08, stroke_color=DIM,
                                           stroke_width=1.5).move_to(p))
                k_ = CLASS_GRID[r_][c_]
                cells[(r_, c_)] = RoundedRectangle(width=0.58, height=0.58, corner_radius=0.08, stroke_width=0,
                                                   fill_color=col_of[k_], fill_opacity=0.88).move_to(p)
        bx0, bw, by = 3.85, 0.5, -1.95
        base = Line([bx0 - 0.35, by - 0.03, 0], [bx0 + 5 * bw + 0.35, by - 0.03, 0], stroke_color=GREY_,
                    stroke_width=2)
        stacks, moves = [], []
        for b, (k_, colr) in enumerate(CLASSES):
            members = [q for q in sorted(cells) if CLASS_GRID[q[0]][q[1]] == k_]
            st = VGroup()
            for h, q in enumerate(members):
                tgt = np.array([bx0 + b * bw, by + 0.21 + 0.42 * h, 0])
                moves.append(cells[q].animate.scale(0.36 / 0.58).move_to(tgt))
                st.add(cells[q])
            stacks.append(st)
        mod2 = VGroup(txt("mod 2:", 26, GREY_), tex(r"1+1=0", 46)).arrange(RIGHT, buff=0.25)
        mod2.move_to([bx0 + 2.5 * bw, 0.4, 0]).align_to(RIGHT * 6.35, RIGHT)
        schem = txt("schematic illustration", 22, GREY_, slant=ITALIC).move_to([GX + 0.3, by - 0.42, 0])
        order = sorted(cells, key=lambda q: q[0] + q[1])
        self.at(self.ph("with coefficients", "claim+7.2") - 0.15, FadeIn(frame),
                LaggedStart(*[GrowFromCenter(cells[q]) for q in order], lag_ratio=0.05),
                FadeIn(schem), rt=0.8)
        t_mul = self.ph("multiply to", "claim+8.7")
        self.go(max(self.now + 0.7, t_mul - 0.05), LaggedStart(*moves, lag_ratio=0.04), Create(base),
                FadeIn(mod2, shift=LEFT * 0.15), lo=0.7)

        # "multiply to exactly zero": every pile is even, so everything cancels
        self.play(Indicate(mod2[1], color=PCOL, scale_factor=1.12),
                  LaggedStart(*[FadeOut(st, scale=0.2) for st in stacks], lag_ratio=0.18), run_time=1.1)
        abz = MathTex(r"\alpha\beta", "=", "0", font_size=76, color=WHITE_).move_to([GX, GY, 0])
        abz[2].set_color(PCOL)
        self.play(FadeOut(frame), FadeOut(base), Write(abz), run_time=0.6)
        t_c = self.ph("A companion", "companion+0.4") - 0.1
        if t_c - self.now > 0.5:
            self.go(t_c, Indicate(abz[2], color=PCOL, scale_factor=1.3))

        # result banner
        banner = result_banner(r"\text{torsion-free } G \text{ and nonzero } \alpha,\beta\in\mathbb{F}_2[G]"
                               r"\text{ with } \alpha\beta=0", lean=CATALOG["196"]["lean"], is_tex=True, size=38)
        banner.move_to([0, -0.55, 0])
        self.play(FadeOut(card, rate_func=early), FadeOut(VGroup(dA, dB, la, lb, mod2, schem, grow), rate_func=early),
                  abz.animate.move_to(banner[1][1]).set_opacity(0),
                  FadeIn(banner, scale=0.97, rate_func=late), run_time=1.0)

        # companion: direct finiteness also broken (family 197)
        sdb, sdt = self.small_card("Direct finiteness", 4.2, RED_)
        sdc = chip("COUNTEREXAMPLE · CLAIMED", RED_, size=15).move_to(sdb.get_bottom() + UP * 0.28)
        dfm = MathTex(r"ab=1", r",\ \ ", r"ba\neq 1", font_size=40, color=WHITE_)
        dfm[2].set_color(RED_)
        df = VGroup(dfm, txt("family 197", 22, GREY_)).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
        df.move_to([4.2, 2.0, 0]).align_to(sdb, RIGHT)
        hdr_u, hdr_z = VGroup(sub, sut, suc), VGroup(szb, szt, szc2)
        self.at(self.ph("direct finiteness", "companion+1.4") - 0.7,
                hdr_u.animate.shift(LEFT * 2.15), hdr_z.animate.shift(LEFT * 2.05), rt=0.5)
        self.play(FadeIn(VGroup(sdb, sdt), shift=LEFT * 0.5), run_time=0.5)
        self.play(FadeIn(sdc, scale=1.3), FadeIn(df, shift=DOWN * 0.15),
                  Circumscribe(sdb, color=RED_, buff=0.06), run_time=0.9)
        # keep the result alive until the end
        self.breathe(banner[0], "end-0.5", PCOL, peak=0.28, period=1.6)
