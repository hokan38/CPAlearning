"""過去問解答例を「問題が載っている教科書ページ」へ振り分ける。

- 軽いページ: type "qa" のプラン行(qa_plan_tN.json) → build_annotated が
  ページ下部の余白(入らなければ右コメント帯)に赤字で直接記載
- 重いページ: qa_pages.json に退避 → build_final2 がそのページの直後に
  解答例ページを挿入する
"""
import json, os, collections

OFFSET = {1: 9, 2: 21, 3: 45, 4: 69, 5: 105, 6: 5, 7: 39,
          8: 11, 9: 21, 10: 35, 11: 51, 12: 63, 13: 71, 14: 79, 15: 115,
          16: 127, 17: 137, 18: 145, 19: 167, 20: 181, 21: 225, 22: 235,
          23: 259, 24: 267}
BOOK_OF = {**{c: 1 for c in range(1, 6)}, **{c: 2 for c in (6, 7)},
           **{c: 3 for c in range(8, 25)}}
PLAN_OF_BOOK = {1: ["plan_ch1.json","plan_ch2.json","plan_ch3.json","plan_ch4.json","plan2_ch05.json"],
                2: ["plan2_ch06.json","plan2_ch07.json"],
                3: [f"plan2_ch{c:02d}.json" for c in range(8,25)]}

def load(path):
    if not os.path.exists(path): return []
    raw = open(path, encoding="utf-8").read().strip()
    try:
        d = json.loads(raw); return d if isinstance(d, list) else [d]
    except json.JSONDecodeError:
        out=[]
        for l in raw.splitlines():
            s=l.strip().rstrip(",")
            if s.startswith("{"):
                try: out.append(json.loads(s))
                except json.JSONDecodeError: pass
        return out

# ページ帯の既存コメント量(plan2 comment + supp_plan comment)
band_chars = collections.Counter()   # (book, page) -> chars
for book, plans in PLAN_OF_BOOK.items():
    for pf in plans + [f"supp_plan_ch{c:02d}.json" for c,b in BOOK_OF.items() if b==book]:
        for e in load(pf):
            if e.get("type") in ("comment","note"):
                band_chars[(book, e["page"])] += len(e.get("text",""))

qa_by_page = collections.defaultdict(list)   # (book,page,ch,ref) -> [(q,a)]
for ch in range(1, 25):
    for d in load(f"extra_qa_ch{ch:02d}.json"):
        ref = str(d.get("ref","")).strip()
        a = (d.get("a") or "").strip(); q=(d.get("q") or "").strip()
        if not a: continue
        try: pg = OFFSET[ch] + int(ref.split("-")[1])
        except Exception: continue
        qa_by_page[(BOOK_OF[ch], pg, ch, ref)].append((q, a))

inline = {1: [], 2: [], 3: []}
heavy = []
n_in = n_hv = 0
for (book, pg, ch, ref), items in sorted(qa_by_page.items()):
    qa_total = sum(len(q)+len(a) for q,a in items)
    if qa_total + band_chars[(book, pg)] <= 1600:
        for q,a in items:
            inline[book].append({"page": pg, "type": "qa",
                                 "text": f"◆解答例｜{q}\n{a}"})
        n_in += 1
    else:
        heavy.append({"book": book, "page": pg, "ch": ch, "ref": ref,
                      "items": [{"q": q, "a": a} for q,a in items]})
        n_hv += 1

for book, entries in inline.items():
    with open(f"qa_plan_t{book}.json","w",encoding="utf-8") as f:
        for e in entries: f.write(json.dumps(e, ensure_ascii=False)+"\n")
json.dump(heavy, open("qa_pages.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"inline pages: {n_in} ({sum(len(v) for v in inline.values())} items), heavy pages: {n_hv}")
for h in heavy: print("  heavy:", h["ref"], "book", h["book"], "p", h["page"], len(h["items"]), "items")
