import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import hashlib
import itertools

import numpy as np

# Chromatic number of the plane (Hadwiger-Nelson), family 158.
# All geometry below is in "inches" (unit distance = 1) and is verified
# numerically at import time: the hexagon 7-colouring, the Moser spindle and
# the decorative unit-distance graph.

ACC = GOLD_
NUM = "158"
CACHE = BUILD / "cache" / "c5_plane"
SQ3 = np.sqrt(3.0)

PAL7 = [GOLD_, YELLOW_, GREEN_, TEAL_, SKY_, PURPLE_, PINK_]
PAL5 = [GOLD_, GREEN_, SKY_, PURPLE_, PINK_]
TRI = [GOLD_, TEAL_, PINK_]          # the three colours tried on the spindle
CIRCLE_BLOCKS = [(0, SKY_), (55, PINK_), (112, TEAL_), (168, PURPLE_),
                 (228, GREEN_), (290, BLUE_)]   # never GOLD_ (the centre's colour)


def P(x, y):
    return np.array([x, y, 0.0])


def mix(c1, c2, a):
    """Blend hex colour c1 over c2 with weight a (returns hex)."""
    return interpolate_color(ManimColor(c2), ManimColor(c1), a).to_hex()


# ------------------------------------------------------------ hexagon 7-colouring
HEX_R = 0.46                      # circumradius (inch): diameter 0.92 < 1


def hex_center(q, s, r=HEX_R):     # flat-top axial coordinates
    return np.array([1.5 * r * q, SQ3 * r * (s + q / 2)])


def hex_verts(q, s, r=HEX_R):
    c = hex_center(q, s, r)
    return [c + r * np.array([np.cos(k * PI / 3), np.sin(k * PI / 3)]) for k in range(6)]


def hex_cidx(q, s):
    return (q + 3 * s) % 7


def _seg_pt(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
    return np.linalg.norm(p - (a + t * ab))


def _poly_dist(A, B):
    return min(_seg_pt(p, Y[i], Y[(i + 1) % len(Y)])
               for X, Y in ((A, B), (B, A)) for p in X for i in range(len(Y)))


def verify_hex():
    # diameter of a tile < 1
    V = hex_verts(0, 0)
    diam = max(np.linalg.norm(a - b) for a, b in itertools.combinations(V, 2))
    assert diam < 1, diam
    # every tile's 6 neighbours carry the 6 other colours
    for q, s in itertools.product(range(-3, 4), repeat=2):
        nb = [hex_cidx(q + dq, s + ds) for dq, ds in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1))]
        assert len(set(nb + [hex_cidx(q, s)])) == 7
    # distinct same-coloured tiles are more than 1 apart
    cells = list(itertools.product(range(-4, 5), repeat=2))
    sep = min(_poly_dist(hex_verts(*a), hex_verts(*b)) for a, b in itertools.combinations(cells, 2)
              if hex_cidx(*a) == hex_cidx(*b) and np.linalg.norm(hex_center(*a) - hex_center(*b)) < 8 * HEX_R)
    assert sep > 1, sep
    return diam, sep


HEX_DIAM, HEX_SEP = verify_hex()      # 0.92, 1.217 (= r*sqrt 7)

# ------------------------------------------------------------ Moser spindle
SPIN_ANG = 2 * np.arcsin(1 / (2 * SQ3))     # angle between the two rhombi (~33.56 deg)


def spindle(rot=0.0):
    """Apex A at the origin; two rhombi of unit equilateral triangles whose
    axes are at 90 -/+ SPIN_ANG/2 degrees (+rot), so the tips are 1 apart."""
    pts = {"A": np.zeros(2)}
    for tag, th in (("1", PI / 2 - SPIN_ANG / 2 + rot), ("2", PI / 2 + SPIN_ANG / 2 + rot)):
        pts["B" + tag] = np.array([np.cos(th - PI / 6), np.sin(th - PI / 6)])
        pts["C" + tag] = np.array([np.cos(th + PI / 6), np.sin(th + PI / 6)])
        pts["D" + tag] = SQ3 * np.array([np.cos(th), np.sin(th)])
    edges = []
    for tag in "12":
        edges += [("A", "B" + tag), ("A", "C" + tag), ("B" + tag, "C" + tag),
                  ("B" + tag, "D" + tag), ("C" + tag, "D" + tag)]
    edges.append(("D1", "D2"))
    return pts, edges


def verify_spindle():
    pts, edges = spindle()
    for a, b in edges:
        assert abs(np.linalg.norm(pts[a] - pts[b]) - 1) < 1e-12, (a, b)
    unit = [(a, b) for a, b in itertools.combinations(pts, 2)
            if abs(np.linalg.norm(pts[a] - pts[b]) - 1) < 1e-9]
    assert len(pts) == 7 and len(edges) == 11 and len(unit) == 11
    # no proper 3-colouring exists (brute force)
    names = list(pts)
    ok = [c for c in itertools.product(range(3), repeat=7)
          if all(c[names.index(a)] != c[names.index(b)] for a, b in edges)]
    assert not ok


verify_spindle()

# ------------------------------------------------------------ schematic unit-distance graph
def wheel(a):
    return [np.zeros(2)] + [np.array([np.cos(a + k * PI / 3), np.sin(a + k * PI / 3)]) for k in range(6)]


def unit_graph():
    """Minkowski sum H + R(H), H = 19-point hexagonal patch (two hexagonal
    wheels), R = rotation by the spindle angle -- a genuine unit-distance
    graph full of Moser spindles, used as a *schematic* stand-in for de Grey's
    1,581-vertex graph (which is not drawn here)."""
    from scipy.spatial import cKDTree
    pts = [np.zeros(2)]
    for a in (0.0, 0.0, SPIN_ANG, SPIN_ANG):
        pts = [p + w for p in pts for w in wheel(a)]
    pts = np.array(pts)
    tree, keep, seen = cKDTree(pts), [], set()
    for i, p in enumerate(pts):
        if i not in seen:
            seen.update(tree.query_ball_point(p, 1e-7))
            keep.append(i)
    V = pts[keep]
    E = sorted((i, j) for i, j in cKDTree(V).query_pairs(1 + 1e-7)
               if abs(np.linalg.norm(V[i] - V[j]) - 1) < 1e-9)
    for i, j in E:
        assert abs(np.linalg.norm(V[i] - V[j]) - 1) < 1e-9
    return V, E


# ------------------------------------------------------------ 5-colour patch (baked PNG)
PATCH_R = 1.75        # inches
PATCH_SP = 0.62       # seed spacing (inches)


def patch_model(seed=11):
    rng = np.random.default_rng(seed)
    seeds = []
    for i in range(-6, 7):
        for j in range(-6, 7):
            p = np.array([PATCH_SP * (i + 0.5 * (j % 2)), PATCH_SP * SQ3 / 2 * j])
            p = p + rng.uniform(-0.22, 0.22, 2) * PATCH_SP
            if np.linalg.norm(p) < PATCH_R + 0.6:
                seeds.append(p)
    seeds = np.array(seeds)
    cols = -np.ones(len(seeds), int)
    order = np.argsort(np.linalg.norm(seeds, axis=1))
    for i in order:
        near = np.linalg.norm(seeds - seeds[i], axis=1) < 1.25 * PATCH_SP
        used = {cols[j] for j in np.nonzero(near)[0] if cols[j] >= 0}
        free = [c for c in range(5) if c not in used] or list(range(5))
        cols[i] = rng.choice(free)
    return seeds, cols


def patch_lookup(seeds, p):
    d = np.linalg.norm(seeds - p, axis=1)
    i = np.argsort(d)[:2]
    return i[0], d[i[1]] - d[i[0]]


def bake_patch(seeds, cols, px=900):
    from PIL import Image
    key = hashlib.md5((seeds.tobytes() + cols.tobytes() + str(px).encode() + b"v2")).hexdigest()[:10]
    out = CACHE / f"patch5_{key}.png"
    if out.exists():
        return out
    CACHE.mkdir(parents=True, exist_ok=True)
    xs = (np.arange(px) + 0.5) / px * 2 * PATCH_R - PATCH_R
    X, Y = np.meshgrid(xs, -xs)
    Q = np.stack([X.ravel(), Y.ravel()], 1)
    d = np.linalg.norm(Q[:, None, :] - seeds[None, :, :], axis=2)
    srt = np.sort(d, axis=1)
    idx = np.argmin(d, axis=1)
    rgb = np.array([[int(h[k:k + 2], 16) for k in (1, 3, 5)] for h in PAL5], float)
    bg = np.array([int(BG[k:k + 2], 16) for k in (1, 3, 5)], float)
    img = rgb[cols[idx]] * 0.78 + bg * 0.22
    border = np.clip((srt[:, 1] - srt[:, 0]) / 0.03, 0, 1)[:, None]
    img = img * border + bg * (1 - border)
    r = np.linalg.norm(Q, axis=1)
    alpha = np.clip((PATCH_R - r) / 0.012, 0, 1)
    arr = np.concatenate([img, 255 * alpha[:, None]], 1).reshape(px, px, 4).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(out)
    return out


def patch_path(seeds, cols, seed=5):
    """Random smooth needle path (unit length) over the patch that ends at the
    first clearly monochromatic pose. Returns (c0, c1, bulge, a0, a1, s_end)."""
    rng = np.random.default_rng(seed)
    S = np.linspace(0, 1, 241)

    def state(c0, c1, bulge, a0, a1, s):
        c, a = needle_pose(c0, c1, bulge, a0, a1, s)
        u = 0.5 * np.array([np.cos(a), np.sin(a)])
        e = (c - u, c + u)
        if max(np.linalg.norm(x) for x in e) > PATCH_R - 0.18:
            return "out"
        (i0, m0), (i1, m1) = patch_lookup(seeds, e[0]), patch_lookup(seeds, e[1])
        if cols[i0] != cols[i1]:
            return "ok"
        return "clash" if (i0 != i1 and min(m0, m1) > 0.3) else "edge"

    for _ in range(6000):
        c0 = rng.uniform(-0.5, 0.5, 2)
        c1 = rng.uniform(-0.55, 0.55, 2)
        if np.linalg.norm(c1 - c0) < 0.6:
            continue
        a0 = rng.uniform(0, PI)
        a1 = a0 + rng.choice([-1, 1]) * rng.uniform(0.8, 1.8)
        bulge = rng.uniform(-0.35, 0.35)
        prm = (c0, c1, bulge, a0, a1)
        sts = [state(*prm, s) for s in S]
        k = next((i for i, st in enumerate(sts) if st != "ok"), None)
        if k is None or sts[k] == "out" or S[k] < 0.5:
            continue
        # the clash entered at k must persist until it is unambiguous
        j = k
        while j < len(S) and sts[j] == "edge":
            j += 1
        if j < len(S) and sts[j] == "clash" and S[j] - S[k] < 0.12:
            j = min(j + 3, len(S) - 1) if all(st == "clash" for st in sts[j:j + 4]) else j
            return c0, c1, bulge, a0, a1, S[j]
    raise RuntimeError("no needle path found")


def needle_pose(c0, c1, bulge, a0, a1, s):
    d = c1 - c0
    perp = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9)
    return c0 + d * s + perp * bulge * np.sin(PI * s), a0 + (a1 - a0) * s


# ============================================================ scene
class C5Plane(VoiceScene):

    def T(self, a, b, f):
        """Absolute time a fraction f of the way from cue a to cue b."""
        ta, tb = self.cue(a), self.cue(b)
        return ta + f * (tb - ta)

    # ------------------------------------------------------------ HUD
    def build_hud(self):
        lab = MathTex(r"\chi(\mathbb{R}^2)", "=", r"\,?", font_size=40, color=WHITE_)
        lab[2].set_color(ACC)
        sub = txt("colors needed", 22, GREY_)
        labg = VGroup(lab, sub).arrange(DOWN, buff=0.06)
        toks = VGroup()
        for n in range(1, 9):
            c = Circle(radius=0.26, stroke_color=GREY_, stroke_width=2, fill_opacity=0)
            t = MathTex(str(n), font_size=32, color=WHITE_).move_to(c)
            toks.add(VGroup(c, t))
        toks.arrange(RIGHT, buff=0.2)
        yslot = txt("2026", 28, GREY_)
        row = VGroup(labg, toks, yslot).arrange(RIGHT, buff=0.55)
        panel = RoundedRectangle(width=row.width + 0.7, height=1.0, corner_radius=0.2,
                                 fill_color=CARD, fill_opacity=0.94, stroke_color=DIM, stroke_width=1.2)
        row.move_to(panel)
        VGroup(panel, row).move_to(UP * 3.12)
        self.hud_panel, self.hud_lab, self.hud_toks = panel, labg, toks
        self.year_pos = yslot.get_center()
        self.strikes = {}
        panel.set_z_index(4)
        labg.set_z_index(6)
        toks.set_z_index(6)
        return VGroup(panel, labg, toks)

    def pill(self, lo, hi, color):
        a, b = self.hud_toks[lo - 1], self.hud_toks[hi - 1]
        x0, x1 = a.get_left()[0] - 0.09, b.get_right()[0] + 0.09
        r = RoundedRectangle(width=x1 - x0, height=0.7, corner_radius=0.35, stroke_color=color,
                             stroke_width=2.5, fill_color=color, fill_opacity=0.16).set_z_index(5)
        return r.move_to([(x0 + x1) / 2, a.get_center()[1], 0])

    def exclude(self, n):
        tk = self.hud_toks[n - 1]
        c = tk.get_center()
        st = Line(c + 0.27 * (DL), c + 0.27 * (UR), color=GREY_, stroke_width=2.5).set_z_index(6)
        self.strikes[n] = st
        return AnimationGroup(tk[0].animate.set_stroke(DIM), tk[1].animate.set_color(DIM), Create(st))

    def note(self, s, x, color, size=24):
        t = txt(s, size, color, weight=SEMIBOLD)
        y = self.hud_panel.get_bottom()[1] - 0.3
        x = np.clip(x, -6.5 + t.width / 2, 6.5 - t.width / 2)
        t.move_to([x, y, 0])
        bg = BackgroundRectangle(t, color=BG, fill_opacity=0.85, buff=0.09, corner_radius=0.08)
        return VGroup(bg, t).set_z_index(6)

    def year_text(self, y, color=GREY_):
        return txt(str(int(y)), 28, color).move_to(self.year_pos).set_z_index(6)

    # ------------------------------------------------------------ needle
    def make_needle(self, length, a=None):
        line = Line(LEFT, RIGHT, color=WHITE_, stroke_width=4.5)
        line.set_stroke(BG, width=10, opacity=0.7, background=True)
        d0 = Dot(radius=0.12, color=WHITE_).set_stroke(WHITE_, 3)
        d1 = Dot(radius=0.12, color=WHITE_).set_stroke(WHITE_, 3)
        g = VGroup(line, d0, d1)
        g.length = length
        return g

    @staticmethod
    def place_needle(g, c, ang):
        u = np.array([np.cos(ang), np.sin(ang), 0.0]) * g.length / 2
        g[0].put_start_and_end_on(c - u, c + u)
        g[1].move_to(c - u)
        g[2].move_to(c + u)

    # ------------------------------------------------------------ construct
    def construct(self):
        rng = np.random.default_rng(7)
        hud = self.build_hud()

        # =========================================================== 1. paint
        U1 = 2.3
        A1 = P(0.0, -0.6)
        grid = VGroup(*[Line(P(x, -4.3), P(x, 4.3)) for x in np.arange(-7, 7.01, 1.0)],
                      *[Line(P(-7.6, y), P(7.6, y)) for y in np.arange(-4, 4.01, 1.0)])
        grid.set_stroke(DIM, 1.2, opacity=0.45)
        dots = VGroup()
        sp = 0.6
        for i in range(-13, 14):
            for j in range(-8, 9):
                p = P(sp * (i + 0.5 * (j % 2)), sp * 0.87 * j) + np.append(rng.uniform(-0.2, 0.2, 2), 0)
                if abs(p[0]) < 7.3 and abs(p[1]) < 4.2:
                    dots.add(Dot(p, radius=0.045, color=PAL7[rng.integers(7)], fill_opacity=0.9))
        dsort = sorted(dots, key=lambda d: np.linalg.norm(d.get_center() - A1))

        self.play_until(self.T("paint", "how", 0.29), FadeIn(grid, run_time=0.6),
                        LaggedStart(*[FadeIn(d, scale=0.2) for d in dsort], lag_ratio=0.02))

        # "with one rule:" -- the painting steps back
        self.play_at(self.T("paint", "how", 0.33), dots.animate.set_opacity(0.22),
                     grid.animate.set_stroke(opacity=0.25), run_time=0.7)

        # "any two points exactly one inch apart"
        nd1 = self.make_needle(U1)
        self.place_needle(nd1, A1 + RIGHT * U1 / 2, 0.0)
        one = txt("1 inch", 30, WHITE_).next_to(nd1[0], UP, buff=0.18)
        self.play_at(self.T("paint", "how", 0.51), GrowFromCenter(nd1[1]), run_time=0.35)
        self.play(GrowFromPoint(nd1[0], A1), GrowFromCenter(nd1[2]), run_time=0.6)
        self.play(FadeIn(one, shift=UP * 0.1), run_time=0.4)

        # "must get different colors" -> spin the partner around the unit circle
        self.play_at(self.T("paint", "how", 0.81),
                     nd1[1].animate.set_fill(ACC), nd1[2].animate.set_fill(CIRCLE_BLOCKS[0][1]),
                     run_time=0.45)
        t_r0, t_r1 = self.now + 0.15, self.T("how", "L0_end", 0.82)
        arcs = VGroup()
        bounds = [b for b, _ in CIRCLE_BLOCKS] + [360]
        for k, (b0, col) in enumerate(CIRCLE_BLOCKS):
            full = Arc(radius=U1, start_angle=b0 * DEGREES, angle=(bounds[k + 1] - b0) * DEGREES,
                       arc_center=A1, stroke_color=col, stroke_width=6)
            a = full.copy().set_stroke(opacity=0)
            a.full, a.b0, a.b1 = full, b0, bounds[k + 1]
            arcs.add(a)

        def theta_now():
            x = np.clip((self.now - t_r0) / (t_r1 - t_r0), 0, 1)
            return 360 * smooth(x)

        def upd_spin(g, dt):
            th = theta_now()
            g[0].put_start_and_end_on(A1, A1 + U1 * np.array([np.cos(th * DEGREES), np.sin(th * DEGREES), 0]))
            g[2].move_to(g[0].get_end())
            for b0, col in CIRCLE_BLOCKS:
                if th >= b0:
                    g[2].set_fill(col)

        def upd_arcs(arcs, dt):
            th = theta_now()
            for a in arcs:
                f = np.clip((th - a.b0) / (a.b1 - a.b0), 0, 1)
                if f <= 1e-3:
                    a.set_stroke(opacity=0)
                else:
                    a.pointwise_become_partial(a.full, 0, f)
                    a.set_stroke(opacity=1)

        self.add(arcs)
        self.add(nd1)
        self.bring_to_front(nd1)
        self.play(FadeOut(one), run_time=0.3)
        nd1.add_updater(upd_spin)
        arcs.add_updater(upd_arcs)

        # "How many colors do you need?"
        self.wait_until("how")
        self.play(FadeIn(hud[0], shift=DOWN * 0.3), FadeIn(hud[1], shift=DOWN * 0.3), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in hud[2]], lag_ratio=0.12), run_time=0.8)
        self.play(Indicate(self.hud_lab[0][2], color=ACC, scale_factor=1.4),
                  run_time=float(np.clip(self.cue("seven") - self.now - 0.05, 0.3, 0.7)))

        # =========================================================== 2. seven
        self.wait_until("seven")
        nd1.clear_updaters()
        arcs.clear_updaters()
        upd_spin(nd1, 0)
        upd_arcs(arcs, 0)
        year = self.year_text(1950)
        n7 = self.note("at most 7", self.hud_toks[6].get_x(), ACC)
        self.play(FadeOut(VGroup(grid, dots, arcs, nd1)), self.exclude(8),
                  self.hud_toks[6][0].animate.set_stroke(ACC, width=3),
                  FadeIn(n7, shift=DOWN * 0.1), FadeIn(year), run_time=0.7)

        U2 = 1.7
        R2 = HEX_R * U2
        O2 = P(0.0, -0.5)
        cells = []
        for q in range(-8, 9):
            for s in range(-9, 10):
                c = O2 + np.append(hex_center(q, s, R2), 0)
                if abs(c[0]) < 7.9 and abs(c[1]) < 4.7:
                    cells.append((q, s, c))
        cells.sort(key=lambda e: np.linalg.norm(e[2] - O2))
        hexes, hcol, centers = VGroup(), [], []
        for q, s, c in cells:
            verts = [O2 + np.append(v, 0) for v in hex_verts(q, s, R2)]
            dist = np.linalg.norm(c[:2] - O2[:2])
            w = float(np.clip(1.0 - (dist - 3.6) / 6.0, 0.5, 1.0))   # gentle vignette
            h = Polygon(*verts, stroke_color=GREY_, stroke_width=2, stroke_opacity=0.8 * w, fill_opacity=0)
            h.w = w
            hexes.add(h)
            hcol.append(PAL7[hex_cidx(q, s)])
            centers.append(c)
        centers = np.array(centers)

        def hex_color_at(p):
            return hcol[int(np.argmin(np.linalg.norm(centers[:, :2] - p[:2], axis=1)))]

        # "Tile the plane with hexagons"
        self.play_between(self.T("seven", "L1_end", 0.14), self.T("seven", "L1_end", 0.46),
                          LaggedStart(*[Create(h) for h in hexes], lag_ratio=0.025))

        # "just under an inch across"
        h0 = hexes[0]
        dia = Line(O2 + LEFT * R2, O2 + RIGHT * R2, color=WHITE_, stroke_width=4)
        dlab = txt("0.92", 26, WHITE_).next_to(dia, UP, buff=0.12)
        ny = O2[1] - R2 * SQ3 / 2 - 0.42
        nd2 = self.make_needle(U2)
        self.place_needle(nd2, P(O2[0] - R2 + U2 / 2, ny, ), 0.0)
        nlab = txt("1 inch", 26, WHITE_)
        nlab.add_background_rectangle(color=BG, opacity=0.8, buff=0.06)
        nlab.next_to(nd2[0], DOWN, buff=0.16)
        guide_l = DashedLine(O2 + LEFT * R2 + UP * 0.25, P(O2[0] - R2, ny - 0.15), dash_length=0.06,
                             color=GREY_, stroke_width=1.5)
        guide_r = DashedLine(O2 + RIGHT * R2 + UP * 0.25, P(O2[0] + R2, ny - 0.15), dash_length=0.06,
                             color=GREY_, stroke_width=1.5)
        self.play_at(self.T("seven", "L1_end", 0.49), h0.animate.set_stroke(WHITE_, width=4, opacity=1),
                     GrowFromCenter(dia), FadeIn(dlab), run_time=0.5)
        self.play(GrowFromPoint(nd2[0], nd2[0].get_start()), FadeIn(nd2[1:]),
                  Create(guide_l), Create(guide_r), FadeIn(nlab), run_time=0.6)

        # "and color them in this repeating pattern"
        flower = [i for i in range(len(hexes)) if np.linalg.norm(centers[i] - O2) < R2 * SQ3 * 1.05]
        rest = [i for i in range(len(hexes)) if i not in flower]
        t_f0 = self.T("seven", "L1_end", 0.71)
        self.wait_until(t_f0)
        self.play(FadeOut(VGroup(dia, dlab, guide_l, guide_r, nlab)),
                  LaggedStart(*[hexes[i].animate.set_fill(hcol[i], opacity=0.72).set_stroke(BG, 3, opacity=1)
                                for i in flower], lag_ratio=0.12),
                  nd2[1].animate.set_fill(hex_color_at(nd2[1].get_center())),
                  nd2[2].animate.set_fill(hex_color_at(nd2[2].get_center())),
                  run_time=0.7)

        # needle glides while the pattern spreads: its two ends never share a colour
        c_start = nd2[0].get_center()
        t_g0, t_g1 = self.now, self.cue("spindle") - 0.5

        def glide_pose(x):
            s = smooth(x)
            c = c_start + P(-3.4 * np.sin(PI * s * 0.9), 1.25 * np.sin(2 * PI * s) + 0.5 * s)
            return c, 1.55 * PI * s

        # verify the claim we are showing (ends always differently coloured)
        for x in np.linspace(0, 1, 400):
            c, a = glide_pose(x)
            u = np.array([np.cos(a), np.sin(a), 0]) * U2 / 2
            assert hex_color_at(c - u) != hex_color_at(c + u)
            assert -6.6 < (c - u)[0] < 6.6 and -3.6 < (c - u)[1] < 2.0
            assert -6.6 < (c + u)[0] < 6.6 and -3.6 < (c + u)[1] < 2.0

        def upd_glide(g, dt):
            x = np.clip((self.now - t_g0) / (t_g1 - t_g0), 0, 1)
            c, a = glide_pose(x)
            self.place_needle(g, c, a)
            g[1].set_fill(hex_color_at(g[1].get_center()))
            g[2].set_fill(hex_color_at(g[2].get_center()))

        self.add(nd2)
        nd2.add_updater(upd_glide)
        self.play(LaggedStart(*[hexes[i].animate.set_fill(hcol[i], opacity=0.72 * hexes[i].w)
                                .set_stroke(BG, 3, opacity=1) for i in rest], lag_ratio=0.012),
                  run_time=max(0.6, min(1.2, self.T("seven", "L1_end", 0.98) - self.now)))

        # =========================================================== 3. four + spindle
        self.wait_until("four")
        pill = self.pill(4, 7, ACC)
        n4 = self.note("at least 4", self.hud_toks[3].get_x(), ACC)
        self.play(LaggedStart(self.exclude(1), self.exclude(2), self.exclude(3), lag_ratio=0.25),
                  self.hud_toks[6][0].animate.set_stroke(GREY_, width=2),
                  FadeIn(pill), FadeTransform(n7, n4), run_time=0.6)
        self.wait_until(t_g1)
        nd2.clear_updaters()
        self.play_until("spindle", FadeOut(hexes), FadeOut(nd2))

        U3 = 2.45
        A3 = P(1.0, -2.85)
        spts, sedges = spindle()
        sp3 = {k: A3 + U3 * np.append(v, 0) for k, v in spts.items()}
        elines = {e: Line(sp3[e[0]], sp3[e[1]], color=WHITE_, stroke_width=3.5) for e in sedges}
        sdots = {k: Dot(p, radius=0.13, color=WHITE_).set_stroke(BG, 2) for k, p in sp3.items()}
        self.play_until(self.T("spindle", "L2_end", 0.32),
                        LaggedStart(*[Create(elines[e]) for e in sedges], lag_ratio=0.18),
                        LaggedStart(*[GrowFromCenter(sdots[k]) for k in ("A", "B1", "C1", "D1", "B2", "C2", "D2")],
                                    lag_ratio=0.3))
        sgroup = VGroup(*elines.values(), *sdots.values())

        # "the Moser spindle"
        cap = bold("Moser spindle", 40, WHITE_)
        csub = txt("7 points · 11 one-inch links", 24, GREY_)
        capg = VGroup(cap, csub).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        capg.move_to(P(-4.15, 0.75))
        self.play_at(self.T("spindle", "L2_end", 0.33),
                     LaggedStart(*[Indicate(elines[e], color=ACC, scale_factor=1.0) for e in sedges], lag_ratio=0.08),
                     run_time=0.8)
        self.play_at(self.T("spindle", "L2_end", 0.49), Write(cap), FadeIn(csub, shift=UP * 0.1), run_time=0.8)

        # "that can't be colored with three"
        sw = VGroup(*[Dot(radius=0.16, color=c) for c in TRI]).arrange(RIGHT, buff=0.16)
        swl = txt("3 colors?", 26, WHITE_)
        swg = VGroup(sw, swl).arrange(RIGHT, buff=0.25).next_to(capg, DOWN, buff=0.45, aligned_edge=LEFT)
        t3 = self.T("spindle", "L2_end", 0.70)
        self.play_at(t3, FadeIn(swg, shift=UP * 0.1), sdots["A"].animate.set_fill(TRI[0]).scale(1.25), run_time=0.4)
        cmap = {"B1": TRI[1], "C1": TRI[2], "B2": TRI[2], "C2": TRI[1]}
        self.play(*[sdots[k].animate.set_fill(c).scale(1.25) for k, c in cmap.items()], run_time=0.4)
        self.play(sdots["D1"].animate.set_fill(TRI[0]).scale(1.25),
                  sdots["D2"].animate.set_fill(TRI[0]).scale(1.25), run_time=0.4)
        bad = elines[("D1", "D2")]
        clash = txt("same color!", 26, RED_, weight=SEMIBOLD).next_to(sdots["D1"], RIGHT, buff=0.35)
        self.play(bad.animate.set_stroke(RED_, width=7), FadeIn(clash, shift=UP * 0.1),
                  Flash(sdots["D1"], color=RED_, flash_radius=0.3), Flash(sdots["D2"], color=RED_, flash_radius=0.3),
                  run_time=0.5)

        # =========================================================== 4. de Grey 2018
        self.wait_until("degrey")
        yv = ValueTracker(1950)
        cur = {"y": 1950}

        def upd_year(m, dt):
            y = int(round(yv.get_value()))
            if y != cur["y"]:
                cur["y"] = y
                m.become(self.year_text(y, WHITE_))

        year.add_updater(upd_year)
        self.play(FadeOut(VGroup(capg, swg, clash)), year.animate.set_color(WHITE_), run_time=0.5)
        self.play_until(self.T("degrey", "L3_end", 0.28), yv.animate.set_value(2018), rate_func=smooth)
        year.clear_updaters()

        # the spindle shrinks into place inside a much bigger unit-distance network
        V, E = unit_graph()
        U4 = 0.71
        O4 = P(2.0, -0.83)
        ext = V.max(axis=0), V.min(axis=0)
        gpts = [O4 + U4 * np.append(v, 0) for v in V]
        # spindle inside the graph: apex 0, rhombi along 30deg and 30deg + SPIN_ANG
        rot = (PI / 6 + SPIN_ANG / 2) - PI / 2
        target = VGroup(*[Line(O4 + U4 * np.append(spindle(rot)[0][a], 0), O4 + U4 * np.append(spindle(rot)[0][b], 0),
                               color=WHITE_, stroke_width=2.2) for a, b in sedges],
                        *[Dot(O4 + U4 * np.append(spindle(rot)[0][k], 0), radius=0.06, color=ACC) for k in sdots])
        # sanity: these are vertices of the graph
        for k, p in spindle(rot)[0].items():
            assert np.min(np.linalg.norm(V - p, axis=1)) < 1e-9
        edges_sorted = sorted(E, key=lambda e: np.linalg.norm(V[e[0]] + V[e[1]]))
        web = VMobject(stroke_color=SKY_, stroke_width=1.3, stroke_opacity=0.55)
        for i, j in edges_sorted:
            web.start_new_path(gpts[i])
            web.add_line_to(gpts[j])
        # each vertex appears when the first of its edges is drawn
        first = {}
        for k, (i, j) in enumerate(edges_sorted):
            first.setdefault(i, k)
            first.setdefault(j, k)
        vorder = sorted(range(len(V)), key=lambda i: first.get(i, 0))
        vdots = VGroup(*[Dot(gpts[i], radius=0.035, color=WHITE_) for i in vorder])
        # LaggedStart with short fades (d = 0.05 of the run) whose start times
        # are re-timed so each dot appears as the web reaches it
        nV, d_fade = len(vorder), 0.05
        lag = (1 - d_fade) / (d_fade * (nV - 1))
        ef = np.append(np.array([first.get(i, 0) + 1 for i in vorder]) / len(E) * (1 - d_fade), 1.0)
        kf = np.append(np.arange(nV) / (nV - 1) * (1 - d_fade), 1.0)

        def dot_rate(t):
            return float(np.interp(t, ef, kf))
        assert O4[1] + U4 * ext[0][1] < 1.95 and O4[1] + U4 * ext[1][1] > -3.65

        self.play_between(self.T("degrey", "L3_end", 0.28), self.T("degrey", "L3_end", 0.37),
                          Transform(sgroup, target))
        dg = bold("Aubrey de Grey, 2018", 36, WHITE_)
        dgs = txt("1,581 points", 28, ACC, weight=SEMIBOLD)
        dgn = txt("schematic (not the real graph)", 22, GREY_)
        dgg = VGroup(dg, dgs, dgn).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(P(-4.0, 0.75))
        dgg.align_to(P(-6.3, 0), LEFT)
        self.play(FadeIn(dg, shift=UP * 0.1), run_time=0.5)
        self.wait_until(self.T("degrey", "L3_end", 0.5))
        self.add(web)
        self.bring_to_front(sgroup)
        self.play_until(self.T("degrey", "L3_end", 0.86), Create(web, rate_func=linear),
                        LaggedStart(*[FadeIn(d) for d in vdots], lag_ratio=lag, rate_func=dot_rate),
                        FadeIn(dgs, shift=UP * 0.1), FadeIn(dgn))

        # "that needs five"
        pill5 = self.pill(5, 7, ACC)
        n5 = self.note("at least 5", self.hud_toks[4].get_x(), ACC)
        self.play_at(self.T("degrey", "L3_end", 0.88), self.exclude(4), Transform(pill, pill5),
                     FadeTransform(n4, n5),
                     web.animate.set_stroke(ACC, opacity=0.75), run_time=0.7)

        # =========================================================== 5. the claim
        self.wait_until("claim")
        card = paper_card(NUM, width=2.9).move_to(P(4.75, -0.45))
        tag = paper_tag(NUM, color=ACC)
        pill6 = self.pill(6, 7, YELLOW_)
        n6 = self.note("at least 6 (claimed)", self.hud_toks[5].get_x() + 0.35, YELLOW_)
        y26 = self.year_text(2026, YELLOW_)
        self.play(FadeOut(VGroup(web, vdots, sgroup, dgg)), self.exclude(5), Transform(pill, pill6),
                  FadeTransform(n5, n6), FadeTransform(year, y26),
                  *[self.hud_toks[k][1].animate.set_color(YELLOW_) for k in (5, 6)],
                  FadeIn(card, shift=LEFT * 2.5), FadeIn(tag), run_time=0.9)
        card.add_updater(lambda m, dt: m.shift(UP * 0.025 * dt))

        # "every five-coloring ... has two points one inch apart with the same color"
        seeds, cols = patch_model()
        png = bake_patch(seeds, cols)
        U5 = 1.3
        O5 = P(-1.3, -0.55)
        patch = ImageMobject(str(png))
        patch.width = 2 * PATCH_R * U5
        patch.move_to(O5)
        sw5 = VGroup(*[Dot(radius=0.13, color=c) for c in PAL5]).arrange(RIGHT, buff=0.12)
        sw5l = txt("5 colors", 26, WHITE_)
        sw5g = VGroup(sw5l, sw5).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        sw5g.next_to(patch, LEFT, buff=0.5).align_to(patch, UP).shift(DOWN * 0.3)
        c0, c1, bulge, a0, a1, s_end = patch_path(seeds, cols)
        nd5 = self.make_needle(U5)

        def pose5(x):
            c, a = needle_pose(c0, c1, bulge, a0, a1, s_end * x)
            return O5 + U5 * np.append(c, 0), a

        def col5(p):
            q = (p - O5)[:2] / U5
            return PAL5[cols[patch_lookup(seeds, q)[0]]]

        def set5(g, x):
            c, a = pose5(x)
            self.place_needle(g, c, a)
            g[1].set_fill(col5(g[1].get_center()))
            g[2].set_fill(col5(g[2].get_center()))

        set5(nd5, 0)
        self.play_at(self.T("claim", "range", 0.27), FadeIn(patch), FadeIn(sw5g, shift=RIGHT * 0.1), run_time=0.6)
        self.play(FadeIn(nd5, scale=0.8), run_time=0.35)
        t_p0, t_p1 = self.now, self.T("claim", "range", 0.83)

        def upd5(g, dt):
            set5(g, smooth(np.clip((self.now - t_p0) / (t_p1 - t_p0), 0, 1)))

        nd5.add_updater(upd5)
        self.wait_until(t_p1)
        nd5.clear_updaters()
        set5(nd5, 1.0)
        assert col5(nd5[1].get_center()) == col5(nd5[2].get_center())
        rings = VGroup(*[Circle(radius=0.22, color=RED_, stroke_width=4).move_to(d) for d in nd5[1:]])
        same = txt("same color!", 26, RED_, weight=SEMIBOLD)
        same.add_background_rectangle(color=BG, opacity=0.85, buff=0.08)
        same.next_to(VGroup(nd5, rings), UP, buff=0.2)
        self.play(nd5[0].animate.set_stroke(RED_, width=6), Create(rings), FadeIn(same, shift=UP * 0.1),
                  run_time=0.5)

        # "If it holds, the answer is six, or seven."
        self.wait_until("range")
        banner = self.claim_banner()
        banner.move_to(P(-1.45, -0.5))
        self.play(FadeOut(Group(patch, sw5g, nd5, rings, same)), FadeIn(banner, shift=UP * 0.2), run_time=0.8)
        n67 = self.note("6 or 7?", (self.hud_toks[5].get_x() + self.hud_toks[6].get_x()) / 2, YELLOW_, size=28)
        self.play_at(self.T("range", "L4_end", 0.48), FadeTransform(n6, n67),
                     *[Indicate(self.hud_toks[k], color=YELLOW_, scale_factor=1.25) for k in (5, 6)],
                     run_time=0.8)
        self.finish()

    def claim_banner(self):
        """result_banner look, with a formula line and a plain-words line."""
        lean = CATALOG[NUM]["lean"]
        f = MathTex(r"\chi(\mathbb{R}^2)\ \ge\ 6", font_size=48, color=WHITE_)
        w = txt("every 5-coloring of the plane has two\npoints at distance 1 with the same color", 26, WHITE_,
                line_spacing=0.9)
        head = Text("CLAIMED RESULT", font=SANS, font_size=15, color=YELLOW_, weight=BOLD)
        header = VGroup(head, lean_badge(13)).arrange(RIGHT, buff=0.25) if lean else VGroup(head)
        content = VGroup(header, f, w).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        box = RoundedRectangle(width=content.width + 0.7, height=content.height + 0.55, corner_radius=0.16,
                               stroke_color=YELLOW_, stroke_width=2, fill_color=CARD, fill_opacity=0.92)
        content.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.35)
        return VGroup(box, content)
