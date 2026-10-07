import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
from lib.voice import VoiceScene
from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...

import numpy as np

# =====================================================================
# Numerics (baked once, cached under build/cache/c9_hotspots/)
#
# First nonconstant Neumann eigenfunction of smooth star-shaped (hence
# simply connected) blobs: 5-point finite differences on a masked grid,
# zero-flux (Neumann) graph Laplacian, scipy eigsh in shift-invert mode.
# Also: insulated heat flow from random "uneven heating" on the main blob
# (implicit Euler), and steepest-ascent/descent paths to the extremes.
# verify.txt records, per shape, that max/min sit on the boundary (strictly
# above/below everything >3h inside) and min |grad u| away from the edge.
# =====================================================================
CACHE = BUILD / "cache" / "c9_hotspots"
SHAPES = [   # R(th) = scale * (1 + sum a cos(k (th - rot) + ph))
    dict(terms=[(2, 0.32, 0.0), (1, 0.12, 2.2), (3, 0.12, 0.9), (5, 0.03, 0.2)], rot=0.25),
    dict(terms=[(2, 0.30, 0.0), (1, 0.16, np.pi / 2), (3, 0.12, 0.0), (4, 0.05, 0.4)], rot=0.5, scale=0.92),
    dict(terms=[(2, 0.36, 0.0), (1, 0.10, 0.0), (3, 0.14, np.pi / 2)], rot=-0.45, scale=0.95),
]
SEG = 22                                   # morph frames per shape-to-shape segment
NTH = 720
TH = np.linspace(-np.pi, np.pi, NTH, endpoint=False)
BOX = (-1.5, 1.5, -1.0, 1.0)               # image box in shape units (bbox-centred)
PX_W, PX_H = 540, 360
GRID = (-1.65, 1.65, -1.25, 1.25)          # solver grid box (polar frame)
H_SOLVE = 0.01


def shape_R(s, th):
    r = np.ones_like(th)
    for k, a, ph in s["terms"]:
        r = r + a * np.cos(k * (th - s["rot"]) + ph)
    return s.get("scale", 1.0) * r


def shape_off(s):
    th = np.linspace(-np.pi, np.pi, 4000)
    r = shape_R(s, th)
    x, y = r * np.cos(th), r * np.sin(th)
    return -np.array([(x.min() + x.max()) / 2, (y.min() + y.max()) / 2])


def pixel_grid():
    x0, x1, y0, y1 = BOX
    px = (x1 - x0) / PX_W
    xs = x0 + (np.arange(PX_W) + 0.5) * px
    ys = y1 - (np.arange(PX_H) + 0.5) * px
    return np.meshgrid(xs, ys), px


def solve_mode(Rtab, h, k=3):
    import scipy.sparse as sp
    import scipy.sparse.linalg as sla
    X = np.arange(GRID[0], GRID[1] + 1e-9, h)
    Y = np.arange(GRID[2], GRID[3] + 1e-9, h)
    XX, YY = np.meshgrid(X, Y)
    Rg = np.interp(np.arctan2(YY, XX), TH, Rtab, period=2 * np.pi)
    mask = np.hypot(XX, YY) < Rg
    idx = -np.ones(mask.shape, int)
    idx[mask] = np.arange(mask.sum())
    n = int(mask.sum())
    rows, cols = [], []
    for dy, dx in ((0, 1), (1, 0)):
        a = mask[:mask.shape[0] - dy, :mask.shape[1] - dx] & mask[dy:, dx:]
        i1 = idx[:mask.shape[0] - dy, :mask.shape[1] - dx][a]
        i2 = idx[dy:, dx:][a]
        rows += [i1, i2]
        cols += [i2, i1]
    rows = np.concatenate(rows)
    cols = np.concatenate(cols)
    Adj = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    deg = np.asarray(Adj.sum(1)).ravel()
    L = (sp.diags(deg) - Adj).tocsc()      # zero-flux (Neumann) Laplacian on the mask
    vals, vecs = sla.eigsh(L, k=k, sigma=-1e-4, which="LM")
    o = np.argsort(vals)
    return dict(X=X, Y=Y, mask=mask, L=L, h=h, vals=vals[o] / h ** 2, vecs=vecs[:, o])


def extend(sol, f):
    """Grid array of f, extended outside the mask by the nearest inside value."""
    from scipy import ndimage
    F = np.zeros(sol["mask"].shape)
    F[sol["mask"]] = f
    _, (iy, ix) = ndimage.distance_transform_edt(~sol["mask"], return_indices=True)
    return F[iy, ix]


def sample(sol, Fext, x, y):
    from scipy import ndimage
    h = sol["h"]
    return ndimage.map_coordinates(Fext, [(np.atleast_1d(y) - sol["Y"][0]) / h,
                                          (np.atleast_1d(x) - sol["X"][0]) / h],
                                   order=1, mode="nearest")


def bnd_extremes(sol, Fext, Rtab):
    th = np.linspace(-np.pi, np.pi, 2048, endpoint=False)
    r = np.interp(th, TH, Rtab, period=2 * np.pi) - 0.5 * sol["h"]
    v = sample(sol, Fext, r * np.cos(th), r * np.sin(th))
    return th[np.argmax(v)], th[np.argmin(v)], v.max(), v.min()


def verify(sol, f):
    from scipy import ndimage
    mask = sol["mask"]
    F = np.full(mask.shape, np.nan)
    F[mask] = f
    dist = ndimage.distance_transform_edt(mask) * sol["h"]
    bnd = mask & (dist <= 1.01 * sol["h"])
    deep = mask & (dist > 3 * sol["h"])
    gy, gx = np.gradient(np.where(mask, F, 0.0), sol["h"])
    g = np.hypot(gx, gy)
    core = mask & (dist > 0.08)
    return (bool(np.nanmax(F[bnd]) > np.nanmax(F[deep])), bool(np.nanmin(F[bnd]) < np.nanmin(F[deep])),
            float(g[core].min() / g[mask & (dist > 2 * sol["h"])].max()))


def to_pixels(sol, Fext, off):
    (PX, PY), _ = pixel_grid()
    return sample(sol, Fext, (PX - off[0]).ravel(), (PY - off[1]).ravel()).reshape(PX.shape)


def bake(seed=7):
    import scipy.sparse as sp
    import scipy.sparse.linalg as sla
    from scipy import ndimage
    CACHE.mkdir(parents=True, exist_ok=True)
    out, report = {}, []
    # ---------------- morph frames along shape 0 -> 1 -> 2 (eigenfunction per frame)
    qs = np.linspace(0, len(SHAPES) - 1, SEG * (len(SHAPES) - 1) + 1)
    Rtabs, offs, fields, thmax, thmin = [], [], [], [], []
    prev = None
    for q in qs:
        i = min(int(q), len(SHAPES) - 2)
        w = q - i
        Rt = (1 - w) * shape_R(SHAPES[i], TH) + w * shape_R(SHAPES[i + 1], TH)
        off = (1 - w) * shape_off(SHAPES[i]) + w * shape_off(SHAPES[i + 1])
        sol = solve_mode(Rt, H_SOLVE)
        f = sol["vecs"][:, 1]
        Fext = extend(sol, f)
        P = to_pixels(sol, Fext, off)
        if prev is None:   # convention: hot end on the left of shape 0
            tmx, tmn, _, _ = bnd_extremes(sol, Fext, Rt)
            flip = np.cos(tmx) > np.cos(tmn)
        else:              # continuity along the morph
            flip = (P * prev).sum() < 0
        if flip:
            f, Fext, P = -f, -Fext, -P
        prev = P
        tmx, tmn, vmx, vmn = bnd_extremes(sol, Fext, Rt)
        s = max(abs(vmx), abs(vmn))
        report.append((round(float(q), 3), np.round(sol["vals"][1:3], 3).tolist()) + verify(sol, f))
        Rtabs.append(Rt)
        offs.append(off)
        fields.append((P / s).astype(np.float16))
        thmax.append(tmx)
        thmin.append(tmn)
        if q == 0:
            solA, fA, FextA, offA, RA, sA = sol, f, Fext, off, Rt, s
    out.update(morph_R=np.array(Rtabs), morph_off=np.array(offs), morph_F=np.array(fields),
               morph_thmax=np.unwrap(np.array(thmax)), morph_thmin=np.unwrap(np.array(thmin)))
    # ---------------- insulated heat flow on shape 0 from uneven heating
    mask = solA["mask"]
    n = int(mask.sum())
    h = solA["h"]
    phi = fA / sA
    rng = np.random.default_rng(seed)
    noise = ndimage.gaussian_filter(rng.standard_normal(mask.shape), 9)
    u0 = noise[mask]
    u0 = u0 - u0.mean()
    u0 /= np.abs(u0).max()
    proj = (u0 @ phi) / (phi @ phi)
    if proj < 0:
        u0, proj = -u0, -proj
    L = solA["L"] / h ** 2
    Id = sp.identity(n, format="csc")
    times = np.concatenate([[0.0], np.geomspace(2e-4, 1.6, 47)])
    snaps, amps = [], []
    u = u0.copy()
    for k, t in enumerate(times):
        if k > 0:
            dt = (t - times[k - 1]) / 3
            lu = sla.splu((Id + dt * L).tocsc())
            for _ in range(3):
                u = lu.solve(u)
        v = u - u.mean()
        amps.append(np.abs(v).max())
        snaps.append(to_pixels(solA, extend(solA, v), offA))
    amps = np.array(amps)
    out.update(heat_F=np.array([s_ / amps[0] for s_ in snaps]).astype(np.float16), heat_amp=amps / amps[0])
    last = snaps[-1] / amps[-1]
    PA = out["morph_F"][0].astype(float)
    corr = (last * PA).sum() / np.sqrt((last ** 2).sum() * (PA ** 2).sum())
    # ---------------- steepest ascent / descent from the nodal line to the extremes
    XX, YY = np.meshgrid(solA["X"], solA["Y"])
    c = -offA
    near = mask & (np.hypot(XX - c[0], YY - c[1]) < 0.35)
    i0 = np.unravel_index(np.argmin(np.where(near, np.abs(FextA), np.inf)), mask.shape)
    start = np.array([XX[i0], YY[i0]])
    paths = []
    for sign, th_end in ((1, thmax[0]), (-1, thmin[0])):
        p = start.copy()
        pts = [p.copy()]
        for _ in range(2000):
            e = 1e-3
            vv = sample(solA, FextA, p[0] + np.array([e, -e, 0, 0]), p[1] + np.array([0, 0, e, -e]))
            g = sign * np.array([vv[0] - vv[1], vv[2] - vv[3]])
            g /= np.linalg.norm(g) + 1e-12
            q_ = p + 0.008 * g
            if np.hypot(*q_) > np.interp(np.arctan2(q_[1], q_[0]), TH, RA, period=2 * np.pi) - 0.03:
                break
            p = q_
            pts.append(p.copy())
        rend = np.interp(th_end, TH, RA, period=2 * np.pi)
        pts.append(np.array([rend * np.cos(th_end), rend * np.sin(th_end)]))
        paths.append(np.array(pts) + offA)
    out.update(path_hot=paths[0], path_cold=paths[1])
    np.savez(CACHE / "fields.npz", **out)
    (CACHE / "verify.txt").write_text(
        "q, [mu_1, mu_2], max on boundary (strictly above all points >3h inside), "
        "min on boundary, min|grad u| at dist>0.08 / max|grad u|\n"
        + "\n".join(map(str, report))
        + f"\nheat flow: initial projection on mode {proj:.3f}, corr(final snapshot, mode) {corr:.6f}\n")


def load_fields():
    f = CACHE / "fields.npz"
    if not f.exists():
        bake()
    d = np.load(f)
    return {k: d[k] for k in d.files}


# colormap: cold (icy blue) -> neutral slate (the bare plate) -> hot (orange / warm white)
_STOPS = [(-1.0, (225, 245, 255)), (-0.72, (88, 196, 221)), (-0.38, (38, 92, 158)), (0.0, (40, 45, 58)),
          (0.38, (176, 72, 40)), (0.72, (255, 158, 100)), (1.0, (255, 236, 196))]
_xs = np.linspace(-1, 1, 256)
LUT = np.stack([np.interp(_xs, [s[0] for s in _STOPS], [s[1][c] for s in _STOPS]) for c in range(3)], 1).astype(np.uint8)
PLATE = "#282D3A"


def lut_hex(v):
    r, g, b = LUT[int(np.clip((v + 1) * 127.5, 0, 255))]
    return "#%02X%02X%02X" % (r, g, b)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


class C9Hotspots(VoiceScene):
    def construct(self):
        D = load_fields()
        heatF, heat_amp = D["heat_F"], D["heat_amp"]
        mF, mR, mOff = D["morph_F"], D["morph_R"], D["morph_off"]
        mthmax, mthmin = D["morph_thmax"], D["morph_thmin"]
        K, M = len(heatF), len(mF)
        (PXg, PYg), px = pixel_grid()
        acc = ORANGE_

        c = self.cue

        def fr(a, b, f):
            return c(a) + f * (c(b) - c(a))

        # ------------------------------------------------ schedule (all from cues)
        t_plate = c("plate")
        t_ins = fr("L0", "L0_end", 0.33)          # "insulated around its edges"
        t_heat = fr("L0", "L0_end", 0.67)         # "heat it unevenly"
        t_wait = fr("L0", "L0_end", 0.86)         # "and wait"
        t_mag0 = fr("mode", "question", 0.30)     # "the leftover unevenness"
        t_mag1 = fr("mode", "question", 0.80)
        t_settle = fr("mode", "question", 0.92)   # "...settles into one basic pattern"
        t_q = c("question")
        t_walk1 = t_q + min(1.6, 0.75 * (c("rauch") - t_q))
        t_holes = c("holes")
        t_claim = c("claim")
        t_m0 = t_claim + 0.8
        t_ban = fr("claim", "L3_end", 0.47)       # end of "...every smooth shape without holes:"
        t_m2 = t_ban + 0.35
        t_m1 = (t_m0 + t_m2) / 2
        t_edge = fr("claim", "L3_end", 0.62)      # "the hot and cold spots always sit on the edge"

        # placements (centre x, centre y, scale: manim units per shape unit)
        P1 = (-0.9, -0.25, 2.1)
        P2 = (-3.45, -0.35, 1.42)
        P4 = (-4.45, 0.45, 1.5)
        moves = [(t_holes + 0.1, t_holes + 1.1, P1, P2), (t_claim, t_claim + 0.9, P2, P4)]

        def placement(t):
            P = P1
            for a, b, A, B in moves:
                if t >= b:
                    P = B
                elif t > a:
                    s = ease((t - a) / (b - a))
                    P = tuple((1 - s) * x + s * y for x, y in zip(A, B))
                    break
                else:
                    break
            return P

        def heat_params(t):
            gain = ease((t - t_heat) / 0.9)
            p = (K - 1) * min(max((t - t_wait) / (t_settle - t_wait), 0.0), 1.0) ** 1.15
            m = ease((t - t_mag0) / (t_mag1 - t_mag0))
            return gain, p, m

        def qparam(t):
            if t <= t_m1:
                return SEG * ease((t - t_m0) / (t_m1 - t_m0))
            return SEG + SEG * ease((t - t_m1) / (t_m2 - t_m1))

        def now():
            return self.renderer.time

        # ------------------------------------------------ shared per-frame state
        st = {"t": None}
        alphaA = None

        def shape_at(q):
            q = min(max(q, 0.0), M - 1.0)
            i = min(int(q), M - 2)
            w = q - i
            return ((1 - w) * mR[i] + w * mR[i + 1], (1 - w) * mOff[i] + w * mOff[i + 1],
                    (1 - w) * mthmax[i] + w * mthmax[i + 1], (1 - w) * mthmin[i] + w * mthmin[i + 1], i, w)

        def alpha_for(Rt, off):
            x = PXg - off[0]
            y = PYg - off[1]
            Rp = np.interp(np.arctan2(y, x), TH, Rt, period=2 * np.pi)
            return np.clip(0.5 + (Rp - np.hypot(x, y)) / px, 0.0, 1.0)

        def state():
            t = now()
            if st["t"] == t:
                return st
            st["t"] = t
            st["P"] = placement(t)
            if t < t_settle:
                gain, p, m = heat_params(t)
                k0 = min(int(p), K - 2)
                w = p - k0
                F = (1 - w) * heatF[k0].astype(np.float32) + w * heatF[k0 + 1].astype(np.float32)
                A = np.exp((1 - w) * np.log(heat_amp[k0]) + w * np.log(heat_amp[k0 + 1]))
                aref = A ** m
                st["key"] = ("h", round(gain, 4), round(p, 4), round(m, 4))
                st["F"] = F * (gain / aref)
                st["contrast"] = 1.0 / aref
                Rt, off, tmx, tmn, _, _ = shape_at(0)
                st["alpha"] = alphaA
            else:
                q = qparam(t)
                Rt, off, tmx, tmn, i, w = shape_at(q)
                st["key"] = ("m", round(q, 4))
                if st.get("lastkey") != st["key"]:
                    st["F"] = (1 - w) * mF[i].astype(np.float32) + w * mF[i + 1].astype(np.float32)
                    st["alpha"] = alphaA if q == 0 else alpha_for(Rt, off)
                st["contrast"] = 1.0 / heat_amp[-1]
            st["R"], st["off"], st["thmax"], st["thmin"] = Rt, off, tmx, tmn
            return st

        alphaA = alpha_for(mR[0], mOff[0])

        def to_scene(xy):
            cx, cy, S = state()["P"]
            xy = np.atleast_2d(xy)
            return np.column_stack([cx + S * xy[:, 0], cy + S * xy[:, 1], np.zeros(len(xy))])

        def boundary_xy(dr=0.0):
            s = state()
            r = s["R"] + dr
            return np.column_stack([r * np.cos(TH) + s["off"][0], r * np.sin(TH) + s["off"][1]])

        def edge_point(which):
            s = state()
            th = s["thmax"] if which == "hot" else s["thmin"]
            r = np.interp(th, TH, s["R"], period=2 * np.pi)
            return np.array([r * np.cos(th) + s["off"][0], r * np.sin(th) + s["off"][1]])

        # ------------------------------------------------ the heat image (one ImageMobject)
        img = ImageMobject(np.zeros((PX_H, PX_W, 4), dtype=np.uint8))
        img_state = {"key": None, "op": None}
        op_tr = ValueTracker(0.0)
        box_w, box_h = BOX[1] - BOX[0], BOX[3] - BOX[2]

        def upd_img(mob, dt=0):
            s = state()
            op = op_tr.get_value()
            if img_state["key"] != s["key"] or img_state["op"] != op:
                img_state["key"], img_state["op"] = s["key"], op
                s["lastkey"] = s["key"]
                idx = np.clip(((s["F"] + 1.0) * 127.5).astype(np.int32), 0, 255)
                arr = np.empty((PX_H, PX_W, 4), dtype=np.uint8)
                arr[..., :3] = LUT[idx]
                arr[..., 3] = (s["alpha"] * (255 * op)).astype(np.uint8)
                mob.pixel_array = arr
                mob.orig_alpha_pixel_array = arr[..., 3].copy()
            cx, cy, S = s["P"]
            mob.stretch_to_fit_width(box_w * S)
            mob.stretch_to_fit_height(box_h * S)
            mob.move_to([cx, cy, 0])

        # outline + insulation band
        outline = VMobject(stroke_color=WHITE_, stroke_width=2.6)
        band = VMobject(stroke_color=GREY_, stroke_width=11, stroke_opacity=0.32)

        def upd_outline(mob, dt=0):
            pts = to_scene(boundary_xy())
            mob.set_points_as_corners(np.vstack([pts, pts[:1]]))

        def upd_band(mob, dt=0):
            pts = to_scene(boundary_xy(0.045))
            mob.set_points_as_corners(np.vstack([pts, pts[:1]]))

        upd_img(img)
        upd_outline(outline)
        upd_band(band)
        img.add_updater(upd_img)
        outline.add_updater(upd_outline)
        band.add_updater(upd_band)

        # ============================================== 1. the plate {plate}
        self.add(img)
        self.play_until(t_ins - 0.1, Create(outline), op_tr.animate.set_value(1.0), rate_func=smooth)

        # insulated edge
        th_lab = 0.42
        Rr = np.interp(th_lab, TH, mR[0], period=2 * np.pi) + 0.05
        anchor = to_scene(np.array([Rr * np.cos(th_lab), Rr * np.sin(th_lab)]) + mOff[0])[0]
        ins_lab = VGroup(bold("insulated edge", 30), txt("no heat escapes", 24, GREY_)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        ins_lab.move_to([4.4, 1.75, 0])
        leader = Line(ins_lab.get_left() + LEFT * 0.15 + DOWN * 0.05, anchor + RIGHT * 0.08 + UP * 0.04,
                      stroke_color=GREY_, stroke_width=2)
        self.add(band)
        self.bring_to_front(outline)
        self.play_until(t_heat - 0.15, Create(band), FadeIn(ins_lab, shift=LEFT * 0.2), Create(leader), rate_func=smooth)

        # heat it unevenly ... and wait  (heat image is driven by the schedule)
        self.wait_until("mode")

        # ============================================== 2. settles into one pattern {mode}
        cb_n = 48
        cbar = VGroup(*[Rectangle(width=0.22, height=2.6 / cb_n, stroke_width=0,
                                  fill_color=lut_hex(-1 + 2 * (i + 0.5) / cb_n), fill_opacity=1)
                        for i in range(cb_n)]).arrange(UP, buff=0)
        cbar_frame = SurroundingRectangle(cbar, buff=0, stroke_color=GREY_, stroke_width=1.2, corner_radius=0)
        hot_l = bold("hot", 24, acc).next_to(cbar, UP, buff=0.14)
        cold_l = bold("cold", 24, BLUE_).next_to(cbar, DOWN, buff=0.14)
        cb = VGroup(cbar, cbar_frame, hot_l, cold_l).move_to([4.15, -0.15, 0])

        c_lab = txt("contrast", 22, GREY_)
        ref = txt("×000", 26, WHITE_, weight=SEMIBOLD)
        ref.next_to(c_lab, DOWN, buff=0.14, aligned_edge=LEFT)
        c_x = ref[0]
        pool = VGroup()
        for i in range(3):
            for d in range(10):
                pool.add(txt(str(d), 26, WHITE_, weight=SEMIBOLD).move_to(ref[i + 1]))
        contrast = VGroup(c_lab, c_x, pool)
        contrast.next_to(cbar_frame, RIGHT, buff=0.35)
        cstate = {"n": None}

        def upd_contrast(mob, dt=0):
            n = int(round(state()["contrast"]))
            if n != cstate["n"]:
                cstate["n"] = n
                digs = str(n)
                for i in range(3):
                    for d in range(10):
                        pool[10 * i + d].set_opacity(1.0 if i < len(digs) and int(digs[i]) == d else 0.0)

        upd_contrast(contrast)

        self.play(LaggedStart(AnimationGroup(FadeOut(ins_lab), FadeOut(leader)), FadeIn(cb, shift=LEFT * 0.2),
                              lag_ratio=0.6), run_time=max(0.4, min(1.0, t_mag0 - self.now - 0.5)))
        contrast.add_updater(upd_contrast)
        self.play(FadeIn(contrast), run_time=0.5)
        self.wait_until("question")

        # ============================================== 3. hottest & coldest {question}
        paths = {"hot": D["path_hot"], "cold": D["path_cold"]}
        walk = ValueTracker(0.0)

        def path_pt(which, s):
            P = paths[which]
            x = s * (len(P) - 1)
            i = min(int(x), len(P) - 2)
            w = x - i
            return (1 - w) * P[i] + w * P[i + 1]

        def dot_xy(which):
            s = walk.get_value()
            return path_pt(which, s) if s < 1 else edge_point(which)

        def make_spot(color):
            g = VGroup(*[Circle(radius=r, stroke_width=0, fill_color=color, fill_opacity=o)
                         for r, o in ((0.30, 0.10), (0.21, 0.16), (0.14, 0.25))])
            g.add(Dot(radius=0.085, color=WHITE_, stroke_color=color, stroke_width=3))
            return g

        spots = {"hot": make_spot(acc), "cold": make_spot(BLUE_)}

        def upd_spot(which):
            def f(mob, dt=0):
                mob.move_to(to_scene(dot_xy(which))[0])
            return f

        for k_, sp_ in spots.items():
            upd_spot(k_)(sp_)
            sp_.add_updater(upd_spot(k_))

        trails = {}
        for k_, col in (("hot", acc), ("cold", BLUE_)):
            tr = VMobject(stroke_color=col, stroke_width=3.5, stroke_opacity=0.9)

            def upd_tr(mob, dt=0, k_=k_):
                s = walk.get_value()
                P = paths[k_]
                n = max(2, int(s * (len(P) - 1)) + 1)
                pts = np.vstack([P[:n - 1], path_pt(k_, s)[None]]) if s < 1 else P
                mob.set_points_as_corners(to_scene(pts))
            upd_tr(tr)
            tr.add_updater(upd_tr)
            trails[k_] = tr

        start_dot = Dot(to_scene(paths["hot"][0])[0], radius=0.07, color=WHITE_)
        self.add(trails["hot"], trails["cold"])
        self.play(FadeIn(start_dot, scale=0.5), FadeIn(spots["hot"]), FadeIn(spots["cold"]), run_time=0.35)
        self.play_until(t_walk1, walk.animate.set_value(1.0), rate_func=smooth)

        def spot_label(which, s, color):
            lab = bold(s, 28, color)

            def f(mob, dt=0):
                p = to_scene(dot_xy(which))[0]
                cx, cy, S = state()["P"]
                d = p - np.array([cx, cy, 0])
                d = d / (np.linalg.norm(d) + 1e-9)
                mob.move_to(p + d * (0.42 + 0.5 * mob.width * abs(d[0]) + 0.5 * mob.height * abs(d[1])))
            f(lab)
            lab.add_updater(f)
            return lab

        lab_hot = spot_label("hot", "hottest", acc)
        lab_cold = spot_label("cold", "coldest", BLUE_)
        self.play(FadeIn(lab_hot, scale=0.8), FadeIn(lab_cold, scale=0.8),
                  Flash(spots["hot"].get_center(), color=acc, line_length=0.18, flash_radius=0.38),
                  Flash(spots["cold"].get_center(), color=BLUE_, line_length=0.18, flash_radius=0.38),
                  FadeOut(start_dot), run_time=0.7)
        self.wait_until("rauch")

        # ============================================== 4. Rauch, 1974 {rauch}
        rauch = VGroup(serif("Jeffrey Rauch, 1974", 44), )
        q_line = VGroup(txt("always on the", 32), txt("boundary", 32, YELLOW_, weight=SEMIBOLD),
                        txt("?", 32)).arrange(RIGHT, buff=0.14)
        q_line[2].shift(LEFT * 0.08)
        head = VGroup(rauch, q_line).arrange(DOWN, buff=0.22).move_to([-0.9, 2.85, 0])
        self.play(FadeIn(rauch, shift=DOWN * 0.15), FadeOut(contrast), FadeOut(cb), run_time=0.8)
        t_bnd = fr("rauch", "L1_end", 0.45)
        self.wait_until(t_bnd)
        hl = outline.copy().clear_updaters().set_stroke(YELLOW_, width=5.5)
        hl_glow = outline.copy().clear_updaters().set_stroke(YELLOW_, width=16, opacity=0.18)
        self.play(FadeIn(q_line, shift=UP * 0.1), Create(hl), Create(hl_glow), run_time=1.4)
        self.play_until(max(self.now + 0.6, c("L1_end") - 0.1),
                        Indicate(lab_hot, color=YELLOW_, scale_factor=1.12),
                        Indicate(lab_cold, color=YELLOW_, scale_factor=1.12),
                        hl_glow.animate.set_stroke(opacity=0.32))
        self.wait_until("holes")

        # ============================================== 5. counterexample with holes {holes}
        self.play(FadeOut(head), FadeOut(lab_hot), FadeOut(lab_cold), FadeOut(trails["hot"]),
                  FadeOut(trails["cold"]), FadeOut(hl), FadeOut(hl_glow), run_time=0.4)
        # schematic holed domain (right)
        hc = np.array([3.35, -0.35, 0])
        thh = np.linspace(0, 2 * np.pi, 240, endpoint=False)
        rr = 1.0 + 0.10 * np.cos(2 * thh) + 0.05 * np.cos(3 * thh + 0.6)
        outer_pts = np.column_stack([2.1 * rr * np.cos(thh), 1.7 * rr * np.sin(thh), 0 * thh]) + hc
        outer = VMobject().set_points_smoothly(np.vstack([outer_pts, outer_pts[:1]]))
        hole1 = Ellipse(width=0.95, height=0.78).move_to(hc + np.array([-0.95, 0.05, 0]))
        hole2 = Ellipse(width=0.85, height=0.72).move_to(hc + np.array([0.95, -0.05, 0]))
        holed = Cutout(outer, hole1, hole2, fill_color=PLATE, fill_opacity=1, stroke_color=WHITE_, stroke_width=2.6)
        holed_band = VGroup(outer.copy(), hole1.copy(), hole2.copy()).set_fill(opacity=0).set_stroke(GREY_, 11, 0.32)
        hot_in = make_spot(acc).move_to(hc + np.array([0.0, 0.0, 0]))
        glow_in = VGroup(*[Circle(radius=r, stroke_width=0, fill_color=acc, fill_opacity=0.075)
                           for r in np.linspace(0.16, 0.7, 7)]).move_to(hot_in)
        in_lab = bold("hot spot inside", 24, acc).next_to(hc, DOWN, buff=0.42)

        hdr_l = bold("no holes", 30, WHITE_).move_to([P2[0], 2.35, 0])
        hdr_r = bold("with holes", 30, WHITE_).move_to([hc[0], 2.35, 0])
        bw_lab = txt("Burdzy & Werner, 1999", 30, WHITE_)
        cx_chip = chip("COUNTEREXAMPLE", RED_, size=20)
        bw = VGroup(bw_lab, cx_chip).arrange(DOWN, buff=0.18).next_to(outer, DOWN, buff=0.35)
        schem = txt("(schematic)", 22, GREY_).next_to(hdr_r, DOWN, buff=0.12)

        self.play_until(t_holes + 1.3, FadeIn(hdr_l), FadeIn(hdr_r),
                        Create(holed_band), DrawBorderThenFill(holed), rate_func=smooth)
        self.play_until(fr("holes", "sc", 0.55), FadeIn(glow_in, scale=0.3), FadeIn(hot_in, scale=0.3),
                        FadeIn(in_lab, shift=UP * 0.1), FadeIn(schem), FadeIn(bw_lab, shift=UP * 0.15))
        self.play_until(fr("holes", "sc", 0.80), FadeIn(cx_chip, scale=1.2))
        self.play_until("sc", Flash(hot_in.get_center(), color=acc, line_length=0.2, flash_radius=0.5),
                        glow_in.animate.scale(1.12))

        # ============================================== 6. no holes: open {sc}
        open_chip = chip("STILL OPEN", YELLOW_, size=20)
        open_chip.move_to([P2[0], bw.get_center()[1], 0])
        right = VGroup(holed_band, holed, glow_in, hot_in, in_lab, hdr_r, bw, schem)
        self.play(right.animate.fade(0.6), Circumscribe(hdr_l, color=YELLOW_, fade_out=True, buff=0.12), run_time=1.1)
        self.wait_until(max(self.now, fr("sc", "L2_end", 0.5)))   # "...the question stayed open"
        self.play(FadeIn(open_chip, scale=1.3), run_time=0.5)
        self.play_until(max(self.now + 0.4, c("L2_end")), Indicate(open_chip, color=YELLOW_, scale_factor=1.12))
        self.wait_until("claim")

        # ============================================== 7. the paper {claim}
        card = paper_card("369", width=3.2)
        card.move_to([2.3, 0.5, 0])
        tag = paper_tag("369", color=acc)
        every = txt("any smooth shape without holes", 26, GREY_)
        every.move_to([0, P4[1] - 1.9, 0]).align_to(np.array([-6.3, 0, 0]), LEFT)
        self.play_until(t_claim + 1.0, LaggedStart(
            AnimationGroup(FadeOut(right, shift=RIGHT * 0.5), FadeOut(hdr_l), FadeOut(open_chip)),
            AnimationGroup(FadeIn(card, shift=LEFT * 1.0), FadeIn(tag, shift=UP * 0.15)), lag_ratio=0.5))
        # every smooth simply connected shape: the extremes ride the edge as the shape morphs
        self.play_until(t_m0 + 0.6, FadeIn(every, shift=UP * 0.1))
        banner = result_banner("Smooth simply connected planar domains:\nhot & cold spots lie on the boundary",
                               lean=CATALOG["369"]["lean"], size=28)
        banner.move_to([6.55 - banner.width / 2, 0.85, 0])
        crit = VGroup(tex(r"\nabla u \neq 0", 36, WHITE_), txt("inside: no interior critical point", 26, GREY_)).arrange(RIGHT, buff=0.25)
        crit.next_to(banner, DOWN, buff=0.4).align_to(banner, LEFT).shift(RIGHT * 0.35)
        self.wait_until(t_ban)
        # the paper folds into its source tag; the claim takes its place
        self.play(LaggedStart(AnimationGroup(FadeOut(card, target_position=tag.get_center() + RIGHT * 0.6, scale=0.12),
                                             FadeOut(every)),
                              FadeIn(banner, shift=LEFT * 0.3), lag_ratio=0.45), run_time=1.0)
        self.wait_until(max(t_edge, self.now))
        self.play(Flash(spots["hot"].get_center(), color=acc, line_length=0.2, flash_radius=0.42),
                  Flash(spots["cold"].get_center(), color=BLUE_, line_length=0.2, flash_radius=0.42),
                  FadeIn(crit, shift=UP * 0.1), run_time=0.9)
        self.finish()
