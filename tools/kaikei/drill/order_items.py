"""各問を教科書の論点（第○節 › 1. › (1) › 1)）に割り当て、論点順の並びを frag/order.json に保存する。
使い方: python3 -I order_items.py <教科書ページダンプのディレクトリ(kaikei_tb)>
自動判定の誤りは frag/order_overrides.json（章 → 問番号 → 見出しパスの一部）で上書きする。
"""
import re, glob, json, os, sys, html as H
TB = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
RANGES = {2:("tb1",22,45),3:("tb1",46,69),4:("tb1",70,105),5:("tb1",106,153),6:("tb2",6,39),7:("tb2",40,69),
          8:("tb3",12,21),9:("tb3",22,35),10:("tb3",36,51),11:("tb3",52,63),12:("tb3",64,71),13:("tb3",72,79),
          14:("tb3",80,115),15:("tb3",116,127),16:("tb3",128,137),17:("tb3",138,145),18:("tb3",146,167),
          19:("tb3",168,181),20:("tb3",182,225),21:("tb3",226,235),22:("tb3",236,259),23:("tb3",260,267),24:("tb3",268,303)}
# 見出しの形式：第１節／1. ／(1)／1)
PAT = [re.compile(r'^\s*\.?第([０-９0-9]+)節\.?\s+(\S.*?)\s*$'),
       re.compile(r'^\s{0,1}([0-9]{1,2})\.\s*(\S.{0,80}?)\s*$'),
       re.compile(r'^\s{0,3}\(([0-9]{1,2})\)\s*(\S.{0,80}?)\s*$'),
       re.compile(r'^\s{2,5}([0-9])\)\s*(\S.{0,80}?)\s*$')]
BAD = re.compile(r'なさい|（\s*①|\(\s*①|①\s*\)|\.\.\.\.|[Ａ-ＺA-Z]社|当期|当事業年度|平成|令和|Ｘ|20X|％|である。|とする。')
NOISE = re.compile(r'Ｘ|X[0-9]|20X|％|%|。|[0-9０-９]{3}')
Z = str.maketrans('０１２３４５６７８９', '0123456789')
norm = lambda s: re.sub(r"\s", "", s)
strip = lambda h: norm(H.unescape(re.sub(r"<[^>]+>", "", h)))
def grams(s, n=4):
    s = re.sub(r"[、。，．・（）()「」『』／\-—\d０-９]", "", s)
    return {s[i:i+n] for i in range(len(s)-n+1)}
def label(lv, n, t):
    t = t if len(t) <= 40 else t[:38] + "…"
    t = norm(t) if len(norm(t)) <= 4 else t          # 「取 得」→「取得」
    return [f"第{n}節 {t}", f"{n}. {t}", f"({n}) {t}", f"{n}) {t}"][lv]

def headings(book, a, z):
    lines, hs = [], []
    for p in range(a, z+1):
        ls = open(os.path.join(TB, book, f"p{p:03d}.txt")).read().split("\n")
        for i, ln in enumerate(ls):
            lines.append(ln)
            for lv, rx in enumerate(PAT):
                m = rx.match(ln)
                if not m: continue
                near = False   # 箇条書き（(1)(2)…が連続する行）は見出しではない
                if lv >= 2:
                    n0 = int(m.group(1))
                    for j in range(max(0, i-4), min(len(ls), i+5)):
                        mm = rx.match(ls[j]) if j != i else None
                        if mm and int(mm.group(1))-n0 == (1 if j > i else -1) and re.match(r"^\s*\(?[0-9]+\)\s", ls[j]): near = True
                if not BAD.search(ln) and not near:
                    t = re.sub(r'（[^）]*$', '', m.group(2)); t = re.sub(r'（[^）]*）\s*$', '', t).strip()
                    hs.append({"lv": lv, "n": int(m.group(1).translate(Z)), "t": t, "page": p, "at": len(lines)-1})
                break
    keep, last = [], [0]*4    # 番号が連番で続くものだけ採用
    for h in hs:
        if h["n"] == last[h["lv"]]+1 and (h["lv"] <= 1 or len(h["t"]) <= 40 and not NOISE.search(h["t"])):
            keep.append(h); last[h["lv"]] = h["n"]
            for j in range(h["lv"]+1, 4): last[j] = 0
    secs, cur = [], [None]*4
    for k, h in enumerate(keep):
        cur[h["lv"]] = (h["t"], label(h["lv"], h["n"], h["t"]))
        for j in range(h["lv"]+1, 4): cur[j] = None
        end = keep[k+1]["at"] if k+1 < len(keep) else len(lines)
        secs.append({"path": [c[0] for c in cur if c], "disp": [c[1] for c in cur if c], "page": h["page"],
                     "text": norm("".join(lines[h["at"]:end]))})
    return secs

OV = json.load(open(os.path.join(HERE, "frag", "order_overrides.json")))
out = {}
for f in sorted(glob.glob(os.path.join(HERE, "frag", "ch*.html"))):
    ch = int(re.search(r"ch(\d+)", f).group(1)); key = f"ch{ch:02d}"; s = open(f).read()
    secs = headings(*RANGES[ch])
    items = re.findall(r'<div class="th">([ABC]-\d+)　([^<]*?)(?:<span>[^<]*</span>)?</div>\s*<div class="q">(.*?)</div>\s*<div class="a">(.*?)(?=<div class="pt">|</div>\s*</div>)', s, re.S)
    res = []
    for lab, title, q, ans in items:
        t = re.sub(r"【[^】]*】", "", title)
        ks = [strip(k) for k in re.findall(r"<k>(.*?)</k>", ans)]
        tg, qg, ag = grams(norm(t)), grams(strip(q)), grams(strip(ans))
        def score(sc):
            txt = sc["text"]
            v = 3*sum(g in txt for g in tg) + sum(g in txt for g in qg) + 0.5*sum(g in txt for g in ag) + 2*sum(1 for k in ks if len(k) >= 4 and k in txt)
            return v/(1+len(txt)/3000)**0.5 + 6*sum(g in norm("".join(sc["path"])) for g in tg)
        if lab in OV.get(key, {}):
            want = OV[key][lab]
            hit = [j for j, sc in enumerate(secs) if want in ">".join(sc["path"]) or want == sc["path"][-1]]
            if not hit: sys.exit(f"{key} {lab}: 見出し「{want}」が見つからない")
            j = hit[0]
        else:
            j = max(range(len(secs)), key=lambda j: score(secs[j]))
        txt = secs[j]["text"]
        pos = min([txt.find(g) for g in (tg or qg) if g in txt] or [len(txt)])
        book = RANGES[ch][0]
        pm = re.search(r"－\s*(\d+-\d+)\s*－", open(os.path.join(TB, book, f"p{secs[j]['page']:03d}.txt")).read())
        res.append({"label": lab, "title": title, "sec": j, "pos": pos, "page": secs[j]["page"],
                    "tbpage": pm.group(1) if pm else "", "ronten": " › ".join(secs[j]["disp"])})
    res.sort(key=lambda r: (r["sec"], r["pos"]))
    out[key] = res
json.dump(out, open(os.path.join(HERE, "frag", "order.json"), "w"), ensure_ascii=False, indent=1)
for ch, rs in out.items():
    print("##", ch)
    for r in rs:
        if not r["label"].startswith("C"): print(f'  {r["label"]:5} p{r["page"]} {r["ronten"]}  ← {r["title"][:24]}')
