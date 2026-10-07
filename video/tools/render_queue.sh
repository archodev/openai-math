#!/bin/bash
# Low-priority final-render queue: renders every scene listed in build/ready.txt whose
# final video is missing or older than its scene file / timing file. Loops until
# build/queue.stop exists.
VIDEO=/home/user/openai-math/video
while [ ! -f $VIDEO/build/queue.stop ]; do
  did=0
  for id in $(cat $VIDEO/build/ready.txt 2>/dev/null); do
    out=$VIDEO/build/final/$id.mp4
    src=$VIDEO/scenes/$id.py
    if [ ! -f $out ] || [ $src -nt $out ] || [ $VIDEO/build/timing/$id.json -nt $out ] || [ $VIDEO/lib -nt $out ]; then
      nice -n 19 bash -c "JOBS=1 $VIDEO/tools/render_final.sh $id"
      did=1
    fi
  done
  [ $did = 0 ] && sleep 30
done
