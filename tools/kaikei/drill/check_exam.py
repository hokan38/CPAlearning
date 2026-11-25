"""答案形式に書き直した章フラグメントの検査。使い方: python3 check_exam.py frag/chNN.html"""
import re
import sys

p = sys.argv[1]
s = open(p).read()
err = []
if not re.search(r'<section class="chap" id="ch\d\d">', s):
    err.append("section開始なし")
if not s.rstrip().endswith("</section>"):
    err.append("</section>で終わっていない")
for tag in ("div", "ol", "ul", "p", "section"):
    o = len(re.findall(rf"<{tag}[\s>]", s))
    c = len(re.findall(rf"</{tag}>", s))
    if o != c:
        err.append(f"<{tag}> 開閉不一致 {o}/{c}")

LIM = {"A": (400, 520), "B": (300, 400), "C": (180, 250)}


def strip(h):
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", h))


over, lens, n = [], [], 0
for m in re.finditer(r'<div class="item">(.*?)(?=<div class="item">|<h2|</section>)', s, re.S):
    b = m.group(1)
    n += 1
    th = re.search(r'<div class="th">([ABC])-(\d+)', b)
    q = re.search(r'<div class="q">(.*?)</div>', b, re.S)
    a = re.search(r'<div class="a">(.*?)</div>', b, re.S)
    if not (th and q and a):
        err.append("th/q/aの欠落: " + strip(b)[:40])
        continue
    r, num, ah, qh = th.group(1), th.group(2), a.group(1), q.group(1)
    tag = f"{r}-{num}"
    if re.search(r"<ol|<ul|<li", ah):
        err.append(f"{tag} 箇条書きタグが残っている")
    if re.search(r"<b>\s*(結論|理由|ポイント)", ah) or re.search(r"(結論|理由)\s*[:：]", strip(ah)):
        err.append(f"{tag} 見出しラベルが残っている")
    if "<p>" not in ah:
        err.append(f"{tag} 段落<p>がない")
    body = strip(ah).replace("解答例", "", 1)
    multi = bool(re.search(r"\(\d\)|（\d）|\([a-e]\)|（[a-eａ-ｅ]）|[①②③]|二つ|三つ|四つ|五つ|[2-9２-９]つ|[2-5２-５二三四五]点|それぞれ|場合", strip(qh)))
    lim = LIM[r][1] if multi else LIM[r][0]
    lens.append(len(body))
    if len(body) > lim:
        over.append(f"{tag} {len(body)}字 (上限{lim})")

avg = int(sum(lens) / len(lens)) if lens else 0
print(f"{p}: items={n} errors={len(err)} 平均{avg}字 長さ超過={len(over)}")
for o in over:
    print("   長さ超過:", o)
for e in err:
    print(" -", e)
sys.exit(1 if err else 0)
