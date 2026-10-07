"""Narration-synchronised scene base class.

Each scene has a narration file built by tools/build_audio.py:
    build/timing/<scene_id>.json = {
        "duration": total seconds,
        "cues": {"name": seconds, ...},      # inline {cue} markers + L0, L0_end, ...
        "lines": [{"text", "start", "end"}, ...]
    }
Animations are scheduled against those absolute times:

    self.play_until("zeros", Create(line))   # finish exactly when the cue is spoken
    self.wait_until("L2")                     # idle until line 2 starts
    self.finish()                             # fade out, end exactly at narration end

The rendered video is silent; audio is laid in during assembly using the
same timing file, so sync is exact up to frame rounding.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from manim import *  # noqa: F401,F403

from .style import ASSETS, BG, BUILD

config.background_color = BG
# Many renders share one media dir: never let one render's LaTeX cleanup delete
# another's in-flight .dvi files (manim deletes all non-svg files in tex_dir).
config.no_latex_cleanup = True


class VoiceScene(Scene):
    SCENE_ID: str | None = None   # defaults to the module file name
    BACKGROUND = True

    # ------------------------------------------------------------ setup
    def setup(self):
        sid = self.SCENE_ID or Path(sys.modules[self.__class__.__module__].__file__).stem
        self.scene_id = sid
        # per-scene LaTeX cache dir avoids cross-render races on identical tex hashes
        try:
            base = Path(config.media_dir) / "Tex"
            config.tex_dir = str(base / sid)
            Path(config.tex_dir).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        path = BUILD / "timing" / f"{sid}.json"
        if path.exists():
            self.timing = json.loads(path.read_text())
        else:  # allow drafting before audio exists
            print(f"[VoiceScene] WARNING: no timing file for {sid}; using dummy 20s timing")
            self.timing = {"duration": 20.0, "cues": {}, "lines": []}
        self.narr_end = float(self.timing["duration"])
        if self.BACKGROUND:
            # Bake the gradient plate into the camera background: zero per-frame cost.
            w, h = self.camera.pixel_width, self.camera.pixel_height
            plate = BUILD / "cache" / f"bg_{w}x{h}.png"
            if not plate.exists():
                from PIL import Image
                plate.parent.mkdir(parents=True, exist_ok=True)
                Image.open(ASSETS / "bg.png").convert("RGBA").resize((w, h), Image.LANCZOS).save(plate)
            self.camera.background_image = str(plate)
            self.camera.init_background()
            self.camera.reset()

    # ------------------------------------------------------------ timing
    @property
    def now(self) -> float:
        return self.renderer.time

    def cue(self, name) -> float:
        """Absolute time (s) of a cue. Accepts a number, a cue name, or
        'name+0.5' / 'name-0.3' offsets."""
        if isinstance(name, (int, float)):
            return float(name)
        off = 0.0
        for sign in ("+", "-"):
            if sign in name[1:]:
                base, _, num = name.rpartition(sign)
                if base in self.timing["cues"] or base in ("end",):
                    off = float(num) * (1 if sign == "+" else -1)
                    name = base
                    break
        if name == "end":
            return self.narr_end + off
        if name not in self.timing["cues"]:
            raise KeyError(f"cue '{name}' not in {sorted(self.timing['cues'])}")
        return self.timing["cues"][name] + off

    def has_cue(self, name) -> bool:
        return name in self.timing["cues"]

    def wait_until(self, t, **kw):
        dt = self.cue(t) - self.now
        if dt > 0.5 / config.frame_rate:   # sub-frame waits would round up a whole frame
            self.wait(dt, **kw)

    def play_until(self, t, *anims, min_time=0.2, **kw):
        """Play `anims` so they END at time t (start now)."""
        rt = self.cue(t) - self.now
        if rt < min_time:
            print(f"[VoiceScene] {self.scene_id}: play_until({t}) only {rt:.2f}s left; using {min_time}s")
            rt = min_time
        self.play(*anims, run_time=rt, **kw)

    def play_at(self, t, *anims, run_time=1.0, **kw):
        """Wait until time t, then play anims for run_time seconds."""
        self.wait_until(t)
        self.play(*anims, run_time=run_time, **kw)

    def play_between(self, t0, t1, *anims, **kw):
        """Start at t0, end at t1."""
        self.wait_until(t0)
        self.play_until(t1, *anims, **kw)

    def finish(self, fade=0.5):
        """Fade everything (except the background) out, ending exactly at the
        narration end, so consecutive scenes cut seamlessly."""
        end = self.narr_end
        start = max(self.now, end - fade)
        self.wait_until(start)
        mobs = list(self.mobjects)
        if mobs and end - self.now > 1e-3:
            self.play(*[FadeOut(m) for m in mobs], run_time=end - self.now)
        else:
            self.wait_until(end)
