# Scene guide — "4,000 Problems" explainer

A ~15 minute YouTube explainer touring the AI-written math preprints in this repo.
Style: **3Blue1Brown visuals** (dark canvas, clean vector animation, LaTeX, one idea at
a time, things *move* to explain) with **Two Minute Papers pacing** (energetic,
paper first-pages shown on screen, quick cuts, "here's the paper" moments).
Narration is fixed (Kokoro TTS, `narration/script.py`); your job is the picture.

## Mechanics

* Manim Community 0.21, Cairo renderer, 1920x1080 @ 60 fps for the final render.
  Python: `/opt/venv/bin/python`, manim: `/opt/venv/bin/manim`.
* One file per scene: `video/scenes/<scene_id>.py`, exactly one Scene subclass,
  CamelCase of the id (e.g. `c1_qrh` → `class C1Qrh(VoiceScene)`). Start the file with
  ```python
  import sys; sys.path.insert(0, __file__.rsplit('/scenes/', 1)[0])
  from lib.voice import VoiceScene
  from lib.style import *        # colours, fonts, txt(), bold(), serif(), tex(), ...
  from lib.components import *   # paper_card, paper_tag, result_banner, lean_badge, chips, ...
  ```
* Read `video/lib/*.py` once — it is short. Use its helpers instead of inventing new styles.
* Timing: `video/build/timing/<scene_id>.json` lists `cues` (seconds from scene start)
  for every `{cue}` marker in the narration, plus `L0, L0_end, L1, ...` for line
  starts/ends, and `duration`. Schedule against cue *names*, never hard-coded seconds:
  * `self.play_until("claim", FadeIn(x))` — starts now, ends exactly at the cue.
  * `self.play_at("claim", FadeIn(x), run_time=0.8)` — waits for the cue, then plays.
  * `self.wait_until("L3")`, `self.cue("claim+0.5")` (offsets ok), `self.now`.
  * Finish every scene with `self.finish()` (fades everything out, ends exactly at
    the narration end, so scenes cut together seamlessly). Do not add the
    background yourself; VoiceScene bakes in a subtle gradient.
  * Narration may be re-synthesized later with small edits: cue NAMES are stable,
    times may shift by a second or two. Code must not assume fixed gaps between cues;
    derive run_times from cues (play_until / play_between) and avoid run_times
    that could exceed the gap to the next cue.
* The rendered video is silent; audio is laid in at assembly from the same timing.

## Look & feel rules

* Safe area: keep content inside x ∈ [-6.7, 6.7], y ∈ [-3.75, 3.75]. In spotlight
  scenes the lower-left corner (x < -1.5, y < -2.9) is reserved for `paper_tag`.
* Colour: each chapter has an accent (`CHAPTER_COLOR[key]`, see lib/style.py).
  YELLOW_ = emphasis / the claimed result; RED_ = failure / counterexample / bad;
  GREEN_ = good / proved; TEAL_ = Lean. Text WHITE_ (primary) / GREY_ (secondary).
* Type: `serif()` (CMU Serif) for big titles, `txt()/bold()` (Inter) for labels,
  `tex()` (LaTeX) for maths. Minimum on-screen text size: font_size 22 for labels,
  26-34 for captions, 44-72 for headings. Never put long sentences on screen —
  short labels and key formulas only; the voice carries the explanation.
* One idea at a time. When the narration moves on, transform or fade the old
  idea away. Never leave the frame static for more than ~3 s: add purposeful
  motion (a slow drift, a pulsing highlight, a flow continuing to move).
* 3b1b motion vocabulary: Create / Write for drawing, Transform/ReplacementTransform
  to show one thing becoming another, LaggedStart for groups, Indicate/Circumscribe
  for emphasis, smooth easing. Avoid gimmicky spins/bounces.
* Mathematical accuracy is mandatory: diagrams must be correct (true geometry, true
  zero heights, correct dates/numbers). Pull facts from `video/data/research.json`
  (entry for your family: history with sources, precise claim, pitfalls) and do not
  put anything on screen that the research notes flag as an overclaim.

## Spotlight scene recipe (Two-Minute-Papers beat)

1. Hook visual within the first 0.5 s, tied to the first words.
2. Build the intuition with the narration (this is the 3b1b part: animate the idea).
3. At the `{claim}` cue: show the paper — `paper_card(num, width≈3)` sliding in
   (it is the actual first page of the preprint), and put `paper_tag(num, color=accent)`
   in the lower-left from then until the end.
4. Close with `result_banner(...)` stating the claim in a few words / one formula
   (`lean=CATALOG[num]['lean']`), held for at least ~2 s, then `self.finish()`.

## Render cost (important: final render is 1080p60 on 4 CPUs)

* ImageMobjects are expensive per frame. At most ~2-3 moving images on screen at
  once; static images are fine. Pre-composite many images into one PNG if needed
  (`lib.components.paper_strip`). Cache generated images under `video/build/cache/`.
* Avoid always_redraw on large groups; keep total submobjects modest (< ~2-3k).
  Heavy numerics (eigenfunctions, streamlines) → compute once with numpy; bake
  heat-maps into a PNG.
* A typical scene should render at 1080p60 in a few minutes at most.

## Preview & self-review loop (do this at least twice)

Use the shared helpers (they limit how many renders run at once on this 4-CPU box —
do NOT call manim directly for previews):
```
/home/user/openai-math/video/tools/preview.sh <scene_id>          # 480p15 preview, prints OUTPUT: <mp4>
/home/user/openai-math/video/tools/preview.sh <scene_id> m 30      # 720p30 if you need to judge small text
/home/user/openai-math/video/tools/stills.sh <scene_id> claim zeta+0.5 end 12.3   # PNG stills at cues/seconds
```
Then LOOK at the stills with the Read tool. Check: overlaps, clipping off-screen,
legibility, alignment, empty/static stretches, sync with the cue words, correctness
of the maths, consistency with the style rules. Fix and re-render. Errors and
VoiceScene timing warnings (e.g. "play_until(...) only 0.05s left") are printed by
preview.sh — fix those too (they mean an animation was squeezed).
