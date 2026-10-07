import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import numpy as np

# ---------------------------------------------------------------- constants
ACC = TEAL_
CACHE = BUILD / "cache" / "c3_kakeya"
PAPER4D = CACHE / "paper4d.png"          # first page of the 4D preprint (pdftoppm)

L = 3.4                    # the needle: one unit on screen
R4 = L / 4                 # deltoid rolling radius (tangent chords have length 4r = L)
K_LEV, ALPHA = 5, 0.8      # Perron tree: 2^5 slices, heart ratio per merge
N_SL = 2 ** K_LEV
H_T = L                    # every slice has height 1 needle
W_T = 2 * L * np.tan(PI / 6)   # 60-degree fan of directions
W_SL = W_T / N_SL


def ease(now, t0, t1, f=smooth):
    if t1 <= t0:
        return 1.0
    return float(f(np.clip((now - t0) / (t1 - t0), 0.0, 1.0)))


def perron_offsets(k, alpha, W):
    """Horizontal offsets of the 2^k slices after each merge level of the
    classical Perron-tree construction (Schoenberg's version): at level j the
    right half of every block slides left so the two halves' hearts overlap
    into a copy of the block's triangle scaled by alpha."""
    n = 2 ** k
    w = W / n
    off = np.zeros(n)
    stages = [off.copy()]
    for j in range(1, k + 1):
        bs = 2 ** j
        wh = (bs // 2) * w
        prod = alpha ** (j - 1)
        s = wh * (1 - prod) + (1 - alpha) * prod * 2 * wh
        off = off.copy()
        for b in range(0, n, bs):
            off[b + bs // 2:b + bs] -= s
        stages.append(off)
    return stages


def recenter(off):
    x0 = -W_T / 2 + np.arange(N_SL) * W_SL + off
    lo = min(x0.min(), off.min())
    hi = max((x0 + W_SL).max(), off.max())
    return off - (lo + hi) / 2


def slice_pts(i, off, B0):
    x0 = -W_T / 2 + i * W_SL + off
    return [B0 + np.array([x0, 0, 0]), B0 + np.array([x0 + W_SL, 0, 0]),
            B0 + np.array([off + 0.0, H_T, 0])]


def union_area(polys, res=1600):
    """Area of a union of polygons by rasterising (exact enough for a meter)."""
    from PIL import Image, ImageDraw
    pts = np.array([p[:2] for poly in polys for p in poly])
    (x0, y0), (x1, y1) = pts.min(0), pts.max(0)
    sc = res / max(x1 - x0, y1 - y0)
    im = Image.new("L", (int((x1 - x0) * sc) + 4, int((y1 - y0) * sc) + 4), 0)
    d = ImageDraw.Draw(im)
    for poly in polys:
        d.polygon([((p[0] - x0) * sc + 2, (y1 - p[1]) * sc + 2) for p in poly], fill=255)
    return (np.asarray(im) > 0).sum() / sc ** 2


def deltoid_curve(center, r, n=240):
    t = np.linspace(0, TAU, n)
    pts = [center + np.array([2 * r * np.cos(u) + r * np.cos(2 * u),
                              2 * r * np.sin(u) - r * np.sin(2 * u), 0]) for u in t]
    return Polygon(*pts[:-1])


def deltoid_needle(center, r, t):
    """Unit chord of the deltoid tangent at parameter t: midpoint on the
    incircle, direction rotating by -t/2 (a full turn of t = half turn of the
    needle)."""
    m = center + r * np.array([np.cos(t), np.sin(t), 0])
    d = np.array([-np.cos(t / 2), np.sin(t / 2), 0])
    return m + 2 * r * d, m - 2 * r * d


def card_from(path, width):
    """Same look as components.paper_card, for an arbitrary page image."""
    img = ImageMobject(str(path))
    img.width = width
    border = Rectangle(width=img.width, height=img.height, stroke_color=GREY_,
                       stroke_width=1.2, stroke_opacity=0.6).move_to(img)
    parts = []
    for i in range(5):
        s = Rectangle(width=img.width + 0.04 * i, height=img.height + 0.04 * i,
                      stroke_width=0, fill_color=BLACK, fill_opacity=0.10)
        s.move_to(img).shift(DR * 0.05)
        parts.append(s)
    return Group(*parts, img, border)


def early(frac=0.3):
    """rate_func that finishes in the first `frac` of the animation."""
    return lambda t: smooth(min(1.0, t / frac))


def late(frac=0.3):
    """rate_func that starts after the first `frac` of the animation."""
    return lambda t: smooth(max(0.0, (t - frac) / (1 - frac)))


def place_left(mob, x, y):
    mob.move_to([x + mob.width / 2, y, 0])
    return mob


class C3Kakeya(VoiceScene):

    # ============================================================ helpers
    def construct(self):
        self.phase_needle()
        self.phase_besicovitch()
        self.phase_conjecture()
        self.phase_wang_zahl()
        self.phase_claims()
        self.finish()

    # ============================================================ 1. needle
    def phase_needle(self):
        C = np.array([-1.6, -0.15, 0])
        self.C = C
        title = caps("The Kakeya needle problem", 20, ACC).move_to(UP * 3.4)
        self.title = title
        needle = Line(C + LEFT * L / 2, C + RIGHT * L / 2, color=YELLOW_, stroke_width=7)
        self.needle = needle
        brace = Brace(needle, DOWN, buff=0.14, color=GREY_)
        one = tex("1", 40, GREY_).next_to(brace, DOWN, buff=0.1)

        self.play_until("needle+0.6", Create(needle), FadeIn(title, shift=DOWN * 0.1))
        self.play_until("needle+1.3", GrowFromCenter(brace), FadeIn(one, shift=UP * 0.1))

        # --- spin it about its midpoint: sweeps a disk of area pi/4
        th = ValueTracker(0.0)

        def sweep_shape():
            a = max(th.get_value(), 1e-3)
            g = VGroup(*[Sector(radius=L / 2, angle=a, start_angle=s, arc_center=C,
                                fill_color=ACC, fill_opacity=0.30, stroke_width=0)
                         for s in (0.0, PI)])
            return g

        sweep = always_redraw(sweep_shape)
        needle.add_updater(lambda m: m.put_start_and_end_on(
            C - L / 2 * np.array([np.cos(th.get_value()), np.sin(th.get_value()), 0]),
            C + L / 2 * np.array([np.cos(th.get_value()), np.sin(th.get_value()), 0])))
        self.add(sweep, needle)
        self.play_until("needle+1.65", FadeOut(brace), FadeOut(one))
        self.play_until("L0_end-1.45", th.animate.set_value(PI), rate_func=smooth)
        needle.clear_updaters()
        sweep.clear_updaters()
        disk = Circle(radius=L / 2, arc_center=C, stroke_color=ACC, stroke_width=2.5,
                      fill_color=ACC, fill_opacity=0.30)
        self.remove(sweep)
        self.add(disk, needle)

        # --- area readout
        area_lbl = txt("area", 26, GREY_)
        v1 = tex(r"\tfrac{\pi}{4}\approx 0.79", 46)
        s1 = txt("disk", 22, GREY_)
        v2 = tex(r"\tfrac{\pi}{8}\approx 0.39", 46)
        s2 = txt("deltoid", 22, GREY_)
        ro = VGroup(area_lbl, v1, s1).arrange(DOWN, buff=0.22).move_to([3.6, 0.0, 0])
        v2.move_to(v1)
        s2.move_to(s1)
        self.play_until("L0_end-1.1", FadeIn(area_lbl, shift=UP * 0.1), Write(v1), FadeIn(s1))

        # --- a deltoid does better: same needle, three-point turn, half the area
        D = C - np.array([R4, 0, 0])
        delt = deltoid_curve(D, R4).set_stroke(ACC, 2.5).set_fill(ACC, 0.30)
        ghost = DashedVMobject(Circle(radius=L / 2, arc_center=C), num_dashes=48)
        ghost.set_stroke(GREY_, 1.6, 0.55)
        self.add(ghost)
        self.play_until("L0_end-0.7", Transform(disk, delt), FadeIn(ghost),
                        FadeTransform(v1, v2), FadeTransform(s1, s2))
        self.ghost = ghost
        t0, t1 = self.now, self.cue("besi+0.75")

        def turn(m, dt):
            a, b = deltoid_needle(D, R4, TAU * ease(self.now, t0, t1, smooth))
            m.put_start_and_end_on(a, b)
        needle.add_updater(turn)
        # Besicovitch enters
        self.wait_until("besi")
        title2 = caps("Besicovitch, 1928", 20, ACC).move_to(title)
        self.play_until("besi+0.5", FadeOut(title, shift=UP * 0.2), FadeIn(title2, shift=UP * 0.2))
        self.title = title2
        self.wait_until("besi+0.75")
        needle.remove_updater(turn)
        self.delt, self.ro = disk, VGroup(area_lbl, v2, s2)

    # ============================================================ 2. Perron tree
    def phase_besicovitch(self):
        needle = self.needle
        B0 = np.array([-1.6, -2.05, 0])
        stages = [recenter(o) for o in perron_offsets(K_LEV, ALPHA, W_T)]
        polys_at = [[slice_pts(i, o[i], B0) for i in range(N_SL)] for o in stages]
        A0 = W_T * H_T / 2
        areas = [union_area(p) / A0 for p in polys_at]

        slices = VGroup(*[Polygon(*polys_at[0][i], stroke_color="#9BE8D5", stroke_width=0.8,
                                  stroke_opacity=0.0, fill_color=ACC, fill_opacity=0.0)
                          for i in range(N_SL)])
        apex = B0 + UP * H_T
        left_dir = normalize(polys_at[0][0][0] - apex)

        # needle goes to the left edge of the fan, apex up
        self.play_until("besi+1.05",
                        needle.animate.put_start_and_end_on(apex, apex + L * left_dir),
                        FadeOut(self.delt), FadeOut(self.ro), FadeOut(self.ghost))
        self.add(slices, needle)

        # sweep: as the needle pivots about the apex, the fan of thin triangles appears
        ph = ValueTracker(0.0)

        def fan_needle(m, dt):
            x = -W_T / 2 + ph.get_value() * W_T
            tip = B0 + np.array([x, 0, 0])
            m.put_start_and_end_on(apex, apex + L * normalize(tip - apex))

        def fan_reveal(m, dt):
            p = ph.get_value()
            for i, s in enumerate(m):
                on = (i + 0.5) / N_SL <= p + 1e-6
                s.set_fill(opacity=0.36 if on else 0.0)
                s.set_stroke(opacity=0.5 if on else 0.0)

        needle.add_updater(fan_needle)
        slices.add_updater(fan_reveal)

        # area meter (relative to the starting triangle)
        mx, my = 4.55, 1.35
        m_lbl = txt("area", 26, GREY_)
        m_pct = DecimalNumber(100, num_decimal_places=0, unit=r"\%", font_size=40,
                              color=WHITE_)
        m_bg = RoundedRectangle(width=2.6, height=0.22, corner_radius=0.06, stroke_color=DIM,
                                stroke_width=1.5, fill_opacity=0)
        m_bar = Rectangle(width=2.6, height=0.22, stroke_width=0, fill_color=ACC,
                          fill_opacity=0.85)
        VGroup(m_lbl, m_pct).arrange(RIGHT, buff=0.35)
        m_bg.next_to(VGroup(m_lbl, m_pct), DOWN, buff=0.25)
        meter = VGroup(m_lbl, m_pct, m_bg).move_to([mx, my, 0])
        m_bar.move_to(m_bg)
        frac = ValueTracker(1.0)

        def bar_upd(m, dt):
            m.stretch_to_fit_width(max(2.6 * frac.get_value(), 1e-3))
            m.align_to(m_bg, LEFT)
        m_bar.add_updater(bar_upd)
        m_pct.add_updater(lambda m, dt: m.set_value(100 * frac.get_value()))

        self.play_until("besi+1.65", ph.animate.set_value(1.0),
                        FadeIn(meter), FadeIn(m_bar), rate_func=linear)
        needle.clear_updaters()
        slices.clear_updaters()
        for s in slices:
            s.set_fill(opacity=0.36).set_stroke(opacity=0.5)

        # slide! each level: right half of every block slides left over its partner
        self.play(FadeOut(needle), run_time=0.15)
        t_start, t_end = self.now, self.cue("zero+0.3")
        weights = np.array([1.35, 1.1, 0.95, 0.85, 0.8])
        bounds = t_start + np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * (t_end - t_start)
        for j in range(1, K_LEV + 1):
            delta = stages[j] - stages[j - 1]
            anims = [s.animate.shift(RIGHT * d) for s, d in zip(slices, delta) if abs(d) > 1e-6]
            self.play_until(bounds[j], *anims, frac.animate.set_value(areas[j]))
        m_bar.clear_updaters()

        # ---- zero: keep slicing finer and the area tends to 0
        lim = tex(r"\to 0", 44, YELLOW_).next_to(m_pct, RIGHT, buff=0.25)
        lim_c = txt("as the slices get thinner", 22, GREY_).next_to(m_bg, DOWN, buff=0.22)
        # directions dial
        dc = np.array([4.55, -1.75, 0])
        RD = 1.1
        d_arc = Arc(radius=RD, start_angle=0, angle=PI, arc_center=dc, stroke_color=DIM,
                    stroke_width=2)
        d_base = Line(dc + LEFT * RD, dc + RIGHT * RD, stroke_color=DIM, stroke_width=2)
        d_lbl = txt("directions", 22, GREY_).next_to(d_base, DOWN, buff=0.18)
        spread = ValueTracker(0.0)

        def dial_fill():
            a = spread.get_value()
            return Sector(radius=RD, start_angle=PI / 3 - a, angle=PI / 3 + 2 * a + 1e-4,
                          arc_center=dc, fill_color=ACC, fill_opacity=0.45, stroke_width=0)
        d_fill = always_redraw(dial_fill)
        self.play_until("zero+0.85", Write(lim), FadeIn(lim_c, shift=UP * 0.1),
                        Create(d_arc), Create(d_base), FadeIn(d_lbl), FadeIn(d_fill))

        # ---- two rotated copies cover the remaining directions
        final = stages[-1]
        hx = -W_T / 2 + final[0]
        pivot = B0 + np.array([hx + ALPHA ** K_LEV * W_T / 2, ALPHA ** K_LEV * H_T, 0])
        cp = slices.copy()
        cm = slices.copy()
        self.add(cp, cm, slices)
        self.play_between("zero+0.9", "zero+2.0",
                          Rotate(cp, PI / 3, about_point=pivot),
                          Rotate(cm, -PI / 3, about_point=pivot),
                          spread.animate.set_value(PI / 3))
        d_fill.clear_updaters()
        trees = {0: cm, 1: slices, 2: cp}   # directions [0,60), [60,120), [120,180]

        # ---- a needle in every direction: sweep psi from 0 to 180 degrees
        def needle_in(psi):
            c = min(int(psi // (PI / 3)), 2)
            loc = psi - (c - 1) * PI / 3            # direction inside the original fan
            x = -H_T / np.tan(loc)
            u = np.clip((x + W_T / 2) / W_SL, 0, N_SL - 1e-6)
            i = int(u)
            f = u - i
            bl, br, ap = trees[c][i].get_vertices()[:3]
            bp = bl + f * (br - bl)
            e, q = br - bl, ap - bl
            h = abs(e[0] * q[1] - e[1] * q[0]) / np.linalg.norm(e)
            return ap, ap + h * normalize(bp - ap)

        psi = ValueTracker(1e-3)
        trail = VGroup()
        trail_psi = []
        for c in (0, 1, 2):
            for i in range(N_SL):
                xm = -W_T / 2 + (i + 0.5) * W_SL
                loc = np.arctan2(H_T, -xm)
                ps = loc + (c - 1) * PI / 3
                a, b = needle_in(ps)
                trail.add(Line(a, b, stroke_color=YELLOW_, stroke_width=1.7, stroke_opacity=0))
                trail_psi.append(ps)
        trail_psi = np.array(trail_psi)

        def trail_upd(m, dt):
            p = psi.get_value()
            for ln, ps in zip(m, trail_psi):
                ln.set_stroke(opacity=0.42 if ps <= p else 0.0)
        trail.add_updater(trail_upd)
        sw = Line(*needle_in(1e-3), stroke_color=YELLOW_, stroke_width=6)
        sw.add_updater(lambda m, dt: m.put_start_and_end_on(*needle_in(psi.get_value())))
        ptr = Line(dc, dc + RIGHT * RD, stroke_color=YELLOW_, stroke_width=4)
        ptr.add_updater(lambda m, dt: m.put_start_and_end_on(
            dc, dc + RD * np.array([np.cos(psi.get_value()), np.sin(psi.get_value()), 0])))
        self.add(trail)
        self.play_until("zero+2.25", FadeIn(sw), FadeIn(ptr))
        self.play_until("zero+4.3", psi.animate.set_value(PI - 1e-3), rate_func=linear)
        trail.clear_updaters()
        sw.clear_updaters()
        ptr.clear_updaters()

        star = VGroup(cm, slices, cp, trail)
        self.star, self.pivot = star, pivot
        # gentle drift while the sentence finishes
        self.play_until("conj", FadeOut(sw, rate_func=early(0.25)), FadeOut(ptr, rate_func=early(0.25)),
                        Rotate(star, -6 * DEGREES, about_point=pivot))
        self.side = VGroup(meter, m_bar, lim, lim_c, d_arc, d_base, d_lbl, d_fill)

    # ============================================================ 3. the conjecture
    def phase_conjecture(self):
        star = self.star
        target = star.copy()
        target.scale(3.0 / max(target.width, 1e-3))
        if target.height > 2.5:
            target.scale(2.5 / target.height)
        target.move_to([4.15, 0.45, 0])
        target[3].set_stroke(opacity=0.22)        # needles recede: the set itself is the subject now
        title3 = caps("The Kakeya conjecture", 20, ACC).move_to(self.title)
        formula = MathTex(r"K\subset\mathbb{R}^n", r"\text{ contains a unit segment in every direction}",
                          r"\;\Longrightarrow\;", r"\dim K = n", font_size=36, color=WHITE_)
        formula.move_to(UP * 2.65)
        self.formula = formula
        self.play_until("conj+0.9", Transform(star, target), FadeOut(self.side),
                        FadeOut(self.title, shift=UP * 0.2), FadeIn(title3, shift=UP * 0.2))
        self.title = title3
        self.play_until("conj+2.4", Write(formula))
        lab_area = VGroup(txt("area", 24, GREY_), tex(r"\to 0", 34, GREY_)).arrange(RIGHT, buff=0.15)
        lab_dim = VGroup(txt("dimension", 26, ACC, weight=SEMIBOLD), tex(r"= 2", 36, ACC)).arrange(RIGHT, buff=0.15)
        lab_area.next_to(star, DOWN, buff=0.35)
        lab_dim.next_to(lab_area, DOWN, buff=0.2)
        star.add_updater(lambda m, dt: m.rotate(-0.05 * dt, about_point=m.get_center()))
        self.play_until("conj+3.0", FadeIn(lab_area, shift=UP * 0.1))
        self.wait_until("ndim-1.3")
        self.play_until("ndim-0.5", FadeIn(lab_dim, shift=UP * 0.1),
                        formula[3].animate.set_color(YELLOW_))
        self.star_labels = VGroup(lab_area, lab_dim)

        # ---- the table: one row per dimension
        X_N, X_D, X_M = -6.3, -4.75, -1.25
        ROWS = {2: 0.75, 3: -0.05, 4: -0.85, 5: -1.65}
        HEAD = 1.5
        self.X_D, self.X_M, self.ROWS, self.HEAD = X_D, X_M, ROWS, HEAD
        h_dim = bold("dimension", 22, GREY_)
        place_left(h_dim, X_D, HEAD)
        labels = {}
        for n, y in ROWS.items():
            s = r"n\ge 5" if n == 5 else f"n={n}"
            labels[n] = place_left(tex(s, 34), X_N, y)
        seps = VGroup(*[Line([-6.45, y - 0.4, 0], [1.05, y - 0.4, 0], stroke_color=DIM,
                             stroke_width=1.2, stroke_opacity=0.7)
                        for y in [HEAD + 0.8] + list(ROWS.values())][1:])
        head_line = Line([-6.45, HEAD - 0.28, 0], [1.05, HEAD - 0.28, 0], stroke_color=GREY_,
                         stroke_width=1.5, stroke_opacity=0.8)
        cells = {}
        for n, y in ROWS.items():
            cells[n] = place_left(txt("?", 26, GREY_), X_D, y)
        self.labels, self.cells = labels, cells
        self.wait_until("ndim")
        self.play_until("ndim+1.3", FadeIn(h_dim), Create(head_line),
                        LaggedStart(*[FadeIn(VGroup(labels[n], cells[n]), shift=RIGHT * 0.2)
                                      for n in ROWS], lag_ratio=0.25),
                        Create(seps))
        # n = 2 is known: Davies 1971 (the planar case of our picture)
        dav = self.check_cell("Davies 1971", X_D, ROWS[2])
        self.play_until("ndim+2.2", FadeOut(cells[2], rate_func=early(0.25)),
                        TransformFromCopy(lab_dim, dav))
        cells[2] = dav
        self.table = VGroup(h_dim, head_line, seps, *labels.values())

    def check_cell(self, label, x, y, color=GREEN_):
        ck = check_mark(color, size=0.22, width=4)
        t = txt(label, 24, WHITE_)
        g = VGroup(ck, t).arrange(RIGHT, buff=0.14)
        return place_left(g, x, y)

    # ============================================================ 4. Wang–Zahl
    def phase_wang_zahl(self):
        ROWS = self.ROWS
        star = self.star
        hl = RoundedRectangle(width=7.65, height=0.72, corner_radius=0.1, stroke_color=ACC,
                              stroke_width=1.6, fill_color=CARD_HI, fill_opacity=0.9)
        hl.move_to([-2.7, ROWS[3], 0])
        self.hl = hl

        # 3D hedgehog of needles, slowly turning
        rng = np.random.default_rng(7)
        n = 44
        k = np.arange(n) + 0.5
        z = k / n
        ph = k * PI * (3 - np.sqrt(5))
        dirs = np.stack([np.sqrt(1 - z ** 2) * np.cos(ph), np.sqrt(1 - z ** 2) * np.sin(ph), z], 1)
        cen = rng.normal(0, 0.10, (n, 3))
        seg = 2.35
        bc = np.array([4.15, 0.8, 0])
        lines = VGroup(*[Line(LEFT, RIGHT, stroke_color=ACC, stroke_width=2.4) for _ in range(n)])
        t0 = self.now
        tilt = 0.42

        def proj(p, w):
            x = p[..., 0] * np.cos(w) - p[..., 1] * np.sin(w)
            y = p[..., 0] * np.sin(w) + p[..., 1] * np.cos(w)
            zz = p[..., 2]
            Y = y * np.sin(tilt) + zz * np.cos(tilt)
            dep = y * np.cos(tilt) - zz * np.sin(tilt)
            return x, Y, dep

        def bush_upd(m, dt):
            w = 0.4 + 0.32 * (self.now - t0)
            a = cen + dirs * seg / 2
            b = cen - dirs * seg / 2
            ax, ay, ad = proj(a, w)
            bx, by, bd = proj(b, w)
            for i, ln in enumerate(m):
                ln.put_start_and_end_on(bc + np.array([ax[i], ay[i], 0]),
                                        bc + np.array([bx[i], by[i], 0]))
                dep = (ad[i] + bd[i]) / 2
                ln.set_stroke(opacity=float(np.clip(0.75 - 0.35 * dep, 0.3, 1.0)))
        bush_upd(lines, 0)
        lines.add_updater(bush_upd)
        bush_lbl = tex(r"\mathbb{R}^3", 32, GREY_).move_to(bc + np.array([1.55, 1.05, 0]))

        name = bold("Hong Wang & Joshua Zahl", 29)
        sub = txt("3D Kakeya set conjecture  ·  2025", 22, GREY_)
        hum = chip("HUMAN PROOF", GREEN_, size=20)
        credit = VGroup(name, sub, hum).arrange(DOWN, buff=0.2).move_to([4.15, -1.75, 0])

        star.clear_updaters()
        self.wait_until("wz")
        self.add(hl)
        self.bring_to_back(hl)
        hl.set_opacity(0)
        self.play_until("wz+0.7", FadeOut(star, shift=RIGHT * 0.4),
                        FadeOut(self.star_labels, shift=RIGHT * 0.4),
                        hl.animate.set_fill(CARD_HI, 0.9).set_stroke(ACC, 1.6, 1.0))
        self.add(lines)
        self.play_until("wz+1.3", FadeIn(lines), FadeIn(bush_lbl))
        self.play_until("wz+2.4", Write(name))
        wzc = self.check_cell("Wang–Zahl 2025", self.X_D, ROWS[3])
        self.wait_until("wz+2.5")
        self.play_until("wz+3.2", FadeOut(self.cells[3], rate_func=early(0.3)),
                        FadeIn(wzc, shift=RIGHT * 0.15, rate_func=late(0.3)),
                        FadeIn(sub, shift=UP * 0.1))
        self.cells[3] = wzc
        self.wait_until("wz+4.7")
        self.play_until("wz+5.3", FadeIn(hum, scale=1.15))
        self.bush = VGroup(lines, bush_lbl)
        self.credit = credit

    # ============================================================ 5. the two AI claims
    def phase_claims(self):
        ROWS, X_M, X_D = self.ROWS, self.X_M, self.X_D
        card3 = paper_card("074", width=2.8).move_to([4.15, -0.2, 0])
        tag = paper_tag("074", color=ACC)

        self.wait_until("claim3")
        self.bush[0].clear_updaters()
        self.play_until("claim3+0.8", FadeOut(self.bush, shift=RIGHT * 0.4),
                        FadeOut(self.credit, shift=RIGHT * 0.4),
                        FadeIn(card3, shift=LEFT * 0.8), FadeIn(tag, shift=RIGHT * 0.2))
        # maximal column
        h_max = bold("maximal", 22, GREY_)
        place_left(h_max, X_M, self.HEAD)
        mcells = {
            2: self.check_cell("Córdoba 1977", X_M, ROWS[2]),
            4: place_left(txt("?", 26, GREY_), X_M, ROWS[4]),
            5: place_left(txt("?", 26, GREY_), X_M, ROWS[5]),
        }
        self.play_until("claim3+1.4", FadeIn(h_max, shift=DOWN * 0.1),
                        LaggedStart(*[FadeIn(mcells[n], shift=RIGHT * 0.15) for n in (2, 4, 5)],
                                    lag_ratio=0.2))
        claimed3 = place_left(chip("CLAIMED", YELLOW_, size=20), X_M, ROWS[3])
        arr = Arrow(self.cells[3].get_right() + RIGHT * 0.05, claimed3.get_left() + LEFT * 0.02,
                    buff=0.05, stroke_width=3, color=GREY_, max_tip_length_to_length_ratio=0.35,
                    max_stroke_width_to_length_ratio=8)
        self.play_until("claim3+2.0", GrowArrow(arr))
        self.play_until("claim3+2.6", FadeIn(claimed3, scale=1.25))
        # "the maximal conjecture"
        mformula = tex(r"\|K_\delta f\|_{L^3(S^2)}\lesssim_\varepsilon \delta^{-\varepsilon}\,\|f\|_{L^3(\mathbb{R}^3)}",
                       32).move_to([4.15, -2.6, 0])
        card3.add_updater(lambda m, dt: m.shift(UP * 0.03 * dt))
        self.wait_until("claim3+2.8")
        self.play_until("claim3+4.0", Write(mformula))
        self.wait_until("tubes-1.5")
        self.play_until("tubes-0.6", Indicate(h_max, color=YELLOW_, scale_factor=1.15),
                        h_max.animate.set_color(YELLOW_))

        # ---- tubes: thin tubes in different directions can't pile up much
        tc = np.array([4.15, 0.35, 0])
        rng = np.random.default_rng(11)
        nt = 13
        angs = np.linspace(0, PI, nt, endpoint=False) + 0.11
        perp = rng.uniform(-1.0, 1.0, nt)
        along = rng.uniform(-0.45, 0.45, nt)
        tubes = VGroup()
        for a, p, s in zip(angs, perp, along):
            d = np.array([np.cos(a), np.sin(a), 0])
            nv = np.array([-np.sin(a), np.cos(a), 0])
            r = Rectangle(width=2.9, height=0.12, stroke_color=ACC, stroke_width=1.0,
                          stroke_opacity=0.7, fill_color=ACC, fill_opacity=0.24)
            r.rotate(a).move_to(tc + p * nv + s * d)
            tubes.add(r)
        cap = VGroup(txt("tubes of width", 22, GREY_), tex(r"\delta", 30, GREY_)).arrange(RIGHT, buff=0.1)
        cap.move_to([4.15, -1.65, 0])
        self.wait_until("tubes")
        card3.clear_updaters()
        self.play_until("tubes+0.5", FadeOut(card3, shift=RIGHT * 0.6))
        self.play_until("tubes+1.3", LaggedStart(*[GrowFromCenter(t) for t in tubes], lag_ratio=0.08),
                        FadeIn(cap))
        self.play_until("tubes+3.0", *[t.animate.move_to(tc) for t in tubes], rate_func=smooth)
        glow_c = Circle(radius=0.32, arc_center=tc, stroke_color=YELLOW_, stroke_width=2.5)
        self.play_until("tubes+3.6", Create(glow_c))
        self.wait_until("L4_end")
        self.play_until("claim4", FadeOut(glow_c))

        # ---- second paper: 4D dimension conjecture
        card4 = card_from(PAPER4D, 2.6).move_to([4.95, -0.3, 0])
        card3b = paper_card("074", width=2.6).move_to([3.35, 0.05, 0])
        new_title = Text("4D Kakeya Hausdorff dimension", font=SANS, font_size=17, color=WHITE_,
                         slant=ITALIC)
        new_title.move_to(tag[1][1]).align_to(tag[1][1], LEFT)
        self.play_until("claim4+0.8", FadeOut(tubes), FadeOut(cap), FadeOut(mformula),
                        FadeIn(card3b, shift=LEFT * 0.6), FadeIn(card4, shift=LEFT * 0.9),
                        Transform(tag[1][1], new_title),
                        self.hl.animate.move_to([-2.7, ROWS[4], 0]))
        claimed4 = place_left(chip("CLAIMED", YELLOW_, size=20), X_D, ROWS[4])
        self.play_until("claim4+1.5", FadeOut(self.cells[4], rate_func=early(0.3)),
                        FadeIn(claimed4, scale=1.25, rate_func=late(0.3)))

        banner = result_banner("3D: Kakeya maximal conjecture   ·   4D: Kakeya sets have full dimension",
                               color=YELLOW_, label="CLAIMED RESULTS", lean=False, size=26)
        banner.move_to(UP * 2.75)
        self.wait_until("claim4+1.6")
        self.play_until("claim4+2.3", FadeOut(self.formula, shift=UP * 0.3),
                        FadeOut(self.title, shift=UP * 0.3), FadeIn(banner, shift=DOWN * 0.2))

        # ---- five and up: open
        self.wait_until("five")
        opens = {}
        for key, (old, x, y) in {"d5": (self.cells[5], X_D, ROWS[5]), "m5": (mcells[5], X_M, ROWS[5]),
                                 "m4": (mcells[4], X_M, ROWS[4])}.items():
            opens[key] = (old, place_left(txt("open", 24, GREY_), x, y))
        self.play_until("five+0.6", self.hl.animate.move_to([-2.7, ROWS[5], 0]).set_stroke(GREY_),
                        *[FadeTransform(o, n) for o, n in opens.values()])
        self.play_until("five+1.2", Indicate(opens["d5"][1], color=WHITE_, scale_factor=1.2),
                        Indicate(opens["m5"][1], color=WHITE_, scale_factor=1.2))
