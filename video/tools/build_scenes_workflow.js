export const meta = {
  name: 'math-video-scenes',
  description: 'Build every animated scene of the explainer (Manim), then an independent critic reviews stills and polishes each',
  phases: [
    { title: 'Build', detail: 'one builder per scene: implement, preview, self-review' },
    { title: 'Polish', detail: 'fresh critic per scene: inspect stills at every cue, fix issues' },
  ],
}

const V = '/home/user/openai-math/video'
const SCENES = args.scenes   // [{id, cls, kind: 'spot'|'grid'|'intro', fam, accent}]

const COMMON = `Project: a ~15 min YouTube explainer ("4,000 Problems") touring AI-written math preprints in /home/user/openai-math. 3Blue1Brown visual style, Two Minute Papers pacing. Narration audio is fixed and already synthesized; you create the animation for ONE scene in Manim (Community 0.21, Cairo).

MANDATORY first reads: ${V}/SCENE_GUIDE.md (rules, helpers, preview loop), then ${V}/lib/style.py, lib/components.py, lib/voice.py${''} (short). Timing for your scene: ${V}/build/timing/<id>.json (line texts, cue names -> seconds, duration).
Constraints: edit ONLY your scene file ${V}/scenes/<id>.py (plus cached assets you generate under ${V}/build/cache/<id>/). Do not edit lib/, narration/, other scenes, or timing files. Never call manim directly; use tools/preview.sh and tools/stills.sh. Previews are throttled to 4 concurrent renders, so be patient and make each render count.`

function buildPrompt(s) {
  const common = COMMON.replaceAll('<id>', s.id)
  if (s.kind === 'grid') {
    return `${common}

Your scene: ${s.id} — a RAPID-FIRE GRID. Class name: ${s.cls}. It must subclass GridScene from ${V}/lib/grid.py (read it): set CHAPTER='${s.chapter}', TILES=[...]${s.cols ? `, COLS=${s.cols}, ROWS=3` : ''}. The tile list (num, name, verdict, caption-for-featured) is in ${V}/data/grids.json["${s.id}"]; use those names/verdicts verbatim and, for tiles that have a caption, set feature=dict(caption=<caption>, big=<callable>, animate=<callable>). Tile order in TILES = order in grids.json (layout order). Family details for every tile: ${V}/data/catalog.json (summary of each family) and, for featured ones, ${V}/data/research.json.

Your main job is the VISUALS:
1. icon for EVERY tile: a zero-arg function returning a small iconic VMobject that visually represents that problem/result (e.g. Gaussian moat: Gaussian-integer lattice dots with prime dots highlighted and a gap; Egyptian fractions: a bar split into unit fractions; Goldbach: two sets summing; etc.). Simple and recognisable at ~3x1.1 scene units: 5-60 submobjects, thin strokes (2-3), chapter accent ${s.accent} + WHITE_/GREY_ (+ RED_ for counterexample hints), at most a tiny maths symbol as text. Consistent style across tiles. No ImageMobjects. Make them genuinely evocative — this grid is where viewers "see" each problem for a second or two.
2. For each FEATURED tile: big=callable returning a richer version (fits ~5x4.4 units; it is placed on the left half of a big card while the caption sits on the right), and animate=callable(scene, mob, run_time) that plays 1-3 meaningful animations on mob totalling ≈ run_time seconds (e.g. self-similar zoom, the tiling assembling, a needle rotating, numbers converging). Use scene.play(...) with explicit run_time values that sum to <= run_time.
Then preview (tools/preview.sh ${s.id}) and inspect stills at the tile cues (tNNN / fNNN+1.0) with tools/stills.sh and Read. Iterate at least twice until every icon reads clearly and looks polished, and nothing overlaps the tile text. Return a short summary (what each icon depicts, any concerns).`
  }
  const spec = s.kind === 'spot' ? `Family ${s.fam}; research notes = the entry with num "${s.fam}" in ${V}/data/research.json (history with sources, precise claim, pitfalls to avoid, visual ideas).` : 'No single family; use data/catalog.json and README.md facts as needed.'
  return `${common}

Your scene: ${s.id}. Class name: ${s.cls} (subclass of VoiceScene). Accent colour: ${s.accent}. ${spec}
Director's notes (beats keyed to cue names) — follow them, but you are the animator: make it beautiful, clear and correct, and improve on them where you see a better visual: ${V}/data/scene_specs.json["${s.id}"].

Quality bar: this should look like a polished 3Blue1Brown segment — purposeful motion explaining the idea in sync with the words, clean composition, generous spacing, correct maths, no clutter, nothing static for long. Every cue in the timing file is a moment the viewer hears something specific; make the picture respond.

Process: write the scene, preview (tools/preview.sh ${s.id}), extract stills at every cue (tools/stills.sh ${s.id} <cues...> end) and look at them with Read; fix overlaps / clipping / tiny text / sync / dead time / inaccuracies; repeat at least twice (3+ is better). Also check that preview.sh printed no errors or VoiceScene squeeze warnings. Return a short summary: what is on screen at each major cue, and any remaining concerns.`
}

function polishPrompt(s, built) {
  const common = COMMON.replaceAll('<id>', s.id)
  return `${common}

You are the independent CRITIC + POLISHER for scene ${s.id} (class ${s.cls}), written by another agent. Its summary: ${JSON.stringify(built || '').slice(0, 1500)}
${s.kind === 'spot' ? `Family ${s.fam}: check facts against the entry with num "${s.fam}" in ${V}/data/research.json (pitfalls!).` : s.kind === 'grid' ? `Tiles: ${V}/data/grids.json["${s.id}"]; family summaries in ${V}/data/catalog.json.` : ''} Director's notes (if any): ${V}/data/scene_specs.json["${s.id}"].

1. Render a fresh preview (tools/preview.sh ${s.id}); extract stills at EVERY cue in build/timing/${s.id}.json (plus a few in-between moments and 'end'), and inspect each with Read.
2. Critique hard, as a demanding 3Blue1Brown-level editor: text overlapping or clipped; elements off the safe area; text too small (< ~22 at 1080p equivalent); visual clutter; stale elements lingering after the narration moves on; dead/static stretches; motion out of sync with the cue words; inconsistent style (fonts/colours vs SCENE_GUIDE); mathematically wrong or misleading pictures or labels; overclaims on screen; ugly or unclear icons. For grids: does every icon evoke its problem? does the featured big card look rich and animate?
3. FIX everything you find directly in ${V}/scenes/${s.id}.py, re-render, re-check the stills. Iterate until clean (at least one fix-and-verify round even if issues are minor).
Return: list of issues found and what you changed, plus anything you could not fix.`
}

const results = await pipeline(
  SCENES,
  (s) => agent(buildPrompt(s), { label: `build:${s.id}`, phase: 'Build' }),
  (built, s) => agent(polishPrompt(s, built), { label: `polish:${s.id}`, phase: 'Polish' })
    .then(p => ({ id: s.id, built, polished: p })),
)
return results
