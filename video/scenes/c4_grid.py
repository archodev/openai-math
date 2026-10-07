import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
from lib.grid import GridScene

import json

# ---------------------------------------------------------------- shared look
A = GREEN_            # chapter accent (Theoretical CS)
SW = 2.0              # main stroke width in icons
SW2 = 1.4             # secondary stroke width
ICON_W = 2.86         # icon box (tile auto-fits; pad keeps the scale ~1)
ICON_H2 = 0.81        # tiles whose name wraps to two lines
ICON_H1 = 1.12        # tiles with a one-line name
BIG_W, BIG_H = 5.2, 4.4


ICON_MAX_W = 2.72     # 1.06x "lit" pulse -> 2.88, still inside the tile's 0.13 side padding


def _pad(content, w=ICON_W, h=ICON_H2):
    """Invisible fixed-size frame around an icon so Tile's auto-fit keeps
    the drawn content at its designed size (stroke widths stay consistent)."""
    if content.width > ICON_MAX_W:
        content.scale_to_fit_width(ICON_MAX_W)
    if content.height > h - 0.02:
        content.scale_to_fit_height(h - 0.02)
    content.move_to(ORIGIN)
    box = Rectangle(width=w, height=h, stroke_width=0, stroke_opacity=0, fill_opacity=0)
    return VGroup(box, content)


def _hide(*mobs):
    """Pre-built element that appears later: remember its style, make it invisible."""
    for m in mobs:
        m._shown = m.copy()
        m.set_opacity(0)


def _show(*mobs):
    for m in mobs:
        m.match_style(m._shown)


def _cell(w, h=None, color=GREY_, sw=SW2, fill=None, fo=0.0):
    h = w if h is None else h
    return Rectangle(width=w, height=h, stroke_color=color, stroke_width=sw,
                     fill_color=fill or color, fill_opacity=fo)


def _node(r=0.07, fill=WHITE_, stroke=None, sw=1.6):
    return Circle(radius=r, stroke_color=stroke or fill, stroke_width=sw,
                  fill_color=fill, fill_opacity=1.0)


def _arrow(a, b, color=GREY_, sw=SW2, tip=0.09, buff=0.0):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color, tip_length=tip,
                 max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=20)


def _coin(r=0.17, tilt=0.42):
    """A coin seen slightly edge-on (mid-flip)."""
    rim = Ellipse(width=2 * r, height=2 * r * tilt, stroke_color=GREY_, stroke_width=SW2,
                  fill_color=DIM, fill_opacity=1.0).shift(DOWN * 0.035)
    face = Ellipse(width=2 * r, height=2 * r * tilt, stroke_color=WHITE_, stroke_width=SW2,
                   fill_color=GREY_, fill_opacity=1.0)
    inner = Ellipse(width=1.3 * r, height=1.3 * r * tilt, stroke_color=WHITE_,
                    stroke_width=1.0, stroke_opacity=0.8)
    return VGroup(rim, face, inner)


# ================================================================ icons
def icon_103():
    """L = RL = BPL: long read-only input tape, a head with a 3-cell work tape
    (log-space memory), and a flipping coin (randomness)."""
    bits = "011010011101"
    tape = VGroup(*[_cell(0.215, color=GREY_, fill=WHITE_, fo=0.3 if b == "1" else 0.0)
                    for b in bits]).arrange(RIGHT, buff=0).move_to(UP * 0.4)
    k = 4
    head = Triangle(stroke_width=0, fill_color=A, fill_opacity=1).scale(0.085)
    head.next_to(tape[k], DOWN, buff=0.04)
    mem = VGroup(*[_cell(0.2, color=A, sw=SW, fill=A, fo=f) for f in (0.6, 0.0, 0.6)])
    mem.arrange(RIGHT, buff=0).next_to(head, DOWN, buff=0.2)
    stem = Line(head.get_bottom(), mem.get_top(), stroke_color=A, stroke_width=SW)
    logn = Text("log n", font=SANS, font_size=20, color=A).next_to(mem, LEFT, buff=0.1)
    tape_n = Text("n", font=SANS, font_size=20, color=GREY_).next_to(tape, LEFT, buff=0.08)
    coin = _coin(0.2).move_to([0.95, -0.22, 0])
    arc = ArcBetweenPoints(coin.get_left() + LEFT * 0.42 + DOWN * 0.14, coin.get_top() + UP * 0.03,
                           angle=-PI / 2.2)
    arc = DashedVMobject(arc.set_stroke(GREY_, SW2), num_dashes=6)
    spin = Arc(radius=0.22, start_angle=PI * 0.15, angle=PI * 0.7, stroke_color=GREY_,
               stroke_width=SW2).move_to(coin.get_top() + UP * 0.14)
    spin.add_tip(tip_length=0.07, tip_width=0.07)
    return _pad(VGroup(tape, tape_n, head, stem, mem, logn, arc, coin, spin), h=ICON_H1)


def icon_109():
    """Integer multiplication: a schoolbook layout of two 7-bit numbers and
    their 14-bit product (91 x 109 = 9919, in binary)."""
    a, b = 91, 109
    p = a * b
    pitch, s = 0.195, 0.165

    def row(n, width, color, fill, sw):
        bs = format(n, "b").rjust(width, "0")[-width:]
        return VGroup(*[_cell(s, color=color, sw=sw, fill=fill, fo=0.85 if c == "1" else 0.0)
                        for c in bs]).arrange(RIGHT, buff=pitch - s)

    ra = row(a, 7, GREY_, WHITE_, SW2)
    rb = row(b, 7, GREY_, WHITE_, SW2)
    rp = row(p, 14, A, A, SW2)
    rp.move_to(DOWN * 0.22)
    rule = Line(rp.get_corner(UR) + UP * 0.07, rp.get_corner(UR) + UP * 0.07 + LEFT * 8.2 * pitch,
                stroke_color=GREY_, stroke_width=SW2)
    rb.next_to(rule, UP, buff=0.06).align_to(rp, RIGHT)
    ra.next_to(rb, UP, buff=0.045).align_to(rp, RIGHT)
    times = MathTex(r"\times", font_size=26, color=GREY_).next_to(rb, LEFT, buff=0.12)
    return _pad(VGroup(ra, rb, rule, times, rp))


SS_A, SS_B, SS_T = (7, 8, 9), (5, 6, 14), 37      # unique solution 8+9+6+14 = 37
SS_PICK = {1, 2, 4, 5}                             # indices into SS_A + SS_B


def icon_138():
    """Subset Sum: six numbers, the chosen ones (8, 9, 6, 14) flow into the
    target 37. Small gap between the two halves (meet-in-the-middle)."""
    nums = SS_A + SS_B
    boxes = VGroup()
    for i, v in enumerate(nums):
        on = i in SS_PICK
        sq = RoundedRectangle(width=0.38, height=0.32, corner_radius=0.05,
                              stroke_color=A if on else GREY_, stroke_width=SW if on else SW2,
                              fill_color=A, fill_opacity=0.16 if on else 0.0)
        t = Text(str(v), font=SANS, font_size=18, color=WHITE_ if on else GREY_, weight=SEMIBOLD)
        t.move_to(sq)
        boxes.add(VGroup(sq, t))
    boxes.arrange(RIGHT, buff=0.07)
    for bx in boxes[3:]:
        bx.shift(RIGHT * 0.12)
    boxes.move_to(UP * 0.3)
    tgt_box = RoundedRectangle(width=0.62, height=0.34, corner_radius=0.06, stroke_color=A,
                               stroke_width=SW, fill_color=A, fill_opacity=0.28)
    tgt_t = Text(str(SS_T), font=SANS, font_size=19, color=WHITE_, weight=BOLD).move_to(tgt_box)
    tgt = VGroup(tgt_box, tgt_t).move_to(DOWN * 0.36 + RIGHT * 0.08)
    lines = VGroup(*[
        Line(boxes[i].get_bottom() + DOWN * 0.02, tgt.get_top() + RIGHT * (j - 1.5) * 0.1,
             stroke_color=A, stroke_width=SW2)
        for j, i in enumerate(sorted(SS_PICK))])
    eq = Text("=", font=SANS, font_size=18, color=GREY_).next_to(tgt, LEFT, buff=0.1)
    return _pad(VGroup(boxes, lines, tgt, eq), h=ICON_H1)


def icon_106():
    """Three-colourable graph: a triangulated strip, properly coloured with
    green / white / grey."""
    top = [np.array([-1.3 + 0.52 * i, 0.27, 0]) for i in range(6)]
    bot = [np.array([-1.04 + 0.52 * i, -0.27, 0]) for i in range(5)]
    order = []
    for i in range(6):
        order.append(top[i])
        if i < 5:
            order.append(bot[i])
    cols = [A, WHITE_, GREY_]
    edges = VGroup()
    for i in range(len(order) - 1):
        edges.add(Line(order[i], order[i + 1]))
    for i in range(5):
        edges.add(Line(top[i], top[i + 1]))
    for i in range(4):
        edges.add(Line(bot[i], bot[i + 1]))
    edges.set_stroke(GREY_, SW2, opacity=0.8)
    nodes = VGroup(*[_node(0.075, fill=cols[i % 3], stroke=BG, sw=1.2).move_to(p)
                     for i, p in enumerate(order)])
    return _pad(VGroup(edges, nodes))


def icon_105():
    """2-to-1 game: labels of u (top) map to labels of v (bottom), every
    v-label has exactly two preimages; one satisfied constraint in green."""
    pi = [1, 0, 2, 0, 1, 2]
    up = VGroup(*[_node(0.06, fill=WHITE_) for _ in range(6)]).arrange(RIGHT, buff=0.24)
    dn = VGroup(*[_node(0.06, fill=WHITE_) for _ in range(3)]).arrange(RIGHT, buff=0.5)
    up.move_to(UP * 0.25)
    dn.move_to(DOWN * 0.25)
    bu = SurroundingRectangle(up, buff=0.08, corner_radius=0.1, stroke_color=GREY_,
                              stroke_width=SW2)
    bd = SurroundingRectangle(dn, buff=0.08, corner_radius=0.1, stroke_color=GREY_,
                              stroke_width=SW2)
    hi = 4
    lines = VGroup(*[Line(up[i].get_center(), dn[pi[i]].get_center(),
                          stroke_color=A if i == hi else GREY_,
                          stroke_width=SW if i == hi else 1.1,
                          stroke_opacity=1 if i == hi else 0.7) for i in range(6)])
    up[hi].set_fill(A).set_stroke(A)
    dn[pi[hi]].set_fill(A).set_stroke(A)
    lab = MathTex(r"2\!:\!1", font_size=24, color=A).next_to(VGroup(bu, bd), RIGHT, buff=0.18)
    lu = MathTex("u", font_size=22, color=GREY_).next_to(bu, LEFT, buff=0.12)
    lv = MathTex("v", font_size=22, color=GREY_).next_to(bd, LEFT, buff=0.12)
    return _pad(VGroup(lines, bu, bd, up, dn, lab, lu, lv))


def icon_104():
    """Mean-payoff game: max nodes (circles), min nodes (squares), weighted
    edges; the highlighted cycle has mean payoff (3-1-2)/3 = 0."""
    P = {"a": np.array([-1.15, -0.05, 0]), "b": np.array([-0.35, 0.22, 0]),
         "c": np.array([0.35, -0.12, 0]), "d": np.array([1.15, 0.15, 0])}
    a = _node(0.12, fill=CARD, stroke=A, sw=SW).move_to(P["a"])
    b = Square(0.22, stroke_color=A, stroke_width=SW, fill_color=CARD, fill_opacity=1).move_to(P["b"])
    c = _node(0.12, fill=CARD, stroke=A, sw=SW).move_to(P["c"])
    d = Square(0.22, stroke_color=WHITE_, stroke_width=SW2, fill_color=CARD, fill_opacity=1).move_to(P["d"])

    e_ab = Arrow(a.get_right(), b.get_left(), buff=0.03, stroke_width=SW, color=A, tip_length=0.08,
                 max_tip_length_to_length_ratio=0.5)
    e_bc = Arrow(b.get_right(), c.get_left(), buff=0.03, stroke_width=SW, color=A, tip_length=0.08,
                 max_tip_length_to_length_ratio=0.5)
    e_ca = CurvedArrow(c.get_bottom() + LEFT * 0.04, a.get_bottom() + RIGHT * 0.04, angle=-PI / 4,
                       stroke_width=SW, color=A, tip_length=0.08)
    e_cd = CurvedArrow(c.get_top() + RIGHT * 0.05, d.get_left() + UP * 0.04, angle=-PI / 4,
                       stroke_width=SW2, color=GREY_, tip_length=0.08)
    e_dc = CurvedArrow(d.get_bottom(), c.get_right() + DOWN * 0.04, angle=-PI / 4,
                       stroke_width=SW2, color=GREY_, tip_length=0.08)
    w = lambda s, col, pos: MathTex(s, font_size=20, color=col).move_to(pos)
    ws = VGroup(
        w("+3", WHITE_, (P["a"] + P["b"]) / 2 + UP * 0.2 + LEFT * 0.05),
        w("-1", WHITE_, (P["b"] + P["c"]) / 2 + UP * 0.17 + RIGHT * 0.1),
        w("-2", WHITE_, (P["a"] + P["c"]) / 2 + DOWN * 0.38),
        w("+2", GREY_, (P["c"] + P["d"]) / 2 + UP * 0.28),
        w("-4", GREY_, (P["c"] + P["d"]) / 2 + DOWN * 0.24 + RIGHT * 0.12),
    )
    return _pad(VGroup(e_ab, e_bc, e_ca, e_cd, e_dc, a, b, c, d, ws))


def _bracket(h, side, color=WHITE_, sw=SW2, lip=0.06):
    s = 1 if side == "L" else -1
    return VMobject(stroke_color=color, stroke_width=sw).set_points_as_corners(
        [[s * lip, h / 2, 0], [0, h / 2, 0], [0, -h / 2, 0], [s * lip, -h / 2, 0]])


def _matrix(size, n_lines, color, dots=False, sw=SW2):
    body = VGroup()
    if dots:
        step = size / n_lines
        for i in range(n_lines):
            for j in range(n_lines):
                body.add(Dot(radius=0.025, color=color).move_to(
                    [(j - (n_lines - 1) / 2) * step, ((n_lines - 1) / 2 - i) * step, 0]))
    else:
        sq = Square(size, stroke_width=0, fill_color=color, fill_opacity=0.12)
        body.add(sq)
        for i in range(1, n_lines):
            x = -size / 2 + size * i / n_lines
            body.add(Line([x, -size / 2, 0], [x, size / 2, 0]))
            body.add(Line([-size / 2, x, 0], [size / 2, x, 0]))
        body[1:].set_stroke(color, 0.8, opacity=0.55)
    lb = _bracket(size + 0.1, "L", color, sw).next_to(body, LEFT, buff=0.05)
    rb = _bracket(size + 0.1, "R", color, sw).next_to(body, RIGHT, buff=0.05)
    return VGroup(lb, body, rb)


def icon_108():
    """perm of a small n x n matrix written as det of a much larger matrix,
    whose size must be at least c n^3."""
    small = _matrix(0.3, 3, WHITE_, dots=True)
    big = _matrix(0.56, 9, A)
    eq = MathTex("=", font_size=28, color=GREY_)
    row = VGroup(small, eq, big).arrange(RIGHT, buff=0.16)
    perm = MathTex(r"\mathrm{perm}", font_size=22, color=WHITE_).next_to(small, UP, buff=0.07)
    det = MathTex(r"\det", font_size=22, color=A).next_to(big, UP, buff=0.07)
    x = big.get_right()[0] + 0.1
    yt, yb = big[1].get_top()[1], big[1].get_bottom()[1]
    tick = VGroup(Line([x, yt, 0], [x, yb, 0]), Line([x - 0.04, yt, 0], [x + 0.04, yt, 0]),
                  Line([x - 0.04, yb, 0], [x + 0.04, yb, 0])).set_stroke(A, SW2)
    size = MathTex(r"\ge c\,n^3", font_size=24, color=A).next_to(tick, RIGHT, buff=0.08)
    return _pad(VGroup(row, perm, det, tick, size))


def icon_113():
    """Perfect matching (green) in a non-bipartite ladder graph (two
    triangles from the diagonals)."""
    T = [np.array([-1.25 + 0.5 * i, 0.26, 0]) for i in range(6)]
    B = [np.array([-1.25 + 0.5 * i, -0.26, 0]) for i in range(6)]
    E = [("t", i, "t", i + 1) for i in range(5)] + [("b", i, "b", i + 1) for i in range(5)]
    E += [("t", i, "b", i) for i in range(6)] + [("t", 1, "b", 2), ("b", 3, "t", 4)]
    M = {("t", 0, "b", 0), ("t", 1, "t", 2), ("b", 1, "b", 2), ("t", 3, "b", 3),
         ("t", 4, "t", 5), ("b", 4, "b", 5)}
    P = lambda s, i: T[i] if s == "t" else B[i]
    edges = VGroup()
    match = VGroup()
    for e in E:
        ln = Line(P(e[0], e[1]), P(e[2], e[3]))
        if e in M:
            match.add(ln.set_stroke(A, 4.2))
        else:
            edges.add(ln.set_stroke(GREY_, SW2, opacity=0.75))
    nodes = VGroup(*[_node(0.06, fill=WHITE_).move_to(p) for p in T + B])
    return _pad(VGroup(edges, match, nodes))


def icon_132():
    """Boolean cube: at input x (green ring) no single bit flip changes f,
    but flipping a block of two bits together does (red) -- block
    sensitivity can exceed sensitivity; the counterexample makes
    bs >= s^alpha with alpha > 2."""
    s = 0.5
    off = np.array([0.24, 0.18, 0])
    F = [np.array(p) for p in ([0, 0, 0], [s, 0, 0], [s, s, 0], [0, s, 0])]
    Bk = [p + off for p in F]
    edges = VGroup(*[Line(F[i], F[(i + 1) % 4]) for i in range(4)],
                   *[Line(Bk[i], Bk[(i + 1) % 4]) for i in range(4)],
                   *[Line(F[i], Bk[i]) for i in range(4)]).set_stroke(GREY_, SW2, opacity=0.8)
    x = F[0]
    nbrs = [F[1], F[3], Bk[0]]
    blk = F[2]
    rest = [Bk[1], Bk[2], Bk[3]]
    dots = VGroup(
        _node(0.07, fill=CARD, stroke=A, sw=2.4).move_to(x),
        *[_node(0.055, fill=CARD, stroke=WHITE_, sw=1.6).move_to(p) for p in nbrs],
        _node(0.07, fill=RED_, stroke=RED_).move_to(blk),
        *[_node(0.04, fill=GREY_).move_to(p) for p in rest],
    )
    flip = DashedVMobject(Line(x + np.array([0.06, 0.06, 0]), blk - np.array([0.08, 0.08, 0]))
                          .set_stroke(RED_, SW), num_dashes=5)
    cube = VGroup(edges, flip, dots)
    f1 = MathTex(r"\mathrm{bs}\ \ge\ s^{\alpha}", font_size=30, color=WHITE_)
    f2 = MathTex(r"\alpha > 2", font_size=28, color=RED_)
    form = VGroup(f1, f2).arrange(DOWN, buff=0.1)
    return _pad(VGroup(cube, form).arrange(RIGHT, buff=0.35))


def icon_124():
    """Three identical machines, unit jobs (squares), precedence arrows;
    idle slots where a job must wait for its predecessors."""
    slots = [(1, 1, 1), (1, 1, 0), (1, 1, 1), (1, 0, 0), (1, 1, 1), (1, 1, 0)]
    pitch, rowh, s = 0.33, 0.3, 0.19
    x0 = -0.9
    jobs = {}
    grp = VGroup()
    rails = VGroup()
    labels = VGroup()
    x_end = x0 + 6 * pitch + 0.02
    for r in range(3):
        y = 0.3 - r * rowh
        rails.add(Line([x0 - 0.06, y - s / 2 - 0.035, 0], [x_end, y - s / 2 - 0.035, 0],
                       stroke_color=DIM, stroke_width=1.0))
        labels.add(MathTex(f"M_{r + 1}", font_size=24, color=GREY_).move_to([x0 - 0.3, y, 0]))
    for t, col in enumerate(slots):
        for r, on in enumerate(col):
            if on:
                sq = RoundedRectangle(width=s, height=s, corner_radius=0.035,
                                      stroke_color=A, stroke_width=SW2, fill_color=A, fill_opacity=0.22)
                sq.move_to([x0 + t * pitch + s / 2, 0.3 - r * rowh, 0])
                jobs[(t, r)] = sq
                grp.add(sq)
    arr = VGroup()
    for (t1, r1), (t2, r2) in [((0, 2), (1, 1)), ((2, 1), (3, 0)), ((3, 0), (4, 2)), ((4, 0), (5, 1))]:
        a_, b_ = jobs[(t1, r1)], jobs[(t2, r2)]
        arr.add(_arrow(a_.get_right() + RIGHT * 0.01, b_.get_left() + LEFT * 0.01,
                       color=WHITE_, sw=1.3, tip=0.07))
    end = DashedLine([x_end, 0.47, 0], [x_end, -0.47, 0],
                     stroke_color=GREY_, stroke_width=1.2, dash_length=0.05)
    cmax = MathTex(r"C_{\max}", font_size=24, color=GREY_).next_to(end, RIGHT, buff=0.06)
    return _pad(VGroup(rails, labels, grp, arr, end, cmax), h=ICON_H1)


def icon_128():
    """Shortest common superstring: ATGC, GCAT, ATCG overlap into ATGCATCG."""
    pitch = 0.3

    def word(w, col0, row, color, sw, fo):
        ls = VGroup(*[Text(c, font=MONO, font_size=18, color=WHITE_ if color != A else WHITE_,
                           weight=BOLD if color == A else NORMAL)
                      .move_to([(col0 + i) * pitch, -row * 0.29, 0]) for i, c in enumerate(w)])
        for l in ls:
            l.set_y(-row * 0.29)
        box = RoundedRectangle(width=len(w) * pitch - 0.07, height=0.24, corner_radius=0.06,
                               stroke_color=color, stroke_width=sw, fill_color=color, fill_opacity=fo)
        box.move_to([(col0 + (len(w) - 1) / 2) * pitch, -row * 0.29, 0])
        return VGroup(box, ls)

    w1 = word("ATGC", 0, 0, GREY_, SW2, 0.0)
    w3 = word("ATCG", 4, 0, GREY_, SW2, 0.0)
    w2 = word("GCAT", 2, 1, GREY_, SW2, 0.0)
    sup = word("ATGCATCG", 0, 2.15, A, SW, 0.18)
    sep = Line([-0.15, -0.47, 0], [8 * pitch - 0.15, -0.47, 0], stroke_color=DIM, stroke_width=1.0)
    return _pad(VGroup(w1, w3, w2, sep, sup))


def icon_142():
    """Complete factorisation over F_5: x^4+4x^3+3x+1 = (x+1)(x+3)(x^2+2);
    the irreducible factors in green."""
    fs = 25
    root = MathTex(r"x^4+4x^3+3x+1", font_size=fs, color=WHITE_).move_to(UP * 0.24)
    leaves = VGroup(MathTex(r"x+1", font_size=fs, color=A), MathTex(r"x+3", font_size=fs, color=A),
                    MathTex(r"x^2+2", font_size=fs, color=A)).arrange(RIGHT, buff=0.42)
    leaves.move_to(DOWN * 0.26)
    edges = VGroup(*[Line(root.get_bottom() + DOWN * 0.03, l.get_top() + UP * 0.04,
                          stroke_color=GREY_, stroke_width=1.3)
                     for l in leaves])
    fp = MathTex(r"\mathbb{F}_5", font_size=24, color=GREY_).next_to(root, RIGHT, buff=0.25)
    return _pad(VGroup(edges, root, leaves, fp))


# ================================================================ featured: 103
def big_103():
    root = VGroup()
    pad = Rectangle(width=BIG_W, height=BIG_H, stroke_width=0, fill_opacity=0)
    bits = "0110100111010"
    cw = 0.36
    tape = VGroup(*[_cell(cw, color=GREY_, sw=1.6, fill=A, fo=0.0) for _ in bits]).arrange(RIGHT, buff=0)
    tape.move_to(UP * 1.45)
    digits = VGroup(*[Text(b, font=MONO, font_size=22, color=WHITE_).move_to(c)
                      for b, c in zip(bits, tape)])
    lab_in = VGroup(Text("input:", font=SANS, font_size=22, color=GREY_),
                    MathTex("n", font_size=30, color=WHITE_),
                    Text("symbols", font=SANS, font_size=22, color=GREY_)).arrange(RIGHT, buff=0.1)
    lab_in[1].shift(DOWN * 0.02)
    lab_in.next_to(tape, UP, buff=0.16).align_to(tape, LEFT)

    # the machine ("cart") that walks along the tape
    k0 = 1
    head = Triangle(stroke_width=0, fill_color=A, fill_opacity=1).scale(0.14)
    head.next_to(tape[k0], DOWN, buff=0.05)
    box = RoundedRectangle(width=1.2, height=0.66, corner_radius=0.12, stroke_color=WHITE_,
                           stroke_width=2.2, fill_color=CARD_HI, fill_opacity=1)
    box.next_to(head, DOWN, buff=0.26)
    mlab = MathTex(r"M", font_size=42, color=WHITE_).move_to(box)
    stem = Line(head.get_bottom(), box.get_top(), stroke_color=A, stroke_width=2.6)
    mem = VGroup(*[_cell(0.36, color=A, sw=2.4, fill=A, fo=0.0) for _ in range(3)]).arrange(RIGHT, buff=0)
    mem.next_to(box, DOWN, buff=0.26)
    link = Line(box.get_bottom(), mem.get_top(), stroke_color=A, stroke_width=2.6)
    mem_lab = MathTex(r"O(\log n)", font_size=32, color=A).next_to(mem, DOWN, buff=0.1)
    mem_lab2 = Text("memory", font=SANS, font_size=22, color=A).next_to(mem_lab, DOWN, buff=0.05)
    coin = _coin(0.32, tilt=1.0)
    coin[0].set_opacity(0)                         # face-on: hide the rim
    coin.next_to(box, RIGHT, buff=0.32)
    coin_lab = Text("coin flips", font=SANS, font_size=22, color=GREY_).next_to(coin, DOWN, buff=0.14)
    coin_lab.shift(RIGHT * 0.2)                    # keep clear of the memory cells
    cart = VGroup(head, stem, box, mlab, link, mem, mem_lab, mem_lab2, coin, coin_lab)

    # known inclusions -> claimed equalities
    form = MathTex(r"\mathsf{L}", r"\subseteq", r"\mathsf{RL}", r"\subseteq", r"\mathsf{BPL}",
                   font_size=60, color=WHITE_)
    form[1].set_color(GREY_)
    form[3].set_color(GREY_)
    form.move_to(DOWN * 1.88)
    tgt = MathTex(r"\mathsf{L}", "=", r"\mathsf{RL}", "=", r"\mathsf{BPL}", font_size=60, color=WHITE_)
    tgt[1].set_color(YELLOW_)
    tgt[3].set_color(YELLOW_)
    tgt.move_to(form)

    root.add(pad, tape, digits, lab_in, cart, form)
    root.tape, root.cart, root.head, root.mem, root.coin = tape, cart, head, mem, coin
    root.coin_lab = coin_lab
    root.mem_lab = VGroup(mem_lab, mem_lab2)
    root.form, root.form_tgt = form, tgt
    return root


def anim_103(scene, mob, rt):
    tape, cart, head, mem, coin = mob.tape, mob.cart, mob.head, mob.mem, mob.coin
    n = len(tape)
    x_start = head.get_center()[0]
    x_far = tape[n - 5].get_center()[0]
    rng = np.random.default_rng(7)
    pattern = rng.integers(0, 2, size=(40, 3))
    state = {"x": x_start, "rot": 0.0, "step": -1}

    def mark(xh):
        idx = int(np.argmin([abs(c.get_center()[0] - xh) for c in tape]))
        for i, c in enumerate(tape):
            c.set_fill(A, opacity=0.35 if i == idx else 0.0)

    def mem_step(alpha, steps):
        st = int(alpha * steps)
        if st != state["step"]:
            state["step"] = st
            for c, b in zip(mem, pattern[st % len(pattern)]):
                c.set_fill(A, opacity=0.6 if b else 0.0)

    def move_to_x(xn):
        cart.shift(RIGHT * (xn - state["x"]))
        state["x"] = xn

    # 1) randomized run: the machine walks the input, scribbles in its tiny
    #    memory, and flips its coin
    flips = 5

    def run_random(m, a):
        e = smooth(a)
        move_to_x(x_start + (x_far - x_start) * e)
        target_rot = 2 * PI * flips * a
        coin.rotate(target_rot - state["rot"], axis=RIGHT, about_point=coin.get_center())
        state["rot"] = target_rot
        mem_step(a, 14)
        mark(head.get_center()[0])

    scene.play(UpdateFromAlphaFunc(mob, run_random), run_time=0.4 * rt, rate_func=linear)
    # 2) coin removed; the deterministic machine walks back with the SAME memory
    state["step"] = -1
    state["ms"] = 1.0
    coin_lab = mob.coin_lab
    cart.remove(coin, coin_lab)    # the coin (and its label) stays behind, floats up and fades
    mob.add(coin, coin_lab)
    coin_saved = coin.copy()
    lab_saved = coin_lab.copy()
    mem_lab = mob.mem_lab

    def run_det(m, a):
        fa = min(1.0, a / 0.3)
        coin.become(coin_saved.copy().set_opacity(0) if fa >= 1 else
                    coin_saved.copy().shift(UP * 0.35 * fa).fade(fa))
        coin_lab.become(lab_saved.copy().set_opacity(0) if fa >= 1 else
                        lab_saved.copy().shift(UP * 0.35 * fa).fade(fa))
        e = smooth(a)
        move_to_x(x_far + (x_start - x_far) * e)
        mem_step(a, 12)
        mark(head.get_center()[0])
        sc = 1 + 0.16 * np.sin(PI * min(1.0, a / 0.6))       # pulse "O(log n) memory"
        mem_lab.scale(sc / state["ms"])
        state["ms"] = sc

    scene.play(UpdateFromAlphaFunc(mob, run_det), run_time=0.28 * rt, rate_func=linear)
    scene.wait(0.04 * rt)
    # 3) the inclusions collapse to equalities
    mob.form_tgt.move_to(mob.form)
    scene.play(Transform(mob.form, mob.form_tgt), run_time=0.16 * rt)


# ================================================================ featured: 109
def big_109():
    root = VGroup()
    pad = Rectangle(width=BIG_W, height=BIG_H, stroke_width=0, fill_opacity=0)
    ox, oy = -2.35, -1.75
    X = lambda yr: -2.2 + (yr - 1950) * (4.65 / 80)
    yax = Arrow([ox, oy, 0], [ox, 2.05, 0], buff=0, stroke_width=2, color=GREY_, tip_length=0.14)
    xax = Arrow([ox, oy, 0], [2.6, oy, 0], buff=0, stroke_width=2, color=GREY_, tip_length=0.14)
    ylab = Text("time  (schematic)", font=SANS, font_size=22, color=GREY_).next_to(yax.get_end(), RIGHT, buff=0.12)
    ticks = VGroup()
    for yr in (1960, 1990, 2020):
        ticks.add(Line([X(yr), oy - 0.06, 0], [X(yr), oy + 0.06, 0], stroke_color=GREY_, stroke_width=2))
        ticks.add(Text(str(yr), font=SANS, font_size=22, color=GREY_).move_to([X(yr), oy - 0.3, 0]))
    # best known bounds: schoolbook, Karatsuba 1962, Toom 1963, Schoenhage-Strassen 1971,
    # Fuerer 2007, Harvey-van der Hoeven 2019 (n log n)
    L = [1.45, 0.95, 0.55, 0.0, -0.4, -0.85]
    yc = -0.93
    yrs = [1962, 1963, 1971, 2007, 2019]
    pts = [[-2.2, L[0]]]
    for i, yr in enumerate(yrs):
        pts += [[X(yr), L[i]], [X(yr), L[i + 1]]]
    pts += [[2.55, L[5]]]
    path = VMobject(stroke_color=WHITE_, stroke_width=3).set_points_as_corners([[x, y, 0] for x, y in pts])
    dots = VGroup(*[Dot([X(yr), L[i + 1], 0], radius=0.055, color=WHITE_) for i, yr in enumerate(yrs)])
    labs = VGroup(
        MathTex(r"n^2", font_size=30, color=WHITE_).next_to([-2.2, L[0], 0], UR, buff=0.08),
        MathTex(r"n^{1.58}", font_size=30, color=WHITE_).next_to([X(1962) - 0.06, L[1], 0], LEFT, buff=0.04),
        MathTex(r"n^{1+\varepsilon}", font_size=30, color=WHITE_).next_to([X(1963), L[2], 0], UR, buff=0.08),
        MathTex(r"n\log n\,\log\log n", font_size=30, color=WHITE_).move_to([(X(1971) + X(2007)) / 2 + 0.12, L[3] + 0.27, 0]),
    )
    limit = DashedLine([X(1971), L[5], 0], [2.55, L[5], 0], dash_length=0.1, stroke_width=3,
                       stroke_color=A)
    lim_lab = MathTex(r"n\log n", font_size=32, color=A).move_to([-0.4, L[5] + 0.26, 0])
    lim_lab2 = Text("conjectured limit (1971)", font=SANS, font_size=22, color=A).move_to([0.0, L[5] - 0.27, 0])
    # the conjecture (and the claim) live in one model of computation
    lim_lab3 = Text("on multitape Turing machines", font=SANS, font_size=20, color=GREY_)
    lim_lab3.next_to(lim_lab2, DOWN, buff=0.05)
    claim = VMobject(stroke_color=YELLOW_, stroke_width=3.4).set_points_as_corners(
        [[X(2026), L[5], 0], [X(2026), yc, 0], [2.55, yc, 0]])
    cdot = Dot([X(2026), yc, 0], radius=0.06, color=YELLOW_)
    spot = Circle(radius=0.16, stroke_color=YELLOW_, stroke_width=2).move_to([X(2026) + 0.05, (L[5] + yc) / 2, 0])
    mc = np.array([1.62, 1.15, 0])
    mag = Circle(radius=0.68, stroke_color=WHITE_, stroke_width=2, fill_color=CARD, fill_opacity=1).move_to(mc)
    m_lim = DashedLine(mc + LEFT * 0.62 + UP * 0.2, mc + RIGHT * 0.62 + UP * 0.2, dash_length=0.1,
                       stroke_width=3, stroke_color=A)
    m_cl = Line(mc + LEFT * 0.62 + DOWN * 0.2, mc + RIGHT * 0.62 + DOWN * 0.2, stroke_width=3.4,
                stroke_color=YELLOW_)
    m_gap = DoubleArrow(mc + UP * 0.17 + RIGHT * 0.15, mc + DOWN * 0.17 + RIGHT * 0.15, buff=0,
                        stroke_width=2, color=WHITE_, tip_length=0.09)
    conn = Line(spot.get_top() + LEFT * 0.03, mag.point_at_angle(-PI * 0.42), stroke_color=YELLOW_,
                stroke_width=1.6, stroke_opacity=0.8)
    c_lab = MathTex(r"n(\log n)^{1-\kappa}", font_size=32, color=YELLOW_).move_to([0.12, 1.55, 0])
    k_lab = MathTex(r"\kappa = 2^{-182}", font_size=30, color=WHITE_).move_to([0.12, 1.05, 0])
    magg = VGroup(mag, m_lim, m_cl, m_gap)
    lim = VGroup(lim_lab, lim_lab2, lim_lab3)
    root.add(pad, yax, xax, ylab, ticks, path, dots, labs, limit, lim,
             claim, cdot, spot, conn, magg, c_lab, k_lab)
    _hide(path, dots, labs, limit, lim_lab, lim_lab2, lim_lab3, claim, cdot, spot, conn, magg, c_lab, k_lab)
    root.parts = dict(path=path, dots=dots, labs=labs, limit=limit, lim=lim,
                      claim=claim, cdot=cdot, spot=spot, conn=conn, mag=magg, c_lab=c_lab, k_lab=k_lab)
    return root


def anim_109(scene, mob, rt):
    p = mob.parts
    # 1) 60 years of faster multiplication: a staircase of best known bounds
    _show(p["path"], p["dots"], p["labs"])
    scene.play(Create(p["path"], rate_func=linear),
               LaggedStart(*[FadeIn(m, scale=0.6) for m in p["dots"]], lag_ratio=0.35),
               LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in p["labs"]], lag_ratio=0.45),
               run_time=0.33 * rt)
    scene.wait(0.03 * rt)
    # 2) since 1971: n log n conjectured to be the speed limit
    _show(p["limit"], *p["lim"])
    scene.play(Create(p["limit"]), FadeIn(p["lim"], shift=RIGHT * 0.15), run_time=0.24 * rt)
    scene.wait(0.06 * rt)
    # 3) the claim: a sliver below the limit (zoomed in)
    _show(p["claim"], p["cdot"], p["spot"], p["conn"], p["mag"], p["c_lab"], p["k_lab"])
    scene.play(Create(p["claim"]), FadeIn(p["cdot"], scale=0.5), Create(p["spot"]),
               Create(p["conn"]), FadeIn(p["mag"], scale=0.7),
               FadeIn(p["c_lab"], shift=UP * 0.1), FadeIn(p["k_lab"], shift=UP * 0.1),
               run_time=0.26 * rt)


# ================================================================ featured: 138
def _sums(h):
    import itertools
    return sorted(sum(c) for r in range(len(h) + 1) for c in itertools.combinations(h, r))


def big_138():
    root = VGroup()
    pad = Rectangle(width=BIG_W, height=BIG_H, stroke_width=0, fill_opacity=0)
    nums = SS_A + SS_B
    xs = [-2.35, -1.85, -1.35, -0.7, -0.2, 0.3]
    boxes = VGroup()
    for i, (v, x) in enumerate(zip(nums, xs)):
        col = A if i < 3 else WHITE_
        sq = RoundedRectangle(width=0.44, height=0.42, corner_radius=0.06, stroke_color=col,
                              stroke_width=2, fill_color=col, fill_opacity=0.0)
        t = MathTex(str(v), font_size=32, color=WHITE_).move_to(sq)
        boxes.add(VGroup(sq, t).move_to([x, 1.8, 0]))
    div = DashedLine([-1.025, 2.1, 0], [-1.025, -1.3, 0], dash_length=0.08, stroke_color=DIM,
                     stroke_width=2)

    def tbox(tx, color, fs=34):
        m = MathTex(tx, font_size=fs, color=WHITE_)
        bx = SurroundingRectangle(m, buff=0.13, corner_radius=0.08, stroke_color=color, stroke_width=2)
        return VGroup(bx, m)

    target = tbox(r"t = 37", A).move_to([1.75, 1.8, 0])
    target2 = tbox(r"17 + 20 = 37", YELLOW_, fs=30).move_to([1.75, 1.8, 0])
    sa = _sums(SS_A)
    sb = _sums(SS_B)[::-1]
    ca = VGroup(*[MathTex(str(v), font_size=28, color=A).move_to([-1.85, 1.15 - 0.31 * i, 0])
                  for i, v in enumerate(sa)])
    cb = VGroup(*[MathTex(str(v), font_size=28, color=WHITE_).move_to([-0.2, 1.15 - 0.31 * i, 0])
                  for i, v in enumerate(sb)])
    ia, ib = sa.index(17), sb.index(20)
    ha = SurroundingRectangle(ca[ia], buff=0.07, corner_radius=0.06, stroke_color=YELLOW_, stroke_width=2)
    hb = SurroundingRectangle(cb[ib], buff=0.07, corner_radius=0.06, stroke_color=YELLOW_, stroke_width=2)
    match = Line(ha.get_right(), hb.get_left(), stroke_color=YELLOW_, stroke_width=2.4)
    cnt_a = MathTex(r"2^{n/2}", font_size=28, color=GREY_).move_to([-1.85, -1.55, 0])
    cnt_b = MathTex(r"2^{n/2}", font_size=28, color=GREY_).move_to([-0.2, -1.55, 0])
    hs = Text("meet in the middle, 1974", font=SANS, font_size=22, color=GREY_).move_to([-1.02, -2.0, 0])
    # running time: true shapes of 2^{n/2} and 2^{0.49 n} on a window n in [88, 100],
    # both divided by 2^{50} (so the claimed curve ends at exactly half height)
    ox, oy, W, H = 0.95, -1.75, 1.45, 2.65
    n0, n1 = 88, 100
    xax = Arrow([ox, oy, 0], [2.55, oy, 0], buff=0, stroke_width=2, color=GREY_, tip_length=0.12)
    yax = Arrow([ox, oy, 0], [ox, 1.2, 0], buff=0, stroke_width=2, color=GREY_, tip_length=0.12)
    nl = MathTex("n", font_size=30, color=GREY_).next_to(xax.get_end(), UP, buff=0.08).shift(LEFT * 0.1)
    tl = Text("time", font=SANS, font_size=22, color=GREY_).next_to(yax.get_end(), RIGHT, buff=0.1)
    f = lambda c: ParametricFunction(
        lambda n: np.array([ox + W * (n - n0) / (n1 - n0), oy + H * 2 ** (c * n - 50), 0]),
        t_range=[n0, n1, 0.1])
    c50 = DashedVMobject(f(0.5).set_stroke(WHITE_, 2.6), num_dashes=28)
    c49 = f(0.49).set_stroke(YELLOW_, 3.4)
    l50 = MathTex(r"2^{n/2}", font_size=32, color=WHITE_).move_to([ox + 0.5, oy + H - 0.1, 0])
    l49 = MathTex(r"2^{0.49n}", font_size=32, color=YELLOW_).move_to([ox + 0.62, oy + H * 0.5 - 0.05, 0])
    # the claimed method is randomized (correct w.p. >= 2/3): say so under its plot
    # (a tag, not plain text, so it doesn't read as a continuation of the grey caption)
    rnd = chip("RANDOMIZED", YELLOW_, size=14)
    rnd.move_to([(ox + 2.55) / 2, hs.get_y(), 0])
    axes = VGroup(xax, yax, nl, tl)
    root.add(pad, boxes, div, target, ca, cb, ha, hb, match, cnt_a, cnt_b, hs,
             axes, c50, c49, l50, l49, rnd)
    _hide(target, ca, cb, ha, hb, match, cnt_a, cnt_b, hs, c50, c49, l50, l49, rnd, xax, yax, nl, tl)
    root.parts = dict(boxes=boxes, ca=ca, cb=cb, ha=ha, hb=hb, match=match, cnt_a=cnt_a, cnt_b=cnt_b,
                      hs=hs, target=target, target2=target2, axes=axes, c50=c50, c49=c49, l50=l50, l49=l49,
                      rnd=rnd)
    return root


def anim_138(scene, mob, rt):
    p = mob.parts
    # 1) the question: do some of these numbers add up to the target?
    _show(p["target"])
    scene.play(LaggedStart(*[Indicate(bx, color=WHITE_, scale_factor=1.15) for bx in p["boxes"]],
                           lag_ratio=0.12),
               FadeIn(p["target"], shift=LEFT * 0.2), run_time=0.2 * rt)
    scene.wait(0.03 * rt)
    # 2) meet in the middle (1974): list each half's 2^{n/2} subset sums, find the pair
    _show(p["ca"], p["cb"], p["cnt_a"], p["cnt_b"], p["hs"])
    scene.play(LaggedStart(*[FadeIn(m, shift=DOWN * 0.12) for m in p["ca"]], lag_ratio=0.12),
               LaggedStart(*[FadeIn(m, shift=DOWN * 0.12) for m in p["cb"]], lag_ratio=0.12),
               FadeIn(p["cnt_a"]), FadeIn(p["cnt_b"]), FadeIn(p["hs"]), run_time=0.15 * rt)
    _show(p["ha"], p["hb"], p["match"])
    pick = [p["boxes"][i][0] for i in sorted(SS_PICK)]
    scene.play(Create(p["ha"]), Create(p["hb"]), Create(p["match"]),
               *[b.animate.set_fill(YELLOW_, opacity=0.25).set_stroke(YELLOW_) for b in pick],
               Transform(p["target"], p["target2"].move_to(p["target"])),
               run_time=0.14 * rt)
    scene.wait(0.06 * rt)
    # 3) the claimed running time drops below the 2^{n/2} curve
    _show(*p["axes"])
    scene.play(LaggedStart(*[FadeIn(m) for m in p["axes"]], lag_ratio=0.15), run_time=0.07 * rt)
    _show(p["c50"], p["c49"], p["l50"], p["l49"], p["rnd"])
    scene.play(Create(p["c50"]), Create(p["c49"]), FadeIn(p["l50"]), FadeIn(p["l49"]),
               FadeIn(p["rnd"], shift=UP * 0.1), rate_func=smooth, run_time=0.27 * rt)


# ================================================================ scene
def _load_tiles():
    data = json.loads((VIDEO / "data" / "grids.json").read_text())["c4_grid"]
    icons = {"103": icon_103, "109": icon_109, "138": icon_138, "106": icon_106,
             "105": icon_105, "104": icon_104, "108": icon_108, "113": icon_113,
             "132": icon_132, "124": icon_124, "128": icon_128, "142": icon_142}
    feats = {"103": (big_103, anim_103), "109": (big_109, anim_109), "138": (big_138, anim_138)}
    tiles = []
    for d in data:
        name = d["name"]
        head, _, last = name.rpartition(" ")
        if head and len(last) <= 2:          # no orphaned "2" / "𝔽ₚ" on a line of its own
            name = head + " " + last
        t = dict(num=d["num"], name=name, verdict=d["verdict"], icon=icons[d["num"]])
        if d.get("caption"):
            big, anim = feats[d["num"]]
            t["feature"] = dict(caption=d["caption"], big=big, animate=anim)
        tiles.append(t)
    return tiles


class C4Grid(GridScene):
    CHAPTER = "cs"
    TILES = _load_tiles()
