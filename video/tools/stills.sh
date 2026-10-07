#!/bin/bash
# Extract stills at given cue names (or seconds) from a scene preview.
#   tools/stills.sh <scene_id> <cue|seconds> [...]
# Prints PNG paths (in build/stills/<id>/).
id="$1"; shift
VIDEO=/home/user/openai-math/video
mp4=$(ls -t $VIDEO/build/media_preview/videos/$id/*/$id.mp4 | head -1)
mkdir -p $VIDEO/build/stills/$id
for c in "$@"; do
  if [[ "$c" =~ ^[0-9.]+$ ]]; then t=$c; else
    t=$(/opt/venv/bin/python -c "import json,sys; d=json.load(open('$VIDEO/build/timing/$id.json')); n='$c'; b,off=(n.split('+')+['0'])[:2] if '+' in n else (n,'0'); print(d['duration']-0.05 if b=='end' else d['cues'][b]+float(off))"); fi
  out=$VIDEO/build/stills/$id/${c//[^A-Za-z0-9_.+-]/_}.png
  ffmpeg -loglevel error -y -ss $t -i "$mp4" -frames:v 1 "$out" && echo "$out  (t=$t)"
done
