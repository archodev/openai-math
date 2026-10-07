"""Chapter title card: 'PART n OF 9', serif title, family counts, and a slow
drifting wall of that field's paper first pages in the background."""
from __future__ import annotations

from manim import *  # noqa: F401,F403

from .components import *  # noqa: F401,F403
from .style import *  # noqa: F401,F403
from .voice import VoiceScene


class ChapterScene(VoiceScene):
    KEY = "nt"
    DRIFT = 0.35  # scene units per second

    def construct(self):
        idx = [k for k, *_ in CHAPTERS].index(self.KEY)
        _, title, _, color = CHAPTERS[idx]
        entries = chapter_entries(self.KEY)
        n, nlean = len(entries), sum(e["lean"] for e in entries)

        rows = []
        for r, y in enumerate((2.45, -2.45)):
            picks = [e["num"] for e in entries[r::2][:7]]
            row = ImageMobject(str(paper_strip(picks, f"{self.KEY}_{r}", height_px=380)))
            row.height = 2.7
            row.move_to(UP * y + RIGHT * (1.0 if r else -1.0))
            row.set_opacity(0.0)
            sgn = -1 if r == 0 else 1
            row.add_updater(lambda m, dt, sgn=sgn: m.shift(RIGHT * sgn * self.DRIFT * dt))
            rows.append(row)

        part = Text(f"PART {idx + 1} OF {len(CHAPTERS)}", font=SANS, font_size=20,
                    color=color, weight=BOLD)
        head = Text(title, font=SERIF, font_size=66 if len(title) < 30 else 50,
                    color=WHITE_, weight=BOLD)
        if head.width > 12.5:
            head.scale_to_fit_width(12.5)
        line = Line(LEFT, RIGHT, color=color, stroke_width=3).set_width(min(head.width * 0.6, 6))
        sub = Text(f"{n} result families  ·  {nlean} with Lean formalizations",
                   font=SANS, font_size=24, color=GREY_)
        block = VGroup(part, head, line, sub).arrange(DOWN, buff=0.28)
        shade = Rectangle(width=config.frame_width + 1, height=block.height + 1.1, stroke_width=0,
                          fill_color=BG, fill_opacity=0.8).move_to(block)

        D = self.narr_end
        write_t = min(1.1, max(0.5, D * 0.3))
        self.add(*rows)
        self.play(*[r.animate.set_opacity(0.13) for r in rows], FadeIn(shade),
                  FadeIn(part, shift=DOWN * 0.15), run_time=0.5)
        self.play(Write(head), GrowFromCenter(line), run_time=write_t)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.45)
        self.finish(fade=0.55)
