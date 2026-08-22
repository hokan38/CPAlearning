"""supp_comments_chNN.json (ref形式) → プラン形式 supp_plan_chNN.json に変換"""
import json
import os

OFFSET = {1: 9, 2: 21, 3: 45, 4: 69, 5: 105, 6: 5, 7: 39,
          8: 11, 9: 21, 10: 35, 11: 51, 12: 63, 13: 71, 14: 79, 15: 115,
          16: 127, 17: 137, 18: 145, 19: 167, 20: 181, 21: 225, 22: 235,
          23: 259, 24: 267}
LAST = {1: 21, 2: 45, 3: 69, 4: 105, 5: 154, 6: 39, 7: 70,
        8: 21, 9: 35, 10: 51, 11: 63, 12: 71, 13: 79, 14: 115, 15: 127,
        16: 137, 17: 145, 18: 167, 19: 181, 20: 225, 21: 235, 22: 259,
        23: 267, 24: 304}
FIRST = {1: 10, 2: 22, 3: 46, 4: 70, 5: 106, 6: 6, 7: 40,
         8: 12, 9: 22, 10: 36, 11: 52, 12: 64, 13: 72, 14: 80, 15: 116,
         16: 128, 17: 138, 18: 146, 19: 168, 20: 182, 21: 226, 22: 236,
         23: 260, 24: 268}

SC = os.path.dirname(os.path.abspath(__file__))
total = 0
for ch in range(1, 25):
    src = f"{SC}/supp_comments_ch{ch:02d}.json"
    if not os.path.exists(src):
        print(f"ch{ch:02d}: MISSING")
        continue
    out = []
    for line in open(src, encoding="utf-8").read().splitlines():
        s = line.strip().rstrip(",")
        if not s.startswith("{"):
            continue
        try:
            d = json.loads(s)
        except json.JSONDecodeError:
            continue
        text = (d.get("text") or "").strip()
        if not text:
            continue
        try:
            n = int(str(d.get("ref")).split("-")[1])
            page = OFFSET[ch] + n
        except (IndexError, ValueError, TypeError):
            page = FIRST[ch]
        page = min(max(page, FIRST[ch]), LAST[ch])
        e = {"page": page, "type": "comment", "text": text}
        if d.get("search"):
            e["search"] = d["search"]
        out.append(e)
    with open(f"{SC}/supp_plan_ch{ch:02d}.json", "w", encoding="utf-8") as f:
        for e in out:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    total += len(out)
    print(f"ch{ch:02d}: {len(out)}")
print("total", total)
