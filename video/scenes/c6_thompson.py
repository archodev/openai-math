import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

from fractions import Fraction as Fr
import re

ACC = PINK_
PIECE_COLS = [SKY_, PURPLE_, PINK_]
AMEN_COL = BLUE_          # "amenable" side
NON_COL = PINK_           # "not amenable" side (where the paper lands)
BND_COL = YELLOW_         # boundary edges
CHUNK_COL = PINK_         # chunk vertices


# ------------------------------------------------------------------ exact dyadic PL maps
class PL:
    """Increasing piecewise-linear map of [0,1] given by its breakpoints (exact)."""

    def __init__(self, pts):
        self.pts = [(Fr(x), Fr(y)) for x, y in pts]

    def __call__(self, x):
        x = Fr(x)
        for (a, fa), (b, fb) in zip(self.pts, self.pts[1:]):
            if a <= x <= b:
                return fa + (fb - fa) * (x - a) / (b - a)
        raise ValueError(x)

    def inv(self):
        return PL([(y, x) for x, y in self.pts])

    def __mul__(self, g):  # composition self o g
        xs = sorted(set([x for x, _ in g.pts] + [g.inv()(x) for x, _ in self.pts]))
        pts = [(x, self(g(x))) for x in xs]
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            (a, fa), (b, fb), (c, fc) = out[-1], pts[i], pts[i + 1]
            if (fb - fa) * (c - b) != (fc - fb) * (b - a):
                out.append(pts[i])
        out.append(pts[-1])
        return PL(out)

    def check(self):
        """Element of Thompson's group F: dyadic breakpoints, slopes in 2^Z."""
        p2 = lambda n: n > 0 and n & (n - 1) == 0
        for (a, fa), (b, fb) in zip(self.pts, self.pts[1:]):
            s = (fb - fa) / (b - a)
            assert s > 0 and p2(s.numerator) and p2(s.denominator), s
        for x, y in self.pts:
            assert p2(x.denominator) and p2(y.denominator)
        assert self.pts[0] == (0, 0) and self.pts[-1] == (1, 1)
        return self


X0 = PL([(0, 0), (Fr(1, 2), Fr(1, 4)), (Fr(3, 4), Fr(1, 2)), (1, 1)]).check()
X1 = PL([(0, 0), (Fr(1, 2), Fr(1, 2)), (Fr(3, 4), Fr(5, 8)), (Fr(7, 8), Fr(3, 4)), (1, 1)]).check()
GHOSTS = [m.check() for m in (X1, X0.inv(), X0 * X0, X1.inv() * X0.inv(), X0 * X1)]


def early(f):
    """rate func: finish within the first fraction f of the animation"""
    return lambda t: smooth(min(1.0, t / f))


def late(f):
    """rate func: start after fraction f of the animation"""
    return lambda t: smooth(max(0.0, (t - f) / (1 - f)))


class C6Thompson(VoiceScene):

    # -------------------------------------------------------------- timing helpers
    def w(self, line, phrase):
        """Estimated start time of `phrase` inside narration line `line`
        (character-proportional, with extra weight for punctuation pauses)."""
        L = self.timing["lines"][line]
        text, s, e = L["text"], L["start"], L["end"]

        def wt(seg):
            seg = re.sub(r"\b(19|20)\d\d\b", "x" * 19, seg)   # years are spoken long
            return (len(seg) + 9 * len(re.findall(r"[:;]", seg)) + 6 * seg.count(",")
                    + 9 * len(re.findall(r"[.?!] ", seg)))
        i = text.index(phrase)
        return s + (e - s) * wt(text[:i]) / wt(text.rstrip(".?!"))

    def seg(self, t0, t1, *anims, min_time=0.25, **kw):
        """Play anims starting at t0 (or now, if later) and ending at t1."""
        self.wait_until(t0)
        rt = self.cue(t1) - self.now
        if rt < min_time:
            print(f"[VoiceScene] c6_thompson seg ending {t1}: only {rt:.2f}s; using {min_time}")
            rt = min_time
        self.play(*anims, run_time=rt, **kw)

    # -------------------------------------------------------------- builders
    def token(self, size):
        """Small 'face' of F: the generator x0 in a card."""
        box = RoundedRectangle(width=size, height=size, corner_radius=0.12 * size,
                               stroke_color=ACC, stroke_width=2, fill_color=CARD, fill_opacity=1)
        a = 0.66 * size
        o = box.get_center() + np.array([-a / 2, -a / 2, 0])
        sq = Square(a, stroke_color=GREY_, stroke_width=1.3, stroke_opacity=0.8).move_to(box)
        pts = [o + a * np.array([float(x), float(y), 0]) for x, y in X0.pts]
        pieces = VGroup(*[Line(p, q, color=ACC, stroke_width=3.2) for p, q in zip(pts, pts[1:])])
        return VGroup(box, sq, pieces)

    def build_tree(self, L, depth):
        dirs = [RIGHT, UP, LEFT, DOWN]
        nodes = [(np.zeros(3), 0, -1, None)]
        frontier = [0]
        for lvl in range(depth):
            nf = []
            for i in frontier:
                p, l, _, din = nodes[i]
                for k, d in enumerate(dirs):
                    if din is not None and k == (din + 2) % 4:
                        continue
                    nodes.append((p + d * L / 2 ** l, l + 1, i, k))
                    nf.append(len(nodes) - 1)
            frontier = nf
        return nodes

    def readout(self, ratio, anchor):
        b = txt("boundary", 26, BND_COL, weight=SEMIBOLD)
        dv = txt("÷", 26, GREY_)
        sz = txt("size", 26, CHUNK_COL, weight=SEMIBOLD)
        eq = txt("=", 26, GREY_)
        num = txt(f"{ratio:.2f}", 28, WHITE_, weight=SEMIBOLD)
        row = VGroup(b, dv, sz, eq, num).arrange(RIGHT, buff=0.14)
        for m in (dv, eq):
            m.align_to(sz, DOWN).shift(UP * 0.02)
        num.align_to(sz, DOWN)
        track = Line(ORIGIN, RIGHT * 2.6, color=DIM, stroke_width=7)
        track.next_to(row, DOWN, buff=0.2).align_to(row, LEFT)
        bar = Line(track.get_start(), track.get_start() + RIGHT * ratio, color=BND_COL,
                   stroke_width=7)
        g = VGroup(row, track, bar)
        g.move_to(anchor)
        g.num, g.bar, g.track = num, bar, track
        return g

    def update_readout(self, ro, ratio):
        """Odometer-style swap of the ratio + bar resize. Call settle() after the play."""
        old = ro.num
        new = txt(f"{ratio:.2f}", 28, WHITE_, weight=SEMIBOLD).move_to(old, aligned_edge=LEFT)
        ro[0].remove(old)
        ro.num = new
        self._pending = getattr(self, "_pending", []) + [(ro, new)]
        s = ro.track.get_start()
        return [FadeOut(old, shift=UP * 0.16), FadeIn(new, shift=UP * 0.16),
                ro.bar.animate.put_start_and_end_on(s, s + RIGHT * ratio * ro.track.get_length() / 2.6)]

    def settle(self):
        for ro, new in getattr(self, "_pending", []):
            ro[0].add(new)
            self.add(ro)
        self._pending = []

    # -------------------------------------------------------------- scene
    def construct(self):
        w = self.w

        # ============================== A. bent-line maps (cue: maps) =========
        S = 4.4
        O = np.array([-5.45, -2.5, 0])

        def P(x, y):
            return O + S * np.array([float(x), float(y), 0])

        title = serif("Thompson's group F", 50).to_corner(UL, buff=0.5).shift(RIGHT * 0.25)
        frame = Square(S, stroke_color=GREY_, stroke_width=2).move_to(P(0.5, 0.5))
        gridl = VGroup(*[Line(P(k / 4, 0), P(k / 4, 1)) for k in (1, 2, 3)],
                       *[Line(P(0, k / 4), P(1, k / 4)) for k in (1, 2, 3)])
        gridl.set_stroke(DIM, 1.2, opacity=0.55)
        diag = DashedLine(P(0, 0), P(1, 1), dash_length=0.07, stroke_width=1.5, color=DIM)
        lab0 = tex("0", 30, GREY_).next_to(P(0, 0), DOWN, buff=0.18)
        labx1 = tex("1", 30, GREY_).next_to(P(1, 0), DOWN, buff=0.18)
        laby1 = tex("1", 30, GREY_).next_to(P(0, 1), LEFT, buff=0.18)
        axes = VGroup(gridl, frame, lab0, labx1, laby1)

        pts = [P(x, y) for x, y in X0.pts]
        curve = VMobject(stroke_color=ACC, stroke_width=5).set_points_as_corners(pts)
        pieces = VGroup(*[Line(p, q, stroke_width=5, color=ACC) for p, q in zip(pts, pts[1:])])
        ghosts = VGroup(*[VMobject(stroke_color=GREY_, stroke_width=2.4, stroke_opacity=0.5)
                          .set_points_as_corners([P(x, y) for x, y in g.pts]) for g in GHOSTS])
        x0lab = tex("x_0", 40, ACC).move_to(P(0.3, 0.72))

        # mapping diagram on the right: the interval [0,1] and its image under x0
        XL, XR, YT, YB = 0.95, 6.3, 1.05, -1.55
        Wd = XR - XL

        def Q(x, y):
            return np.array([XL + Wd * float(x), y, 0])

        brk_in = [x for x, _ in X0.pts]
        brk_out = [y for _, y in X0.pts]
        top_track = Line(Q(0, YT), Q(1, YT), color=DIM, stroke_width=9)
        bot_track = Line(Q(0, YB), Q(1, YB), color=DIM, stroke_width=9)
        top_segs = VGroup(*[Line(Q(a, YT), Q(b, YT), color=DIM, stroke_width=9)
                            for a, b in zip(brk_in, brk_in[1:])])
        bot_segs = VGroup(*[Line(Q(a, YB), Q(b, YB), color=c, stroke_width=9)
                            for (a, b), c in zip(zip(brk_out, brk_out[1:]), PIECE_COLS)])

        def ticks(xs, y, labels, up):
            g = VGroup()
            for x, s in zip(xs, labels):
                tk = Line(Q(x, y) + DOWN * 0.13, Q(x, y) + UP * 0.13, color=GREY_, stroke_width=2)
                lb = tex(s, 30 if len(s) == 1 else 32, GREY_).next_to(tk, UP if up else DOWN, buff=0.1)
                g.add(VGroup(tk, lb))
            return g

        top_ends = ticks([0, 1], YT, ["0", "1"], True)
        top_mid = ticks([Fr(1, 2), Fr(3, 4)], YT, [r"\frac12", r"\frac34"], True)
        bot_ticks = ticks([0, Fr(1, 4), Fr(1, 2), 1], YB,
                          ["0", r"\frac14", r"\frac12", "1"], False)
        dy = (YT - YB) / 2
        top_grp = VGroup(top_track, top_segs, top_ends, top_mid)
        top_grp.shift(DOWN * dy)
        quads = VGroup(*[Polygon(Q(a, YT), Q(b, YT), Q(d, YB), Q(c, YB), stroke_width=0,
                                 fill_color=col, fill_opacity=0.16)
                         for a, b, c, d, col in zip(brk_in, brk_in[1:], brk_out, brk_out[1:], PIECE_COLS)])
        arrow = Arrow(Q(0, YT) + LEFT * 0.42 + DOWN * 0.12, Q(0, YB) + LEFT * 0.42 + UP * 0.12,
                      buff=0, stroke_width=3, color=ACC, max_tip_length_to_length_ratio=0.08)
        arrow_lab = tex("x_0", 34, ACC).next_to(arrow, LEFT, buff=0.1)

        stretch_src = [r"\times\frac12", r"\times 1", r"\times 2"]
        stretch_pow = [r"\times 2^{-1}", r"\times 2^{0}", r"\times 2^{1}"]
        mids = [(Q((a + b) / 2, YT) + Q((c + d) / 2, YB)) / 2 + DOWN * 0.05
                for a, b, c, d in zip(brk_in, brk_in[1:], brk_out, brk_out[1:])]
        stretch = VGroup(*[tex(s, 38, c).move_to(m) for s, c, m in zip(stretch_src, PIECE_COLS, mids)])
        stretch2 = VGroup(*[tex(s, 38, c).move_to(m) for s, c, m in zip(stretch_pow, PIECE_COLS, mids)])

        # breakpoints + guides on the graph
        bpts = [(Fr(1, 2), Fr(1, 4)), (Fr(3, 4), Fr(1, 2))]
        bdots = VGroup(*[Dot(P(x, y), radius=0.085, color=YELLOW_) for x, y in bpts])
        guides = VGroup(*[VGroup(DashedLine(P(x, y), P(x, 0), dash_length=0.08, stroke_width=2, color=YELLOW_),
                                 DashedLine(P(x, y), P(0, y), dash_length=0.08, stroke_width=2, color=YELLOW_))
                          for x, y in bpts])
        xl = VGroup(tex(r"\frac12", 34, YELLOW_).next_to(P(0.5, 0), DOWN, buff=0.16),
                    tex(r"\frac34", 34, YELLOW_).next_to(P(0.75, 0), DOWN, buff=0.16))
        yl = VGroup(tex(r"\frac14", 32, GREY_).next_to(P(0, 0.25), LEFT, buff=0.16),
                    tex(r"\frac12", 32, GREY_).next_to(P(0, 0.5), LEFT, buff=0.16))
        slope_pos = [P(0.41, 0.095), P(0.70, 0.29), P(0.955, 0.6)]
        slopes = VGroup(*[tex(s, 34, c).move_to(p)
                          for s, c, p in zip([r"\frac12", "1", "2"], PIECE_COLS, slope_pos)])

        # ---- 0.0: hook — title + axes
        self.play(Write(title, run_time=1.1), Create(frame, run_time=1.0),
                  FadeIn(gridl, run_time=1.0), FadeIn(VGroup(lab0, labx1, laby1), run_time=1.0))
        # ---- "made of bent-line maps": many elements of F, then x0 in front
        t_maps = w(0, "bent-line")
        self.seg(self.now, t_maps + 0.45,
                 LaggedStart(*[Create(g) for g in ghosts], lag_ratio=0.18),
                 Create(diag))
        t_int = w(0, "interval")
        self.seg(self.now, t_int + 0.4, Create(curve), FadeIn(x0lab, shift=UP * 0.1))
        # ---- "of an interval": the interval appears on the right
        self.add(pieces)
        self.remove(curve)
        t_str = w(0, "straight")
        self.seg(self.now, t_str - 0.02,
                 ghosts.animate.set_stroke(opacity=0.0),
                 GrowFromEdge(top_track, LEFT), FadeIn(top_ends))
        self.remove(ghosts)
        # ---- "straight pieces": the three pieces light up one by one
        self.add(top_segs)
        t_bends = w(0, "bends")
        anims = []
        for i in range(3):
            anims.append(AnimationGroup(
                pieces[i].animate.set_color(PIECE_COLS[i]).set_stroke(width=7),
                top_segs[i].animate.set_color(PIECE_COLS[i])))
        self.seg(self.now, t_bends, LaggedStart(*anims, lag_ratio=0.45))
        # ---- "bends at points like one half or three quarters"
        self.play(*[p.animate.set_stroke(width=5) for p in pieces], run_time=0.3)
        t_half, t_3q = w(0, "one half"), w(0, "three quarters")
        self.seg(t_half - 0.25, t_half + 0.45, GrowFromCenter(bdots[0]), Create(guides[0]),
                 FadeIn(xl[0], shift=UP * 0.1), FadeIn(yl[0]), FadeIn(top_mid[0], shift=DOWN * 0.1))
        self.seg(t_3q - 0.2, t_3q + 0.5, GrowFromCenter(bdots[1]), Create(guides[1]),
                 FadeIn(xl[1], shift=UP * 0.1), FadeIn(yl[1]), FadeIn(top_mid[1], shift=DOWN * 0.1))
        # ---- "slopes that are powers of two": the interval splits; its image is
        #      squeezed (x1/2), kept (x1) and stretched (x2)
        t_slopes = w(0, "slopes")
        t_pow = w(0, "powers")
        movers = top_segs.copy()
        self.seg(t_slopes - 0.3, t_slopes + 0.45,
                 top_grp.animate.shift(UP * dy), Transform(movers, bot_segs),
                 FadeIn(bot_ticks, rate_func=late(0.4)))
        self.seg(self.now, t_pow + 0.1,
                 FadeIn(quads), GrowArrow(arrow), FadeIn(arrow_lab),
                 LaggedStart(*[FadeIn(m, scale=0.7) for m in stretch], lag_ratio=0.25),
                 LaggedStart(*[FadeIn(m, scale=0.7) for m in slopes], lag_ratio=0.25))
        self.seg(self.now, "L0_end+0.15", *[TransformMatchingShapes(a, b) for a, b in zip(stretch, stretch2)],
                 *[Indicate(m, scale_factor=1.15, color=m.get_color()) for m in slopes])

        # ============================== B. the question (cue: amen) ============
        T_big = self.token(2.3).move_to(UP * 0.95)
        mapping = VGroup(top_track, top_segs, top_ends, top_mid, bot_ticks, quads,
                         movers, stretch2, arrow, arrow_lab)
        self.wait_until("amen")
        box = T_big[0]
        box.save_state()
        box.set_fill(opacity=0).set_stroke(opacity=0)
        self.add(box)
        self.bring_to_back(box)
        self.play(FadeOut(mapping, shift=RIGHT * 0.3, rate_func=early(0.5)),
                  FadeOut(title, shift=UP * 0.3, rate_func=early(0.5)),
                  FadeOut(VGroup(gridl, lab0, labx1, laby1, diag, bdots, guides, xl, yl, slopes, x0lab),
                          rate_func=early(0.4)),
                  ReplacementTransform(frame, T_big[1], rate_func=late(0.2)),
                  ReplacementTransform(pieces, T_big[2], rate_func=late(0.2)),
                  Restore(box, rate_func=late(0.55)),
                  run_time=1.2)
        self.remove(T_big[0], T_big[1], T_big[2])
        self.add(T_big)
        tok = T_big
        open_cap = caps("open since 1979", 24, GREY_, spacing=0.05).next_to(tok, DOWN, buff=0.55)
        t_open = w(1, "open since")
        self.seg(t_open - 0.1, t_open + 0.7, FadeIn(open_cap, shift=UP * 0.12),
                 tok.animate.scale(1.03))
        question = serif("Is F amenable?", 60).next_to(open_cap, DOWN, buff=0.45)
        t_is = w(1, "is it amenable")
        self.seg(t_is - 0.15, "grid-0.05", Write(question), tok.animate.scale(1 / 1.03))

        # ============================== C. Følner intuition (cue: grid) =========
        N, s = 20, 0.24
        gO = np.array([-N * s / 2, -N * s / 2 - 0.25, 0])

        def G(i, j):
            return gO + s * np.array([i, j, 0])

        def lat_line(a, b, off):
            ln = Line(a, b)
            op = 1 - 0.7 * off ** 2
            ln.set_stroke(color=[BG, DIM, DIM, DIM, DIM, BG], width=1.6, opacity=op)
            return ln

        lattice = VGroup(*[lat_line(G(i, 0), G(i, N), abs(i - N / 2) / (N / 2)) for i in range(N + 1)],
                         *[lat_line(G(0, j), G(N, j), abs(j - N / 2) / (N / 2)) for j in range(N + 1)])
        c = N // 2

        def chunk_parts(n):
            lo, hi = c - (n - 1) // 2, c + (n - 1) // 2
            fill = Rectangle(width=n * s, height=n * s, stroke_width=0, fill_color=CHUNK_COL,
                             fill_opacity=0.13).move_to((G(lo, lo) + G(hi, hi)) / 2)
            ks = range(lo, hi + 1)
            stubs = VGroup(VGroup(*[Line(G(lo, k), G(lo - 1, k)) for k in ks]),
                           VGroup(*[Line(G(hi, k), G(hi + 1, k)) for k in ks]),
                           VGroup(*[Line(G(k, lo), G(k, lo - 1)) for k in ks]),
                           VGroup(*[Line(G(k, hi), G(k, hi + 1)) for k in ks]))
            stubs.set_stroke(BND_COL, 4.0)
            ring = VGroup(*[Dot(G(i, j), radius=0.045, color=CHUNK_COL)
                            for i in range(lo, hi + 1) for j in range(lo, hi + 1)
                            if max(abs(i - c), abs(j - c)) == (n - 1) // 2])
            return fill, stubs, ring

        hq = serif("Is F amenable?", 40).move_to(UP * 3.22)
        header = VGroup(self.token(0.62).next_to(hq, LEFT, buff=0.38), hq)
        sizes = [3, 5, 7, 9, 11, 13]
        fill, stubs, ring = chunk_parts(sizes[0])
        inner = chunk_parts(1)[2]
        dots = VGroup(*inner, *ring)
        g_ro = self.readout(4 / sizes[0], np.array([0, -3.2, 0]))
        self.wait_until("grid")
        self.play(ReplacementTransform(tok, header[0]), ReplacementTransform(question, header[1]),
                  FadeOut(open_cap),
                  LaggedStart(*[Create(l) for l in lattice], lag_ratio=0.02),
                  run_time=1.0)
        self.play(FadeIn(fill), LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.05),
                  LaggedStart(*[Create(l) for side in stubs for l in side], lag_ratio=0.03),
                  FadeIn(g_ro, shift=UP * 0.1), run_time=0.7)
        gridp = VGroup(lattice, fill, dots, stubs)
        self.add(gridp)
        t_grid_end = min(w(1, "on a grid") + 0.1, self.cue("tree") - 0.55)
        step_t = (t_grid_end - self.now) / (len(sizes) - 1)
        for n in sizes[1:]:
            nf, ns, nr = chunk_parts(n)
            self.play(Transform(fill, nf), *[Transform(a, b) for a, b in zip(stubs, ns)],
                      LaggedStart(*[GrowFromCenter(d) for d in nr], lag_ratio=0.01),
                      *self.update_readout(g_ro, 4 / n),
                      run_time=step_t, rate_func=smooth)
            dots.add(*nr)
            self.add(gridp)
            self.settle()
        to0 = tex(r"\to 0", 34, BND_COL).next_to(g_ro[0], RIGHT, buff=0.2)
        self.seg(self.now, "tree-0.02", Write(to0))
        g_ro.add(to0)
        self.add(g_ro)

        # ---- tree: the 4-regular tree (same local picture, exponential growth)
        Lt = 1.03
        nodes = self.build_tree(Lt, 5)
        tC = np.array([3.55, -0.3, 0])
        skel = VGroup()
        edge_of = {}
        for idx, (p, l, par, _) in enumerate(nodes):
            if par < 0:
                continue
            ln = Line(nodes[par][0] + tC, p + tC, stroke_width=2.6 * 0.8 ** (l - 1),
                      color=DIM, stroke_opacity=0.95)
            edge_of[idx] = ln
            skel.add(ln)

        def t_edge(i, kind):
            l = nodes[i][1]
            if kind == "in":
                return edge_of[i].copy().set_stroke(CHUNK_COL, opacity=1, width=3.0 * 0.8 ** (l - 1))
            return edge_of[i].copy().set_stroke(BND_COL, opacity=1, width=4.6 * 0.8 ** (l - 1))

        def t_dot(i):
            return Dot(nodes[i][0] + tC, radius=0.075 * 0.78 ** nodes[i][1], color=CHUNK_COL)

        def at_level(l):
            return [i for i in range(len(nodes)) if nodes[i][1] == l]

        def ratio_tree(r):      # ball of radius r: 2*3^r - 1 vertices, 4*3^r edges leaving
            return 4 * 3 ** r / (2 * 3 ** r - 1)

        gL = np.array([-3.55, -0.3, 0])
        by_level = [VGroup(*[edge_of[i] for i in edge_of if nodes[i][1] == l]) for l in range(1, 6)]
        t_ro = self.readout(ratio_tree(1), np.array([3.55, -3.2, 0]))
        t0, t1 = self.cue("tree"), self.cue("both") + 0.08
        span = t1 - t0
        self.wait_until("tree")
        self.play(gridp.animate.scale(0.85).move_to(gL),
                  g_ro.animate.move_to(np.array([gL[0], -3.2, 0])),
                  LaggedStart(*[Create(g) for g in by_level], lag_ratio=0.3),
                  run_time=0.36 * span)
        ins = VGroup(*[t_edge(i, "in") for i in at_level(1)])
        bnd = VGroup(*[t_edge(i, "bnd") for i in at_level(2)])
        dts = VGroup(*[t_dot(i) for i in at_level(0) + at_level(1)])
        self.play(FadeIn(dts), Create(ins), Create(bnd), FadeIn(t_ro, shift=UP * 0.1),
                  run_time=0.2 * span)
        treep = VGroup(skel, ins, bnd, dts)
        self.add(treep)
        ge2 = tex(r"\geq 2", 34, BND_COL).next_to(t_ro[0], RIGHT, buff=0.2)
        for r in (2, 3):
            # the old boundary edges join the chunk; new boundary edges sprout outward
            old = list(bnd.submobjects)
            new_b = [t_edge(i, "bnd") for i in at_level(r + 1)]
            new_d = [t_dot(i) for i in at_level(r)]
            extra = [Write(ge2)] if r == 3 else []
            self.seg(self.now, t0 + (0.76 if r == 2 else 0.98) * span,
                     *[e.animate.set_stroke(CHUNK_COL, width=3.0 * 0.8 ** (r - 1)) for e in old],
                     LaggedStart(*[GrowFromCenter(d) for d in new_d], lag_ratio=0.02),
                     LaggedStart(*[Create(e) for e in new_b], lag_ratio=0.01),
                     *self.update_readout(t_ro, ratio_tree(r)), *extra)
            bnd.remove(*old)
            ins.add(*old)
            bnd.add(*new_b)
            dts.add(*new_d)
            self.add(treep)
            self.settle()
        t_ro.add(ge2)
        self.add(t_ro)

        # ============================== D. claims both ways (cue: both) =========
        rowY = 2.42
        lab_am = bold("AMENABLE", 24, AMEN_COL).move_to(np.array([gL[0], rowY, 0]))
        lab_non = bold("NOT AMENABLE", 24, NON_COL).move_to(np.array([tC[0], rowY, 0]))
        track = Line(lab_am.get_right() + RIGHT * 0.3, lab_non.get_left() + LEFT * 0.3,
                     color=DIM, stroke_width=3)
        tok = header[0]
        self.seg("both", "both+0.6",
                 FadeIn(lab_am, shift=DOWN * 0.1), FadeIn(lab_non, shift=DOWN * 0.1), Create(track),
                 tok.animate(path_arc=PI / 3).scale(1.25).move_to(np.array([0, rowY, 0])),
                 gridp.animate.fade(0.6), treep.animate.fade(0.5))

        def claim_chip(name, year, col):
            t = VGroup(txt(name, 22, WHITE_, weight=SEMIBOLD), txt(year, 22, col, weight=BOLD)).arrange(RIGHT, buff=0.16)
            box = RoundedRectangle(width=t.width + 0.36, height=t.height + 0.26, corner_radius=0.1,
                                   stroke_color=col, stroke_width=1.6, fill_color=CARD, fill_opacity=0.96)
            t.move_to(box)
            return VGroup(box, t)

        cl = [claim_chip("Shavgulidze", "2009", AMEN_COL).move_to(np.array([gL[0], 1.5, 0])),
              claim_chip("Moore", "2012", AMEN_COL).move_to(np.array([gL[0], 0.8, 0])),
              claim_chip("Akhmedov", "2021", NON_COL).move_to(np.array([tC[0], 1.5, 0]))]
        nudges = [-0.6, -1.1, 0.8]
        t_claim = self.cue("claim")
        slot = (t_claim - 0.4 - self.now) / 3
        for chp, dx in zip(cl, nudges):
            self.play(GrowFromPoint(chp, tok.get_center()),
                      tok.animate.move_to(np.array([dx, rowY, 0])),
                      run_time=max(0.3, slot), rate_func=smooth)
        self.seg(self.now, "claim", tok.animate.move_to(np.array([0, rowY, 0])))

        # ============================== E. the paper (cue: claim) ==============
        card = paper_card("248", width=2.9)
        card.move_to(np.array([-3.0, 0.78, 0]))
        card_target = card.get_center()
        card.shift(LEFT * 4.8)
        tag = paper_tag("248", color=ACC)
        tree_tgt = np.array([2.8, 0.42, 0])
        tok_size = tok.width * 0.8
        row_w = tok_size + 0.38 + lab_non.width
        tok_tgt = np.array([2.8 - row_w / 2 + tok_size / 2, 2.98, 0])
        lab_tgt = np.array([2.8 + row_w / 2 - lab_non.width / 2, 2.98, 0])
        self.add(card)
        self.seg("claim", "claim+1.0",
                 FadeOut(VGroup(*cl, lab_am, track, hq), rate_func=early(0.45)),
                 FadeOut(gridp, shift=DOWN * 0.3, rate_func=early(0.45)),
                 FadeOut(g_ro, shift=DOWN * 0.3, rate_func=early(0.4)),
                 FadeOut(t_ro, shift=DOWN * 0.3, rate_func=early(0.4)),
                 treep.animate.fade(-1.0).scale(0.8).move_to(tree_tgt),
                 lab_non.animate.move_to(lab_tgt),
                 tok.animate.scale(0.8).move_to(tok_tgt),
                 card.animate.move_to(card_target),
                 FadeIn(tag, shift=RIGHT * 0.2, rate_func=late(0.45)))
        geo = txt("as Geoghegan conjectured in 1979", 22, GREY_).move_to(np.array([2.8, 2.48, 0]))
        banner = result_banner("Thompson's group F is not amenable", lean=CATALOG["248"]["lean"], size=32)
        banner.move_to(np.array([0, -2.15, 0]))
        t_no = w(2, "says no")
        self.seg(max(self.now, t_no - 0.1), max(self.now, t_no - 0.1) + 0.5,
                 Indicate(lab_non, color=NON_COL, scale_factor=1.08),
                 tok.animate(rate_func=there_and_back).scale(1.1))
        t_ban = max(self.now, w(2, "Thompson's group F is not") - 0.45)
        self.seg(t_ban, t_ban + 0.6, FadeIn(banner, shift=UP * 0.2), FadeIn(geo, shift=UP * 0.08))
        # living hold: the tree's boundary breathes, the card drifts a touch
        hold = self.narr_end - 0.5 - self.now
        if hold > 0.3:
            bnd_now = treep[2]
            self.play(card.animate.scale(1.025),
                      bnd_now.animate.set_stroke(opacity=0.45),
                      run_time=hold, rate_func=there_and_back)
        self.finish()
