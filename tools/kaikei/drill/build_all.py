"""章別フラグメント(frag/chNN.html)を1冊のPDFに綴じる。
使い方: python3 build_all.py  → 会計実務_論述ドリル_全章.pdf
"""
import glob, os, re, subprocess, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
FRAG = os.path.join(HERE, "frag")
CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
OUT_HTML = os.path.join(HERE, "all_drill.html")
OUT_PDF = os.path.join(HERE, "会計実務_論述ドリル_全章.pdf")

CSS = """
@page { size: 7.1667in 10.125in; margin: 0.5in 0.5in 0.55in; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; }
body { font-family:"Noto Sans CJK JP","Noto Sans JP",sans-serif; font-size:9.3pt; line-height:1.65; color:#222; background:#fff; }
h1.cover { font-size:22pt; color:#c1121f; margin:120pt 0 8pt; }
.cover-sub { font-size:11pt; color:#444; margin-bottom:30pt; }
h1.chap { font-size:15pt; margin:0 0 10pt; color:#c1121f; break-before:page; }
h1.chap small { display:block; font-size:8.5pt; color:#444; font-weight:normal; margin-top:2pt; }
.pb { height:14pt; }
h2 { font-size:12pt; margin:0 0 10pt; color:#fff; background:#c1121f; padding:4pt 8pt; border-radius:3pt; }
h2 span { font-weight:normal; font-size:8.5pt; margin-left:8pt; }
h2.b { background:#8a1c26; } h2.c { background:#666; }
h2.toc { break-before:page; }
.lead { font-size:8.8pt; padding:6pt 9pt; border-left:3px solid #c1121f; background:#fdf1f2; margin:0 0 12pt; line-height:1.6; }
.item { margin:0 0 16pt; break-inside:avoid; }
.item .th { font-weight:bold; color:#c1121f; font-size:11pt; border-bottom:1.2pt solid #c1121f; padding-bottom:2pt; margin-bottom:6pt; }
.item .th span { font-weight:normal; color:#666; font-size:8.5pt; margin-left:8pt; }
.q { background:#f4f4f4; border-radius:3pt; padding:6pt 9pt; margin:0 0 6pt; }
.q b { color:#c1121f; margin-right:6pt; }
.a { padding:2pt 4pt 0; }
.a .l { display:inline-block; font-weight:bold; color:#fff; background:#c1121f; font-size:8pt; padding:0 6pt; border-radius:2pt; margin-bottom:3pt; }
.a p { margin:0 0 4pt; }
.a ol, .a ul { margin:0 0 4pt; padding-left:18pt; }
.a li { margin:0 0 2pt; }
k { color:#c1121f; font-weight:bold; font-style:normal; }
.pt { margin:4pt 0 0; padding:4pt 9pt; border-top:0.6pt dotted #c1121f; font-size:8.3pt; color:#555; }
.pt b { color:#c1121f; margin-right:4pt; }
table.toc { border-collapse:collapse; width:100%; font-size:9.5pt; }
table.toc td { padding:3pt 4pt; border-bottom:0.5pt dotted #bbb; vertical-align:top; }
table.toc td.n { text-align:right; width:36pt; white-space:nowrap; }
table.toc td.c { width:130pt; color:#555; font-size:8.5pt; white-space:nowrap; }
.foot { font-size:7pt; color:#777; margin-top:8pt; }
"""

def load_frags():
    frags = []
    for f in sorted(glob.glob(os.path.join(FRAG, "ch*.html"))):
        s = open(f).read()
        m = re.search(r'<h1 class="chap">(第(\d+)章[^<]*)<small>([^<]*)</small>', s)
        if not m:
            print("skip (no h1):", f); continue
        frags.append({"file": f, "num": int(m.group(2)), "title": m.group(1).strip(), "sub": m.group(3), "html": s})
    frags.sort(key=lambda x: x["num"])
    return frags

def counts(sub):
    m = re.search(r'A\s*(\d+)問／B\s*(\d+)問／C\s*(\d+)問', sub)
    return m.groups() if m else ("-", "-", "-")

def build_html(frags, pages=None):
    toc_rows = []
    for fr in frags:
        a, b, c = counts(fr["sub"])
        pg = pages.get(fr["num"], "") if pages else ""
        toc_rows.append(f'<tr><td>{fr["title"]}</td><td class="c">A{a}・B{b}・C{c}</td><td class="n">{pg}</td></tr>')
    total = sum(len(re.findall(r'<div class="item">', fr["html"])) for fr in frags)
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>会計実務 論述ドリル 全章</title><style>{CSS}</style></head><body>
<h1 class="cover">会計実務 論述ドリル</h1>
<div class="cover-sub">修了考査対策編 全章｜重要度A・B・C別｜問題文＋解答例文｜全{total}問</div>
<div class="lead"><b>使い方</b><br>
①問題文を読み、解答例を隠して6分で答案を書く。Aは全文、Bは骨子、Cは結論と理由1行。<br>
②解答例と照合し、末尾の「入れる語」が答案に入っていれば合格。<br>
③章内はA→B→Cの順に周回。2周目からはAだけ書き、B・Cは読んで再現できるかを確認する。<br>
④章の順番は教科書どおり。先にやるなら出題頻度の高い章（企業結合・金融商品・収益認識・連結・税効果・退職給付）から。</div>
<div class="lead" style="background:#f4f4f4;border-color:#888"><b>重要度の意味</b><br>
A＝過去に記述で問われた、または講師が「復元できるように」と指示した論点。白紙に書けるまで。<br>
B＝合格のために説明できる必要がある論点。骨子が書ければよい。<br>
C＝費用対効果が低い論点。結論と理由が1行で言えれば十分、直前期に一読。</div>
<h2 class="toc">目次</h2>
<table class="toc">{''.join(toc_rows)}</table>
{''.join(fr["html"] for fr in frags)}
<p class="foot">出典：CPA会計学院 修了考査対策講座2026 会計実務テキスト（講義反映版）、講義音声、修了考査過去問解答例。</p>
</body></html>"""
    return html

def render(html):
    open(OUT_HTML, "w").write(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    f"--print-to-pdf={OUT_PDF}", "--no-pdf-header-footer", OUT_HTML],
                   check=True, capture_output=True)
    return pymupdf.open(OUT_PDF)

def chapter_pages(doc, frags):
    pages = {}
    for fr in frags:
        key = fr["title"].split("　")[0]  # 第N章
        for i in range(doc.page_count):
            big = "".join(sp["text"] for b in doc[i].get_text("dict")["blocks"]
                          for l in b.get("lines", []) for sp in l["spans"] if 14 < sp["size"] < 16)
            if big.startswith(key):
                pages[fr["num"]] = i + 1; break
    return pages

def stamp_page_numbers(doc):
    for i in range(1, doc.page_count):
        p = doc[i]
        p.insert_text((p.rect.width / 2 - 8, p.rect.height - 20), str(i + 1),
                      fontname="helv", fontsize=8, color=(0.4, 0.4, 0.4))

def main():
    frags = load_frags()
    print("chapters:", [f["num"] for f in frags])
    doc = render(build_html(frags))
    pages = chapter_pages(doc, frags)
    doc.close()
    doc = render(build_html(frags, pages))
    pages2 = chapter_pages(doc, frags)
    if pages2 != pages:  # 目次のページ数が変わってずれた場合はもう一度
        doc.close(); doc = render(build_html(frags, pages2)); pages = pages2
    stamp_page_numbers(doc)
    doc.save(OUT_PDF + ".tmp", garbage=3, deflate=True)
    doc.close(); os.replace(OUT_PDF + ".tmp", OUT_PDF)
    d = pymupdf.open(OUT_PDF)
    print("pages:", d.page_count, "size MB:", round(os.path.getsize(OUT_PDF) / 1e6, 2))
    for fr in frags: print(f'  {fr["title"]}: p.{pages.get(fr["num"])}')

if __name__ == "__main__":
    main()
