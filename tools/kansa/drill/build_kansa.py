"""監査論ドリル（全節）を1つのPDFにまとめる。
使い方: python3 -I build_kansa.py
frag/<book>_<章>-<節>.html を教科書順に並べ、見開き（左＝問題／右＝テキストの原文）で組む。
"""
import os, re, sys, glob, subprocess, html as H
import pymupdf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "kaikei", "drill"))
import build_all as B   # 会計実務ドリルと同じ CSS・Chrome・ページ番号処理を使う

FRAG = os.path.join(HERE, "frag")
OUT_HTML = os.path.join(HERE, "kansa_drill.html")
OUT_PDF = os.path.join(HERE, "監査論_ドリル_全範囲.pdf")
BOOKS = [("k1", "基本論点編1"), ("k2", "基本論点編2"), ("k3", "修了考査対策編1"),
         ("k4", "修了考査対策編2（改正論点）"), ("k5", "修了考査対策編3（倫理規則・法規）")]
YEARS = ["平28", "平29", "平30", "令1", "令2", "令3", "令4", "令5", "令6", "令7"]
# 修了考査の出題実績（対策編1 序章①「(1) 出題実績」H28〜R7 を節に対応させたもの）
FREQ = {
    "k1_2-02": "平28 平29 平30", "k1_3-01": "平29 令1 令3 令4 令5 令6 令7", "k1_3-02": "平29 令2 令3 令4",
    "k1_3-03": "平29", "k1_3-04": "平30 令2 令3", "k1_3-05": "平28 令3", "k1_3-06": "平28 平30 令2 令3 令5 令6 令7",
    "k1_3-07": "平28 令1 令5 令6 令7", "k1_3-08": "平29", "k1_3-09": "令5", "k1_3-10": "令1 令4 令6 令7",
    "k1_3-11": "令6", "k1_3-13": "平29 令1 令5", "k1_3-14": "平28 平29 平30 令1 令2 令3 令5 令6",
    "k1_3-15": "平29 令1 令4", "k1_3-16": "平30 令1 令5 令6 令7", "k1_3-17": " ".join(YEARS),
    "k2_4-01": "令7", "k2_4-04": "令4", "k2_4-05": "令1 令4 令5 令7", "k2_4-06": "平28 平30 令1 令3",
    "k2_4-07": "平30 令3", "k2_4-08": "平30 令1 令6", "k2_5-01": "平28 令2 令4 令6 令7", "k2_5-02": "令1 令4",
    "k2_6-02": "平29 令3 令5 令6", "k2_6-03": "平28 平29 平30 令3 令4 令6", "k2_6-05": "平28 平29 平30 令4",
    "k2_6-06": "令7", "k2_6-07": "平29 令1 令4", "k2_6-08": "令3 令7",
    "k3_1-01": " ".join(YEARS), "k3_1-02": "令3 令7", "k3_1-06": "平29 令2 令3 令4",
}
NOTE = {"k3_2": "修了考査特有の論点", "k4": "近年の改正論点", "k5": "職業倫理・法規"}

CSS = B.CSS + """
.row .th { font-weight:bold; color:#c1121f; font-size:10.5pt; border-bottom:1.2pt solid #c1121f; padding-bottom:2pt; margin-bottom:6pt; }
.row .th span { font-weight:normal; color:#777; font-size:8.3pt; margin-left:8pt; }
.row .th .rk { color:#fff; font-weight:bold; font-size:7.5pt; margin-left:0; }
.row .th .no { color:#c1121f; font-weight:bold; font-size:10.5pt; margin:0 6pt 0 0; }
.a table { border-collapse:collapse; width:100%; margin:2pt 0 5pt; font-size:8.8pt; }
.a th, .a td { border:0.6pt solid #bbb; padding:2pt 5pt; vertical-align:top; text-align:left; }
.a th { background:#fbeaec; }
h1.part { font-size:20pt; color:#c1121f; break-before:page; margin:150pt 0 6pt; }
.partsub { font-size:10pt; color:#555; }
table.plan { border-collapse:collapse; width:100%; font-size:9pt; margin:4pt 0 10pt; }
table.plan th, table.plan td { border:0.6pt solid #ccc; padding:3pt 6pt; text-align:left; vertical-align:top; }
table.plan th { background:#fbeaec; }
.freq { color:#c1121f; font-weight:bold; }
"""

def load():
    out = []
    for book, bname in BOOKS:
        files = sorted(glob.glob(os.path.join(FRAG, f"{book}_*.html")),
                       key=lambda f: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", os.path.basename(f))])
        for f in files:
            s = open(f).read()
            key = os.path.basename(f)[:-5]
            m = re.search(r'<h1 class="chap">(.*?)(?:<small>.*?</small>)?</h1>', s, re.S)
            title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else key
            items = re.findall(r'<div class="item" data-rank="([AB])" data-pdf="([\d,]+)" data-head="([^"]*)">(.*?)</div>\s*(?=<div class="item"|</section>)', s, re.S)
            out.append(dict(book=book, bname=bname, key=key, title=title, items=items))
    return out

def freq_label(sec):
    if sec["key"] in FREQ:
        ys = FREQ[sec["key"]].split()
        return f'出題実績 <span class="freq">{len(ys)}/10回</span>（{"・".join(ys)}）'
    for k, v in NOTE.items():
        if sec["key"].startswith(k): return v
    return "出題実績 0/10回"

def section_html(sec):
    a = sum(1 for x in sec["items"] if x[0] == "A"); b = len(sec["items"]) - a
    head = (f'<h1 class="chap">{sec["bname"]}｜{sec["title"]}'
            f'<small>重要度A {a}問／B {b}問｜{freq_label(sec)}</small></h1>'
            '<div class="spreadhead"><div>問題（解答を隠して書く）</div><div>解答（テキストの原文）</div></div>')
    rows = []
    for n, (rk, pdf, dh, body) in enumerate(sec["items"], 1):
        th = re.search(r'<div class="th">(.*?)</div>', body, re.S).group(1)
        q = re.search(r'(<div class="q">.*?</div>)', body, re.S).group(1)
        a_ = re.search(r'(<div class="a">.*?</div>)\s*<div class="pt">', body, re.S).group(1)
        pt = re.search(r'(<div class="pt">.*?</div>)\s*$', body, re.S)
        pt = pt.group(1) if pt else ""
        ron = f'<div class="ron"><b>見出し</b>{H.escape(H.unescape(dh))}</div>' if dh else ""
        th = f'<div class="th"><span class="rk rk{rk}">重要度{rk}</span><span class="no">問{n}</span>{th}</div>'
        rows.append(f'<div class="row"><div class="left">{ron}{th}{q}</div><div class="right">{a_}{pt}</div></div>')
    return head + "".join(rows)

def find_pages(doc, secs):
    pages = {}; texts = []
    for i in range(doc.page_count):
        big = "".join(sp["text"] for bl in doc[i].get_text("dict")["blocks"]
                      for l in bl.get("lines", []) for sp in l["spans"] if 14 < sp["size"] < 16)
        texts.append(re.sub(r"\s", "", big))
    cur = 0
    for s in secs:
        key = re.sub(r"\s", "", f'{s["bname"]}｜{s["title"]}')[:18]
        for i in range(cur, doc.page_count):
            if texts[i].startswith(key):
                pages[s["key"]] = i + 1; cur = i; break
    return pages

PLAN = [("11/1", "基本論点編1 第1〜2章", "監査総論・監査基準論・品質管理(3)"),
        ("11/2", "基本論点編1 第3章 第1〜4節", "監査実施論総論(7)・確認(4)・分析的手続・内部統制(3)"),
        ("11/3", "基本論点編1 第3章 第5〜9節", "リスクの識別と評価(7)・評価したリスクへの対応(5)・特別な検討を必要とするリスク・重要性"),
        ("11/4", "基本論点編1 第3章 第10〜14節", "虚偽表示の評価(4)・監査計画・監査調書・サンプリング(3)・会計上の見積り(8)"),
        ("11/5", "基本論点編1 第3章 第15〜17節＋対策編1 第1章 第1節", "経営者確認書(3)・特定項目(5)・項目別監査手続(10)"),
        ("11/6", "対策編1 第1章 第2〜7節", "関連当事者Ⅱ・後発事象Ⅱ・実査Ⅱ・立会Ⅱ・確認Ⅱ・不備事例"),
        ("11/7", "復習日", "1週目のA問題を2周目（書く）＋答案練習1"),
        ("11/8", "基本論点編2 第4章 第1〜7節", "報告書の基本形・除外事項・KAM・その他の記載内容(4)・追記情報(4)"),
        ("11/9", "基本論点編2 第4章 第8節・第5章・第6章 第1節", "グループ監査(5)・専門家(2)・内部監査人・継続企業"),
        ("11/10", "基本論点編2 第6章 第2〜8節", "不正(4)・不正リスク対応基準(6)・法令・監査役等(4)・内部統制の不備・交代(3)・関連当事者(2)"),
        ("11/11", "対策編1 第2章", "実務ガイダンス・実務指針（修了考査特有）"),
        ("11/12", "対策編2", "令和4〜7年改正"),
        ("11/13", "対策編3", "倫理規則・法規"),
        ("11/14", "総仕上げ", "×の付いたA問題を3周目＋2週目のA問題")]

def build(secs, pages=None):
    total = sum(len(s["items"]) for s in secs)
    ta = sum(1 for s in secs for x in s["items"] if x[0] == "A")
    plan = "".join(f"<tr><td>{d}</td><td>{r}</td><td>{t}</td></tr>" for d, r, t in PLAN)
    toc = []
    for book, bname in BOOKS:
        ss = [s for s in secs if s["book"] == book]
        if not ss: continue
        toc.append(f'<tr><td colspan="3"><b>{bname}</b></td></tr>')
        for s in ss:
            a = sum(1 for x in s["items"] if x[0] == "A")
            toc.append(f'<tr><td>　{s["title"]}</td><td class="c">A{a}・B{len(s["items"])-a}</td>'
                       f'<td class="n">{(pages or {}).get(s["key"], "")}</td></tr>')
    body = []
    for book, bname in BOOKS:
        ss = [s for s in secs if s["book"] == book]
        if not ss: continue
        body.append(f'<h1 class="part">{bname}</h1><div class="partsub">{len(ss)}節・{sum(len(s["items"]) for s in ss)}問</div>')
        body += [section_html(s) for s in ss]
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>監査論ドリル</title><style>{CSS}</style></head><body>
<h1 class="cover">監査論ドリル（監査に関する理論及び実務）</h1>
<div class="cover-sub">基本論点編1・2／修了考査対策編1〜3｜テキストの重要度〔Ａ〕〔Ｂ〕の見出しを全部問題化｜全{total}問（A{ta}・B{total-ta}）</div>
<div class="cover-wrap"><div class="lead"><b>使い方</b><br>
①見開き構成。左が問題、右が解答。右を隠して左だけ見て、答えを書く（Aは全文、Bは骨子）。<br>
②解答はテキストの文章そのまま。赤字の語句が書けていれば正解。書けなかった問に×を付ける。<br>
③×の問だけ、テキストの該当ページ（問の右上の印字ページ）に戻って前後の文脈を読む。<br>
④並びは教科書の記載順。各節の見出しに、修了考査での出題実績（平成28年〜令和7年の10回）を付けている。</div>
<div class="lead" style="background:#f4f4f4;border-color:#888"><b>重要度の意味（テキストの表示どおり）</b><br>
A＝テキストで〔Ａ〕の見出し。白紙に書けるまで。B＝〔Ｂ〕の見出し。骨子が書ければよい。〔Ｃ〕は収録していない。</div></div>
<h2 class="toc">2週間プラン（11/1〜11/14）</h2>
<table class="plan"><tr><th>日</th><th>範囲</th><th>主な論点（ ）は10回中の出題回数</th></tr>{plan}</table>
<div class="lead">毎日：その日の範囲の問題を解く → ×の問だけテキストに戻る → 寝る前に×の問をもう一度。復習日と最終日は×の問だけを回す。</div>
<h2 class="toc">目次</h2>
<table class="toc">{''.join(toc)}</table>
{''.join(body)}
<p class="foot">出典：CPA会計学院 修了考査対策講座2026 監査実務テキスト（基本論点編1・2、修了考査対策編1〜3）。出題実績は対策編1 序章①による。</p>
</body></html>"""

def render(html):
    open(OUT_HTML, "w").write(html)
    subprocess.run([B.CHROME, "--headless", "--disable-gpu", "--no-sandbox", f"--print-to-pdf={OUT_PDF}",
                    "--no-pdf-header-footer", OUT_HTML], check=True, capture_output=True)
    return pymupdf.open(OUT_PDF)

def main():
    secs = [s for s in load() if s["items"]]
    doc = render(build(secs)); pages = find_pages(doc, secs); doc.close()
    doc = render(build(secs, pages)); pages = find_pages(doc, secs)
    toc = [[1, "2週間プラン・目次", 2]]
    for book, bname in BOOKS:
        ss = [s for s in secs if s["book"] == book and s["key"] in pages]
        if not ss: continue
        toc.append([1, bname, max(1, pages[ss[0]["key"]] - 1)])
        for s in ss: toc.append([2, s["title"].replace("　", " "), pages[s["key"]]])
    doc.set_toc(toc)
    B.stamp_page_numbers(doc)
    tmp = OUT_PDF + ".tmp"; doc.save(tmp, garbage=3, deflate=True); doc.close(); os.replace(tmp, OUT_PDF)
    n = sum(len(s["items"]) for s in secs)
    print(f"sections {len(secs)} items {n} pages {pymupdf.open(OUT_PDF).page_count} outline {len(toc)} size {os.path.getsize(OUT_PDF)/1e6:.1f}MB")

if __name__ == "__main__":
    main()
