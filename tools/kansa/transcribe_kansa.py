import json
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel

BASE = Path(__file__).parent
AUDIO = BASE / "audio_kansa"
OUT = BASE / "transcripts"
OUT.mkdir(exist_ok=True)

FILES = ['kansa1_1', 'kansa2_1', 'kansa3_1', 'kansa3_2', 'kansa3_3', 'kansa3_4', 'kansa3_5', 'kansa4_1', 'kansa4_2', 'kansa4_3', 'kansa4_4', 'kansa4_5', 'kansa4_6', 'kansa4_7', 'kansa4_8', 'kansa5_1', 'kansa5_2', 'kansa5_3', 'kansa5_4', 'kansa5_5', 'kansa5_6', 'kansa5_7', 'kansa5_8', 'kansa5_9', 'rinri5_10', 'rinri5_11', 'rinri6_1', 'rinri6_2', 'rinri6_3']

model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)

for name in FILES:
    out_path = OUT / f"{name}.txt"
    if out_path.exists():
        print(f"skip {name}", flush=True)
        continue
    t0 = time.time()
    print(f"start {name}", flush=True)
    segments, info = model.transcribe(
        str(AUDIO / f"{name}.mp3"),
        language="ja",
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    lines = []
    for seg in segments:
        m, s = divmod(int(seg.start), 60)
        h, m = divmod(m, 60)
        lines.append(f"[{h:d}:{m:02d}:{s:02d}] {seg.text.strip()}")
        if len(lines) % 200 == 0:
            print(f"  {name}: {len(lines)} segs, at {h:d}:{m:02d}:{s:02d}", flush=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"done {name}: {len(lines)} segments, {time.time()-t0:.0f}s, dur={info.duration:.0f}s", flush=True)

print("ALL DONE", flush=True)
