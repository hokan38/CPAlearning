import sys, re, json, html
SRC_PDF, PREV_FRAG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
exec(open("build_items.py").read().split("digest = segment")[0].replace("d = pymupdf.open(sys.argv[1])", "d = pymupdf.open(SRC_PDF)"))
det = segment(rows(range(4, 11)), detail=True)
assert len(det) == 29, len(det)

SUM = [
 (["のれんの規則的償却を行わない"], ["のれんの規則的償却を行う"]),
 (["リサイクリングが禁止される"], ["リサイクリングを行う"]),
 (["一定の要件を満たした開発費用は資産計上する"], ["研究開発費は発生時に全額費用処理する"]),
 (["投資不動産…公正価値モデル or 原価モデル", "有形固定資産…原価モデル or 再評価モデル"], ["いずれも取得原価により評価する"]),
 (["（ＯＣＩオプションを選択した資本性金融商品について）リサイクリングが禁止される"], ["（時価評価差額をその他の包括利益としたその他有価証券について）リサイクリングを行う"]),
 (["新株の発行等に係る費用…資本から控除する", "自己株式に関する付随費用…純損益に含めず資本に直接認識する（ex.取得費用…自己株式の取得原価）"], ["営業外費用として処理する", "（株式交付費は繰延資産計上が認められる）"]),
 (["会計上の見積りの変更"], ["会計方針の変更を会計上の見積りの変更と区別することが困難な場合"]),
 (["回収可能価額が帳簿価額を下回っている場合"], ["割引前将来キャッシュ・フローが帳簿価額を下回っている場合"]),
 (["のれんを除き戻入れを行う"], ["戻入れを行わない"]),
 (["現在の義務であることが求められる"], ["現在の義務であることは求められない"]),
 (["給付算定式基準"], ["給付算定式基準 or 期間定額基準"]),
 (["購入のれん方式 or 全部のれん方式"], ["購入のれん方式"]),
 (["（他と同様に）資産負債法に基づく処理"], ["（例外的に）繰延法に基づく処理"]),
 (["一定の要件を満たした資産に係る借入コストは取得原価に算入する"], ["自家建設で取得した固定資産に限り，借入資本利子を取得原価に含めることが容認される"]),
 (["資産を細分化して減価償却することを求められる場合がある"], ["減価償却の最小単位は個々の資産とされる"]),
 (["（例外的に）減損の兆候の有無を問わず，毎年減損テストを実施する"], ["（他と同様に）減損の兆候がある場合に減損損失の認識の判定を行う"]),
 (["期末日現在の割引率"], ["負債計上時の割引率"]),
 (["純損益に認識する"], ["その他の包括利益とする（連結）"]),
 (["積立超過額の資産計上に上限が設けられている"], ["積立超過額の資産計上に制限はない"]),
 (["新株予約権の戻入れによる利益計上は行わない"], ["新株予約権の戻入れによる利益計上を行う"]),
 (["非支配持分がマイナスになっても負担させる"], ["通常，非支配株主持分はゼロが下限となる"]),
 (["支配喪失日の公正価値"], ["個別財務諸表上の帳簿価額"]),
 (["購入原価から控除"], ["営業外収益として処理"]),
 (["繰延収益処理 or 直接減額処理"], ["直接減額方式 or 積立金方式"]),
 (["有給休暇引当金の計上が行われる"], ["有給休暇引当金は計上されない"]),
 (["金融資産は次の３分類", "・事後に償却原価で測定（ＡＣ）", "・その他の包括利益を通じて公正価値で測定（ＦＶＯＣＩ）", "・純損益を通じて公正価値で測定（ＦＶＰＬ）"],
  ["有価証券は次の４分類", "・売買目的有価証券", "・満期保有目的の債券", "・子会社株式及び関連会社株式", "・その他有価証券"]),
 (["（他の資本性金融商品と同様に）公正価値"], ["取得原価"]),
 (["ヘッジ関係は次の３分類", "・公正価値ヘッジ", "・キャッシュ・フロー・ヘッジ", "・在外営業活動体に対する純投資のヘッジ"], ["ヘッジ会計の方法は次の２つ", "・繰延ヘッジ", "・時価ヘッジ"]),
 (["為替予約の振当処理や金利スワップの特例処理は認められない"], ["一定の要件を満たす場合には，為替予約の振当処理や金利スワップの特例処理が認められる"]),
]
nos = lambda s: re.sub(r"\s", "", s)

def strip_summary(rows_, summ):
    target = nos("".join(summ)); acc = ""; i = 0
    while i < len(rows_) and len(nos(acc)) < len(target):
        acc += rows_[i]; i += 1
    assert nos(acc).startswith(target[:len(nos(acc))][:10]) and nos(acc) == target, (nos(acc), target)
    return "".join(rows_[i:])

def body_html(text):
    text = text.strip()
    if not text: return ""
    # 条文ごとに分ける（「（基準名…）。」の直後で区切る）
    parts = re.split(r"(?<=）。)(?=.)", text)
    out = []
    for p in parts:
        p = html.escape(p)
        p = re.sub(r"(?<!^)([①②③④⑤])", r"<br>\1", p)
        out.append(f"<li>{p}</li>")
    return "<ul>" + "".join(out) + "</ul>"

items = []
for k, dt in enumerate(det):
    isum, jsum = SUM[k]
    ib = strip_summary(dt["ifrs"], isum)
    jb = strip_summary(dt["jp"], jsum)
    items.append({"name": dt["name"], "isum": isum, "jsum": jsum, "ib": ib, "jb": jb, "cm": dt["comment"]})

# 前版から問題文と見出しを取得
prev = open(PREV_FRAG).read()
prev_items = re.findall(r'<div class="th">([SABC]-\d+)　([^<]*)</div>\s*<div class="q">(.*?)</div>', prev, re.S)
labels = [p for p in prev_items]
order = list(range(0, 5)) + list(range(5, 13)) + list(range(13, 22)) + ["B10"] + list(range(22, 29))
assert len(labels) == len(order) == 30

NOTES = {
 "S": "実務対応報告第18号「連結財務諸表作成における在外子会社等の会計処理に関する当面の取扱い」で列挙されている５項目は，「ＩＦＲＳに準拠した会計処理が日本基準に共通する考え方と乖離するものであり，一般に当該差異に重要性がある」とされているものであり，最優先で押さえなければならない。",
 "A": "ＩＦＲＳと日本基準との主要な差異の中には，教材や講義で触れられているため，実は既に知っているというものが少なくない。これらの項目について，日本基準に基づく会計処理を学習する際に対比する形で説明されるのがＩＦＲＳの取扱いである。いずれも重要なものであるため，優先的に押さえたい。",
 "B": "ここでは，日本基準の会計処理と対比されることは多くはないものの，決して軽微とはいえない差異が存在するＩＦＲＳの会計処理を確認する。教材や講義の中で触れられているものもあれば，そうではないものもあるが，ここまでの範囲は知識として頭に入れておきたい。",
 "C": "ＩＦＲＳと日本基準との差異は細部まで含めるとかなりの量があるが，本対照表に掲載しているのは主要な差異のみである。このうち，広く知られているとはいえないものをここで確認する。興味があったら眺める程度の取扱いで構わない。",
}
HEAD = {
 "S": ('<section class="chap" id="tierS">\n<h1 class="chap">Tier S　最優先の5差異<small>実務対応報告第18号の5項目</small></h1>\n', '<h2>Tier S<span>白紙に「IFRS／日本基準」の要旨と解説が書けるまで</span></h2>\n'),
 "A": ('<section class="chap" id="tierA">\n<h1 class="chap">Tier A　教材・講義で対比済みの8差異<small>優先的に押さえる</small></h1>\n', '<h2>Tier A<span>要旨と解説が書けるまで</span></h2>\n'),
 "B": ('<section class="chap" id="tierB">\n<h1 class="chap">Tier B　軽微とはいえない9差異＋総合問題<small>知識として頭に入れておく</small></h1>\n', '<h2 class="b">Tier B<span>要旨が言えるまで</span></h2>\n'),
 "C": ('<section class="chap" id="tierC">\n<h1 class="chap">Tier C　広く知られていない7差異<small>眺める程度で可</small></h1>\n', '<h2 class="c">Tier C<span>要旨（IFRS／日本基準）だけ言えればよい</span></h2>\n'),
}

def block(cls, tag, summ, body):
    s = "<br>".join(html.escape(x) for x in summ)
    return f'<div class="std {cls}"><span class="tag">{tag}</span><b>{s}</b>{body_html(body)}</div>\n'

out = []; cur = None
for (lab, title, q), src in zip(labels, order):
    tier = lab[0]
    if tier != cur:
        if cur: out.append("</section>\n\n")
        out.append(HEAD[tier][0]); out.append(f'<p class="tiernote">{NOTES[tier]}</p>\n'); out.append(HEAD[tier][1]); cur = tier
    out.append(f'<div class="item"><div class="th">{lab}　{title}</div>\n<div class="q">{q}</div>\n<div class="a"><span class="l">解答例</span>\n')
    if src == "B10":
        rows_ = "".join(f'<tr><td>{html.escape(items[i]["name"])}</td><td>{"<br>".join(map(html.escape, items[i]["isum"]))}</td><td>{"<br>".join(map(html.escape, items[i]["jsum"]))}</td></tr>' for i in range(5))
        out.append(f'<table class="cmp"><tr><th>項目</th><th>ＩＦＲＳ</th><th>日本基準</th></tr>{rows_}</table>\n')
        out.append(f'<p class="why"><b>解説</b>{NOTES["S"]}</p>\n')
    else:
        it = items[src]
        out.append(block("ifrs", "ＩＦＲＳ", it["isum"], it["ib"]))
        out.append(block("jp", "日本基準", it["jsum"], it["jb"]))
        out.append(f'<p class="why"><b>解説</b>{html.escape(it["cm"])}</p>\n')
    out.append('</div></div>\n\n')
out.append("</section>\n")
open(OUT, "w").write("".join(out))
json.dump(items, open("items_final.json", "w"), ensure_ascii=False, indent=1)
print("written", OUT)
