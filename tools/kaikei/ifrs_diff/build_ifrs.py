"""会計基準差異対照表(IFRS-JGAAP)の論述ドリルを見開きPDFにする。"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drill"))
import build_all as B
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "ifrs_drill.html")
OUT_PDF = os.path.join(HERE, "会計基準差異対照表_論述ドリル.pdf")

EXTRA = """
.std { border-left:3pt solid #999; border-radius:2pt; padding:3pt 7pt 3pt 8pt; margin:3pt 0 6pt; }
.std.ifrs { border-color:#1d4e89; background:#f1f5fa; }
.std.jp { border-color:#c1121f; background:#fdf3f4; }
.std .tag { display:inline-block; font-size:7.6pt; font-weight:bold; color:#fff; padding:0 6pt; border-radius:2pt; margin-right:6pt; }
.std.ifrs .tag { background:#1d4e89; }
.std.jp .tag { background:#c1121f; }
.std > b { font-size:9.2pt; }
.std ul { margin:3pt 0 0; padding-left:15pt; }
.std li { margin:0 0 2pt; }
.common, .why { margin:2pt 0 5pt; font-size:8.9pt; }
.common b, .why b { color:#555; margin-right:4pt; }
.tiernote { font-size:8.6pt; color:#444; background:#f6f6f6; border-radius:3pt; padding:5pt 8pt; margin:0 0 10pt; }
.why b { display:block; }
table.cmp { border-collapse:collapse; width:100%; font-size:8.6pt; margin:2pt 0 6pt; }
table.cmp th { background:#f1f1f1; text-align:left; }
table.cmp th, table.cmp td { border:0.5pt solid #aaa; padding:2pt 4pt; vertical-align:top; }
table.cmp th:nth-child(2), table.cmp td:nth-child(2) { color:#1d4e89; }
"""

def main():
    frag = open(os.path.join(HERE, "frag_ifrs.html")).read()
    n = len(re.findall(r'<div class="item">', frag))
    # Tier C も収録する（build_all の C 除去を迂回）
    body = B.ITEM_RE.sub(lambda m: f'<div class="row"><div class="left">{m.group(1)}{m.group(2)}</div><div class="right">{m.group(3) if m.group(3).rstrip().endswith("</div>") else m.group(3)+"</div>"}{m.group(4) or ""}</div></div>', frag)
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>会計基準差異対照表 論述ドリル</title><style>{B.CSS}{EXTRA}</style></head><body>
<h1 class="cover">会計基準差異対照表 論述ドリル</h1>
<div class="cover-sub">IFRSと日本基準との主要な差異｜CPA会計学院 補助教材（令和7年12月）準拠｜Tier S・A・B・C 全{n}問</div>
<div class="cover-wrap"><div class="lead"><b>使い方</b><br>
⓪見開き構成。左ページが問題、右ページが解答例。右を隠して左だけ読み、書いてから右を開く。<br>
①解答例は元資料の文章をそのまま収録している。青枠＝ＩＦＲＳ欄、赤枠＝日本基準欄（太字が要旨、その下が基準の規定）、最後が元資料の解説。<br>答案は「ＩＦＲＳ＝要旨／日本基準＝要旨／解説の理由」の順で書く。基準番号は書けなくてよい。<br>
②Tier Sの5つは実務対応報告第18号の5項目。B-10はその総合問題（本ドリル独自）。<br>
③問題文は本ドリルで作成。元資料は29項目（Tier S 5・A 8・B 9・C 7）。</div></div>
{body}
<p class="foot">出典：CPA会計学院「財務会計論 補助教材 会計基準差異対照表」（令和7年12月27日）。解答例の本文（要旨・規定・解説）は同資料の記載をそのまま転記。</p>
</body></html>"""
    open(OUT_HTML, "w").write(html)
    subprocess.run([B.CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    f"--print-to-pdf={OUT_PDF}", "--no-pdf-header-footer", OUT_HTML], check=True, capture_output=True)
    d = pymupdf.open(OUT_PDF)
    # アウトライン（Tier > 各問）
    secs = re.findall(r'<section class="chap" id="(\w+)">(.*?)</section>', frag, re.S)
    frags = []
    for k, (sid, body) in enumerate(secs, start=1):
        m = re.search(r'<h1 class="chap">([^<]*)<small>', body)
        frags.append({"num": k, "title": m.group(1).strip(), "html": body})
    pages = {}
    for fr in frags:
        key = fr["title"].split("\u3000")[0]
        for i in range(d.page_count):
            big = "".join(sp["text"] for b in d[i].get_text("dict")["blocks"] for l in b.get("lines", []) for sp in l["spans"] if 14 < sp["size"] < 16)
            if big.startswith(key):
                pages[fr["num"]] = i + 1; break
    B.build_outline(d, frags, pages, ranks=("S", "A", "B", "C"), rank_label="Tier {r}", include_toc=False)
    B.stamp_page_numbers(d)
    d.save(OUT_PDF + ".tmp", garbage=3, deflate=True); d.close(); os.replace(OUT_PDF + ".tmp", OUT_PDF)
    d = pymupdf.open(OUT_PDF)
    print("items", n, "pages", d.page_count, "MB", round(os.path.getsize(OUT_PDF)/1e6, 2), "outline", len(d.get_toc()))

if __name__ == "__main__":
    main()
