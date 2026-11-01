"""監査ドリルのフラグメント検査。
使い方: python3 -I check_kfrag.py <frag.html> <テキストのページダンプdir(kansa_tb)> [開始PDFページ 終了PDFページ]
- 各問の解答がテキストの文章そのままか（引用元ページ±1との一致率）を調べる
- 範囲を指定すると、その範囲の〔Ａ〕〔Ｂ〕見出しが問になっているかも調べる
"""
import re, sys, os, html as H
frag, tb = sys.argv[1], sys.argv[2]
rng = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else None
s = open(frag).read()
m = re.search(r'<section class="chap" data-book="(k\d)" id="([^"]+)">', s)
if not m: sys.exit("NG: <section class=\"chap\" data-book=\"kN\" id=\"...\"> がない")
book = m.group(1)
norm = lambda t: re.sub(r"\s+", "", H.unescape(re.sub(r"<[^>]+>", "", t)))
def page(p):
    f = os.path.join(tb, book, f"p{p:03d}.txt")
    return norm(open(f).read()) if os.path.exists(f) else ""
items = re.findall(r'<div class="item" data-rank="([ABC])" data-pdf="([\d,]+)" data-head="([^"]*)">(.*?)</div>\s*(?=<div class="item"|</section>)', s, re.S)
if not items: sys.exit("NG: 問が0件（.item の属性 data-rank / data-pdf / data-head を確認）")
err = 0; heads = []
for i, (rk, pdf, head, body) in enumerate(items, 1):
    heads.append(norm(head))
    for part in ("th", "q", "a", "pt"):
        if f'<div class="{part}">' not in body: print(f"NG 問{i}: .{part} がない"); err += 1
    a = re.search(r'<div class="a">(.*?)</div>\s*<div class="pt">', body, re.S)
    if not a: continue
    ans = norm(re.sub(r'<span class="l">.*?</span>', "", a.group(1)))
    pages = [int(x) for x in pdf.split(",")]
    src = "".join(page(q) for p in pages for q in (p - 1, p, p + 1))
    if not src: print(f"NG 問{i}: data-pdf={pdf} のページが見つからない"); err += 1; continue
    mark = [False] * len(ans)
    for j in range(len(ans) - 7):
        if ans[j:j+8] in src:
            for k in range(j, j + 8): mark[k] = True
    cov = sum(mark) / max(1, len(ans))
    if cov < 0.9:
        bad = "".join(c if not mk else "・" for c, mk in zip(ans, mark))
        print(f"NG 問{i}（{head[:20]}）: テキストとの一致率 {cov:.0%}（90%以上必要）。一致しない部分: {re.sub('・+', '…', bad)[:160]}")
        err += 1
if rng:
    missing = []
    for p in range(rng[0], rng[1] + 1):
        f = os.path.join(tb, book, f"p{p:03d}.txt")
        if not os.path.exists(f): continue
        ls = [l.strip() for l in open(f).read().split("\n")]
        for i, l in enumerate(ls):
            mm = re.search(r"〔([ＡＢ])〕", l)
            if not mm: continue
            t = l.replace(mm.group(0), "").strip()
            if not t:
                prev = [x for x in ls[:i] if x]
                t = prev[-1] if prev else ""
            nt = norm(t)[:12]
            if nt and not any(nt[:8] in h or h[:8] in nt for h in heads if h):
                missing.append(f"p{p} {t[:30]}（{mm.group(1)}）")
    for x in missing: print("未収録の見出し:", x)
    err += len(missing)
print(f"{frag}: 問{len(items)}（A{sum(1 for x in items if x[0]=='A')}・B{sum(1 for x in items if x[0]=='B')}）／指摘{err}件")
