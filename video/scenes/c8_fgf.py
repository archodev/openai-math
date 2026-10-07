import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

ACC = SKY_
GEN_COLORS = [SKY_, PINK_, GOLD_]          # a, b, c
GEN_TEX = ["a", "b", "c"]


# ---------------------------------------------------------------- Cayley trees
def seg_points(A, B, t=1.0):
    """Straight segments A->A+t(B-A) as one multi-subpath point array."""
    D = (B - A) * t
    P = np.stack([A, A + D / 3, A + 2 * D / 3, A + D], axis=1)
    return P.reshape(-1, 3)


def gen_dirs(ngen):
    """Generator g points at angle pi*g/ngen; its inverse points the other way.
    ngen=2: a horizontal, b vertical (4-regular). ngen=3: 60 deg apart (6-regular)."""
    out = []
    for g in range(ngen):
        ang = PI * g / ngen
        d = np.array([np.cos(ang), np.sin(ang), 0.0])
        out += [(g, 1, d), (g, -1, -d)]
    return out


class CayleyTree(VGroup):
    """Cayley graph of the free group F_n, drawn as a fractal tree: edge length
    shrinks by `ratio` per level; one VMobject per (level, generator)."""

    def __init__(self, ngen, ratio, depth, L1, center=ORIGIN, widths=None,
                 dot_levels=2, dot_r=0.075, **kw):
        super().__init__(**kw)
        self.ngen, self.ratio, self.nlev, self.L1 = ngen, ratio, depth, L1
        widths = widths or [3.0] * depth
        dirs = gen_dirs(ngen)
        segs = {}
        verts = {0: [np.array(center, float)]}
        frontier = [(np.array(center, float), None)]
        L = L1
        for lvl in range(1, depth + 1):
            new = []
            for p, last in frontier:
                for g, s, d in dirs:
                    if last == (g, -s):          # reduced words only: no x x^-1
                        continue
                    q = p + L * d
                    A, B = segs.setdefault((lvl, g), ([], []))
                    A.append(p)
                    B.append(q)
                    new.append((q, (g, s)))
            verts[lvl] = [q for q, _ in new]
            frontier = new
            L *= ratio
        self.layers = VGroup()
        for (lvl, g) in sorted(segs):
            A, B = (np.array(x) for x in segs[(lvl, g)])
            m = VMobject(stroke_color=GEN_COLORS[g], stroke_width=widths[lvl - 1])
            m.set_points(seg_points(A, B))
            m.lvl, m.gen = lvl, g
            self.layers.add(m)
        self.dots = VGroup()
        for lvl in range(dot_levels + 1):
            for v in verts[lvl]:
                d = Dot(v, radius=dot_r * (0.62 ** lvl), color=WHITE_)
                d.lvl = lvl
                self.dots.add(d)
        self.add(self.layers, self.dots)

    def scale_widths(self, f):
        for m in self.layers:
            m.set_stroke(width=m.get_stroke_width() * f)
        return self

    def hide_from(self, lvl):
        """Collapse layers >= lvl to zero length (ready to be grown)."""
        for m in self.layers:
            if m.lvl >= lvl:
                P = m.points.reshape(-1, 4, 3)
                m._A, m._B = P[:, 0].copy(), P[:, 3].copy()
                m.set_points(seg_points(m._A, m._B, 1e-4))
        for d in self.dots:
            if d.lvl >= lvl:
                d.set_opacity(0)
        return self

    def grow(self, lo=1, hi=None, speed_ratio=0.62, **kw):
        """Grow levels lo..hi outward; level k takes time ~ speed_ratio**k
        (deeper, shorter levels pop faster: Zeno-like)."""
        hi = hi or self.nlev
        r = speed_ratio
        S = [(1 - r ** i) / (1 - r) for i in range(self.nlev + 1)]
        s0, s1 = S[lo - 1], S[hi]
        layers = [m for m in self.layers if lo <= m.lvl <= hi]
        for m in layers:
            if not hasattr(m, "_A"):
                P = m.points.reshape(-1, 4, 3)
                m._A, m._B = P[:, 0].copy(), P[:, 3].copy()
        dots = [d for d in self.dots if lo <= d.lvl <= hi]

        def upd(mob, a):
            s = s0 + a * (s1 - s0)
            for m in layers:
                t = np.clip((s - S[m.lvl - 1]) / (S[m.lvl] - S[m.lvl - 1]), 1e-4, 1)
                m.set_points(seg_points(m._A, m._B, t))
            for d in dots:
                d.set_opacity(float(np.clip((s - S[d.lvl]) / (0.3 * r ** d.lvl) + 1, 0, 1)))

        return UpdateFromAlphaFunc(self, upd, **kw)


def word_path(word, ngen, ratio, L1, center):
    dirs = {(g, s): d for g, s, d in gen_dirs(ngen)}
    pts = [np.array(center, float)]
    L = L1
    for g, s in word:
        pts.append(pts[-1] + L * dirs[(g, s)])
        L *= ratio
    return pts


def letter_tex(g, s):
    return GEN_TEX[g] + ("^{-1}" if s < 0 else "")


def algebra_box(n, center, w=3.7, h=1.6, size=56):
    rect = RoundedRectangle(width=w, height=h, corner_radius=0.18, stroke_color=ACC,
                            stroke_width=2.4, fill_color=CARD, fill_opacity=0.92)
    rect.move_to(center)
    lab = tex(r"L(\mathbb F_{%s})" % n, size=size)
    cap = txt("von Neumann algebra", size=24, color=GREY_)
    VGroup(lab, cap).arrange(DOWN, buff=0.14).move_to(rect)
    pill_t = txt("infinite-dimensional", size=22, color=ACC, weight=SEMIBOLD)
    pill = RoundedRectangle(width=pill_t.width + 0.36, height=pill_t.height + 0.2,
                            corner_radius=(pill_t.height + 0.2) / 2, stroke_color=ACC,
                            stroke_width=1.6, fill_color=BG, fill_opacity=1)
    pill_t.move_to(pill)
    pill_g = VGroup(pill, pill_t).next_to(rect, DOWN, buff=0.14)
    g = VGroup(rect, lab, cap)
    g.rect, g.lab, g.cap, g.pill = rect, lab, cap, pill_g
    return g


def row_of_factors(y, x=0.6):
    """L(F2) _ L(F3) _ L(F4) _ ... _ L(F_inf) with empty link slots."""
    items, boxes, dots_m = [], [], None
    for n in ["2", "3", "4", None, r"\infty"]:
        if n is None:
            dots_m = tex(r"\cdots", size=40)
            items.append(dots_m)
            continue
        rect = RoundedRectangle(width=1.55, height=0.8, corner_radius=0.14, stroke_color=ACC,
                                stroke_width=2, fill_color=CARD, fill_opacity=0.92)
        lab = tex(r"L(\mathbb F_{%s})" % n, size=34).move_to(rect)
        b = VGroup(rect, lab)
        b.rect, b.lab = rect, lab
        items.append(b)
        boxes.append(b)
    slots = [Rectangle(width=0.5, height=0.1, stroke_width=0, fill_opacity=0) for _ in range(4)]
    seq = []
    for i, it in enumerate(items):
        seq.append(it)
        if i < len(slots):
            seq.append(slots[i])
    VGroup(*seq).arrange(RIGHT, buff=0.16).move_to([x, y, 0])
    row = VGroup(*items)
    row.boxes, row.dots, row.slots = boxes, dots_m, slots
    return row


class C8Fgf(VoiceScene):
    def frac(self, a, b, f):
        ta, tb = self.cue(a), self.cue(b)
        return ta + f * (tb - ta)

    def construct(self):
        # ============================================================ 1. free group
        C0 = np.array([-2.45, -0.3, 0])
        L1A = 1.6
        W_A = [5.0, 4.0, 3.2, 2.5, 1.9, 1.4]
        f2 = CayleyTree(2, 0.5, 6, L1A, center=C0, widths=W_A, dot_levels=2, dot_r=0.09)
        f2.hide_from(1)
        root2 = f2.dots[0]
        root2.set_opacity(0)
        self.add(f2)

        head = tex(r"\mathbb F_2=\langle a,\,b\rangle", size=60)
        head.move_to([3.85, 2.55, 0])
        head[0][4].set_color(GEN_COLORS[0])
        head[0][6].set_color(GEN_COLORS[1])
        sub = txt("free group on two letters", size=26, color=GREY_)
        sub.next_to(head, DOWN, buff=0.22)

        # generator labels beside the four first-level edges
        glabs = VGroup()
        for g, s, d in gen_dirs(2):
            lab = tex(letter_tex(g, s), size=40, color=GEN_COLORS[g])
            perp = np.array([-d[1], d[0], 0]) * (1 if s > 0 else -1)
            lab.next_to(C0 + d * L1A * 0.5, perp, buff=0.14)
            glabs.add(lab)

        self.wait_until("free")
        t_words = self.frac("free", "tree", 0.36)
        self.play_until(min(self.cue("free") + 1.4, t_words - 0.15),
                        Write(head), root2.animate.set_opacity(1), f2.grow(1, 1),
                        FadeIn(sub, shift=UP * 0.15),
                        LaggedStart(*[FadeIn(l, scale=0.6) for l in glabs], lag_ratio=0.25))

        # ---- words, each traced as a walk from the identity
        words = [
            [(0, 1), (1, 1), (0, 1)],                 # a b a
            [(1, -1), (0, 1), (1, -1)],               # b^-1 a b^-1
            [(0, -1), (1, 1), (1, 1), (0, -1)],       # a^-1 b b a^-1
        ]
        word_mobs = VGroup()
        for w in words:
            m = MathTex(*[letter_tex(g, s) for g, s in w], font_size=52, color=WHITE_,
                        arg_separator=r"\,")
            for part, (g, s) in zip(m, w):
                part.set_color(GEN_COLORS[g])
            word_mobs.add(m)
        word_mobs.arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        word_mobs.next_to(sub, DOWN, buff=0.6).align_to(sub, LEFT).shift(RIGHT * 0.1)

        def make_walker():
            w_ = Dot(C0, radius=0.1, color=WHITE_)
            return VGroup(glow(Circle(radius=0.1).move_to(C0), color=WHITE_, layers=4, width=10,
                               opacity=0.12), w_)

        paths, ends = VGroup(), VGroup()
        self.wait_until(t_words)
        # absolute schedule (frame rounding must not accumulate)
        t0 = self.now
        per_word = (self.cue("tree") - 0.05 - t0) / len(words)
        for wi, (w, wm) in enumerate(zip(words, word_mobs)):
            pts = word_path(w, 2, 0.5, L1A, C0)
            ws = t0 + wi * per_word
            step = (per_word - 0.15) / len(w)
            wk = make_walker()
            for k, (g, s) in enumerate(w):
                seg = Line(pts[k], pts[k + 1], color=GEN_COLORS[g], stroke_width=W_A[k] + 2.5)
                paths.add(seg)
                self.add(seg, wk)
                self.play_until(ws + (k + 1) * step, Create(seg), wk.animate.move_to(pts[k + 1]),
                                FadeIn(wm[k], shift=LEFT * 0.15), rate_func=smooth, min_time=0.1)
            end = Dot(pts[-1], radius=0.075, color=WHITE_)
            ends.add(end)
            self.add(end)
            self.play_until(ws + per_word, FadeOut(wk, scale=1.6), min_time=0.07)
        self.bring_to_front(paths, ends)

        # ============================================================ 2. the tree
        self.wait_until("tree")
        self.play_until(self.frac("tree", "L1", 0.62), f2.grow(2), rate_func=linear)
        self.play_until("L1", FadeOut(paths), FadeOut(ends), FadeOut(word_mobs, shift=RIGHT * 0.2),
                        FadeOut(sub), FadeOut(glabs))

        # ============================================================ 3. von Neumann algebras
        P2 = np.array([-3.6, 1.15, 0])
        P3 = np.array([3.6, 1.15, 0])
        B2c = np.array([-3.6, -2.0, 0])
        B3c = np.array([3.6, -2.0, 0])
        q = lambda f: self.frac("vn", "question", f)
        f2.generate_target()
        f2.target.scale(0.47).move_to(P2)
        f2.target.scale_widths(0.62)
        for d in f2.target.dots:
            d.scale(0.85)
        head2 = tex(r"\mathbb F_2=\langle a,\,b\rangle", size=44)
        head2[0][4].set_color(GEN_COLORS[0])
        head2[0][6].set_color(GEN_COLORS[1])
        head2.move_to(P2 + UP * 2.05)

        f3 = CayleyTree(3, 1 / 3, 4, 1.0, center=P3, widths=[3.2, 2.4, 1.6, 1.1],
                        dot_levels=2, dot_r=0.075)
        f3.hide_from(1)
        root3 = f3.dots[0]
        root3.set_opacity(0)
        head3 = tex(r"\mathbb F_3=\langle a,\,b,\,c\rangle", size=44)
        for i, g in ((4, 0), (6, 1), (8, 2)):
            head3[0][i].set_color(GEN_COLORS[g])
        head3.move_to(P3 + UP * 2.05)

        # "From any group": F2 moves aside, F3 grows next to it
        self.play_until(q(0.15), MoveToTarget(f2), ReplacementTransform(head, head2))
        self.add(f3)
        self.play_until(q(0.3), f3.grow(1), root3.animate.set_opacity(1),
                        FadeIn(head3, shift=DOWN * 0.15), rate_func=linear)

        # "you can build an algebra of operators": each tree flows into a box
        box2, box3 = algebra_box(2, B2c), algebra_box(3, B3c)
        arrs = VGroup(*[Arrow(P + DOWN * 1.58, Bc + UP * 0.92, buff=0, stroke_width=3, color=GREY_,
                              max_tip_length_to_length_ratio=0.3) for P, Bc in ((P2, B2c), (P3, B3c))])
        ghosts = VGroup(f2.copy(), f3.copy())
        for gh in ghosts:
            gh.set_stroke(opacity=0.75)
        self.play_until(q(0.37), Create(box2.rect), Create(box3.rect))
        self.add(ghosts)
        self.play_until(q(0.46),
                        ghosts[0].animate.scale(0.3).move_to(B2c),
                        ghosts[1].animate.scale(0.3).move_to(B3c),
                        *[GrowArrow(a) for a in arrs], rate_func=smooth)
        self.play_until(q(0.53),
                        FadeOut(ghosts[0], scale=0.2), FadeOut(ghosts[1], scale=0.2),
                        FadeIn(box2.lab, scale=0.5), FadeIn(box3.lab, scale=0.5))
        self.remove(ghosts)
        # "its von Neumann algebra"
        self.play_until(q(0.62), FadeIn(box2.cap, shift=UP * 0.1), FadeIn(box3.cap, shift=UP * 0.1))
        # "which for a free group is infinite-dimensional"
        self.wait_until(q(0.8))
        self.play_until(q(0.92), FadeIn(box2.pill, scale=0.7), FadeIn(box3.pill, scale=0.7))

        # ---- two letters, or three: same algebra?
        g_ = lambda f: self.frac("question", "groups", f)
        self.wait_until("question")
        self.play_until(g_(0.2), *[Indicate(head2[0][i], color=WHITE_, scale_factor=1.3) for i in (4, 6)],
                        Indicate(f2, color=None, scale_factor=1.06),
                        FadeOut(box2.pill), FadeOut(box3.pill))
        self.play_until(g_(0.4), *[Indicate(head3[0][i], color=WHITE_, scale_factor=1.3) for i in (4, 6, 8)],
                        Indicate(f3, color=None, scale_factor=1.06))
        qc = tex(r"\cong", size=80)
        qm = tex(r"?", size=56, color=YELLOW_)
        qm.next_to(qc, UP, buff=0.16)
        qg = VGroup(qc, qm).move_to((B2c + B3c) / 2 + UP * 0.2)
        self.wait_until(g_(0.45))
        self.play_until(g_(0.68), Write(qc), FadeIn(qm, shift=DOWN * 0.2))
        self.play_until(g_(0.95), Wiggle(qm, scale_value=1.25, rotation_angle=0.05 * TAU))

        # ---- the groups themselves differ
        ncong = tex(r"\mathbb F_2\not\cong\mathbb F_3", size=50)
        ncong.move_to((P2 + P3) / 2 + UP * 0.15)
        ncap = txt("as groups", size=24, color=GREY_).next_to(ncong, DOWN, buff=0.2)
        self.wait_until("groups")
        self.play_until(self.frac("groups", "L1_end", 0.45), Write(ncong), FadeIn(ncap, shift=UP * 0.1))

        # ============================================================ 4. history
        TOP = 2.95
        h_ = lambda f: self.frac("history", "dichotomy", f)
        f2.generate_target()
        f2.target.scale(0.42).move_to([-5.75, TOP, 0]).scale_widths(0.75)
        f3.generate_target()
        f3.target.scale(0.42).move_to([5.75, TOP, 0]).scale_widths(0.75)
        r2 = RoundedRectangle(width=2.35, height=0.95, corner_radius=0.16, stroke_color=ACC,
                              stroke_width=2.2, fill_color=CARD, fill_opacity=0.92).move_to([-3.1, TOP, 0])
        r3 = r2.copy().move_to([3.1, TOP, 0])
        self.wait_until("history")
        # staggered: the trees clear out to the corners first, then the boxes rise
        # into the gap they left (no tree ever sweeps across a box)
        tree_rf = lambda t: smooth(min(1.0, t / 0.6))
        box_rf = lambda t: smooth(max(0.0, (t - 0.3) / 0.7))
        self.play_until(h_(0.26),
                        MoveToTarget(f2, rate_func=tree_rf), MoveToTarget(f3, rate_func=tree_rf),
                        Transform(box2.rect, r2, rate_func=box_rf),
                        Transform(box3.rect, r3, rate_func=box_rf),
                        box2.lab.animate(rate_func=box_rf).scale(0.72).move_to(r2),
                        box3.lab.animate(rate_func=box_rf).scale(0.72).move_to(r3),
                        *[FadeOut(m, rate_func=lambda t: smooth(min(1.0, t / 0.4)))
                          for m in (box2.cap, box3.cap, arrs, head2, head3, ncong, ncap)],
                        qg.animate(rate_func=box_rf).scale(0.75).move_to([0, TOP + 0.1, 0]))

        kad = txt("Richard Kadison's question", size=24, color=GREY_)
        kad.move_to([0, TOP - 0.9, 0])
        self.play_until(h_(0.42), FadeIn(kad, shift=UP * 0.12))

        # timeline: decades pass. It sits low while it is the only thing happening
        # (balances the frame under the question row), then rises at {dichotomy}
        # to make room for the two rows of factors.
        TL_Y, TL_Y1 = -0.8, 1.05
        x_of = lambda yr: -6.0 + (yr - 1940) * 12.0 / 90
        tl = Line([x_of(1940), TL_Y, 0], [x_of(2030), TL_Y, 0], stroke_color=DIM, stroke_width=2)
        ticks = VGroup()
        for y_ in range(1950, 2030, 10):
            tk = Line([x_of(y_), TL_Y - 0.08, 0], [x_of(y_), TL_Y + 0.08, 0], stroke_color=GREY_,
                      stroke_width=2)
            lb = txt(f"{y_}s", size=24, color=GREY_).move_to([x_of(y_), TL_Y - 0.4, 0])
            ticks.add(VGroup(tk, lb))
        yr = ValueTracker(1940)
        rider = tex("?", size=54, color=YELLOW_).move_to([x_of(1940), TL_Y + 0.46, 0])
        self.play_until(h_(0.6), Create(tl), FadeIn(rider),
                        LaggedStart(*[FadeIn(t, shift=UP * 0.08) for t in ticks], lag_ratio=0.12))
        # fixed mobject updated in place (no always_redraw: avoids Cairo ghosting)
        bar = Line([x_of(1940), TL_Y, 0], [x_of(1941), TL_Y, 0], stroke_width=6).set_color(
            [interpolate_color(BG, ACC, 0.3), ACC])
        bar.add_updater(lambda m: m.set_points_as_corners(
            [[x_of(1940), tl.get_y(), 0], [x_of(yr.get_value()) + 1e-3, tl.get_y(), 0]]))
        rider.add_updater(lambda m: m.move_to([x_of(yr.get_value()), TL_Y + 0.46, 0]))
        self.add(bar, rider)
        self.play_until(h_(0.98), yr.animate.set_value(2020), rate_func=smooth)

        # ============================================================ 5. dichotomy
        d_ = lambda f: self.frac("dichotomy", "L2_end", f)
        x94 = x_of(1994)
        m94 = Dot([x94, TL_Y1, 0], radius=0.09, color=WHITE_)
        l94 = txt("1994 · Dykema, Rădulescu", size=22, color=WHITE_)
        l94.move_to([x94, TL_Y1 + 0.38, 0])
        self.wait_until("dichotomy")
        rider.clear_updaters()
        self.play_until(d_(0.1), VGroup(tl, ticks).animate.shift(UP * (TL_Y1 - TL_Y)),
                        rider.animate.shift(UP * (TL_Y1 - TL_Y)).scale(0.7, about_edge=DOWN))
        self.play_until(d_(0.18), FadeIn(m94, scale=0.3), FadeIn(l94, shift=DOWN * 0.1),
                        rider.animate.set_opacity(0.35))

        # one row of factors, two possible futures
        rowA = row_of_factors(-0.35)
        self.play_until(d_(0.36), LaggedStart(*[
            GrowFromPoint(it, m94.get_center()) for it in rowA], lag_ratio=0.15))

        lab_e = txt("either", size=26, color=GREY_)
        lab_e.next_to(rowA, LEFT, buff=0.35)
        linksA = VGroup(*[tex(r"\cong", size=44).move_to(s) for s in rowA.slots])
        self.wait_until(d_(0.43))
        self.play_until(d_(0.58), FadeIn(lab_e, shift=RIGHT * 0.1),
                        LaggedStart(*[Write(l) for l in linksA], lag_ratio=0.2),
                        *[b.rect.animate.set_fill(ACC, opacity=0.22) for b in rowA.boxes])

        rowB = row_of_factors(-1.9)
        b_cols = [SKY_, PINK_, GOLD_, PURPLE_]
        linksB = VGroup(*[tex(r"\not\cong", size=44).move_to(s) for s in rowB.slots])
        lab_o = txt("or", size=26, color=GREY_)
        lab_o.next_to(rowB, LEFT, buff=0.35).align_to(lab_e, RIGHT)
        self.wait_until(d_(0.76))
        self.play_until(d_(0.86),
                        TransformFromCopy(VGroup(*rowA.boxes, rowA.dots), VGroup(*rowB.boxes, rowB.dots)),
                        FadeIn(lab_o, shift=RIGHT * 0.1))
        self.play_until(d_(0.98), LaggedStart(*[Write(l) for l in linksB], lag_ratio=0.2),
                        *[b.rect.animate.set_stroke(c).set_fill(c, opacity=0.2)
                          for b, c in zip(rowB.boxes, b_cols)])

        # ============================================================ 6. claim
        MID = np.array([-1.35, 0.15, 0])
        card = paper_card("287", width=3.0)
        CARD_POS = np.array([4.95, 0.15, 0])
        card.move_to(CARD_POS + RIGHT * 5.5)
        tag = paper_tag("287", color=ACC)
        c_ = lambda f: self.frac("claim", "invisible", f)
        rowA_all = VGroup(rowA, linksA)
        self.wait_until("claim")
        self.play_until(c_(0.48),
                        card.animate.move_to(CARD_POS),
                        FadeOut(VGroup(rowB, linksB, lab_o, lab_e), shift=DOWN * 0.3),
                        FadeOut(VGroup(tl, ticks, bar, rider, m94, l94, kad)),
                        rowA_all.animate.scale(0.8).move_to(MID),
                        FadeIn(tag, shift=RIGHT * 0.2))
        self.remove(bar)
        self.play_until(c_(0.98),
                        qm.animate.set_opacity(0).shift(UP * 0.25),
                        qc.animate.set_color(YELLOW_).move_to([0, TOP, 0]),
                        box2.rect.animate.set_stroke(YELLOW_), box3.rect.animate.set_stroke(YELLOW_),
                        LaggedStart(*[l.animate.set_color(YELLOW_) for l in linksA], lag_ratio=0.25),
                        *[b.rect.animate.set_stroke(YELLOW_).set_fill(YELLOW_, opacity=0.1)
                          for b in rowA.boxes])

        # ============================================================ 7. invisible
        ban = result_banner(r"L(\mathbb F_2)\cong L(\mathbb F_3)\cong\cdots\cong L(\mathbb F_\infty)",
                            is_tex=True, lean=CATALOG["287"]["lean"], size=48)
        body_old = ban[1][1]
        body = MathTex(r"L(\mathbb F_2)", r"\cong", r"L(\mathbb F_3)", r"\cong", r"\cdots", r"\cong",
                       r"L(\mathbb F_\infty)", font_size=48, color=WHITE_)
        body.move_to(body_old).align_to(body_old, LEFT)
        ban[1].submobjects[1] = body
        ban.move_to(MID)
        i_ = lambda f: self.frac("invisible", "L3_end", f)
        B = rowA.boxes
        self.wait_until("invisible")
        # "with two or more letters": the trees, then they vanish into their algebras
        self.play_until(i_(0.14), *[Indicate(t, color=None, scale_factor=1.15) for t in (f2, f3)])
        self.play_until(i_(0.27), FadeOut(f2, target_position=box2.rect.get_left(), scale=0.2),
                        FadeOut(f3, target_position=box3.rect.get_right(), scale=0.2))
        # the question line drops into the row
        self.play_until(i_(0.37),
                        Transform(VGroup(box2.rect, box2.lab), B[0].copy()),
                        Transform(VGroup(box3.rect, box3.lab), B[1].copy()),
                        Transform(qc, linksA[0].copy()))
        self.remove(box2.rect, box2.lab, box3.rect, box3.lab, qc)
        # ... and the whole row collapses into ONE box
        tg = lambda i: VGroup(body[i].copy())
        anims = [
            Transform(B[0].lab, tg(0)), Transform(linksA[0], tg(1)),
            Transform(B[1].lab, tg(2)), Transform(linksA[1], tg(3)),
            Transform(rowA.dots, tg(4)), Transform(linksA[3], tg(5)),
            Transform(B[3].lab, tg(6)),
            FadeOut(VGroup(B[2].lab, linksA[2]), target_position=body[4].get_center(), scale=0.3),
            Transform(B[0].rect, ban[0].copy()),
        ]
        for b in B[1:]:
            anims.append(Transform(b.rect, ban[0].copy()))
        self.play_until(i_(0.5), *anims)
        self.remove(rowA_all, *[b.rect for b in B])
        self.add(ban[0], body)
        self.play_until(i_(0.57), FadeIn(ban[1][0], shift=DOWN * 0.1))
        self.remove(ban[0], body, ban[1][0])
        self.add(ban)
        gl = glow(ban[0], color=YELLOW_, layers=5, width=16, opacity=0.0)
        self.bring_to_back(gl)
        self.play_until("end-0.55", gl.animate.set_stroke(opacity=0.08),
                        card.animate.shift(UP * 0.08), rate_func=there_and_back)
        self.finish()
