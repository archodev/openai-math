#!/bin/bash
# Extract stills at given cue names (or seconds) from a scene preview.
#   tools/stills.sh <scene_id> <cue|cue+0.5|cue-0.3|seconds|end|end-0.6> [...]
# 'end' always means the last frame of the scene (narration end).
id="$1"; shift
VIDEO=/home/user/openai-math/video
mp4=$(ls -t $VIDEO/build/media_preview/videos/$id/*/$id.mp4 | head -1)
mkdir -p $VIDEO/build/stills/$id
for c in "$@"; do
  t=$(/opt/venv/bin/python - "$VIDEO/build/timing/$id.json" "$c" <<'PY'
import json, re, sys
d = json.load(open(sys.argv[1])); n = sys.argv[2]
if re.fullmatch(r"[0-9.]+", n): print(n); sys.exit()
m = re.fullmatch(r"(.+?)([+-][0-9.]+)?", n)
base, off = m.group(1), float(m.group(2) or 0)
t = d["duration"] - 0.05 if base == "end" else d["cues"][base]
print(max(0.0, min(d["duration"] - 0.05, t + off)))
PY
)
  out=$VIDEO/build/stills/$id/${c//[^A-Za-z0-9_.+-]/_}.png
  ffmpeg -loglevel error -y -ss $t -i "$mp4" -frames:v 1 "$out" && echo "$out  (t=$t)"
done
