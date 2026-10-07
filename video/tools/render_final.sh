#!/bin/bash
# Final 1080p60 renders, N scenes in parallel (default 4).
#   tools/render_final.sh [scene_id ...]     (default: every scene in narration order)
# Output: build/final/<scene_id>.mp4 ; logs in build/final/logs/
VIDEO=/home/user/openai-math/video
JOBS=${JOBS:-4}
mkdir -p $VIDEO/build/final/logs
if [ $# -gt 0 ]; then ids="$@"; else
  ids=$(/opt/venv/bin/python -c "
import importlib.util
s=importlib.util.spec_from_file_location('s','$VIDEO/narration/script.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(' '.join(x['id'] for x in m.SCENES))"); fi
render_one() {
  id=$1
  file=$VIDEO/scenes/$id.py
  cls=$(grep -oP '^class \K\w+(?=\()' "$file" | head -1)
  start=$(date +%s)
  cd $VIDEO/scenes && /opt/venv/bin/manim -qh --fps 60 "$file" "$cls" --disable_caching \
     --media_dir $VIDEO/build/final_media -o "$id.mp4" > $VIDEO/build/final/logs/$id.log 2>&1
  src=$(ls -t $VIDEO/build/final_media/videos/$id/1080p60/$id.mp4 2>/dev/null | head -1)
  if [ -n "$src" ] && grep -q "File ready" $VIDEO/build/final/logs/$id.log; then
    cp "$src" $VIDEO/build/final/$id.mp4
    echo "OK   $id  ($(( $(date +%s) - start ))s)"
  else
    echo "FAIL $id  (see build/final/logs/$id.log)"
  fi
}
export -f render_one; export VIDEO
echo $ids | tr ' ' '\n' | xargs -P $JOBS -I{} bash -c 'render_one {}'
