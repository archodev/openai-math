"""Rapid-fire grid scene template.

Subclass GridScene and set CHAPTER and TILES. Each tile dict:
    num      : catalog family number, e.g. "005"
    name     : short display name
    verdict  : key of components.VERDICTS ("proved", "counterexample", ...)
    icon     : zero-arg callable returning a VMobject (auto-fitted into the tile)
    feature  : optional dict for a 'zoom-in' one-liner:
                 caption : one plain sentence shown on the big card
                 big     : optional zero-arg callable returning a larger VMobject
                           (defaults to a fresh icon())
                 animate : optional callable(scene, big_mob, run_time) that plays
                           animations on big_mob lasting ~run_time seconds total

Narration cues (written into the script as {t005}, {f005}, {f005_end}):
    t<num>       : tile is named -> it lights up
    f<num>       : featured tile expands to a big card
    f<num>_end   : big card collapses back
"""
from __future__ import annotations

import textwrap

from manim import *  # noqa: F401,F403

from .components import *  # noqa: F401,F403
from .style import *  # noqa: F401,F403
from .voice import VoiceScene


class GridScene(VoiceScene):
    CHAPTER = "nt"
    HEADER = "Rapid fire"
    TILES: list = []
    COLS, ROWS = 4, 3
    MORE_TEXT = True

    def build_tiles(self):
        color = CHAPTER_COLOR[self.CHAPTER]
        pos, w, h = grid_layout(len(self.TILES), self.COLS, self.ROWS)
        tiles = []
        for d, p in zip(self.TILES, pos):
            icon = d["icon"]() if d.get("icon") else None
            t = Tile(d["num"], d["name"], d["verdict"], icon=icon, color=color, w=w, h=h)
            t.move_to(p)
            t.spec = d
            tiles.append(t)
        return tiles

    def header(self):
        color = CHAPTER_COLOR[self.CHAPTER]
        title = next(t for k, t, _, _ in CHAPTERS if k == self.CHAPTER)
        a = Text(self.HEADER.upper(), font=SANS, font_size=18, color=color, weight=BOLD)
        dot = Dot(radius=0.035, color=GREY_)
        b = Text(title, font=SANS, font_size=18, color=GREY_, weight=SEMIBOLD)
        g = VGroup(a, dot, b).arrange(RIGHT, buff=0.18)
        g.to_corner(UL, buff=0.32).shift(DOWN * 0.02)
        return g

    def construct(self):
        color = CHAPTER_COLOR[self.CHAPTER]
        tiles = self.build_tiles()
        self.tiles = tiles
        head = self.header()
        n_total = len(chapter_entries(self.CHAPTER))
        counter = Text(f"{len(tiles)} of {n_total} families shown", font=SANS, font_size=16,
                       color=GREY_).to_corner(UR, buff=0.34)
        first = min([self._cue_time(t) for t in tiles if self._cue_time(t) is not None] + [self.narr_end])
        intro_time = max(0.6, min(1.6, first - 0.15))
        self.play(FadeIn(head, shift=RIGHT * 0.2), FadeIn(counter),
                  LaggedStart(*[FadeIn(t, shift=UP * 0.25, scale=0.94) for t in tiles],
                              lag_ratio=0.05), run_time=intro_time)
        events = sorted([t for t in tiles if self._cue_time(t) is not None], key=self._cue_time)
        # slow push-in so the frame is never static during long name lists
        grid = VGroup(*tiles)
        grid_center = grid.get_center()
        rate = 0.035 / max(self.narr_end, 1.0)          # total ~3.5% growth over the scene
        grid.add_updater(lambda m, dt: m.scale(1 + rate * dt, about_point=grid_center))
        # the tiles were added individually by the intro; re-parent them under `grid`
        # (an updater only runs on a mobject that is in the scene)
        self.remove(*tiles)
        self.add(grid)
        current = None
        for t in events:
            if t.spec.get("feature") and self.has_cue(f"f{t.num}"):
                if current is not None:
                    self.play(*current.visited(), run_time=0.2)
                    current = None
                self.feature(t, color)
            else:
                self.wait_until(max(self.now, self._cue_time(t) - 0.12))
                anims = t.lit() + [Indicate(t.label, color=color, scale_factor=1.06)]
                if len(t.icon) or t.icon.points.size:
                    anims.append(t.icon.animate(rate_func=there_and_back).scale(1.06))
                if current is not None:
                    anims += current.visited()
                self.play(*anims, run_time=0.35)
                current = t
        if current is not None:
            self.play(*current.visited(), run_time=0.25)
        rest = n_total - len(tiles)
        if self.MORE_TEXT and rest > 0 and self.narr_end - self.now > 1.2:
            more = Text(f"+ {rest} more families in this field", font=SANS, font_size=18,
                        color=color, weight=SEMIBOLD).move_to(counter, aligned_edge=RIGHT)
            self.play(FadeOut(counter, shift=UP * 0.2), FadeIn(more, shift=UP * 0.2), run_time=0.5)
        grid.clear_updaters()
        self.finish()

    def _cue_time(self, t):
        for key in (f"f{t.num}", f"t{t.num}"):
            if self.has_cue(key):
                return self.cue(key)
        return None

    # ---------------------------------------------------------------- feature
    def big_card(self, t, color):
        spec = t.spec
        f = spec["feature"]
        W, H = 12.2, 5.6
        box = RoundedRectangle(width=W, height=H, corner_radius=0.22, stroke_color=color,
                               stroke_width=2.4, fill_color=CARD, fill_opacity=1.0)
        if f.get("big"):
            vis = f["big"]()
        elif spec.get("icon"):
            vis = spec["icon"]()
        else:
            vis = paper_card(t.num, width=2.6)
        if vis.width > 0 and vis.height > 0:
            s = min(5.2 / vis.width, 4.4 / vis.height)
            vis.scale(s)
        vis.move_to(box.get_left() + RIGHT * 3.0)
        title = Text("\n".join(textwrap.wrap(spec["name"], 24)), font=SANS, font_size=36,
                     color=WHITE_, weight=BOLD, line_spacing=0.8)
        cap = Text("\n".join(textwrap.wrap(f["caption"], 34)), font=SANS, font_size=25,
                   color=GREY_, line_spacing=0.9)
        chips = VGroup(verdict_chip(spec["verdict"], size=15))
        if CATALOG.get(t.num, {}).get("lean"):
            chips.add(lean_badge(15))
        chips.arrange(RIGHT, buff=0.15)
        fam = Text(f"Family {t.num}", font=SANS, font_size=15, color=GREY_, weight=SEMIBOLD)
        right = VGroup(fam, title, cap, chips).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        if right.width > 5.6:
            right.scale_to_fit_width(5.6)
        right.move_to(box.get_right() + LEFT * 3.15)
        return VGroup(box, vis, right), vis

    def feature(self, t, color):
        start, end = self.cue(f"f{t.num}"), self.cue(f"f{t.num}_end")
        self.wait_until(max(self.now, start - 0.15))
        card, vis = self.big_card(t, color)
        dim = Rectangle(width=config.frame_width + 1, height=config.frame_height + 1,
                        stroke_width=0, fill_color=BG, fill_opacity=0.86)
        dim.set_z_index(50)
        card.set_z_index(60)
        card.save_state()
        card.scale(t.frame.width / card[0].width).move_to(t)
        card.set_opacity(0)
        self.play(*t.lit(), FadeIn(dim), Restore(card), run_time=0.55)
        anim = t.spec["feature"].get("animate")
        avail = end - self.now - 0.15
        if anim and avail > 0.6:
            anim(self, vis, avail)
        # hold the card until the line's last word has landed, then collapse during the pause
        self.wait_until(max(self.now, end - 0.08))
        self.play(card.animate.scale(t.frame.width / card[0].width).move_to(t).set_opacity(0),
                  FadeOut(dim), *t.visited(), run_time=0.4)
        self.remove(card)
