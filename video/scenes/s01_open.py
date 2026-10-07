import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import random

from manim.animation.animation import prepare_animation

import numpy as np

# Cold open + title card.
#   problems : ~4,000 dots pour in around a small "AI model" glyph, counter -> 4,000
#   decades  : a few dots flare with the years famous open problems were posed
#   hours    : clock sweeping 3 hours  ("~3 hours of thinking per result, on average")
#   L3       : most dots fade; 722 survivors gather into a compact block
#   papers   : the block becomes a wall of real first pages (one per family) -> "722 papers"
#   families : pages become coloured family cards -> "372 families of results"
#   fields   : cards sort into a unit chart, one row per subject -> "17 areas"
#   kinds/counter/famous : three cards  NEW BOUNDS / COUNTEREXAMPLES / FAMOUS PROBLEMS
#   zeta/pi/kakeya/ugc/plane : five quick, mathematically exact vignettes
#   title    : "4,000 Problems" over the returning dot field

CACHE = BUILD / "cache" / "s01_open"
KAPPA = 0.5522847498
FIELD_COLOR = "#B9C4D3"

# mosaic of first pages (one per family): 31 x 12 = 372 tiles
TW, TH, GAP = 86, 122, 8
COLS, ROWS = 31, 12
WPX = COLS * TW + (COLS - 1) * GAP
HPX = ROWS * TH + (ROWS - 1) * GAP
MOSAIC_SMALL_W = 6.6
MOSAIC_FULL_W = 14.9

SHORT = {
    "Number theory": "Number theory",
    "Algebraic and complex geometry": "Algebraic & complex geometry",
    "Real and complex analysis": "Real & complex analysis",
    "Convex and metric geometry": "Convex & metric geometry",
    "Theoretical computer science": "Theoretical computer science",
    "Combinatorics": "Combinatorics",
    "Algebra": "Algebra",
    "Group theory": "Group theory",
    "Mathematical logic": "Mathematical logic",
    "Dynamical systems and ergodic theory": "Dynamics & ergodic theory",
    "Probability and statistical mechanics": "Probability & stat. mechanics",
    "Mathematical physics": "Mathematical physics",
    "Operator algebras": "Operator algebras",
    "Topology": "Topology",
    "Functional analysis": "Functional analysis",
    "Differential geometry": "Differential geometry",
    "Partial differential equations": "Partial differential equations",
}

# first nontrivial zeros of zeta: 1/2 + i t
ZETA_T = [14.134725, 21.022040, 25.010858, 30.424876, 32.935062, 37.586178, 40.918719, 43.327073]


# ------------------------------------------------------------------ geometry helpers
def circle_pts(cx, cy, r):
    k = KAPPA * r
    P = [(cx + r, cy), (cx, cy + r), (cx - r, cy), (cx, cy - r), (cx + r, cy)]
    H = [((cx + r, cy + k), (cx + k, cy + r)), ((cx - k, cy + r), (cx - r, cy + k)),
         ((cx - r, cy - k), (cx - k, cy - r)), ((cx + k, cy - r), (cx + r, cy - k))]
    out = []
    for i in range(4):
        out += [P[i], H[i][0], H[i][1], P[i + 1]]
    return out


def rect_pts(cx, cy, w, h):
    c = [np.array(p) for p in [(cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2),
                               (cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                               (cx + w / 2, cy + h / 2)]]
    out = []
    for a, b in zip(c[:-1], c[1:]):
        out += [tuple(a), tuple(a + (b - a) / 3), tuple(a + 2 * (b - a) / 3), tuple(b)]
    return out


def multi_vm(pts, color, opacity):
    """One VMobject holding many disjoint closed sub-paths (cheap to draw)."""
    vm = VMobject()
    arr = np.zeros((len(pts), 3))
    arr[:, :2] = np.array(pts)
    vm.set_points(arr)
    vm.set_fill(color, opacity).set_stroke(width=0)
    return vm


def dots_vm(xy, radii, color, opacity):
    pts = []
    for (x, y), r in zip(xy, radii):
        pts += circle_pts(x, y, r)
    return multi_vm(pts, color, opacity)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def win(anim, t0, t1, T):
    """Place `anim` in the window [t0, t1] of a play lasting T seconds."""
    if not isinstance(anim, Animation):
        anim = prepare_animation(anim)
    t0 = max(0.0, min(t0, T - 0.05))
    t1 = max(t0 + 0.05, min(t1, T))
    anim.run_time = t1 - t0
    parts = []
    if t0 > 1e-3:
        parts.append(Wait(t0))
    parts.append(anim)
    if T - t1 > 1e-3:
        parts.append(Wait(T - t1))
    return Succession(*parts, suspend_mobject_updating=anim.suspend_mobject_updating)


def fade_fill(vm, target, color=None, rate_func=smooth):
    """Animate fill opacity (and optionally colour) without touching points, so
    drift updaters can keep running."""
    st = {}

    def f(m, a):
        if "o" not in st:
            st["o"] = m.get_fill_opacity()
            st["c"] = ManimColor(m.get_fill_color())
        a = rate_func(a)
        if color is not None:
            m.set_fill(st["c"].interpolate(ManimColor(color), a), interpolate(st["o"], target, a))
        else:
            m.set_fill(opacity=interpolate(st["o"], target, a))
    return UpdateFromAlphaFunc(vm, f, rate_func=linear, suspend_mobject_updating=False)


def tile_center(i, W, center=ORIGIN):
    k = W / WPX
    c, r = i % COLS, i // COLS
    x = (c * (TW + GAP) + TW / 2 - WPX / 2) * k
    y = (HPX / 2 - (r * (TH + GAP) + TH / 2)) * k
    return np.array([x, y, 0]) + center


class S01Open(VoiceScene):

    # ------------------------------------------------------------ bookkeeping
    # (1) Render every mobject every frame: things introduced mid-play inside a
    #     Succession (see win()) must appear immediately, not when the play ends.
    def get_moving_and_static_mobjects(self, animations):
        return [], []

    # (2) Never add composition wrapper Groups to the scene (they would pull
    #     their members to the top of the z-order and keep them alive after a
    #     FadeOut); add only leaf mobjects that are not in the scene yet.
    def add_mobjects_from_animations(self, animations):
        curr = set(self.get_mobject_family_members())

        def leaves(a):
            if isinstance(a, Wait):
                return []
            if isinstance(a, AnimationGroup):
                out = []
                for b in a.animations:
                    if not b.is_introducer():
                        out += leaves(b)
                return out
            return [a.mobject]
        for anim in animations:
            if anim.is_introducer():
                continue
            for mob in leaves(anim):
                if mob is None:
                    continue
                fam = mob.get_family()
                if not any(m in curr for m in fam):
                    self.add(mob)
                    curr.update(fam)

    # (3) Removing a mobject removes its whole family wherever it sits.
    def remove(self, *mobjects):
        fam = []
        for m in mobjects:
            fam += m.get_family()
        for name in ("mobjects", "foreground_mobjects"):
            self.restructure_mobjects(fam, name, False)
        return self

    # ------------------------------------------------------------ utilities
    def wait_until(self, t, **kw):
        dt = self.cue(t) - self.now
        if dt > 1.0 / config.frame_rate - 1e-6:
            self.wait(dt, **kw)

    def run(self, until, *items):
        """Play from now until cue `until`. Items are animations (spanning the
        whole play) or (anim, t0, t1) with absolute cue times."""
        T = self.cue(until) - self.now
        if T < 0.2:
            print(f"[VoiceScene] s01_open: run({until}) only {T:.2f}s left; using 0.2s")
            T = 0.2
        anims = []
        for it in items:
            if isinstance(it, tuple):
                a, t0, t1 = it
                anims.append(win(a, self.cue(t0) - self.now, self.cue(t1) - self.now, T))
            else:
                anims.append(it)
        self.play(*anims, run_time=T)

    def drift(self, mob, t0, rate):
        """Slow push-in: scale points about the origin by 1 + rate*(t - t0)."""
        for m in mob.family_members_with_points():
            m.base_pts = m.points.copy()

        def upd(m, dt):
            s = 1 + rate * max(0.0, self.now - t0)
            for sm in m.family_members_with_points():
                if hasattr(sm, "base_pts") and len(sm.points) == len(sm.base_pts):
                    sm.points = sm.base_pts * s
        mob.add_updater(upd)

    # ------------------------------------------------------------ data
    def build_field(self):
        rng = np.random.default_rng(11)
        NX, NY = 80, 50                       # exactly 4,000 dots
        xs = np.linspace(-7.3, 7.3, NX)
        ys = np.linspace(-4.15, 4.15, NY)
        px, py = xs[1] - xs[0], ys[1] - ys[0]
        X, Y = np.meshgrid(xs, ys)
        X = X.ravel() + rng.uniform(-0.33, 0.33, NX * NY) * px
        Y = Y.ravel() + rng.uniform(-0.33, 0.33, NX * NY) * py
        N = len(X)
        rad = rng.uniform(0.013, 0.025, N)
        lvl = rng.choice(3, size=N, p=[0.45, 0.35, 0.20])
        d = np.sqrt((X / 3.9) ** 2 + ((Y - 0.15) / 2.75) ** 2)
        clear = smoothstep(0.62, 1.08, d)
        self.F = dict(X=X, Y=Y, rad=rad, lvl=lvl, d=d, clear=clear)

        cand = np.where(clear > 0.65)[0]
        surv = rng.choice(cand, size=722, replace=False)
        is_s = np.zeros(N, bool)
        is_s[surv] = True
        self.surv_idx = surv

        LVL_OP = [0.28, 0.48, 0.78]
        NR = 14
        dmax = d.max() + 1e-6
        ring = np.minimum((d / dmax * NR).astype(int), NR - 1)
        bins = []   # (ring, vm, target_opacity, is_survivor)
        for rg in range(NR - 1, -1, -1):          # outer rings first
            for lv in range(3):
                idx = np.where((ring == rg) & (lvl == lv) & ~is_s & (clear > 0.02))[0]
                if len(idx) == 0:
                    continue
                op = LVL_OP[lv] * float(clear[idx].mean())
                vm = dots_vm(np.c_[X[idx], Y[idx]], rad[idx], FIELD_COLOR, 0)
                bins.append((rg, vm, op, False))
            idx = np.where((ring == rg) & is_s)[0]
            if len(idx):
                op = LVL_OP[1] * float(clear[idx].mean())
                vm = dots_vm(np.c_[X[idx], Y[idx]], rad[idx], FIELD_COLOR, 0)
                vm.idx = idx
                bins.append((rg, vm, op, True))
        self.bins = bins
        self.ring_ids = sorted({b[0] for b in bins}, reverse=True)

    def build_families(self):
        fams = list(CATALOG.values())
        order = sorted(fams, key=lambda e: e["num"])
        random.Random(5).shuffle(order)
        self.order = order
        CACHE.mkdir(parents=True, exist_ok=True)
        out = CACHE / "mosaic_s5_b62_stack.png"
        if not out.exists():
            # each family = its principal first page, stacked on top of one
            # offset sheet per further paper (max 3), so the wall holds all 722
            from PIL import Image, ImageEnhance, ImageDraw
            canvas = Image.new("RGBA", (WPX, HPX), (0, 0, 0, 0))
            dr = ImageDraw.Draw(canvas)
            OFF, NSH = 4, 3
            PW, PH = TW - OFF * NSH, TH - OFF * NSH
            for i, e in enumerate(order):
                c, r = i % COLS, i // COLS
                x0, y0 = c * (TW + GAP), r * (TH + GAP) + OFF * NSH
                for j in range(min(len(e["papers"]) - 1, NSH), 0, -1):
                    dr.rectangle([x0 + OFF * j, y0 - OFF * j, x0 + OFF * j + PW - 1, y0 - OFF * j + PH - 1],
                                 fill=(112, 117, 125, 255), outline=(44, 49, 58, 255))
                im = Image.open(thumb_path(e["num"])).convert("RGB").resize((PW, PH), Image.LANCZOS)
                im = ImageEnhance.Brightness(im).enhance(0.62)
                canvas.paste(im, (x0, y0))
            canvas.save(out)
        self.mosaic_path = str(out)

    # ------------------------------------------------------------ glyphs
    def net_glyph(self):
        layers = [3, 5, 5, 3]
        xs = [-0.95, -0.32, 0.32, 0.95]
        cols = [[np.array([x, (i - (L - 1) / 2) * 0.34, 0]) for i in range(L)]
                for L, x in zip(layers, xs)]
        edge_layers = []
        for a, b in zip(cols[:-1], cols[1:]):
            edge_layers.append(VGroup(*[Line(p, q, stroke_width=1.3, color=GREY_, stroke_opacity=0.5)
                                        for p in a for q in b]))
        node_layers = [VGroup(*[Circle(radius=0.075, stroke_color=BLUE_, stroke_width=2.4,
                                       fill_color=BG, fill_opacity=1).move_to(p) for p in c])
                       for c in cols]
        net = VGroup(VGroup(*edge_layers), VGroup(*node_layers))
        return net, edge_layers, node_layers

    def net_pulse(self, edge_layers, node_layers, color=BLUE_):
        steps = []
        for i, lay in enumerate(edge_layers):
            flashes = [ShowPassingFlash(e.copy().set_stroke(color, 2.6, 1), time_width=0.7) for e in lay]
            steps.append(AnimationGroup(*flashes,
                                        *[Indicate(n, color=color, scale_factor=1.25) for n in node_layers[i + 1]]))
        return LaggedStart(*steps, lag_ratio=0.55)

    def clock_glyph(self, r=0.56):
        face = Circle(radius=r, stroke_color=WHITE_, stroke_width=3)
        ticks = VGroup(*[Line(UP * (r - (0.13 if i % 3 == 0 else 0.07)), UP * (r - 0.02),
                              stroke_width=2.5 if i % 3 == 0 else 1.5, color=GREY_).rotate(-i * TAU / 12, about_point=ORIGIN)
                         for i in range(12)])
        wedge = Sector(radius=r - 0.03, start_angle=PI / 2, angle=-0.001, fill_color=YELLOW_,
                       fill_opacity=0.28, stroke_width=0)
        hour = Line(ORIGIN, UP * r * 0.55, stroke_width=5, color=WHITE_)
        minute = Line(ORIGIN, UP * r * 0.82, stroke_width=3, color=YELLOW_)
        hub = Dot(radius=0.045, color=WHITE_)
        g = VGroup(wedge, face, ticks, hour, minute, hub)
        g.parts = dict(wedge=wedge, hour=hour, minute=minute, face=face, r=r)
        return g

    def clock_sweep(self, clock):
        p = clock.parts

        def f(m, a):
            c = p["face"].get_center()
            th = PI / 2 - a * PI / 2           # hour hand: 12 -> 3
            tm = PI / 2 - a * 3 * TAU          # minute hand: three full turns
            p["hour"].put_start_and_end_on(c, c + p["r"] * 0.55 * np.array([np.cos(th), np.sin(th), 0]))
            p["minute"].put_start_and_end_on(c, c + p["r"] * 0.82 * np.array([np.cos(tm), np.sin(tm), 0]))
            p["wedge"].become(Sector(radius=p["r"] - 0.03, start_angle=PI / 2, angle=-max(a, 1e-3) * PI / 2,
                                     arc_center=c, fill_color=YELLOW_, fill_opacity=0.28, stroke_width=0))
        return UpdateFromAlphaFunc(clock, f, rate_func=smooth)

    # ------------------------------------------------------------ cards (kinds)
    def kind_card(self, x, color, label):
        frame = RoundedRectangle(width=3.95, height=3.35, corner_radius=0.18, stroke_color=color,
                                 stroke_width=2, stroke_opacity=0.7, fill_color=CARD, fill_opacity=0.95)
        frame.move_to([x, 0.05, 0])
        ch = chip(label, color, size=24, pad_x=0.18, pad_y=0.1)
        ch.move_to([x, -1.12, 0])
        return frame, ch

    def icon_bounds(self, x):
        o = np.array([x - 1.25, -0.25, 0])
        axes = VGroup(Line(o, o + RIGHT * 2.5, color=GREY_, stroke_width=2),
                      Line(o, o + UP * 1.55, color=GREY_, stroke_width=2))
        xs = np.linspace(0, 2.4, 60)
        ys = 0.42 + 0.22 * np.sin(3.1 * xs + 0.4) + 0.12 * np.sin(7.3 * xs) + 0.08 * xs
        curve = VMobject(stroke_color=WHITE_, stroke_width=3).set_points_smoothly(
            [o + np.array([a + 0.05, b, 0]) for a, b in zip(xs, ys)])
        top = ys.max()
        old = DashedLine(o + UP * 1.42, o + UP * 1.42 + RIGHT * 2.45, dash_length=0.08,
                         color=GREY_, stroke_width=2.5)
        new = Line(o + UP * 1.42, o + UP * 1.42 + RIGHT * 2.45, color=BLUE_, stroke_width=4)
        drop = (1.42 - top - 0.07)
        return VGroup(axes, curve, old), new, drop

    def icon_counter(self, x):
        checks = VGroup(*[check_mark(GREEN_, size=0.42, width=6) for _ in range(3)])
        xg = VGroup(Line(UL * 0.17, DR * 0.17, color=RED_, stroke_width=7),
                    Line(UR * 0.17, DL * 0.17, color=RED_, stroke_width=7))
        ring = Circle(radius=0.34, color=RED_, stroke_width=3.5)
        bad = VGroup(ring, xg)
        row = VGroup(*checks, bad).arrange(RIGHT, buff=0.42)
        row.move_to([x, 0.5, 0])
        return checks, bad

    def icon_star(self, x):
        st = Star(n=5, outer_radius=0.82, density=2, color=YELLOW_)
        st.set_fill(YELLOW_, 0.18).set_stroke(YELLOW_, 3.5)
        st.move_to([x, 0.52, 0])
        gl = glow(st, YELLOW_, layers=6, width=26, opacity=0.07)
        return st, gl

    # ------------------------------------------------------------ vignettes
    def vig_zeta(self):
        SX, SY, y0 = 2.0, 0.105, -2.3
        strip = Rectangle(width=SX, height=5.0, stroke_width=0, fill_color=BLUE_, fill_opacity=0.13)
        strip.move_to([0, y0 + 2.5, 0])
        e0 = Line([-SX / 2, y0, 0], [-SX / 2, y0 + 5.0, 0], color=BLUE_, stroke_width=1.5, stroke_opacity=0.6)
        e1 = Line([SX / 2, y0, 0], [SX / 2, y0 + 5.0, 0], color=BLUE_, stroke_width=1.5, stroke_opacity=0.6)
        axis = Arrow([-2.3, y0, 0], [2.5, y0, 0], buff=0, stroke_width=2.5, color=GREY_,
                     tip_length=0.16, max_tip_length_to_length_ratio=0.1)
        crit = DashedLine([0, y0, 0], [0, y0 + 5.0, 0], dash_length=0.12, color=YELLOW_, stroke_width=3)
        l0 = tex("0", 28, GREY_).next_to([-SX / 2, y0, 0], DOWN, buff=0.14)
        lh = tex(r"\tfrac12", 30, YELLOW_).next_to([0, y0, 0], DOWN, buff=0.1)
        l1 = tex("1", 28, GREY_).next_to([SX / 2, y0, 0], DOWN, buff=0.14)
        zlab = tex(r"\zeta(s)=0", 40, WHITE_).move_to([-2.45, 1.5, 0])
        static = VGroup(strip, e0, e1, axis, crit, l0, lh, l1, zlab)
        zeros = VGroup(*[Dot([0, y0 + SY * t, 0], radius=0.075, color=YELLOW_) for t in ZETA_T])
        halos = VGroup(*[glow(Circle(radius=0.05).move_to(z), YELLOW_, layers=4, width=14, opacity=0.12)
                         for z in zeros])
        labs = VGroup()
        for t in ZETA_T[:3]:
            lb = tex(f"{t:.2f}" + r"\ldots", 30, WHITE_)
            lb.next_to([0.16, y0 + SY * t, 0], RIGHT, buff=0.0)
            labs.add(lb)
        V = VGroup(static, halos, zeros, labs).shift(UP * 0.12)
        return V, static, zeros, halos, labs

    def vig_pi(self):
        lo, hi, x0, x1, yl = 3.138, 3.146, -3.2, 3.2, 0.95
        X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
        line = Line([x0 - 0.15, yl, 0], [x1 + 0.15, yl, 0], color=GREY_, stroke_width=2.5)
        ticks = VGroup()
        for k in range(9):
            v = lo + k * 0.001
            big = k % 2 == 0
            ticks.add(Line([X(v), yl - (0.11 if big else 0.06), 0], [X(v), yl + (0.11 if big else 0.06), 0],
                           color=GREY_, stroke_width=2 if big else 1.2))
        tl = VGroup(*[tex(s, 28, GREY_).next_to([X(v), yl - 0.12, 0], DOWN, buff=0.1)
                      for s, v in [("3.140", 3.140), ("3.144", 3.144)]])
        xp = X(np.pi)
        ptick = Line([xp, yl - 0.2, 0], [xp, yl + 0.32, 0], color=YELLOW_, stroke_width=4)
        plab = tex(r"\pi", 54, YELLOW_).next_to(ptick, UP, buff=0.08)
        static = VGroup(line, ticks, tl, ptick, plab)
        x22 = X(22 / 7)
        d22 = Dot([x22, yl, 0], radius=0.085, color=BLUE_)
        l22 = tex(r"\tfrac{22}{7}", 42, BLUE_).next_to([x22, yl - 0.12, 0], DOWN, buff=0.14)
        x355 = X(355 / 113)
        d355 = Dot([x355, yl, 0], radius=0.085, color=GREEN_)
        l355 = tex(r"\tfrac{355}{113}", 42, GREEN_).next_to([x355, yl - 0.12, 0], DOWN, buff=0.14)
        r1 = MathTex(r"\pi", "=", "3.141592", r"65\ldots", font_size=54, color=WHITE_)
        r2 = MathTex(r"\tfrac{355}{113}", "=", "3.141592", r"92\ldots", font_size=54, color=WHITE_)
        for r in (r1, r2):
            r[2].set_color(YELLOW_)
            r[3].set_color(GREY_)
        r2[0].set_color(GREEN_)
        r1.move_to([0, -1.05, 0])
        r2.move_to([0, -1.95, 0])
        # align on '='
        r1.shift(RIGHT * (r2[1].get_center()[0] - r1[1].get_center()[0]))
        digits = VGroup(r1, r2)
        digits.set_x(0)
        V = VGroup(static, d22, l22, d355, l355, digits).shift(UP * 0.1)
        return V, static, (d22, l22), (d355, l355), digits

    def vig_kakeya(self, t_start, dur):
        r = 0.85                        # needle length 4r = 3.4 scene units = "1"
        rot = 1j                        # turn the deltoid so one cusp points up
        ts = np.linspace(0, TAU, 400)
        Z = rot * (2 * r * np.exp(1j * ts) + r * np.exp(-2j * ts))
        cy = -(Z.imag.max() + Z.imag.min()) / 2 + 0.15
        anchor = Dot(ORIGIN, radius=0.001, fill_opacity=0).move_to([0, cy, 0])
        pts = [np.array([z.real, z.imag + cy, 0]) for z in Z]
        delt = VMobject(stroke_color=TEAL_, stroke_width=2.5, stroke_opacity=0.85).set_points_as_corners(pts)
        delt.set_fill(TEAL_, 0.10)
        NG = 20
        ghosts = VGroup(*[Line(LEFT, RIGHT, stroke_color=TEAL_, stroke_width=1.6, stroke_opacity=0) for _ in range(NG)])
        needle = Line(LEFT, RIGHT, color=YELLOW_, stroke_width=6)
        ends = VGroup(Dot(radius=0.06, color=YELLOW_), Dot(radius=0.06, color=YELLOW_))

        def seg(t):
            a = anchor.get_center()
            m = rot * r * np.exp(1j * t)
            u = rot * np.exp(-1j * t / 2)
            p = m - 2 * r * u
            q = m + 2 * r * u
            return a + np.array([p.real, p.imag, 0]), a + np.array([q.real, q.imag, 0])

        def tparam():
            return TAU * smooth(np.clip((self.now - t_start) / dur, 0, 1))

        def upd_needle(m, dt):
            p, q = seg(tparam())
            needle.put_start_and_end_on(p, q)
            ends[0].move_to(p)
            ends[1].move_to(q)

        def upd_ghosts(m, dt):
            t = tparam()
            fac = delt.get_stroke_opacity() / 0.85
            for k, g in enumerate(ghosts):
                tk = TAU * (k + 0.5) / NG
                p, q = seg(tk)
                g.put_start_and_end_on(p, q)
                g.set_stroke(opacity=0.45 * fac if t >= tk else 0)

        dyn = VGroup(ghosts, needle, ends)
        upd_needle(needle, 0)
        upd_ghosts(ghosts, 0)
        needle.add_updater(upd_needle)
        ghosts.add_updater(upd_ghosts)
        V = VGroup(delt, anchor, dyn)
        return V

    def vig_ugc(self):
        P = {"A": (-2.35, 0.95), "B": (0, 2.05), "C": (2.35, 0.95), "D": (1.45, -1.55), "E": (-1.45, -1.55)}
        P = {k: np.array([x, y, 0]) for k, (x, y) in P.items()}
        val = {"A": 0, "B": 1, "C": 2, "D": 1, "E": 0}
        EDGES = [("A", "B", 1), ("B", "C", 1), ("C", "D", 2), ("D", "E", 2), ("E", "A", 0), ("A", "C", 1), ("A", "D", 1)]
        LCOL = [BLUE_, GOLD_, PINK_]
        cen = sum(P.values()) / 5
        arrows, elabs, ok = VGroup(), VGroup(), []
        for u, v, c in EDGES:
            a = Arrow(P[u], P[v], buff=0.37, stroke_width=3.2, color=GREY_, tip_length=0.2,
                      max_tip_length_to_length_ratio=0.12)
            arrows.add(a)
            mid = (P[u] + P[v]) / 2
            d = P[v] - P[u]
            nrm = np.array([-d[1], d[0], 0]) / np.linalg.norm(d)
            if np.dot(nrm, mid - cen) < 0:
                nrm = -nrm
            if (u, v) == ("A", "C"):
                nrm = DOWN
            lab = tex(f"+{c}", 28, WHITE_)
            bg = RoundedRectangle(width=lab.width + 0.14, height=lab.height + 0.1, corner_radius=0.06,
                                  stroke_width=0, fill_color=BG, fill_opacity=0.9)
            g = VGroup(bg, lab).move_to(mid + nrm * 0.27)
            elabs.add(g)
            ok.append((val[u] + c) % 3 == val[v])
        verts = VGroup(*[Circle(radius=0.33, stroke_color=GREY_, stroke_width=2.5, fill_color=CARD,
                                fill_opacity=1).move_to(P[k]) for k in "ABCDE"])
        discs = VGroup()
        for k in "ABCDE":
            d = Circle(radius=0.33, stroke_width=0, fill_color=LCOL[val[k]], fill_opacity=1).move_to(P[k])
            n = tex(str(val[k]), 32, BG).move_to(P[k])
            discs.add(VGroup(d, n))
        static = VGroup(arrows, elabs, verts)
        V = VGroup(static, discs).shift(DOWN * 0.15)
        return V, static, arrows, discs, ok

    def vig_plane(self, t_start):
        k = 1.3                          # scene units per unit distance
        R = 0.4 * k                      # hexagon circumradius 2/5 (diameter 0.8 < 1)
        COL7 = [BLUE_, TEAL_, GREEN_, YELLOW_, ORANGE_, RED_, PURPLE_]
        anchor = Dot(ORIGIN, radius=0.001, fill_opacity=0)

        def hc(q, r):
            return np.array([np.sqrt(3) * R * (q + r / 2), 1.5 * R * r, 0])
        hexes = []
        for q in range(-9, 10):
            for r in range(-7, 8):
                c = hc(q, r)
                d = np.sqrt((c[0] / 3.45) ** 2 + (c[1] / 2.5) ** 2)
                if d > 0.97:
                    continue
                op = 0.85 * (1 - 0.55 * smoothstep(0.7, 0.97, d))
                h = RegularPolygon(n=6, radius=R, start_angle=PI / 6)
                h.move_to(c).set_fill(COL7[(q + 3 * r) % 7], op).set_stroke(BG, 2.5)
                h.dist = d
                hexes.append(h)
        hexes.sort(key=lambda h: h.dist)
        hexes = VGroup(*hexes)

        def axial(p):
            x, y = p[0], p[1]
            qf = (np.sqrt(3) / 3 * x - y / 3) / R
            rf = (2 / 3 * y) / R
            sf = -qf - rf
            q, r, s = round(qf), round(rf), round(sf)
            dq, dr, ds = abs(q - qf), abs(r - rf), abs(s - sf)
            if dq > dr and dq > ds:
                q = -r - s
            elif dr > ds:
                r = -q - s
            return q, r

        hl = VGroup(*[RegularPolygon(n=6, radius=R, start_angle=PI / 6).set_stroke(WHITE_, 3.5).set_fill(opacity=0)
                      for _ in range(2)])
        ruler = Line(LEFT, RIGHT, color=WHITE_, stroke_width=5)
        ends = VGroup(Dot(radius=0.075, color=WHITE_), Dot(radius=0.075, color=WHITE_))
        one = tex("1", 36, WHITE_)
        one_bg = Circle(radius=0.2, stroke_width=0, fill_color=BG, fill_opacity=0.85)
        lab = VGroup(one_bg, one)

        def state():
            tau = max(0.0, self.now - t_start)
            c = np.array([1.05 * np.sin(0.85 * tau + 0.2), 0.62 * np.sin(1.15 * tau + 0.9), 0])
            th = 0.35 + 0.75 * tau
            u = np.array([np.cos(th), np.sin(th), 0])
            return c, u

        def upd(m, dt):
            a = anchor.get_center()
            c, u = state()
            p, q = c - u * k / 2, c + u * k / 2
            ruler.put_start_and_end_on(a + p, a + q)
            ends[0].move_to(a + p)
            ends[1].move_to(a + q)
            for h, pt in zip(hl, (p, q)):
                h.move_to(a + hc(*axial(pt)))
            nrm = np.array([-u[1], u[0], 0])
            lab.move_to(a + c + nrm * 0.34)

        dyn = VGroup(hl, ruler, ends, lab)
        upd(dyn, 0)
        dyn.add_updater(upd)
        V = VGroup(anchor, hexes, dyn).shift(UP * 0.1)
        return V, hexes, dyn

    # ------------------------------------------------------------ main
    def construct(self):
        C = self.cue
        self.build_field()
        self.build_families()

        # ============ 0. "Here's an experiment. Take an AI model ..."
        head = caps("an experiment", size=22, color=GREY_).move_to(UP * 3.2)
        net, edge_layers, node_layers = self.net_glyph()
        net.scale(1.3).move_to(UP * 1.42)
        ai_lab = txt("AI model", 28, GREY_).move_to(UP * 0.12)
        net_glow = VGroup(*[Circle(radius=r, stroke_width=0, fill_color=BLUE_, fill_opacity=0.022).move_to(net)
                            for r in np.linspace(0.5, 1.85, 9)])

        create_net = AnimationGroup(
            FadeIn(net_glow),
            LaggedStart(*[LaggedStart(*[GrowFromCenter(n) for n in lay], lag_ratio=0.15) for lay in node_layers],
                        lag_ratio=0.35),
            LaggedStart(*[Create(lay, lag_ratio=0.02) for lay in edge_layers], lag_ratio=0.4),
        )
        pulse_end = C("problems") - 0.85
        self.run(pulse_end,
                 (FadeIn(head, shift=DOWN * 0.1), 0.0, 0.5),
                 (create_net, 0.05, "L0+0.85"),
                 (FadeIn(ai_lab, shift=UP * 0.1), "L0+0.9", "L0+1.4"),
                 (self.net_pulse(edge_layers, node_layers), min(C("L0") + 1.5, pulse_end - 0.8), pulse_end))

        # ============ "{problems} four thousand open problems"
        bins = self.bins
        field = VGroup(*[b[1] for b in bins])
        self.add(field)
        # put the glyphs above the field
        self.add(net_glow, net, ai_lab, head)
        t_wave = self.now
        self.drift(field, t_wave, 0.0045)
        by_ring = {}
        for rg, vm, op, _ in bins:
            by_ring.setdefault(rg, []).append(fade_fill(vm, op))
        wave = LaggedStart(*[AnimationGroup(*by_ring[rg], suspend_mobject_updating=False) for rg in self.ring_ids],
                           lag_ratio=0.18, suspend_mobject_updating=False)

        cnt = ValueTracker(0)
        cop = ValueTracker(0)
        CY = -0.88

        def make_counter():
            g = VGroup(MathTex(r"\approx", font_size=100, color=WHITE_),
                       Integer(int(round(cnt.get_value())), font_size=100, color=WHITE_))
            g.arrange(RIGHT, buff=0.22).move_to([0, CY, 0])
            g.set_opacity(cop.get_value())
            return g
        counter = always_redraw(make_counter)
        self.add(counter)
        cnt_lab = txt("open problems", 32, GREY_).move_to([0, CY - 0.88, 0])
        self.run("problems+0.85",
                 (FadeOut(head), "problems-0.85", "problems-0.45"),
                 (wave, "problems-0.85", "problems+0.85"),
                 (cop.animate.set_value(1), "problems-0.6", "problems-0.3"),
                 (cnt.animate(rate_func=rate_functions.ease_out_cubic).set_value(4000), "problems-0.6", "problems+0.6"),
                 (FadeIn(cnt_lab, shift=UP * 0.1), "problems+0.35", "problems+0.85"))
        counter.clear_updaters()
        counter_static = make_counter()
        self.remove(counter)
        self.add(counter_static)

        # ============ "{decades} some open for decades, a few for over a century"
        flares = VGroup()
        specs = [("1974", (4.75, 2.55), WHITE_), ("1950", (-5.1, -2.35), WHITE_), ("1939", (5.6, -1.15), WHITE_),
                 ("1917", (-5.75, 1.35), GOLD_), ("1900", (3.55, -2.95), GOLD_), ("1859", (-3.35, 2.95), GOLD_)]
        fl_anims = []
        for year, (x, y), col in specs:
            p = np.array([x, y, 0])
            d = Dot(p, radius=0.06, color=col)
            ring = Circle(radius=0.07, stroke_color=col, stroke_width=3).move_to(p)
            lab = txt(year, 26, col, weight=SEMIBOLD).next_to(d, RIGHT, buff=0.14)
            bg = BackgroundRectangle(lab, color=BG, fill_opacity=0.65, buff=0.06)
            flares.add(VGroup(bg, d, lab))

            def ring_f(m, a, p=p, col=col):
                m.become(Circle(radius=0.07 + 0.55 * a, stroke_color=col,
                                stroke_width=3 * (1 - a) + 0.5).move_to(p)
                         .set_stroke(opacity=(1 - a) if a > 0 else 0))
            fl_anims.append(AnimationGroup(GrowFromCenter(d), UpdateFromAlphaFunc(ring, ring_f, remover=True),
                                           FadeIn(bg), FadeIn(lab, shift=RIGHT * 0.12)))
        # "Real research problems:" -- a soft shimmer rolls outward through the field
        rings_out = list(reversed(self.ring_ids))
        shimmer = LaggedStart(*[AnimationGroup(*[fade_fill(vm, min(1.0, op * 1.9), rate_func=there_and_back)
                                                 for rg2, vm, op, _ in bins if rg2 == rg],
                                               suspend_mobject_updating=False) for rg in rings_out],
                              lag_ratio=0.12, suspend_mobject_updating=False)
        t_dec = C("decades")
        sh0 = max(self.now, min(C("L1"), t_dec - 1.0))
        self.wait_until(sh0)
        self.run(t_dec - 0.02, (shimmer, sh0, t_dec - 0.02))
        t_cen = t_dec + 0.45 * (C("L1_end") - t_dec)
        self.run(t_dec + 1.0, (LaggedStart(*fl_anims[:3], lag_ratio=0.3), 0, t_dec + 1.0))
        self.wait_until(t_cen)
        self.run(t_cen + 1.0, (LaggedStart(*fl_anims[3:], lag_ratio=0.3), 0, t_cen + 1.0))

        # ============ "{hours} about three hours of thinking behind each result"
        clock = self.clock_glyph()
        hrs = MathTex(r"\approx 3", r"\text{ hours}", font_size=100, color=WHITE_)
        row = VGroup(clock, hrs).arrange(RIGHT, buff=0.5).move_to([0, CY, 0])
        hrs_sub = txt("of thinking per result, on average", 30, GREY_).move_to([0, CY - 0.88, 0])
        self.wait_until("hours-0.35")
        self.run("hours+0.4",
                 (FadeOut(VGroup(counter_static, cnt_lab), shift=UP * 0.35), "hours-0.35", "hours+0.05"),
                 (FadeIn(row, shift=UP * 0.35), "hours-0.2", "hours+0.4"))
        h_end = min(C("hours") + 2.9, C("L3") - 0.1)
        self.run(h_end,
                 (self.clock_sweep(clock), "hours+0.4", h_end),
                 (FadeOut(flares), "hours+0.5", "hours+1.1"),
                 (FadeIn(hrs_sub, shift=UP * 0.1), "hours+0.45", "hours+0.95"),
                 (self.net_pulse(edge_layers, node_layers, YELLOW_), "hours+0.5", "hours+1.5"),
                 (self.net_pulse(edge_layers, node_layers, YELLOW_), "hours+1.6", min(C("hours") + 2.6, h_end)))

        # ============ "Then keep only what's worth keeping."
        keep = []
        for _, vm, _, is_s in bins:
            keep.append(fade_fill(vm, 0.95, YELLOW_) if is_s else fade_fill(vm, 0.0))
        self.wait_until("L3")
        self.run("L3+0.9",
                 FadeOut(VGroup(row, hrs_sub, net, ai_lab, net_glow)),
                 AnimationGroup(*keep, suspend_mobject_updating=False))
        # swap the survivor bins for one VMobject (same look), then gather
        X, Y, rad = self.F["X"], self.F["Y"], self.F["rad"]
        s_now = 1 + 0.0045 * (self.now - t_wave)
        s_idx = np.concatenate([b[1].idx for b in bins if b[3]])
        field.clear_updaters()
        self.remove(field)
        # targets: each family's papers as small dots inside its tile of the small mosaic
        slots, slot_col = [], []
        for i, e in enumerate(self.order):
            n = len(e["papers"])
            tc = tile_center(i, MOSAIC_SMALL_W)
            nc = 1 if n == 1 else (2 if n <= 4 else 3)
            nr = int(np.ceil(n / nc))
            for j in range(n):
                cc, rr = j % nc, j // nc
                slots.append(tc + np.array([(cc - (nc - 1) / 2) * 0.056, ((nr - 1) / 2 - rr) * 0.052, 0]))
                slot_col.append(i % COLS)
        slots = np.array(slots)
        col_of_slot = np.array(slot_col)
        assert len(slots) == len(s_idx) == 722
        # order-preserving assignment: sort sources by x, chunk per mosaic column, then by y
        src = np.c_[X[s_idx], Y[s_idx]] * s_now
        s_order = np.argsort(src[:, 0], kind="stable")
        assign = np.empty(722, int)
        pos = 0
        for c in range(COLS):
            tgt = np.where(col_of_slot == c)[0]
            chunk = s_order[pos:pos + len(tgt)]
            pos += len(tgt)
            chunk = chunk[np.argsort(-src[chunk, 1])]
            tgt = tgt[np.argsort(-slots[tgt, 1])]
            assign[chunk] = tgt
        surv = dots_vm(src, rad[s_idx] * s_now, YELLOW_, 0.95)
        surv_t = dots_vm(slots[assign][:, :2], np.full(722, 0.019), YELLOW_, 0.95)
        self.add(surv)
        self.run("papers-0.02", Transform(surv, surv_t, rate_func=rate_functions.ease_in_out_cubic))

        # ============ "{papers} Seven hundred and twenty-two papers."
        mosaic = ImageMobject(self.mosaic_path)
        mosaic.width = MOSAIC_SMALL_W
        mosaic.move_to(ORIGIN)
        self.run("papers+0.4", FadeIn(mosaic), FadeOut(surv))
        panel = RoundedRectangle(width=5.4, height=2.55, corner_radius=0.22, stroke_color=GREY_,
                                 stroke_width=1.5, stroke_opacity=0.5, fill_color=BG, fill_opacity=0.9)
        pv = ValueTracker(0)
        PY = 0.0

        def make_num():
            n = Integer(int(round(pv.get_value())), font_size=120, color=WHITE_)
            n.move_to([0, PY + 0.38, 0])
            return n
        num = always_redraw(make_num)
        lab_p = txt("papers", 36, GREY_).move_to([0, PY - 0.72, 0])
        self.add(num)
        self.run("papers+1.7",
                 (mosaic.animate(rate_func=rate_functions.ease_in_out_cubic).scale(MOSAIC_FULL_W / MOSAIC_SMALL_W),
                  "papers+0.4", "papers+1.7"),
                 (FadeIn(panel, scale=0.9), "papers+0.5", "papers+0.9"),
                 (pv.animate(rate_func=rate_functions.ease_out_cubic).set_value(722), "papers+0.5", "papers+1.5"),
                 (FadeIn(lab_p, shift=UP * 0.1), "papers+0.8", "papers+1.2"))
        num.clear_updaters()
        self.remove(num)
        num = Integer(722, font_size=120, color=WHITE_).move_to([0, PY + 0.38, 0])
        self.add(num)
        self.bring_to_front(panel, num, lab_p)
        self.run("families-0.02", mosaic.animate(rate_func=linear).scale(1.025))

        # ============ "{families} Three hundred and seventy-two families of results"
        W = mosaic.width
        mc = mosaic.get_center()
        k = W / WPX
        tw, th = TW * k * 0.9, TH * k * 0.92
        subj_of = {}
        for chk, _, subs, col in CHAPTERS:
            for s in subs:
                subj_of[s] = col
        subjects = [s for _, _, subs, _ in CHAPTERS for s in subs]
        fam_rects, fam_idx = {}, {}
        for s in subjects:
            ids = [i for i, e in enumerate(self.order) if e["subject"] == s]
            fam_idx[s] = ids
            pts = []
            for i in ids:
                c = tile_center(i, W, mc)
                pts += rect_pts(c[0], c[1], tw, th)
            fam_rects[s] = multi_vm(pts, subj_of[s], 0.75)
        rects = VGroup(*[fam_rects[s] for s in subjects])
        lab_f = txt("families of results", 36, GREY_).move_to(lab_p)
        num372 = Integer(372, font_size=120, color=WHITE_).move_to(num)
        self.add(rects, panel, num, lab_p)
        rects.set_opacity(0)
        self.run("families+0.85",
                 (FadeOut(mosaic), 0, "families+0.6"),
                 (rects.animate.set_fill(opacity=0.75), "families+0.1", "families+0.7"),
                 (FadeOut(VGroup(num, lab_p), shift=UP * 0.35), "families", "families+0.3"),
                 (FadeIn(VGroup(num372, lab_f), shift=UP * 0.35), "families+0.25", "families+0.65"))
        num = num372
        self.run("fields-0.02", rects.animate(rate_func=linear).scale(1.02))

        # ============ "{fields} across seventeen areas of mathematics"
        ROW0, RP, X0, SP, SQ = 2.6, 0.368, -1.92, 0.2, 0.165
        row_labels, row_counts, targets = VGroup(), VGroup(), {}
        for ri, s in enumerate(subjects):
            y = ROW0 - ri * RP
            ids = fam_idx[s]
            # keep left-to-right order of the cards
            ids_sorted = sorted(range(len(ids)), key=lambda j: tile_center(ids[j], W, mc)[0])
            pts = [None] * len(ids)
            for rank, j in enumerate(ids_sorted):
                pts[j] = rect_pts(X0 + rank * SP, y, SQ, SQ)
            flat = [p for q in pts for p in q]
            targets[s] = multi_vm(flat, subj_of[s], 0.9)
            lb = txt(SHORT[s], 22, WHITE_)
            lb.move_to([0, y, 0]).align_to([-2.2, 0, 0], RIGHT)
            row_labels.add(lb)
            ct = txt(str(len(ids)), 22, GREY_)
            ct.move_to([0, y, 0]).align_to([X0 + len(ids) * SP - 0.02, 0, 0], LEFT)
            row_counts.add(ct)
        hdr = VGroup(MathTex("17", font_size=72, color=YELLOW_), txt("areas of mathematics", 36, WHITE_))
        hdr.arrange(RIGHT, buff=0.25, aligned_edge=DOWN).move_to([0, 3.3, 0])
        hdr[1].shift(UP * 0.06)
        self.run("fields+1.5",
                 (LaggedStart(*[Transform(fam_rects[s], targets[s]) for s in subjects], lag_ratio=0.035,
                              rate_func=linear), "fields", "fields+1.5"),
                 (FadeOut(panel), "fields", "fields+0.35"),
                 (ReplacementTransform(num, hdr[0]), "fields", "fields+0.7"),
                 (FadeTransform(lab_f, hdr[1]), "fields", "fields+0.7"),
                 (LaggedStart(*[FadeIn(l, shift=RIGHT * 0.15) for l in row_labels], lag_ratio=0.06),
                  "fields+0.4", "fields+1.5"))
        t_cnt_end = min(C("fields") + 2.3, C("L4_end") - 0.25)
        self.run(t_cnt_end, LaggedStart(*[FadeIn(c) for c in row_counts], lag_ratio=0.05))

        # ============ "{kinds} Some are sharper bounds. {counter} Some are counterexamples. {famous} ..."
        chart = VGroup(rects, row_labels, row_counts, hdr)
        t_out = max(self.now, min(C("L4_end") - 0.1, C("kinds") - 0.35))
        self.wait_until(t_out)
        fr1, ch1 = self.kind_card(-4.45, BLUE_, "NEW BOUNDS")
        fr2, ch2 = self.kind_card(0.0, RED_, "COUNTEREXAMPLES")
        fr3, ch3 = self.kind_card(4.45, YELLOW_, "FAMOUS PROBLEMS")
        ic1, newb, drop = self.icon_bounds(-4.45)
        checks, bad = self.icon_counter(0.0)
        star, star_glow = self.icon_star(4.45)
        self.run("kinds+0.5",
                 (FadeOut(chart), t_out, max(t_out + 0.3, C("kinds") - 0.02)),
                 (FadeIn(VGroup(fr1, ch1, ic1), shift=UP * 0.25), "kinds", "kinds+0.5"))
        k_end = min(C("kinds") + 1.25, C("counter") - 0.05)
        self.run(k_end, (Create(newb), "kinds+0.5", "kinds+0.75"),
                 (newb.animate.shift(DOWN * drop), "kinds+0.75", k_end))
        self.wait_until("counter")
        c_end = min(C("counter") + 1.3, C("famous") - 0.05)
        self.run(c_end,
                 (FadeIn(VGroup(fr2, ch2), shift=UP * 0.25), "counter", "counter+0.45"),
                 (LaggedStart(*[Create(c) for c in checks], lag_ratio=0.35), "counter+0.25", "counter+0.8"),
                 (GrowFromCenter(bad), "counter+0.8", "counter+1.1"))
        self.wait_until("famous")
        self.run("famous+0.95",
                 (FadeIn(VGroup(fr3, ch3), shift=UP * 0.25), "famous", "famous+0.45"),
                 (DrawBorderThenFill(star), "famous+0.2", "famous+0.95"),
                 (FadeIn(star_glow), "famous+0.5", "famous+0.95"))
        dim = VGroup(fr1, ch1, ic1, newb, fr2, ch2, checks, bad)
        hi_end = min(C("famous") + 1.7, C("zeta") - 0.5)
        c3 = fr3.get_center()
        self.run(hi_end,
                 dim.animate.fade(0.68),
                 VGroup(ch3, star, star_glow).animate.scale(1.08, about_point=c3),
                 fr3.animate.set_stroke(width=3.5, opacity=1).scale(1.08))
        # gentle breathing while the sentence finishes
        t_tz = C("zeta") - 0.35
        if t_tz - self.now > 0.6:
            self.run(t_tz, star.animate(rate_func=there_and_back).scale(1.07),
                     star_glow.animate(rate_func=there_and_back).set_stroke(opacity=0.13))

        # ============ teaser vignettes
        header = chip("FAMOUS PROBLEMS", YELLOW_, size=22, pad_x=0.18, pad_y=0.09).move_to([0, 3.4, 0])
        CAPY = -3.12

        def cap(s):
            return bold(s, 30, WHITE_).move_to([0, CAPY, 0])

        SH = LEFT * 1.3
        # zeta
        Vz, z_static, zeros, halos, zlabs = self.vig_zeta()
        cz = cap("Zeros of the Riemann zeta function")
        self.run("zeta+0.35",
                 FadeOut(VGroup(fr1, ch1, ic1, newb, fr2, ch2, checks, bad, fr3, star, star_glow)),
                 ReplacementTransform(ch3, header),
                 (FadeIn(z_static, shift=SH), "zeta-0.15", "zeta+0.35"),
                 (FadeIn(cz), "zeta-0.1", "zeta+0.35"))
        z_end = min(C("zeta") + 1.45, C("pi") - 0.05)
        self.run(z_end,
                 LaggedStart(*[AnimationGroup(GrowFromCenter(z), FadeIn(h)) for z, h in zip(zeros, halos)],
                             lag_ratio=0.3),
                 (LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in zlabs], lag_ratio=0.5),
                  "zeta+0.45", z_end))
        # pi
        Vp, p_static, m22, m355, digits = self.vig_pi()
        cp = cap("How well fractions approximate π")
        self.wait_until("pi-0.05")
        self.run("pi+0.4",
                 FadeOut(Vz, shift=SH), FadeOut(cz),
                 FadeIn(p_static, shift=SH), FadeIn(cp))
        p_end = min(C("pi") + 1.9, C("kakeya") - 0.05)
        self.run(p_end,
                 (AnimationGroup(FadeIn(m22[0], shift=DOWN * 0.4), FadeIn(m22[1])), "pi+0.4", "pi+0.75"),
                 (AnimationGroup(FadeIn(m355[0], shift=DOWN * 0.4), FadeIn(m355[1])), "pi+0.8", "pi+1.15"),
                 (Flash(m355[0], color=GREEN_, line_length=0.18, flash_radius=0.2), "pi+1.1", "pi+1.45"),
                 (FadeIn(digits, shift=UP * 0.15), "pi+1.15", p_end))
        # kakeya
        t_k = C("kakeya") - 0.05
        k_dur = (C("ugc") + 0.35) - t_k
        Vk = self.vig_kakeya(t_k, k_dur)
        ck = cap("The Kakeya conjecture")
        self.wait_until(t_k)
        self.run("kakeya+0.35",
                 FadeOut(Vp, shift=SH), FadeOut(cp),
                 FadeIn(Vk, shift=SH, suspend_mobject_updating=False), FadeIn(ck))
        # UGC
        Vu, u_static, arrows, discs, ok = self.vig_ugc()
        cu = cap("The Unique Games Conjecture")
        self.wait_until("ugc-0.05")
        self.run("ugc+0.35",
                 FadeOut(Vk, shift=SH, suspend_mobject_updating=False), FadeOut(ck),
                 FadeIn(u_static, shift=SH), FadeIn(cu))
        u_end = min(C("ugc") + 1.6, C("plane") - 0.05)
        self.run(u_end,
                 (LaggedStart(*[GrowFromCenter(d) for d in discs], lag_ratio=0.18), "ugc+0.35", "ugc+0.85"),
                 (LaggedStart(*[a.animate.set_color(GREEN_ if g else RED_) for a, g in zip(arrows, ok)],
                              lag_ratio=0.15), "ugc+0.85", "ugc+1.4"),
                 (Indicate(arrows[5], color=RED_, scale_factor=1.06), "ugc+1.35", u_end))
        # plane
        t_p = C("plane") - 0.05
        Vpl, hexes, pdyn = self.vig_plane(t_p)
        cpl = cap("How many colors to paint the plane?")
        self.wait_until(t_p)
        self.run("plane+0.5",
                 FadeOut(Vu, shift=SH), FadeOut(cu),
                 FadeIn(Vpl, shift=SH, suspend_mobject_updating=False), FadeIn(cpl))

        # ============ title
        self.wait_until("title-0.15")
        X, Y, rad, lvl = self.F["X"], self.F["Y"], self.F["rad"], self.F["lvl"]
        dt_ = np.sqrt((X / 5.9) ** 2 + ((Y - 0.05) / 1.9) ** 2)
        ft = smoothstep(0.72, 1.12, dt_)
        is_s = np.zeros(len(X), bool)
        is_s[self.surv_idx] = True
        tfield = VGroup()
        tops = []
        for lv, op in enumerate([0.22, 0.36, 0.55]):
            idx = np.where((lvl == lv) & ~is_s & (ft > 0.05))[0]
            tfield.add(dots_vm(np.c_[X[idx], Y[idx]], rad[idx], FIELD_COLOR, 0))
            tops.append(op * float(ft[idx].mean()))
        idx = np.where(is_s & (ft > 0.05))[0]
        tfield.add(dots_vm(np.c_[X[idx], Y[idx]], rad[idx], YELLOW_, 0))
        tops.append(0.6 * float(ft[idx].mean()))
        self.add(tfield)
        self.drift(tfield, C("title"), 0.006)

        title = serif("4,000 Problems", 108, WHITE_)
        title[:5].set_color(YELLOW_)
        title.move_to(UP * 0.55)
        rule = Line(LEFT, RIGHT, color=YELLOW_, stroke_width=3).set_width(5.2).next_to(title, DOWN, buff=0.38)
        sub = txt("A guided tour of AI-written mathematics", 36, WHITE_).next_to(rule, DOWN, buff=0.38)
        stats = txt("722 preprints  ·  17 fields  ·  372 result families  ·  235 with Lean",
                    24, GREY_).next_to(sub, DOWN, buff=0.3)
        self.run("title+0.45",
                 FadeOut(Vpl, suspend_mobject_updating=False), FadeOut(cpl), FadeOut(header))
        self.run("title+2.6",
                 (AnimationGroup(*[fade_fill(m, o) for m, o in zip(tfield, tops)],
                                 suspend_mobject_updating=False), "title+0.2", "title+1.8"),
                 (Write(title, run_time=1.2), "title+0.3", "title+1.5"),
                 (GrowFromCenter(rule), "title+1.2", "title+1.7"),
                 (FadeIn(sub, shift=UP * 0.12), "title+1.45", "title+2.0"),
                 (FadeIn(stats, shift=UP * 0.12), "title+1.95", "title+2.55"))
        self.finish(fade=0.6)
