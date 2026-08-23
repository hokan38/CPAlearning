import json
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel

BASE = Path(__file__).parent
AUDIO = BASE / "audio_keiei"
OUT = BASE / "transcripts"
OUT.mkdir(exist_ok=True)

FILES = ['nagata1_1', 'nagata1_2', 'nagata1_3', 'nagata1_4', 'nagata1_5', 'nagata1_6', 'nagata2_1', 'nagata2_2', 'nagata2_3', 'ao1_1', 'ao1_2', 'ao1_3', 'ao1_4', 'ao1_5', 'ao1_6', 'ao2_1', 'ao2_2', 'ao2_3', 'ao2_4', 'ao3_1', 'ao3_2', 'ao3_3', 'ao3_4', 'ao3_5', 'ao3_6', 'ao4_1', 'ao4_2', 'ao4_3', 'ao4_4', 'ao5_1', 'ao5_2', 'ao5_3', 'ao5_4']

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
