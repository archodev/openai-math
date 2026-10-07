"""WIP rough cut: newest available render of every scene (final 1080p60 if present,
else the latest preview), normalised to 1280x720@30 and exactly the narration length,
then assembled with narration + music via tools/assemble.py."""
import importlib.util, json, subprocess, sys, glob, os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
V = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("s", V / "narration/script.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out = V / "build/roughcut/clips"; out.mkdir(parents=True, exist_ok=True)

def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],
                                capture_output=True,text=True).stdout)
def job(sc):
    sid = sc["id"]
    cands = glob.glob(str(V/f"build/final/{sid}.mp4")) + glob.glob(str(V/f"build/media_preview/videos/{sid}/*/{sid}.mp4"))
    src = max(cands, key=os.path.getmtime)
    T = json.loads((V/f"build/timing/{sid}.json").read_text())["duration"]
    d = dur(src)
    pad_start = T - d if (sid.endswith("_grid") and T - d > 0.8) else 0.0
    vf = f"scale=1280:720:flags=lanczos,fps=30,format=yuv420p,tpad=start_duration={pad_start:.3f}:start_mode=clone:stop_mode=clone:stop_duration=5"
    subprocess.run(["ffmpeg","-loglevel","error","-y","-i",src,"-vf",vf,"-t",f"{T:.3f}","-an",
                    "-c:v","libx264","-preset","veryfast","-crf","18",str(out/f"{sid}.mp4")],check=True)
    return sid, Path(src).parent.name, round(d,2), T, round(pad_start,2)
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(job, m.SCENES):
        print(*r)
