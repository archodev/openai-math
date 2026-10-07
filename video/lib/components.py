"""Reusable visual components: badges, chips, paper cards, result banners,
rapid-fire grid tiles."""
from __future__ import annotations

import textwrap

from manim import *  # noqa: F401,F403

from .style import *  # noqa: F401,F403

# ---------------------------------------------------------------- chips
VERDICTS = {
    "proved": ("PROVED", GREEN_),
    "resolved": ("RESOLVED", GREEN_),
    "disproved": ("DISPROVED", RED_),
    "counterexample": ("COUNTEREXAMPLE", RED_),
    "bound": ("NEW BOUND", BLUE_),
    "algorithm": ("ALGORITHM", TEAL_),
    "hardness": ("HARDNESS", ORANGE_),
    "construction": ("CONSTRUCTION", GOLD_),
    "classified": ("CLASSIFIED", GOLD_),
    "independent": ("INDEPENDENT", PURPLE_),
    "exact": ("EXACT VALUE", YELLOW_),
}


def chip(label, color, size=14, pad_x=0.12, pad_y=0.07, fill_opacity=0.14):
    t = Text(label, font=SANS, font_size=size, color=color, weight=BOLD)
    box = RoundedRectangle(
        width=t.width + 2 * pad_x, height=t.height + 2 * pad_y,
        corner_radius=min(0.08, (t.height + 2 * pad_y) / 2),
        stroke_color=color, stroke_width=1.4, fill_color=color, fill_opacity=fill_opacity)
    t.move_to(box)
    return VGroup(box, t)


def verdict_chip(kind, size=14):
    label, color = VERDICTS[kind]
    return chip(label, color, size=size)


def check_mark(color=TEAL_, size=0.18, width=3):
    return VMobject(stroke_color=color, stroke_width=width).set_points_as_corners(
        [LEFT * 0.5 + UP * 0.05, DOWN * 0.38 + LEFT * 0.12, RIGHT * 0.55 + UP * 0.48]
    ).scale(size / 0.9)


def lean_badge(size=14):
    """Small badge meaning 'a Lean formalization accompanies this result'."""
    t = Text("LEAN", font=SANS, font_size=size, color=TEAL_, weight=BOLD)
    ck = check_mark(TEAL_, size=t.height * 1.15, width=2.2 * size / 14)
    row = VGroup(t, ck).arrange(RIGHT, buff=0.06 * size / 14)
    box = RoundedRectangle(width=row.width + 0.24 * size / 14, height=row.height + 0.16 * size / 14,
                           corner_radius=0.07 * size / 14, stroke_color=TEAL_, stroke_width=1.4,
                           fill_color=TEAL_, fill_opacity=0.14)
    row.move_to(box)
    return VGroup(box, row)


# ---------------------------------------------------------------- papers
def thumb_path(num, hires=False):
    p = ASSETS / ("hires" if hires else "thumbs") / f"{num}.png"
    if hires and not p.exists():
        p = ASSETS / "thumbs" / f"{num}.png"
    return str(p)


def paper_strip(nums, key, height_px=420, gap_px=50):
    """Pre-composite several first pages side by side into one PNG (cheap to
    animate: one image instead of many)."""
    from PIL import Image
    out = BUILD / "cache" / f"strip_{key}.png"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    ims = [Image.open(thumb_path(n, False)).convert("RGBA") for n in nums]
    ims = [im.resize((int(im.width * height_px / im.height), height_px), Image.LANCZOS) for im in ims]
    W = sum(im.width for im in ims) + gap_px * (len(ims) - 1)
    canvas = Image.new("RGBA", (W, height_px), (0, 0, 0, 0))
    x = 0
    for im in ims:
        canvas.paste(im, (x, 0))
        x += im.width + gap_px
    canvas.save(out)
    return out


def paper_card(num, width=3.0, hires=True, shadow=True, border_color=GREY_):
    """First page of the family's principal paper, as a floating card."""
    img = ImageMobject(thumb_path(num, hires))
    img.width = width
    border = Rectangle(width=img.width, height=img.height, stroke_color=border_color,
                       stroke_width=1.2, stroke_opacity=0.6).move_to(img)
    parts = []
    if shadow:
        for i in range(5):
            s = Rectangle(width=img.width + 0.04 * i, height=img.height + 0.04 * i,
                          stroke_width=0, fill_color=BLACK, fill_opacity=0.10)
            s.move_to(img).shift(DR * 0.05)
            parts.append(s)
    return Group(*parts, img, border)


def paper_tag(num, color=BLUE_, size=17):
    """Lower-left source tag shown during spotlights (Two-Minute-Papers style)."""
    e = CATALOG[num]
    title = e["papers"][0]["title"] if e["papers"] else e["title"]
    title = title.replace("$", "")
    if len(title) > 70:
        title = title[:67].rstrip() + "…"
    label = Text(f"Family {num}", font=SANS, font_size=size - 3, color=GREY_, weight=SEMIBOLD)
    t = Text(title, font=SANS, font_size=size, color=WHITE_, slant=ITALIC)
    row = VGroup(label, t).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
    if e.get("lean"):
        lb = lean_badge(12)
        lb.next_to(label, RIGHT, buff=0.15)
        row.add(lb)
    bar = Line(UP * 0.0, DOWN * row.height, color=color, stroke_width=3)
    bar.next_to(row, LEFT, buff=0.15)
    g = VGroup(bar, row)
    g.to_corner(DL, buff=0.35)
    return g


def set_tag_color(tag, color):
    tag[0].set_color(color)
    return tag


# ---------------------------------------------------------------- banners
def result_banner(statement, color=YELLOW_, label="CLAIMED RESULT", lean=False,
                  width=None, size=34, is_tex=False):
    """Boxed statement shown at the end of a spotlight.
    statement: plain text (Text) or LaTeX string if is_tex=True."""
    body = (MathTex(statement, font_size=size, color=WHITE_) if is_tex
            else Text(statement, font=SANS, font_size=size, color=WHITE_, weight=MEDIUM))
    head = Text(label, font=SANS, font_size=15, color=color, weight=BOLD)
    items = [head]
    if lean:
        items.append(lean_badge(13))
    header = VGroup(*items).arrange(RIGHT, buff=0.25)
    content = VGroup(header, body).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
    w = width or content.width + 0.7
    box = RoundedRectangle(width=w, height=content.height + 0.55, corner_radius=0.16,
                           stroke_color=color, stroke_width=2, fill_color=CARD, fill_opacity=0.92)
    content.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.35)
    return VGroup(box, content)


def wrap(s, width_chars):
    return "\n".join(textwrap.wrap(s, width_chars))


# ---------------------------------------------------------------- grid tiles
class Tile(VGroup):
    """A rapid-fire tile: icon on top, name, verdict chip (+ Lean badge)."""

    def __init__(self, num, name, verdict, icon=None, color=BLUE_, w=3.05, h=2.0,
                 name_size=17, lean=None):
        super().__init__()
        self.num, self.name, self.verdict, self.accent = num, name, verdict, color
        lean = CATALOG.get(num, {}).get("lean", False) if lean is None else lean
        self.frame = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                                      stroke_color=color, stroke_width=1.6, stroke_opacity=0.32,
                                      fill_color=CARD, fill_opacity=1.0)
        self.add(self.frame)
        pad = 0.13
        # bottom block: name (<=2 lines) above chips
        chips = VGroup(verdict_chip(verdict, size=10))
        if lean:
            chips.add(lean_badge(10))
        chips.arrange(RIGHT, buff=0.08)
        chips.next_to(self.frame.get_corner(DL), UR, buff=pad)
        lines = textwrap.wrap(name, 28)
        if len(lines) > 2:
            lines = textwrap.wrap(name, 34)[:2]
        nm = Text("\n".join(lines), font=SANS, font_size=name_size, color=WHITE_,
                  weight=SEMIBOLD, line_spacing=0.7)
        if nm.width > w - 2 * pad:
            nm.scale_to_fit_width(w - 2 * pad)
        nm.next_to(chips, UP, buff=0.09, aligned_edge=LEFT)
        self.label, self.chips = nm, chips
        # icon fills what is left above the name
        top = self.frame.get_top()[1] - pad
        bottom = nm.get_top()[1] + 0.08
        icon_h = max(0.3, top - bottom)
        icon_w = w - 2 * pad
        if icon is None:
            icon = VGroup()  # caller may add a thumbnail separately
        if icon.width > 0 and icon.height > 0:
            icon.scale(min(icon_w / icon.width, icon_h / icon.height))
        icon.move_to([self.frame.get_center()[0], (top + bottom) / 2, 0])
        self.icon = icon
        self.add(icon, nm, chips)

    # state helpers ------------------------------------------------------
    def lit(self):
        return [self.frame.animate.set_stroke(self.accent, width=3.0, opacity=1.0)
                .set_fill(CARD_HI, opacity=1.0)]

    def visited(self):
        return [self.frame.animate.set_stroke(self.accent, width=1.8, opacity=0.75)
                .set_fill(CARD, opacity=1.0)]


def grid_layout(n, cols=4, rows=3, top=2.95, bottom=-3.55, left=-6.6, right=6.6, gap=0.22):
    w = (right - left - (cols - 1) * gap) / cols
    h = (top - bottom - (rows - 1) * gap) / rows
    pos = []
    for i in range(n):
        r, c = divmod(i, cols)
        x = left + w / 2 + c * (w + gap)
        y = top - h / 2 - r * (h + gap)
        pos.append(np.array([x, y, 0]))
    return pos, w, h
