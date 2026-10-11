"""各問が教科書のどのページ（と位置）の論点かを推定し、frag/order.json に保存する。
使い方: python3 -I order_items.py <教科書ページダンプのディレクトリ(kaikei_tb)>
"""
import re, glob, json, os, sys, html as H
TB = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
RANGES = {2:("tb1",22,45),3:("tb1",46,69),4:("tb1",70,105),5:("tb1",106,153),6:("tb2",6,39),7:("tb2",40,69),
          8:("tb3",12,21),9:("tb3",22,35),10:("tb3",36,51),11:("tb3",52,63),12:("tb3",64,71),13:("tb3",72,79),
          14:("tb3",80,115),15:("tb3",116,127),16:("tb3",128,137),17:("tb3",138,145),18:("tb3",146,167),
          19:("tb3",168,181),20:("tb3",182,225),21:("tb3",226,235),22:("tb3",236,259),23:("tb3",260,267),24:("tb3",268,303)}
norm = lambda s: re.sub(r"\s", "", s)
strip = lambda h: norm(H.unescape(re.sub(r"<[^>]+>", "", h)))
def grams(s, n=4):
    s = re.sub(r"[、。，．・（）()「」『』／\-—\d０-９]", "", s)
    return {s[i:i+n] for i in range(len(s)-n+1)}
out = {}
for f in sorted(glob.glob(os.path.join(HERE, "frag", "ch*.html"))):
    ch = int(re.search(r"ch(\d+)", f).group(1)); s = open(f).read()
    book, a, b = RANGES[ch]
    pages = {p: norm(open(os.path.join(TB, book, f"p{p:03d}.txt")).read()) for p in range(a, b+1)}
    items = re.findall(r'<div class="th">([ABC]-\d+)　([^<]*?)(?:<span>[^<]*</span>)?</div>\s*<div class="q">(.*?)</div>\s*<div class="a">(.*?)(?=<div class="pt">|</div>\s*</div>)', s, re.S)
    res = []
    for lab, title, q, ans in items:
        t = re.sub(r"【[^】]*】", "", title)
        ks = [strip(k) for k in re.findall(r"<k>(.*?)</k>", ans)]
        tg, qg, ag = grams(norm(t)), grams(strip(q)), grams(strip(ans))
        scores = {}
        for p, txt in pages.items():
            sc = 3*sum(g in txt for g in tg) + 1.0*sum(g in txt for g in qg) + 0.5*sum(g in txt for g in ag) + 2*sum(1 for k in ks if len(k) >= 4 and k in txt)
            scores[p] = sc
        mx = max(scores.values()) or 1
        cand = [p for p in sorted(scores) if scores[p] >= 0.7*mx]
        pg = cand[0]
        txt = pages[pg]; pos = min([txt.find(g) for g in (tg or qg) if g in txt] or [len(txt)])
        res.append({"label": lab, "title": title, "page": pg, "pos": pos, "best": max(scores, key=scores.get)})
    res.sort(key=lambda r: (r["page"], r["pos"]))
    out[f"ch{ch:02d}"] = res
json.dump(out, open(os.path.join(HERE, "frag", "order.json"), "w"), ensure_ascii=False, indent=1)
for ch, rs in out.items():
    print(ch, " ".join(f'{r["label"]}@{r["page"]}' for r in rs))
