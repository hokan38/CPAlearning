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

LIM = {"A": (300, 450), "B": (250, 400), "C": (200, 300)}


def strip(h):
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", h))


def norm(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("国際財務報告基準", "IFRS").replace("ＩＦＲＳ", "IFRS")
    for a, b in (("または", "又は"), ("および", "及び"), ("ならびに", "並びに"), ("％", "%")):
        t = t.replace(a, b)
    return re.sub(r"[\s、。「」『』・,，（）()：:]", "", t)


def bigrams(t):
    return {t[i:i + 2] for i in range(len(t) - 1)}


def missing_terms(pt_html, body_html):
    pt = re.sub(r"<[^>]+>", "", pt_html).replace("入れる語", "", 1)
    pt = pt.split("。")[0]
    body = norm(body_html)
    bb = bigrams(body)
    miss = []
    for seg in re.split(r"[／/]", pt):
        for ch in re.split(r"[＝=→⇒＋+・（）()]", seg):
            c = norm(ch)
            if len(c) < 2:
                continue
            if c in body:
                continue
            g = bigrams(c)
            if g and len(g & bb) / len(g) >= 0.75:
                continue
            miss.append(ch.strip())
    return miss


over, lens, n, kw = [], [], 0, []
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
    ptm = re.search(r'<div class="pt">(.*?)</div>', b, re.S)
    if ptm:
        mt = missing_terms(ptm.group(1), ah)
        if mt:
            kw.append(f"{tag} 入れる語の欠落？: " + "／".join(mt))
    if len(body) > lim:
        over.append(f"{tag} {len(body)}字 (上限{lim})")

avg = int(sum(lens) / len(lens)) if lens else 0
print(f"{p}: items={n} errors={len(err)} 平均{avg}字 長さ超過={len(over)} 入れる語欠落={len(kw)}")
for k in kw:
    print("   ", k)
for o in over:
    print("   長さ超過:", o)
for e in err:
    print(" -", e)
sys.exit(1 if err else 0)
