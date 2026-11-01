"""JICPAの監査基準報告書（最新版）を1冊にまとめる。
使い方: python3 -I build_kihou_all.py <pdfs.json>
latest/<id>.pdf を順に結合し、表紙（一覧・最終改正日・適用時期の注意）としおりを付ける。"""
import json, os, re, sys, subprocess, html as H
import pymupdf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "kaikei", "drill"))
import build_all as B
res = json.load(open(sys.argv[1]))
ORDER = ["000"] + [r["id"] for r in res if re.fullmatch(r"\d{3}", r["id"]) and r["id"] != "000"] + ["hnk1", "hnk2", "nkh", "rkh1", "rkh2"]
byid = {r["id"]: r for r in res}
OUT = os.path.join(HERE, "監査基準報告書_最新版_全部.pdf")
NOTE = {"720": "2026/3/18改正分は2027年4月1日以後開始事業年度から適用", "805": "2026/3/18改正分は2027年4月1日以後開始事業年度から適用",
        "hnk1": "2026/3/18改正分は2027年4月1日以後開始事業年度から適用", "hnk2": "2026/3/18改正分は2027年4月1日以後開始事業年度から適用",
        "rkh1": "2026/3/18改正分は2026年4月1日以後開始の中間会計期間から適用", "rkh2": "2026/3/18改正分は2026年4月1日以後開始の会計期間から適用"}
rows = []
for i in ORDER:
    r = byid[i]
    rows.append(f'<tr><td>{H.escape(r["title"])}</td><td class="d">{r["date"]}</td><td class="n">{NOTE.get(i, "")}</td><td class="p" id="p{i}"></td></tr>')
ROMAN = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ"
def headings(src):
    """本文の見出しからしおりを作る：《Ⅰ 範囲及び目的》《Ⅱ 要求事項》《Ⅲ 適用指針》《付録…》＝第2階層、《１．…》＝第3階層。
    見出しが2行に折り返されている場合（《Ⅲ／適用指針》）はつなげて読む。"""
    out, body = [], False
    for pi, page in enumerate(src):
        ls = [l.strip() for l in page.get_text().split("\n")]
        k = 0
        while k < len(ls):
            t = ls[k]; k += 1
            if t.startswith("《") and "》" not in t:
                for _ in range(2):
                    if k < len(ls):
                        t += ls[k]; k += 1
                        if "》" in t: break
            m = re.match(r"^《\s*([" + ROMAN + r"]+)[\s　．.]*(.+?)》", t)
            if m:
                body = True; out.append([2, f"{m.group(1)} {m.group(2).strip()}", pi + 1]); continue
            if not body: continue
            m = re.match(r"^《\s*(付録\s*[０-９0-9]*)[\s　]*(.+?)》", t)
            if m:
                out.append([2, f"{m.group(1)} {m.group(2).strip()}", pi + 1]); continue
            m = re.match(r"^《\s*([０-９0-9]+)\s*[．.]\s*(.+?)》", t)
            if m:
                out.append([3, f"{m.group(1)}. {m.group(2).strip()}", pi + 1])
    if not out:   # 《Ⅰ》がない報告書（監基報（序））は《１．…》を第2階層にする
        for pi, page in enumerate(src):
            for t in page.get_text().split("\n"):
                m = re.match(r"^《\s*([０-９0-9]+)\s*[．.]\s*(.+?)》", t.strip())
                if m: out.append([2, f"{m.group(1)}. {m.group(2).strip()}", pi + 1])
    return out

def cover(pages):
    body = "".join(rows)
    for i, p in pages.items(): body = body.replace(f'<td class="p" id="p{i}"></td>', f'<td class="p">{p}</td>')
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 12mm 12mm; }} body {{ font-family:"Noto Sans CJK JP",sans-serif; font-size:8.3pt; color:#222; }}
h1 {{ font-size:15pt; color:#c1121f; margin:0 0 3pt; }} .sub {{ font-size:8.5pt; color:#555; margin:0 0 8pt; line-height:1.5; }}
table {{ border-collapse:collapse; width:100%; }} td {{ border-bottom:0.5pt solid #ddd; padding:2.2pt 4pt; vertical-align:top; }}
td.d {{ white-space:nowrap; color:#444; }} td.n {{ color:#c1121f; font-size:7.5pt; }} td.p {{ text-align:right; white-space:nowrap; }}
</style></head><body><h1>監査基準報告書 最新版（全部）</h1>
<div class="sub">日本公認会計士協会「監査実務指針等」一覧（https://jicpa.or.jp/specialized_field/publication/kansa/）の各報告書の最新改正の本文PDFを結合したもの（2026年11月1日取得）。監基報（序）・200〜910の41本に、品質管理基準報告書第1号・第2号、財務報告内部統制監査基準報告書第1号、期中レビュー基準報告書第1号・第2号を加えた。各PDF先頭の改正履歴の最終日付が一覧の最終改正日と一致することを確認済み。<br>
修了考査は「4月1日現在施行（適用）」の法令等で解答する。赤字の報告書は、2026年3月18日改正分の適用時期がそれより後なので注意。右端の数字はこのPDFのページ。</div>
<table>{body}</table></body></html>"""
def render_cover(pages):
    h = os.path.join(HERE, "_cover.html"); p = os.path.join(HERE, "_cover.pdf")
    open(h, "w").write(cover(pages))
    subprocess.run([B.CHROME, "--headless", "--disable-gpu", "--no-sandbox", f"--print-to-pdf={p}", "--no-pdf-header-footer", h], check=True, capture_output=True)
    d = pymupdf.open(p); os.remove(h); return d, p
c, cp = render_cover({}); ncov = c.page_count; c.close()
pages, n = {}, ncov + 1
for i in ORDER:
    pages[i] = n; n += pymupdf.open(os.path.join(HERE, "latest", f"{i}.pdf")).page_count
doc, cp = render_cover(pages)
toc = [[1, "一覧（最終改正日・適用時期）", 1]]
for i in ORDER:
    src = pymupdf.open(os.path.join(HERE, "latest", f"{i}.pdf"))
    start = doc.page_count + 1
    doc.insert_pdf(src)
    toc.append([1, re.sub(r"\s+", " ", byid[i]["title"]), start])
    for lv, t, p in headings(src):
        toc.append([lv, t[:60], start + p - 1])
doc.set_toc(toc)
doc.save(OUT, garbage=3, deflate=True); os.remove(cp)
print(OUT, pymupdf.open(OUT).page_count, "pages", f"{os.path.getsize(OUT)/1e6:.1f}MB", "toc", len(toc))
