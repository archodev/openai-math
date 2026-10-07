import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

# Unique Games Conjecture spotlight (family 102).
ACC = GREEN_
LAB = [BLUE_, PINK_, GOLD_, PURPLE_]      # the k = 4 labels a node may pick
R = 0.22                                  # node radius

# A 12-node network (hand-placed, planar drawing) used throughout.
P0 = {0: (-5.6, 1.5), 1: (-3.9, 2.3), 2: (-2.2, 1.7), 3: (-0.4, 2.2),
      4: (-4.7, 0.0), 5: (-2.9, 0.2), 6: (-1.1, 0.3), 7: (0.6, 0.3),
      8: (-5.5, -1.7), 9: (-3.6, -1.8), 10: (-1.8, -1.5), 11: (0.1, -1.8)}
EDGES = [(0, 1), (0, 4), (1, 2), (2, 3), (2, 5), (2, 6), (3, 6), (3, 7), (4, 5), (5, 6),
         (6, 7), (4, 8), (8, 9), (5, 9), (9, 10), (5, 10), (10, 11), (6, 11), (7, 11)]
EIDX = {e: k for k, e in enumerate(EDGES)}
U, V = 6, 7                                # the link whose rule we zoom into
PI_UV = {0: 2, 1: 0, 2: 3, 3: 1}           # its permutation: label of u -> label of v
# Planted labelling: every rule is consistent with it except on BAD.
PLANT = {0: 2, 1: 0, 2: 3, 3: 2, 4: 3, 5: 2, 6: 1, 7: 0, 8: 1, 9: 0, 10: 1, 11: 3}
BAD = (8, 9)
# Second network ("only 1% satisfiable"): its best labelling, only one link satisfied.
NO_LAB = {0: 1, 1: 3, 2: 0, 3: 2, 4: 2, 5: 0, 6: 3, 7: 1, 8: 2, 9: 3, 10: 0, 11: 1}
NO_GOOD = (4, 5)
# Max-Cut: an optimal split (15 of 19 links cut), as two columns.
COL0 = [0, 2, 5, 7, 11, 8]     # team A (top to bottom)
COL1 = [1, 3, 6, 4, 10, 9]     # team B
TEAM_C = [BLUE_, PINK_]


def v3(p):
    return np.array([p[0], p[1], 0.0])


def make_net(pos, r=R, edge_w=3.0):
    edges = VGroup(*[Line(v3(pos[a]), v3(pos[b]), stroke_color=DIM, stroke_width=edge_w)
                     for a, b in EDGES])
    nodes = VGroup(*[Circle(radius=r, stroke_color=GREY_, stroke_width=3, fill_color=CARD,
                            fill_opacity=1).move_to(v3(pos[i])) for i in range(12)])
    edges.set_z_index(1)
    nodes.set_z_index(3)
    return edges, nodes


def bfs_layers(start):
    adj = {i: [] for i in range(12)}
    for a, b in EDGES:
        adj[a].append(b)
        adj[b].append(a)
    seen = set(start)
    frontier = list(start)
    layers, tree = [], set()
    while frontier:
        nxt, layer = [], []
        for p in frontier:
            for c in adj[p]:
                if c not in seen:
                    seen.add(c)
                    nxt.append(c)
                    layer.append((p, c))
                    tree.add(tuple(sorted((p, c))))
        if layer:
            layers.append(layer)
        frontier = nxt
    return layers, tree


def gauge(x0, x1, y, frac, flip=False):
    """Horizontal gauge: green (efficient) up to `frac`, red (NP-hard) beyond."""
    xb = x0 + frac * (x1 - x0)
    axis = Line([x0, y, 0], [x1, y, 0], stroke_color=GREY_, stroke_width=2.5)
    g = Line([x0, y, 0], [xb, y, 0], stroke_color=GREEN_, stroke_width=14, stroke_opacity=0.85)
    r = Line([xb, y, 0], [x1, y, 0], stroke_color=RED_, stroke_width=14, stroke_opacity=0.85)
    mk = Line([xb, y + 0.26, 0], [xb, y - 0.26, 0], stroke_color=YELLOW_, stroke_width=4)
    end = Line([x1, y + 0.16, 0], [x1, y - 0.16, 0], stroke_color=GREY_, stroke_width=2.5)
    return VGroup(axis, g, r, mk, end)


class C4Ugc(VoiceScene):

    # estimated time of a phrase inside a narration segment (char-proportional)
    def tw(self, phrase, a, a_words, b, b_words=None, fallback=0.5):
        ta, tb = self.cue(a), self.cue(b)
        for ln in self.timing.get("lines", []):
            text = ln["text"]
            if a_words in text:
                i0 = text.index(a_words)
                ip = text.find(phrase, i0)
                i1 = text.find(b_words, i0) if b_words else len(text)
                if ip >= 0 and i1 > i0:
                    return ta + (ip - i0) / (i1 - i0) * (tb - ta)
        return ta + fallback * (tb - ta)

    def construct(self):
        # ============================================================ 1. the game
        edges, nodes = make_net(P0)
        net = VGroup(edges, nodes)
        self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes], lag_ratio=0.07),
                  LaggedStart(*[Create(e) for e in edges], lag_ratio=0.05), run_time=1.8)

        # "every node must pick a label": palette of k = 4 labels
        t_label = self.tw("pick a label", "graph", "Picture", "rule", "if you pick", 0.3)
        t_link = self.tw("every link", "graph", "Picture", "rule", "if you pick", 0.65)
        dots = VGroup(*[Circle(radius=0.17, stroke_color=c, stroke_width=2, fill_color=c,
                               fill_opacity=1) for c in LAB]).arrange(RIGHT, buff=0.24)
        pal_lab = txt("labels", 26, GREY_)
        pal = VGroup(pal_lab, dots).arrange(RIGHT, buff=0.3).move_to([4.3, 2.75, 0])
        self.wait_until(max(self.now, t_label - 0.2))
        self.play(FadeIn(pal_lab, shift=LEFT * 0.2),
                  LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.15),
                  LaggedStart(*[Indicate(n, scale_factor=1.25, color=LAB[i % 4])
                                for i, n in enumerate(nodes)], lag_ratio=0.06),
                  run_time=min(1.3, max(0.6, t_link - self.now - 0.05)))
        # "every link carries a rule": a pulse runs along every link
        self.wait_until(max(self.now, t_link))
        self.play(LaggedStart(*[ShowPassingFlash(e.copy().set_stroke(WHITE_, 5).set_z_index(2),
                                                 time_width=0.6) for e in edges], lag_ratio=0.04),
                  run_time=min(1.0, max(0.4, self.cue("rule") - 0.45 - self.now)))

        # zoom into the rule on link u-v
        pu, pv = v3(P0[U]), v3(P0[V])
        lu = tex("u", 34, GREY_).move_to(pu + np.array([-0.38, -0.36, 0]))
        lv = tex("v", 34, GREY_).move_to(pv + np.array([0.42, 0.0, 0]))
        box = RoundedRectangle(width=2.95, height=1.12, corner_radius=0.14, stroke_color=WHITE_,
                               stroke_width=2).move_to([(-1.7 + 1.25) / 2, 0.2, 0])
        card = RoundedRectangle(width=3.8, height=4.4, corner_radius=0.16, stroke_color=GREY_,
                                stroke_width=1.5, fill_color=CARD, fill_opacity=0.96).move_to([4.3, -0.25, 0])
        conn = VGroup(Line(box.get_corner(UR), card.get_corner(UL), stroke_color=GREY_, stroke_width=1.5),
                      Line(box.get_corner(DR), card.get_corner(DL), stroke_color=GREY_, stroke_width=1.5))
        conn.set_stroke(opacity=0.6)
        head = bold("RULE ON THIS LINK", 22, GREY_).move_to(card.get_top() + DOWN * 0.38)
        xl, xr = 3.35, 5.25
        ys = [0.6, 0.05, -0.5, -1.05]
        ldots = VGroup(*[Circle(radius=0.17, stroke_color=c, stroke_width=2, fill_color=c, fill_opacity=1)
                         .move_to([xl, y, 0]) for c, y in zip(LAB, ys)])
        rdots = VGroup(*[Circle(radius=0.17, stroke_color=c, stroke_width=2, fill_color=c, fill_opacity=1)
                         .move_to([xr, y, 0]) for c, y in zip(LAB, ys)])
        cu = tex("u", 34, GREY_).next_to(ldots, UP, buff=0.2)
        cv = tex("v", 34, GREY_).next_to(rdots, UP, buff=0.2)
        arrows = VGroup(*[Arrow(ldots[i].get_center(), rdots[PI_UV[i]].get_center(), buff=0.31,
                                stroke_width=3.5, tip_length=0.17, color=GREY_,
                                max_tip_length_to_length_ratio=0.2) for i in range(4)])
        formula = tex(r"a(v) = \pi\big(a(u)\big)", 38).move_to([4.3, -1.87, 0])
        rule_card = VGroup(card, head, cu, cv, ldots, rdots, arrows, formula)
        self.wait_until(max(self.now, self.cue("rule") - 0.45))
        self.play(Create(box), FadeIn(lu), FadeIn(lv), edges[EIDX[(U, V)]].animate.set_stroke(WHITE_, 4),
                  run_time=0.4)
        self.play(Create(conn), FadeIn(card), FadeIn(head), FadeIn(cu), FadeIn(cv),
                  LaggedStart(*[GrowFromCenter(d) for d in [*ldots, *rdots]], lag_ratio=0.05),
                  LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.12),
                  FadeIn(formula), run_time=0.7)
        self.wait_until(max(self.now, self.cue("rule") + 0.3))

        # "if you pick this ..."
        a_u = 1
        ring_l = Circle(radius=0.27, stroke_color=WHITE_, stroke_width=3).move_to(ldots[a_u])
        ring_r = Circle(radius=0.27, stroke_color=WHITE_, stroke_width=3).move_to(rdots[PI_UV[a_u]])
        self.play(nodes[U].animate.set_fill(LAB[a_u], 1).set_stroke(LAB[a_u]), Create(ring_l),
                  run_time=0.45)
        # "... your neighbor must pick exactly that"
        t_nb = self.tw("your neighbor", "rule", "if you pick", "unique", "One choice", 0.35)
        self.wait_until(max(self.now, t_nb))
        a_v = PI_UV[a_u]
        self.play(*[arrows[i].animate.set_opacity(0.2) for i in range(4) if i != a_u],
                  arrows[a_u].animate.set_color(WHITE_).set_stroke(width=5),
                  run_time=0.4)
        self.play(Create(ring_r), nodes[V].animate.set_fill(LAB[a_v], 1).set_stroke(LAB[a_v]),
                  ShowPassingFlash(Line(pu, pv).set_stroke(LAB[a_v], 8).set_z_index(2), time_width=0.7),
                  run_time=0.6)
        self.play(edges[EIDX[(U, V)]].animate.set_stroke(GREEN_, 4.5), run_time=0.35)

        # "one choice forces a unique answer next door": propagate
        layers, tree = bfs_layers([U, V])
        t0, t1 = self.cue("unique"), self.tw("That's a unique", "unique", "One choice", "L0_end", None, 0.62)
        self.wait_until(t0)
        d = max(0.35, (t1 - t0 - 1.1) / len(layers))
        self.play(FadeOut(VGroup(box, conn, lu, lv)), run_time=0.3)
        for k, layer in enumerate(layers):
            fl = [ShowPassingFlash(Line(v3(P0[p]), v3(P0[c])).set_stroke(LAB[PLANT[c]], 8).set_z_index(2),
                                   time_width=0.8) for p, c in layer]
            self.play(*fl, run_time=(d - 0.3 if k == 0 else d) * 0.55)
            self.play(*[nodes[c].animate.set_fill(LAB[PLANT[c]], 1).set_stroke(LAB[PLANT[c]])
                        for _, c in layer],
                      *[edges[EIDX[tuple(sorted(e))]].animate.set_stroke(GREEN_, 4.5) for e in layer],
                      run_time=(d - 0.3 if k == 0 else d) * 0.45)
        # remaining links: check the rule
        rest = [e for e in EDGES if e not in tree and e != (U, V)]
        self.play(LaggedStart(*[edges[EIDX[e]].animate.set_stroke(RED_ if e == BAD else GREEN_, 4.5)
                                for e in rest], lag_ratio=0.12), run_time=0.7)
        title = serif("Unique Game", 52).to_corner(UL, buff=0.45).shift(DOWN * 0.05)
        self.wait_until(max(self.now, t1 - 0.1))
        self.play(Write(title), Wiggle(edges[EIDX[BAD]], scale_value=1.15, rotation_angle=0.03 * TAU),
                  run_time=0.9)

        # ============================================================ 2. the conjecture
        PL, PR = np.array([-4.3, -0.6, 0]), np.array([4.3, -0.6, 0])
        pw, ph = 4.3, 3.15
        s = min((pw - 0.4) / net.width, (ph - 0.35) / net.height)

        def panel(center, color):
            return RoundedRectangle(width=pw, height=ph, corner_radius=0.16, stroke_color=color,
                                    stroke_width=1.6, stroke_opacity=0.6, fill_color=CARD,
                                    fill_opacity=0.55).move_to(center)

        def header(pct, color, center, frac):
            h = VGroup(bold(pct, 40, color), txt("of rules satisfiable", 26, GREY_)) \
                .arrange(RIGHT, buff=0.2, aligned_edge=DOWN)
            h.move_to(center + UP * (ph / 2 + 0.78))
            bg = RoundedRectangle(width=pw - 0.5, height=0.11, corner_radius=0.05, stroke_width=0,
                                  fill_color=DIM, fill_opacity=0.8).move_to(center + UP * (ph / 2 + 0.28))
            fill = Rectangle(width=(pw - 0.5) * frac, height=0.11, stroke_width=0, fill_color=color,
                             fill_opacity=1).align_to(bg, LEFT).set_y(bg.get_y())
            return h, bg, fill

        tgt = net.copy().scale(s).move_to(PL)
        for e in tgt[0]:
            e.set_stroke(width=3.2)
        frame_l = panel(PL, GREEN_)
        hl, bgl, fl_ = header("99%", GREEN_, PL, 0.99)
        yes_g = VGroup(frame_l, hl, bgl, fl_, tgt)
        cL, KC = yes_g.get_center(), 1.18
        yes_g.scale(KC).move_to([0, -0.75, 0])
        self.wait_until("promise")
        self.play(FadeOut(VGroup(rule_card, ring_l, ring_r, pal, title)), run_time=0.5)
        self.play(Transform(net, tgt), FadeIn(frame_l), run_time=1.1)
        self.play(FadeIn(hl, shift=DOWN * 0.15), FadeIn(bgl), run_time=0.5)
        self.play(GrowFromEdge(fl_, LEFT), run_time=1.3, rate_func=smooth)
        greens = [e for k, e in enumerate(edges) if EDGES[k] != BAD]
        self.play(LaggedStart(*[ShowPassingFlash(e.copy().set_stroke(GREEN_, 7).set_z_index(2),
                                                 time_width=0.5) for e in greens], lag_ratio=0.05),
                  run_time=min(1.5, max(0.3, self.cue("conj") - self.now - 0.1)))

        # title: the Unique Games Conjecture (Khot, 2002)
        utitle = serif("The Unique Games Conjecture", 46).move_to([0, 3.15, 0])
        khot = txt("Subhash Khot, 2002", 26, GREY_).next_to(utitle, DOWN, buff=0.18)
        self.wait_until("conj")
        self.play(Write(utitle), run_time=1.2)
        t_khot = self.tw("posed by", "conj", "The Unique Games", "L1_end", None, 0.12)
        self.wait_until(max(self.now, t_khot))
        self.play(FadeIn(khot, shift=UP * 0.12), run_time=0.6)

        # "no efficient algorithm can tell that apart ..."
        algo_box = RoundedRectangle(width=2.5, height=1.25, corner_radius=0.14, stroke_color=WHITE_,
                                    stroke_width=2, fill_color=CARD, fill_opacity=1).move_to([0, -0.4, 0])
        algo_t = txt("efficient\nalgorithm", 26, WHITE_, line_spacing=0.8).move_to(algo_box)
        arr_l = Arrow([-2.12, -0.4, 0], [-1.27, -0.4, 0], buff=0, stroke_width=3, color=GREY_,
                      tip_length=0.18, max_tip_length_to_length_ratio=0.3)
        arr_r = Arrow([2.12, -0.4, 0], [1.27, -0.4, 0], buff=0, stroke_width=3, color=GREY_,
                      tip_length=0.18, max_tip_length_to_length_ratio=0.3)
        t_noeff = self.tw("no efficient", "conj", "The Unique Games", "L1_end", None, 0.4)
        self.wait_until(max(self.now, t_noeff))
        self.play(VGroup(net, frame_l, hl, bgl, fl_).animate.scale(1 / KC).move_to(cL), run_time=0.8)
        self.play(FadeIn(algo_box), Write(algo_t), GrowArrow(arr_l), run_time=0.7)
        # the algorithm "reads" the network: a light runs around the panel and into the box
        t_one = self.tw("one percent", "conj", "The Unique Games", "L1_end", None, 0.62)
        if t_one - 0.5 - self.now > 1.6:
            self.wait_until(max(self.now, (self.now + t_one - 0.5) / 2 - 0.75))
            self.play(ShowPassingFlash(frame_l.copy().set_stroke(WHITE_, 3, opacity=1), time_width=0.35),
                      run_time=1.1)
            self.play(ShowPassingFlash(Line(arr_l.get_start(), arr_l.get_end()).set_stroke(WHITE_, 5),
                                       time_width=1.0), Indicate(algo_t, scale_factor=1.05, color=WHITE_),
                      run_time=0.5)

        # "... from a network where only one percent can"
        edges2, nodes2 = make_net({i: (-x, y) for i, (x, y) in P0.items()})
        for k, e in enumerate(EDGES):
            edges2[k].set_stroke(GREEN_ if e == NO_GOOD else RED_, 4.5)
        for i in range(12):
            nodes2[i].set_fill(LAB[NO_LAB[i]], 1).set_stroke(LAB[NO_LAB[i]])
        net2 = VGroup(edges2, nodes2)
        net2.scale(s).move_to(PR)
        for e in edges2:
            e.set_stroke(width=3.2)
        frame_r = panel(PR, RED_)
        hr, bgr, fr_ = header("1%", RED_, PR, 0.01)
        fr_.stretch_to_fit_width(0.06).align_to(bgr, LEFT)
        t_one = self.tw("one percent", "conj", "The Unique Games", "L1_end", None, 0.62)
        self.wait_until(max(self.now, t_one - 0.5))
        self.play(FadeIn(frame_r), LaggedStart(*[GrowFromCenter(n) for n in nodes2], lag_ratio=0.04),
                  LaggedStart(*[Create(e) for e in edges2], lag_ratio=0.03),
                  FadeIn(hr, shift=DOWN * 0.15), FadeIn(bgr), FadeIn(fr_), GrowArrow(arr_r), run_time=1.0)
        qm = serif("?", 80, YELLOW_).move_to([0, -1.75, 0])
        self.play(FadeIn(qm, scale=0.5), run_time=0.45)
        unl1 = txt("(unless P = NP)", 26, GREY_).move_to([0, -2.75, 0])
        t_unl1 = self.tw("unless P", "conj", "The Unique Games", "L1_end", None, 0.88)
        self.wait_until(max(self.now, t_unl1 - 0.15))
        self.play(FadeIn(unl1, shift=UP * 0.1), Indicate(qm, scale_factor=1.15, color=YELLOW_), run_time=0.8)

        # ============================================================ 3. why: Max-Cut
        ubox = RoundedRectangle(width=3.5, height=1.6, corner_radius=0.16, stroke_color=ACC,
                                stroke_width=2.2, fill_color=CARD, fill_opacity=1).move_to([-4.2, 0, 0])
        ubox_t = bold("Unique Games\nConjecture", 32, WHITE_, line_spacing=0.85).move_to(ubox)
        ukhot = txt("Khot, 2002", 24, GREY_).next_to(ubox, DOWN, buff=0.22)
        names = ["Max-Cut", "Vertex Cover", "Max-2-SAT", "… and many more"]
        chip_ys = [1.35, 0.45, -0.45, -1.35]
        chips_ = VGroup()
        for nm, y in zip(names, chip_ys):
            frm = RoundedRectangle(width=3.4, height=0.7, corner_radius=0.12, stroke_color=GREY_,
                                   stroke_width=1.4, fill_color=CARD, fill_opacity=1).move_to([3.4, y, 0])
            t = txt(nm, 28, WHITE_ if not nm.startswith("…") else GREY_).move_to(frm)
            chips_.add(VGroup(frm, t))
        darrs = VGroup(*[Arrow(ubox.get_right(), c[0].get_left(), buff=0.12, stroke_width=3,
                               color=GREY_, tip_length=0.16) for c in chips_])
        opt_lab = bold("BEST POSSIBLE APPROXIMATION FOR", 22, GREY_).next_to(chips_, UP, buff=0.32)
        opt_lab.set_x(chips_.get_x())
        self.wait_until("why")
        ubox_t.set_z_index(2)
        self.play(FadeOut(VGroup(net, net2, frame_l, frame_r, hl, hr, bgl, bgr, fl_, fr_,
                                 algo_box, algo_t, arr_l, arr_r, qm, unl1)), run_time=0.45)
        self.play(ReplacementTransform(utitle, ubox_t), ReplacementTransform(khot, ukhot),
                  FadeIn(ubox), run_time=0.8)
        self.play(LaggedStart(*[GrowArrow(a) for a in darrs], lag_ratio=0.18),
                  LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in chips_], lag_ratio=0.18),
                  FadeIn(opt_lab), run_time=min(1.6, max(0.5, self.cue("maxcut") - self.now - 0.6)))
        chips_[0][1].set_z_index(3)
        self.play(Indicate(chips_[0][1], scale_factor=1.12, color=YELLOW_),
                  chips_[0][0].animate.set_stroke(YELLOW_, 2.5),
                  run_time=min(0.8, max(0.3, self.cue("maxcut") - self.now)))

        # "Take Max-Cut": a fresh copy of the network
        shift = np.array([2.5, -0.05, 0])
        PM = {i: v3(P0[i]) + shift for i in range(12)}
        medges, mnodes = make_net({i: PM[i][:2] for i in range(12)})
        mnet = VGroup(medges, mnodes)
        mc_head = serif("Max-Cut", 52).to_corner(UL, buff=0.45).shift(DOWN * 0.05)
        self.wait_until("maxcut")
        self.play(FadeOut(VGroup(ubox, ubox_t, ukhot, darrs, opt_lab, *chips_[1:], chips_[0][0])),
                  ReplacementTransform(chips_[0][1], mc_head), run_time=0.6)
        self.play(LaggedStart(*[GrowFromCenter(n) for n in mnodes], lag_ratio=0.05),
                  LaggedStart(*[Create(e) for e in medges], lag_ratio=0.04), run_time=0.8)

        # "split a network into two teams"
        team = {i: 0 for i in COL0}
        team.update({i: 1 for i in COL1})
        cx = {0: -1.8, 1: 1.8}
        NP_ = {}
        for col, lst in ((0, COL0), (1, COL1)):
            for k, i in enumerate(lst):
                NP_[i] = np.array([cx[col], 2.2 - 0.8 * k, 0])
        t_split = self.tw("split", "maxcut", "Take Max-Cut", "gw", "A famous", 0.3)
        self.wait_until(max(self.now, t_split))
        self.play(*[mnodes[i].animate.set_fill(TEAM_C[team[i]], 1).set_stroke(TEAM_C[team[i]])
                    for i in range(12)], run_time=0.4)
        cut = [k for k, (a, b) in enumerate(EDGES) if team[a] != team[b]]
        unc = [k for k in range(len(EDGES)) if k not in cut]

        def inner_arc(k):   # a link inside one team: arc bulging outwards
            a, b = EDGES[k]
            top, bot = (NP_[a], NP_[b]) if NP_[a][1] > NP_[b][1] else (NP_[b], NP_[a])
            ang = PI * (1 if team[a] == 0 else -1)
            return ArcBetweenPoints(top, bot, angle=ang, stroke_color=GREY_, stroke_width=3)
        self.play(*[mnodes[i].animate.move_to(NP_[i]) for i in range(12)],
                  *[medges[k].animate.put_start_and_end_on(NP_[a], NP_[b])
                    for k, (a, b) in enumerate(EDGES) if k in cut],
                  *[Transform(medges[k], inner_arc(k)) for k in unc],
                  run_time=1.1)

        # "with as many links between them as possible"
        cutline = DashedLine([0, 2.65, 0], [0, -2.25, 0], dash_length=0.12, stroke_color=WHITE_,
                             stroke_width=2).set_opacity(0.55)
        counter = VGroup(bold(str(len(cut)), 72, YELLOW_),
                         txt(f"of {len(EDGES)} links cut", 30, GREY_)).arrange(DOWN, buff=0.12)
        counter.move_to([4.7, 0.25, 0])
        t_many = self.tw("as many links", "maxcut", "Take Max-Cut", "gw", "A famous", 0.6)
        self.wait_until(max(self.now, t_many - 0.2))
        self.play(Create(cutline),
                  LaggedStart(*[medges[k].animate.set_stroke(YELLOW_, 4.5) for k in cut], lag_ratio=0.06),
                  *[medges[k].animate.set_stroke(GREY_, 2.5, opacity=0.75) for k in unc], run_time=0.9)
        self.play(FadeIn(counter, shift=LEFT * 0.2), run_time=0.5)

        # "A famous 1995 algorithm always gets at least 87.8% of the best"
        X0, X1, YA = -5.6, 5.6, -0.95

        def fx(x):
            return X0 + x * (X1 - X0)
        axis = Line([X0, YA, 0], [X1, YA, 0], stroke_color=GREY_, stroke_width=3)
        ticks = VGroup(*[Line([fx(x), YA + 0.15, 0], [fx(x), YA - 0.15, 0], stroke_color=GREY_,
                              stroke_width=3) for x in (0, 1)])
        t0l = tex("0", 32, GREY_).next_to([fx(0), YA, 0], DOWN, buff=0.3)
        t1l = tex("1", 32, GREY_).next_to([fx(1), YA, 0], DOWN, buff=0.3)
        gbar = Line([fx(0), YA, 0], [fx(0.878), YA, 0], stroke_color=GREEN_, stroke_width=14,
                    stroke_opacity=0.85)
        rbar = Line([fx(0.878), YA, 0], [fx(1), YA, 0], stroke_color=RED_, stroke_width=14,
                    stroke_opacity=0.85)
        mark = Line([fx(0.878), YA + 0.35, 0], [fx(0.878), YA - 0.35, 0], stroke_color=YELLOW_,
                    stroke_width=4)
        m878 = tex("0.878", 34, YELLOW_).next_to([fx(0.878), YA, 0], DOWN, buff=0.3)
        gw_lab = txt("Goemans–Williamson, 1995", 26, WHITE_).next_to(gbar, UP, buff=0.28)
        cap = txt("fraction of the best cut", 24, GREY_).next_to(axis, DOWN, buff=0.85)
        cap.align_to([X0, 0, 0], LEFT)
        mcg = VGroup(mnet, cutline)
        mc_tgt = mcg.copy().scale(0.55).move_to([-3.4, 1.5, 0])
        for k in cut:
            mc_tgt[0][0][k].set_stroke(width=3)
        for k in unc:
            mc_tgt[0][0][k].set_stroke(width=2)
        cnt_tgt = counter.copy().scale(0.75).next_to(mc_tgt, RIGHT, buff=0.7)
        self.wait_until("gw")
        self.play(Transform(mcg, mc_tgt), Transform(counter, cnt_tgt),
                  Create(axis), FadeIn(ticks), FadeIn(t0l), FadeIn(t1l), run_time=1.0)
        t_always = self.tw("always gets", "gw", "A famous", "opt", "conjecture implies", 0.3)
        t_878 = self.tw("eighty-seven", "gw", "A famous", "opt", "conjecture implies", 0.55)
        self.wait_until(max(self.now, t_always - 0.1))
        self.play(Create(gbar), FadeIn(gw_lab, shift=UP * 0.1),
                  run_time=max(0.6, min(2.0, t_878 + 0.4 - self.now)))
        self.play(Create(mark), Write(m878), run_time=0.6)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.5)
        self.play(Circumscribe(m878, color=YELLOW_, buff=0.08),
                  run_time=min(0.9, max(0.3, self.cue("opt") - self.now - 0.05)))

        # "the conjecture implies nothing efficient can do better"
        hard = bold("NP-hard", 28, RED_)
        hard_sub = txt("if the conjecture holds", 22, GREY_)
        hard_g = VGroup(hard_sub, hard).arrange(DOWN, buff=0.08).next_to(rbar, UP, buff=0.5)
        hard_g.set_x(min(fx(0.939), 6.55 - hard_g.width / 2))
        kkmo = txt("Khot–Kindler–Mossel–O'Donnell, 2007", 22, GREY_)
        kkmo.next_to(axis, DOWN, buff=0.85).align_to([X1, 0, 0], RIGHT)
        self.wait_until("opt")
        self.play(Create(rbar), FadeIn(hard_g, shift=DOWN * 0.1), run_time=0.8)
        t_nothing = self.tw("nothing efficient", "opt", "conjecture implies", "L2_end", None, 0.4)
        self.wait_until(max(self.now, t_nothing))
        self.play(FadeIn(kkmo, shift=UP * 0.1), Indicate(rbar, color=RED_, scale_factor=1.05), run_time=0.8)

        # ============================================================ 4. the claim
        card102 = paper_card("102", width=3.0)
        card102.move_to([4.65, 0.15, 0])
        card_mid = paper_card("102", width=3.4).move_to([1.0, -0.55, 0])
        card_start = card_mid.copy().shift(RIGHT * 7.5)
        tag = paper_tag("102", color=ACC)
        uhead = serif("Unique Games Conjecture", 44).to_corner(UL, buff=0.45).shift(DOWN * 0.05)
        st_open = chip("OPEN SINCE 2002", GREY_, size=20).next_to(uhead, DOWN, buff=0.22, aligned_edge=LEFT)
        st_claim = chip("CLAIMED PROOF · 2026", ACC, size=20).move_to(st_open, aligned_edge=LEFT)
        self.wait_until("claim")
        self.add(card_start)
        old = VGroup(mcg, counter, gw_lab, cap, kkmo, hard_g, t0l, t1l, ticks, axis, gbar, rbar, mark, m878)
        self.play(Succession(AnimationGroup(FadeOut(old, shift=LEFT * 0.3), FadeOut(mc_head, shift=UP * 0.3),
                                            run_time=0.4), Wait(run_time=0.9)),
                  Succession(Wait(run_time=0.1), card_start.animate(run_time=1.2).move_to(card_mid)),
                  Succession(Wait(run_time=0.4), Write(uhead, run_time=0.9)),
                  Succession(Wait(run_time=0.5), FadeIn(tag, shift=RIGHT * 0.2, run_time=0.8)),
                  run_time=1.3)
        self.play(FadeIn(st_open, shift=UP * 0.1), run_time=0.4)
        self.play(ReplacementTransform(st_open, st_claim), Circumscribe(card_start, color=ACC, buff=0.06),
                  run_time=min(1.0, max(0.3, self.cue("direct") - self.now - 0.1)))

        # "Companions claim direct proofs that Max-Cut's 87.8% ... and factor two ... Vertex Cover"
        GX0, GX1 = -3.0, 1.9
        Y1, Y2 = 0.45, -1.3

        def row(name, y, frac, bnd, lo_txt=None):
            g = gauge(GX0, GX1, y, frac)
            lab = bold(name, 30).move_to([0, y, 0]).align_to([-6.3, 0, 0], LEFT)
            b = tex(bnd, 30, YELLOW_).next_to(g[3], DOWN, buff=0.1)
            one = tex("1", 30, GREY_).next_to(g[4], DOWN, buff=0.17).set_y(b.get_y())
            eff = txt("efficient", 22, GREEN_).next_to(g[1], UP, buff=0.4)
            hrd = bold("NP-hard", 24, RED_).next_to(g[2], UP, buff=0.4)
            hrd.set_x(min(hrd.get_x(), 2.75 - hrd.width / 2))
            extra = VGroup()
            if lo_txt:
                extra.add(txt(lo_txt, 22, GREY_).next_to(b, LEFT, buff=0.15))
            return g, lab, b, one, eff, hrd, extra

        def build_row(r, t_end):
            g, lab, b, one, eff, hrd, extra = r
            self.play(Write(lab), Create(g[0]), Create(g[4]), FadeIn(one), run_time=0.6)
            self.play(Create(g[1]), Create(g[3]), FadeIn(b), FadeIn(extra), FadeIn(eff, shift=UP * 0.1),
                      run_time=0.6)
            self.play(Create(g[2]), FadeIn(hrd, shift=UP * 0.1), run_time=0.5)

        comp = bold("COMPANION PAPERS: CLAIMED DIRECT PROOFS", 22, GREY_).move_to([0, 1.55, 0]).align_to([-6.3, 0, 0], LEFT)
        self.wait_until("direct")
        self.play(card_start.animate(run_time=0.9).scale(3.0 / 3.4).move_to(card102),
                  Succession(Wait(run_time=0.55), FadeIn(comp, shift=DOWN * 0.1, run_time=0.55)),
                  run_time=1.1)
        t_mc = min(self.tw("Max-Cut", "direct", "Compan", "L3_end", None, 0.2),
                   self.tw("eighty-seven", "direct", "Compan", "L3_end", None, 0.25))
        self.wait_until(max(self.now, t_mc - 0.25))
        r1 = row("Max-Cut", Y1, 0.878, "0.878")
        build_row(r1, None)
        self.play(Indicate(r1[2], color=YELLOW_), run_time=0.6)

        # Vertex Cover: factor axis from 2.6 (left) down to 1 (right, perfect); NP-hard below 2
        r2 = row("Vertex Cover", Y2, (2.6 - 2.0) / (2.6 - 1.0), "2", lo_txt="factor")
        t_vc = self.tw("factor two", "direct", "Compan", "L3_end", None, 0.55)
        self.wait_until(max(self.now, t_vc - 0.3))
        build_row(r2, None)

        # "... can't be beaten, unless P equals NP" -> closing banner
        unl = bold("unless P = NP", 28, WHITE_).move_to([(GX0 + GX1) / 2, -2.4, 0])
        t_unl = self.tw("unless P", "direct", "Compan", "L3_end", None, 0.9)
        banner = result_banner("Unique games: telling 99% from 1% satisfiable is NP-hard",
                               color=YELLOW_, lean=CATALOG["102"]["lean"], size=28)
        if banner.width > 9.0:
            banner.scale_to_fit_width(9.0)
        banner.to_corner(UL, buff=0.45)
        t_ban = min(max(self.now, t_unl - 0.4), self.narr_end - 3.4)
        self.wait_until(max(self.now, t_ban))
        self.play(FadeOut(VGroup(uhead, st_claim), shift=UP * 0.25), run_time=0.35)
        self.play(FadeIn(banner, shift=DOWN * 0.2), run_time=0.6)
        self.wait_until(max(self.now, t_unl - 0.1))
        self.play(FadeIn(unl, shift=UP * 0.1), run_time=0.5)
        self.play(Indicate(unl, color=YELLOW_, scale_factor=1.06),
                  run_time=min(0.9, max(0.3, self.narr_end - 0.6 - self.now)))
        self.finish()
