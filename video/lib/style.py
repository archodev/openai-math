"""Shared visual language for the video.

Everything that should look the same across scenes lives here: colours,
fonts, text helpers. Scenes import with `from lib.style import *`.
"""
from __future__ import annotations

import json
from pathlib import Path

from manim import *  # noqa: F401,F403

VIDEO = Path(__file__).resolve().parents[1]          # .../video
REPO = VIDEO.parent                                  # .../openai-math
ASSETS = VIDEO / "assets"
BUILD = VIDEO / "build"

# ---------------------------------------------------------------- palette
BG = "#0D1117"
WHITE_ = "#ECEFF4"      # main text
GREY_ = "#8B93A1"       # secondary text
DIM = "#4A5363"         # tertiary / grid lines
CARD = "#141A23"        # tile fill
CARD_HI = "#1C2430"     # highlighted tile fill

BLUE_ = "#58C4DD"
TEAL_ = "#5CD0B3"
GREEN_ = "#83C167"
YELLOW_ = "#F7D96F"
GOLD_ = "#F0AC5F"
ORANGE_ = "#FF9E64"
RED_ = "#FC6255"
PINK_ = "#E07AB5"
PURPLE_ = "#A67FD8"
SKY_ = "#7FA7FF"

# ---------------------------------------------------------------- fonts
SERIF = "CMU Serif"      # headings, 3b1b feel
SANS = "Inter"           # labels, UI
DISPLAY = "Inter Display"
MONO = "JetBrains Mono"

# ---------------------------------------------------------------- chapters
CHAPTERS = [
    # key, title, subjects in catalog, accent colour
    ("nt", "Number Theory", ["Number theory"], BLUE_),
    ("ag", "Algebraic & Complex Geometry", ["Algebraic and complex geometry"], PURPLE_),
    ("an", "Analysis & Convex Geometry", ["Real and complex analysis", "Convex and metric geometry"], TEAL_),
    ("cs", "Theoretical Computer Science", ["Theoretical computer science"], GREEN_),
    ("co", "Combinatorics", ["Combinatorics"], GOLD_),
    ("al", "Algebra, Groups & Logic", ["Algebra", "Group theory", "Mathematical logic"], PINK_),
    ("dp", "Dynamics, Probability & Physics", ["Dynamical systems and ergodic theory", "Probability and statistical mechanics", "Mathematical physics"], YELLOW_),
    ("oa", "Operator Algebras, Topology & Functional Analysis", ["Operator algebras", "Topology", "Functional analysis"], SKY_),
    ("gp", "Geometry & PDE", ["Differential geometry", "Partial differential equations"], ORANGE_),
]
CHAPTER_COLOR = {k: c for k, _, _, c in CHAPTERS}


def load_catalog():
    return json.loads((VIDEO / "data" / "catalog.json").read_text())


CATALOG = {e["num"]: e for e in load_catalog()}


def chapter_entries(key):
    subjects = next(s for k, _, s, _ in CHAPTERS if k == key)
    return [e for e in CATALOG.values() if e["subject"] in subjects]


# ---------------------------------------------------------------- text helpers
def txt(s, size=28, color=WHITE_, font=SANS, weight=NORMAL, **kw) -> Text:
    """Sans-serif label. `size` is a font_size (48 = Manim default)."""
    return Text(s, font=font, font_size=size, color=color, weight=weight, **kw)


def bold(s, size=28, color=WHITE_, **kw) -> Text:
    return txt(s, size=size, color=color, weight=SEMIBOLD, **kw)


def serif(s, size=48, color=WHITE_, weight=BOLD, **kw) -> Text:
    """Serif heading in the 3b1b spirit."""
    return Text(s, font=SERIF, font_size=size, color=color, weight=weight, **kw)


def mono(s, size=20, color=GREY_, **kw) -> Text:
    return Text(s, font=MONO, font_size=size, color=color, **kw)


def tex(s, size=40, color=WHITE_, **kw) -> MathTex:
    return MathTex(s, font_size=size, color=color, **kw)


def textex(s, size=36, color=WHITE_, **kw) -> Tex:
    return Tex(s, font_size=size, color=color, **kw)


def caps(s, size=20, color=GREY_, spacing=0.12):
    """Letter-spaced small caps style label (e.g. 'PART 3 OF 9')."""
    t = Text(s.upper(), font=SANS, font_size=size, color=color, weight=SEMIBOLD)
    # Pango letter spacing via manual spacing of sub-mobjects
    if len(t) > 1:
        for i, ch in enumerate(t):
            ch.shift(RIGHT * spacing * i * size / 20)
        t.move_to(ORIGIN)
    return t


def glow(mob: VMobject, color=None, layers=6, width=18, opacity=0.06):
    """Soft glow behind a VMobject: stacked wide translucent strokes."""
    color = color or mob.get_stroke_color()
    g = VGroup()
    for i in range(layers):
        c = mob.copy().set_fill(opacity=0)
        c.set_stroke(color, width=width * (i + 1) / layers, opacity=opacity)
        g.add(c)
    return g


def underline(mob, color=None, buff=0.12, width=3):
    color = color or mob.get_color()
    return Line(mob.get_corner(DL) + DOWN * buff, mob.get_corner(DR) + DOWN * buff,
                color=color, stroke_width=width)
