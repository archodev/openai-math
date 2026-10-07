#!/bin/bash
# Low-quality preview render with a global concurrency limit (4 slots) so many
# agents can share the 4-CPU box.
#   tools/preview.sh <scene_id> [quality: l|m|h] [fps]
# Writes build/media_preview/videos/<id>/<res>/<id>.mp4 and prints its path.
set -e
id="$1"; q="${2:-l}"; fps="${3:-15}"
VIDEO=/home/user/openai-math/video
file="$VIDEO/scenes/$id.py"
cls=$(grep -oP '^class \K\w+(?=\()' "$file" | head -1)
mkdir -p /tmp/manim_slots
while true; do
  for s in 1 2 3 4; do
    exec 9>/tmp/manim_slots/slot$s
    if flock -n 9; then
      cd "$VIDEO/scenes"
      /opt/venv/bin/manim -q$q --fps $fps "$file" "$cls" --disable_caching \
        --media_dir "$VIDEO/build/media_preview" -o "$id.mp4" 2>&1 | grep -E -A12 "Traceback|Error|rror:|WARNING|VoiceScene" | head -60
      out=$(ls -t $VIDEO/build/media_preview/videos/$id/*/$id.mp4 2>/dev/null | head -1)
      echo "OUTPUT: $out"
      exit 0
    fi
  done
  sleep 3
done
