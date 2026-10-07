import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import json

import numpy as np

# --------------------------------------------------------------------------- mosaic
# All 372 first pages in one pre-composited PNG (31 x 12 grid). Tile size is
# chosen so the mosaic is ~1:1 with the 1080p frame at its rest size.
CACHE = BUILD / "cache" / "s99_outro"
COLS, ROWS = 31, 12
TW, TH, GAP = 43, 61, 6
MW = COLS * TW + (COLS - 1) * GAP          # 1513 px
MH = ROWS * TH + (ROWS - 1) * GAP          # 798 px
REST_H = 5.4                               # scene units (times the slow drift g(t))
REST_C = np.array([0.0, 0.80, 0.0])
BAND_Y = -2.95                             # lower-third caption row


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = np.clip(x, 0.0, 1.0)
    return 1 - (1 - x) ** 3


def keyed(keys, t):
    """keys: [(time, value, ease)], value scalar or tuple; ease applies to the
    segment that ends at that key."""
    if t <= keys[0][0]:
        return np.array(keys[0][1], dtype=float)
    for (t0, v0, _), (t1, v1, ez) in zip(keys, keys[1:]):
        if t <= t1:
            a = ez((t - t0) / max(t1 - t0, 1e-6))
            v0, v1 = np.array(v0, dtype=float), np.array(v1, dtype=float)
            return v0 + (v1 - v0) * a
    return np.array(keys[-1][1], dtype=float)


def tile_slices(i):
    r, c = divmod(i, COLS)
    y, x = r * (TH + GAP), c * (TW + GAP)
    return slice(y, y + TH), slice(x, x + TW)


def build_pages(nums):
    from PIL import Image
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"mosaic_{COLS}x{ROWS}_{TW}x{TH}.png"
    if not out.exists():
        canvas = Image.new("RGBA", (MW, MH), (0, 0, 0, 0))
        for i, n in enumerate(nums):
            r, c = divmod(i, COLS)
            im = Image.open(thumb_path(n)).convert("RGB").resize((TW, TH), Image.LANCZOS)
            canvas.paste(im, (c * (TW + GAP), r * (TH + GAP)))
        canvas.save(out)
    return np.asarray(Image.open(out).convert("RGBA")).astype(np.float32)


def qmark_mask():
    """Antialiased '?' glyph (Inter Bold) sized to one tile, as a 0..1 mask."""
    from PIL import Image, ImageDraw, ImageFont
    s = 4
    font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", int(TH * 0.62 * s))
    im = Image.new("L", (TW * s, TH * s), 0)
    ImageDraw.Draw(im).text((TW * s / 2, TH * s / 2), "?", font=font, fill=255, anchor="mm")
    im = im.resize((TW, TH), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def make_variant(base, spec):
    """spec(i) -> dict(b=brightness, tint=rgb|None, ta=tint amount,
    border=rgb|None, stamp=(mask, rgb)|None)."""
    out = base.copy()
    for i in range(len(spec)):
        s = spec[i]
        ys, xs = tile_slices(i)
        px = out[ys, xs, :3]
        px *= s.get("b", 1.0)
        if s.get("tint") is not None:
            ta = s["ta"]
            px *= (1 - ta) + ta * s["tint"] / 255.0
        if s.get("border") is not None:
            col, bw = s["border"], s.get("bw", 2)
            px[:bw] = col
            px[-bw:] = col
            px[:, :bw] = col
            px[:, -bw:] = col
        if s.get("stamp") is not None:
            m, col = s["stamp"]
            px[:] = px * (1 - m[..., None]) + col * m[..., None]
    return out


PAD = 4


def fast_draw_image(cam, im, pa):
    """Axis-aligned replacement for Camera.display_image_mobject: resize only the
    on-screen part (PIL resize with a float source box keeps sub-pixel motion) and
    alpha-composite just that region. ~10x cheaper than the generic perspective path."""
    from PIL import Image
    arr = im.pixel_array
    if getattr(im, "_pil_src", None) is not arr:
        im._pil = Image.fromarray(np.pad(arr, ((PAD, PAD), (PAD, PAD), (0, 0))), "RGBA")
        im._pil_src = arr
    H, W = arr.shape[:2]
    pw, ph = cam.pixel_width, cam.pixel_height
    fw, fh = cam.frame_width, cam.frame_height
    fc = cam.frame_center
    ul, dr = im.get_corner(UL), im.get_corner(DR)
    x0 = (ul[0] - fc[0] + fw / 2) / fw * pw
    y0 = (fc[1] + fh / 2 - ul[1]) / fh * ph
    x1 = (dr[0] - fc[0] + fw / 2) / fw * pw
    y1 = (fc[1] + fh / 2 - dr[1]) / fh * ph
    if x1 - x0 < 1 or y1 - y0 < 1:
        return
    ox0, oy0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
    ox1, oy1 = min(pw, int(np.ceil(x1))), min(ph, int(np.ceil(y1)))
    if ox1 <= ox0 or oy1 <= oy0:
        return
    sx, sy = W / (x1 - x0), H / (y1 - y0)
    box = ((ox0 - x0) * sx + PAD, (oy0 - y0) * sy + PAD, (ox1 - x0) * sx + PAD, (oy1 - y0) * sy + PAD)
    res = im._pil.resize((ox1 - ox0, oy1 - oy0), Image.BILINEAR, box=box)
    region = Image.fromarray(np.ascontiguousarray(pa[oy0:oy1, ox0:ox1]), "RGBA")
    pa[oy0:oy1, ox0:ox1] = np.asarray(Image.alpha_composite(region, res))


class FastImage(ImageMobject):
    pass


class Mosaic:
    """One ImageMobject driven entirely by scene time: per-tile cross-fades
    between pre-built variants (waves), global opacity, and pose (zoom)."""

    def __init__(self, scene, base):
        self.scene = scene
        self.n = COLS * ROWS
        self.cur = base
        tm = np.full((MH, MW), self.n, dtype=np.int32)
        for i in range(self.n):
            ys, xs = tile_slices(i)
            tm[ys, xs] = i
        self.tile_map = tm
        self.trans = []          # dicts: t0, t1, target, delays, tau
        self.alpha_keys = [(0, 1.0, smooth)]
        self.pose_keys = [(0, (1.0, 0, 0), smooth)]
        self.drift = lambda t: 1.0
        self.glints = []         # dicts: t0, t1, delta, phase, period
        self._shown_key = None
        self.img = FastImage(base.astype(np.uint8))
        self.img.height = REST_H
        self.img.add_updater(lambda m, dt: self.update(self.scene.now))

    # -------------------------------------------------------------- schedule
    def wave(self, t0, dur, target, delays=None, tau=0.35):
        delays = np.zeros(self.n) if delays is None else np.asarray(delays, float)
        if delays.max() > 0:
            delays = delays / delays.max() * max(dur - tau, 0.0)
        self.trans.append(dict(t0=t0, t1=t0 + dur, target=target, delays=delays, tau=tau))
        self.trans.sort(key=lambda d: d["t0"])

    def glint(self, t0, t1, delta, phase, period=2.2):
        """Slow staggered shimmer: tiles move towards settled + delta and back."""
        self.glints.append(dict(t0=t0, t1=t1, delta=delta, phase=phase, period=period))

    def weights(self, tr, t):
        return smooth((t - tr["t0"] - tr["delays"]) / tr["tau"])

    def lit(self, k, t, subset):
        """How many tiles of `subset` (bool array) are >= half-way in wave k."""
        tr = self.trans[k]
        if t <= tr["t0"]:
            return 0
        return int(np.sum((self.weights(tr, t) >= 0.5) & subset))

    # -------------------------------------------------------------- per frame
    def update(self, t):
        # pixel content
        key, arr = None, None
        done = [tr for tr in self.trans if t >= tr["t1"]]
        settled = done[-1]["target"] if done else self.cur
        active = [tr for tr in self.trans if tr["t0"] <= t < tr["t1"]]
        a = float(keyed(self.alpha_keys, t))
        if active:
            tr = active[0]
            prev = [d for d in self.trans if d["t1"] <= tr["t0"]]
            src = prev[-1]["target"] if prev else self.cur
            w = np.append(self.weights(tr, t), 0.0).astype(np.float32)
            W = w[self.tile_map][..., None]
            arr = src + (tr["target"] - src) * W
            key = ("w", round(t, 4), round(a, 4))
        else:
            arr = settled
            key = ("s", id(settled), round(a, 4))
            for g in self.glints:
                if g["t0"] <= t < g["t1"]:
                    env = smooth((t - g["t0"]) / 0.8) * smooth((g["t1"] - t) / 0.5)
                    w = env * 0.5 * (1 - np.cos(2 * np.pi * (t - g["t0"]) / g["period"] + g["phase"]))
                    W = np.append(w, 0.0).astype(np.float32)[self.tile_map][..., None]
                    arr = settled + g["delta"] * W
                    key = ("g", round(t, 4), round(a, 4))
        if key != self._shown_key:
            out = arr.copy() if a < 0.999 else arr
            if a < 0.999:
                out[..., 3] *= a
            self.img.pixel_array = np.clip(out, 0, 255).astype(np.uint8)
            self._shown_key = key
        # pose
        s, cx, cy = keyed(self.pose_keys, t)
        self.img.height = REST_H * s * self.drift(t)
        self.img.move_to([cx, cy, 0])


class S99Outro(VoiceScene):
    def setup(self):
        super().setup()
        cam = self.camera
        generic = cam.display_image_mobject

        def display(im, pa):
            if isinstance(im, FastImage):
                fast_draw_image(cam, im, pa)
            else:
                generic(im, pa)
        cam.display_image_mobject = display

    def construct(self):
        C = self.timing["cues"]
        T = self.narr_end
        t_mos, t_cav, t_test = C["mosaic"], C["caveat"], C["test"]
        t_lean, t_pub, t_end, t_link = C["lean"], C["public"], C["end"], C["link"]
        L0, L0e, L1e, L2e, L3e = C["L0"], C["L0_end"], C["L1_end"], C["L2_end"], C["L3_end"]

        # ---------------------------------------------------------- data
        cat = load_catalog()
        nums = sorted(e["num"] for e in cat)
        assert len(nums) == COLS * ROWS
        named = set(json.loads((VIDEO / "data" / "named.json").read_text()))
        spot = {r["num"] for r in json.loads((VIDEO / "data" / "research.json").read_text())}
        is_named = np.array([n in named for n in nums])
        is_lean = np.array([CATALOG[n]["lean"] for n in nums])
        n_named, n_lean, N = int(is_named.sum()), int(is_lean.sum()), len(nums)
        rr = np.array([i // COLS for i in range(N)], float)
        cc = np.array([i % COLS for i in range(N)], float)
        rng = np.random.default_rng(7)

        # a few named, non-Lean, non-spotlight tiles get a question mark (spread out)
        cand = [i for i in range(N) if is_named[i] and not is_lean[i] and nums[i] not in spot
                and 2 <= cc[i] <= COLS - 3 and 1 <= rr[i] <= ROWS - 2]
        qs = [cand[len(cand) // 2]]
        while len(qs) < min(7, len(cand)):
            d = [min((cc[i] - cc[j]) ** 2 + (2.0 * (rr[i] - rr[j])) ** 2 for j in qs) for i in cand]
            qs.append(cand[int(np.argmax(d))])
        q_order = sorted(qs, key=lambda i: cc[i])
        frac = rng.choice(N, size=40, replace=False)
        is_frac = np.zeros(N, bool)
        is_frac[frac] = True

        # ---------------------------------------------------------- variants
        base = build_pages(nums)
        qm = qmark_mask()
        Y, TL, R = rgb(YELLOW_), rgb(TEAL_), rgb(RED_)
        dimb = 0.17
        V0 = make_variant(base, [dict(b=0.85)] * N)
        V_named = make_variant(base, [dict(b=1.0, border=Y, tint=Y, ta=0.06) if is_named[i]
                                      else dict(b=dimb) for i in range(N)])
        V_q = make_variant(base, [dict(b=0.28, border=R, stamp=(qm, R)) if i in qs
                                  else dict(b=1.0, border=Y, tint=Y, ta=0.06) if is_named[i]
                                  else dict(b=dimb) for i in range(N)])
        V_lean = make_variant(base, [dict(b=0.97, tint=TL, ta=0.30, border=TL) if is_lean[i]
                                     else dict(b=dimb) for i in range(N)])
        V_all = make_variant(base, [dict(b=0.86)] * N)
        V_survive = make_variant(base, [dict(b=0.86) if is_frac[i] else dict(b=0.2) for i in range(N)])
        V_frac = make_variant(base, [dict(b=1.0, tint=Y, ta=0.38, border=Y) if is_frac[i]
                                     else dict(b=0.2) for i in range(N)])
        V_frac_lo = make_variant(base, [dict(b=0.72, tint=Y, ta=0.38, border=Y) if is_frac[i]
                                        else dict(b=0.2) for i in range(N)])
        V_dim = make_variant(base, [dict(b=0.5)] * N)

        M = Mosaic(self, V0)
        jit = rng.uniform(0, 1, N)
        sweep = 0.75 * cc / COLS + 0.25 * rr / ROWS + 0.10 * jit
        cols_sweep = cc / COLS + 0.12 * jit
        radial = np.hypot((cc - (COLS - 1) / 2) / COLS, 1.6 * (rr - (ROWS - 1) / 2) / COLS) + 0.05 * jit
        q_delay = np.zeros(N)
        for k, i in enumerate(q_order):
            q_delay[i] = k + 1e-3
        M.wave(t_mos + 0.55, 2.0, V_named, sweep)                       # 0: named light up
        q_t0 = t_cav + 0.75
        q_dur = max(1.5, min(4.4, (t_test - 0.9) - q_t0))
        M.wave(q_t0, q_dur, V_q, q_delay, tau=0.4)                      # 1: question marks
        M.wave(t_lean + 0.3, 1.5, V_lean, cols_sweep)                   # 2: Lean (lands just after "...thirty-five")
        M.wave(t_pub + 0.1, 1.6, V_all, radial)                         # 3: all public
        # "If even a fraction...": the room dims almost uniformly (no random flicker under
        # the closing line), then on "fraction" the 40 survivors warm to gold.
        M.wave(t_end - 0.15, 0.65, V_survive, radial, tau=0.5)          # 4a: lights down (in the pause)
        M.wave(t_end + 0.6, 0.9, V_frac, rng.uniform(0, 1, N), tau=0.35)   # 4b: a fraction
        M.wave(t_link - 0.15, 0.9, V_dim, tau=0.9)                      # 5: end-card wall
        M.glint(t_end + 1.7, t_link - 0.15, V_frac_lo - V_frac, rng.uniform(0, 2 * np.pi, N))

        M.alpha_keys = [(0, 0.0, smooth), (0.8, 1.0, smooth), (t_link - 0.15, 1.0, smooth),
                        (t_link + 0.85, 0.12, smooth), (T, 0.12, smooth)]
        rest = (1.0, REST_C[0], REST_C[1])
        push = (1.24, 0.0, 0.03)
        wall = (1.62, 0.0, 0.0)       # full-bleed (mosaic is wider than 16:9)
        wall_out = (1.5, 0.0, 0.0)
        t_wall = min(2.6, 0.6 * (t_link - t_end))   # slow push to full-bleed under the closing line
        M.pose_keys = [(0, (1.65, 0.9, -0.2), smooth), (t_mos + 2.3, rest, ease_out),
                       (t_cav, rest, smooth), (t_cav + 1.6, push, smooth),
                       (t_test - 0.2, push, smooth), (t_test + 0.8, rest, smooth),
                       (t_end, rest, smooth), (t_end + t_wall, wall, smooth),
                       (T, wall_out, lambda x: np.clip(x, 0, 1))]
        M.drift = lambda t: 1.0 + 0.06 * (1 - t / T)
        M.update(0)
        self.add(M.img)

        # ---------------------------------------------------------- counters
        def counter(value_fn, color_fn, opacity_fn, right_x, y, size=64, slots=3):
            """Time-driven integer. Fixed glyph slots (no submobject swapping), so
            Cairo's per-play moving-mobject list never holds stale digits."""
            cache = {}
            holder = VGroup(*[VMobject(stroke_width=0, fill_opacity=0) for _ in range(slots)])
            st = {"k": None}

            def upd(m, dt):
                t = self.now
                v, col, op = int(value_fn(t)), color_fn(t), float(opacity_fn(t))
                rx = float(right_x(t)) if callable(right_x) else right_x
                k = (v, col, round(op, 3), round(rx, 4))
                if k == st["k"]:
                    return
                st["k"] = k
                if v not in cache:
                    tx = Text(str(v), font=SANS, font_size=size, weight=BOLD)
                    tx.move_to([-tx.width / 2, y, 0])
                    cache[v] = [g.points.copy() for g in tx.submobjects]
                glyphs = cache[v]
                for j, slot in enumerate(m.submobjects):
                    if j < len(glyphs):
                        slot.set_points(glyphs[j] + np.array([rx, 0, 0]))
                        slot.set_fill(col, opacity=op).set_stroke(width=0)
                    else:
                        slot.set_points(np.zeros((0, 3)))
            holder.add_updater(upd)
            upd(holder, 0)
            return holder

        def fade_fn(t_in, t_out=None, d=0.35):
            def f(t):
                a = smooth((t - t_in) / d)
                if t_out is not None:
                    a *= 1 - smooth((t - t_out) / d)
                return a
            return f

        def slash372():
            return Text("/ 372", font=SANS, font_size=44, color=GREY_)

        SL = 0.26   # gap between the number and '/ 372'

        def place_row(num_w, label, gap=0.45):
            """Centre [number][/ 372][label] on BAND_Y; returns (right_x of number, D)."""
            D = slash372()
            total = num_w + SL + D.width + gap + label.width
            left = -total / 2
            rx = left + num_w
            D.move_to([rx + SL + D.width / 2, BAND_Y, 0])
            ref = Text("0", font=SANS, font_size=64, weight=BOLD).move_to([0, BAND_Y, 0])
            D.align_to(ref, DOWN)
            label.next_to(D, RIGHT, buff=gap)
            label.set_y(BAND_Y - 0.06)
            return rx, D

        w372 = Text("372", font=SANS, font_size=64, weight=BOLD).width

        # row 1: 126 / 372 featured in this video
        lab1 = txt("featured in this video", 30, WHITE_)
        w126 = Text(str(n_named), font=SANS, font_size=64, weight=BOLD).width
        rx1, D1 = place_row(w126, lab1)
        lab1_final = lab1.get_center()
        # before '/ 372' arrives: [126]  featured in this video  (centred), then make room
        tot_i = w126 + 0.45 + lab1.width
        rx1_i = -tot_i / 2 + w126
        lab1.set_x(rx1_i + 0.45 + lab1.width / 2)
        t_out = L0 + 0.56 * (L0e - L0)          # "... out of three hundred and seventy-two"
        N1 = counter(lambda t: M.lit(0, t, is_named), lambda t: YELLOW_,
                     fade_fn(t_mos + 0.8, t_cav),
                     lambda t: rx1_i + (rx1 - rx1_i) * smooth((t - t_out) / 0.6), BAND_Y)
        self.add(N1)

        # row 3: 235 / 372 [LEAN] with Lean proofs / of at least part of the result
        badge3 = lean_badge(16)
        lab3a = txt("with Lean proofs", 30, WHITE_)
        lab3b = txt("of at least part of the result", 22, GREY_)
        lab3t = VGroup(lab3a, lab3b).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        lab3 = VGroup(badge3, lab3t).arrange(RIGHT, buff=0.22)
        rx3, D3 = place_row(w372, lab3)
        lab3.set_y(BAND_Y - 0.02)
        lab4 = txt("public, for anyone to check", 30, WHITE_)
        lab4.next_to(D3, RIGHT, buff=0.45).set_y(BAND_Y - 0.06)

        def n3_val(t):
            if t < M.trans[3]["t0"]:
                return M.lit(2, t, is_lean)
            return n_lean + M.lit(3, t, ~is_lean)

        def n3_col(t):
            a = float(smooth((t - (t_pub + 0.1)) / 0.6))
            return interpolate_color(ManimColor(TEAL_), ManimColor(WHITE_), a).to_hex()

        N3 = counter(n3_val, n3_col, fade_fn(t_lean + 0.35, t_end), rx3, BAND_Y)
        self.add(N3)

        # ---------------------------------------------------------- beat 1: mosaic
        self.play_at(t_mos + 1.0, FadeIn(lab1, shift=UP * 0.12), run_time=0.5)
        self.play_at(t_out, lab1.animate.move_to(lab1_final), FadeIn(D1, scale=0.9), run_time=0.6)

        # ---------------------------------------------------------- beat 2: caveat
        self.play_at(t_cav, FadeOut(lab1, shift=DOWN * 0.12), FadeOut(D1, shift=DOWN * 0.12),
                     run_time=0.4)

        # ---------------------------------------------------------- beat 3: the real test
        span = L1e - t_test
        t_expert = t_test + 0.40 * span
        t_formal = t_test + 0.70 * span

        mag = VGroup(Circle(radius=0.12, stroke_color=BLUE_, stroke_width=3.5),
                     Line(ORIGIN, DR * 0.12, stroke_color=BLUE_, stroke_width=4))
        mag[1].shift(mag[0].point_at_angle(-PI / 4) - mag[1].get_start())
        chip1_row = VGroup(mag, txt("expert checking", 30, WHITE_)).arrange(RIGHT, buff=0.2)
        badge2 = lean_badge(16)
        chip2_row = VGroup(txt("formal verification", 30, WHITE_), badge2).arrange(RIGHT, buff=0.22)

        def boxed(row, color):
            box = RoundedRectangle(width=row.width + 0.55, height=row.height + 0.36, corner_radius=0.16,
                                   stroke_color=color, stroke_width=2, fill_color=color,
                                   fill_opacity=0.12)
            row.move_to(box)
            return VGroup(box, row)

        chip1, chip2 = boxed(chip1_row, BLUE_), boxed(chip2_row, TEAL_)
        plus = txt("+", 36, GREY_)
        head = caps("the real test", 22, GREY_)
        chips = VGroup(chip1, plus, chip2).arrange(RIGHT, buff=0.35)
        chips.move_to([0, BAND_Y - 0.14, 0])
        head.next_to(chips, UP, buff=0.2)

        self.play_at(t_test + 0.55, FadeIn(head, shift=UP * 0.1), run_time=0.5)
        self.play_at(t_expert, GrowFromCenter(chip1[0]), FadeIn(chip1[1], scale=0.9), run_time=0.5)
        self.play_at(t_formal, FadeIn(plus), GrowFromCenter(chip2[0]), FadeIn(chip2[1], scale=0.9),
                     run_time=0.5)

        # ---------------------------------------------------------- beat 4: Lean
        self.wait_until(t_lean)
        self.play(FadeOut(head, shift=DOWN * 0.25), FadeOut(chip1, shift=DOWN * 0.25),
                  FadeOut(plus, shift=DOWN * 0.25), FadeOut(chip2[0], shift=DOWN * 0.25),
                  FadeOut(chip2[1][0], shift=DOWN * 0.25), run_time=0.35)
        self.play(ReplacementTransform(badge2, badge3), FadeIn(D3, shift=LEFT * 0.15), run_time=0.6)
        span2 = t_pub - t_lean   # "...already have Lean proofs of at least part of the result,"
        self.play_at(t_lean + 0.55 * span2, FadeIn(lab3a, shift=UP * 0.1), run_time=0.5)
        self.play_at(t_lean + 0.70 * span2, FadeIn(lab3b, shift=UP * 0.1), run_time=0.5)

        # ---------------------------------------------------------- beat 5: public
        self.play_at(t_pub + 0.1, FadeOut(lab3, shift=UP * 0.15), run_time=0.3)
        t_public = max(self.now + 0.1, t_pub + 0.40 * (L2e - t_pub))   # "...every paper is public"
        self.play_at(t_public, FadeIn(lab4, shift=UP * 0.15), run_time=0.45)

        # ---------------------------------------------------------- beat 6: closing line
        line = Text("If even a fraction hold up…", font=SERIF, font_size=56, weight=BOLD,
                    color=WHITE_, t2c={"fraction": YELLOW_})
        shade = Rectangle(width=config.frame_width + 1, height=line.height + 1.2, stroke_width=0,
                          fill_color=BG, fill_opacity=0.82)
        self.wait_until(t_end)
        self.play(FadeOut(lab4, shift=DOWN * 0.12, run_time=0.35),
                  FadeOut(D3, shift=DOWN * 0.12, run_time=0.35),
                  FadeIn(shade, run_time=0.5), Write(line, run_time=1.35))

        # ---------------------------------------------------------- beat 7: end card
        title = Text("4,000 Problems", font=SERIF, font_size=40, weight=BOLD, color=WHITE_)
        url = Text("github.com/openai/math", font=MONO, font_size=46, color=WHITE_,
                   t2c={"github.com/": GREY_})
        url_box = RoundedRectangle(width=url.width + 0.8, height=url.height + 0.6, corner_radius=0.18,
                                   stroke_color=BLUE_, stroke_width=2.2, fill_color=CARD,
                                   fill_opacity=0.95)
        url.move_to(url_box)
        hint = txt("link in the description", 24, GREY_)
        card = VGroup(title, VGroup(url_box, url), hint).arrange(DOWN, buff=0.45)
        card.move_to(ORIGIN)
        rule = Line(LEFT, RIGHT, color=BLUE_, stroke_width=2.5).set_width(title.width * 0.5)
        rule.next_to(title, DOWN, buff=0.16)

        self.wait_until(t_link - 0.15)   # "...about to change." has ended; card lands on "repository"
        self.play(LaggedStart(
            AnimationGroup(FadeOut(line, shift=UP * 0.35), FadeOut(shade)),
            AnimationGroup(FadeIn(title, shift=UP * 0.2), GrowFromCenter(rule),
                           FadeIn(url_box, scale=0.96)),
            lag_ratio=0.45), run_time=0.85)
        self.play(AddTextLetterByLetter(url, time_per_char=0.03), run_time=0.65)
        self.play(FadeIn(hint, shift=UP * 0.1), run_time=0.4)
        t_look = t_link + 0.73 * (L3e - t_link)   # "Go take a look."
        flash = url_box.copy().set_fill(opacity=0).set_stroke(YELLOW_, width=5)
        self.play_at(t_look, ShowPassingFlash(flash, time_width=0.35), run_time=1.3)

        self.finish()
