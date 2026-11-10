"""監査の流れ（1ページ目＝A3の監基報マップ）＋段階ごとの論点一覧（2ページ目以降）を1つのPDFにする。
使い方: python3 -I build_flow_issues.py <問題集の問題JSON> <論点名JSON> <問題集PDF>
論点＝問題集（基準編）の各問題、テキスト掲載の過去問、答練第1回・第3回、問題集の事例問題。"""
import json, os, re, sys, subprocess, html as H
import pymupdf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "kaikei", "drill"))
import build_all as B
QS, LB, MQ = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), pymupdf.open(sys.argv[3])
OUT = os.path.join(HERE, "財務諸表監査の流れ_監基報マップ.pdf")

# 問題集の基準区分（PDF開始ページ, 表示名, 重要性）
DOCS = [(9, "品基報1 事務所における品質管理", "B"), (11, "220 監査業務における品質管理", "B"), (14, "230 監査調書", "B"),
    (15, "240 財務諸表監査における不正", "A"), (21, "260 監査役等とのコミュニケーション", "B"), (24, "315 重要な虚偽表示リスクの識別と評価", "A"),
    (31, "315実ガ1 ITの利用の理解（Q&A）", "B"), (33, "320 監査の計画及び実施における重要性", "B"), (34, "330 評価したリスクに対応する監査人の手続", "A"),
    (39, "450 監査の過程で識別した虚偽表示の評価", "B"), (42, "500 監査証拠", "A"), (43, "500実指1 イメージ文書", "B"), (46, "500周知3 PDF証憑の真正性", "B"),
    (47, "501 特定項目の監査証拠", "A"), (49, "501実指1 顧問弁護士への質問書", "B"), (50, "505 確認", "A"), (52, "505周知2 ウェブサイトを用いた確認", "B"),
    (53, "510 初年度監査の期首残高", "B"), (54, "520 分析的手続", "B"), (56, "530 監査サンプリング", "B"), (57, "540 会計上の見積りの監査", "A"),
    (60, "540実ガ2 工事契約等の収益認識", "B"), (63, "550 関連当事者", "B"), (65, "560 後発事象", "A"), (67, "560実指1・2 後発事象の取扱い／訂正報告書", "B"),
    (70, "570 継続企業", "B"), (73, "580 経営者確認書", "B"), (75, "600 グループ監査", "B"), (80, "610 内部監査人の作業の利用", "B"),
    (82, "620 専門家の業務の利用", "B"), (84, "700 意見の形成と監査報告", "B"), (87, "701 KAM", "A"), (89, "706 強調事項・その他の事項", "B"),
    (91, "710 過年度の比較情報", "B"), (93, "720 その他の記載内容", "A"), (96, "900 監査人の交代", "B"), (98, "内基報1 内部統制監査", "B"), (100, "期レ報1 期中レビュー", "B")]
STAGE_OF = {"品基報1": 0, "220": 0, "900": 0, "510": 0, "320": 1, "315": 2, "315実ガ1": 2, "240": 2, "550": 2,
    "330": 3, "500": 3, "500実指1": 3, "500周知3": 3, "501": 3, "501実指1": 3, "505": 3, "505周知2": 3, "520": 3, "530": 3, "540": 3, "540実ガ2": 3,
    "600": 3, "610": 3, "620": 3, "450": 4, "560": 4, "560実指1・2": 4, "570": 4, "580": 4, "260": 4, "230": 4,
    "700": 5, "701": 5, "706": 5, "710": 5, "720": 5, "内基報1": 5, "期レ報1": 5}
STAGES = [("⓪ 契約・準備", "#6c757d"), ("① 監査計画", "#2a6f97"), ("② リスク評価", "#7b2cbf"), ("③ リスク対応", "#c1121f"), ("④ 評価・完了", "#b5651d"), ("⑤ 意見・報告", "#1d3557")]
# 本番（テキスト掲載の過去問）・答練・事例問題で出た論点
EXAM = {
 0: [("答練1", "監査人の交代の懸念（理由とともに）"), ("答練1", "交代時に必要となる書類等の内容"), ("答練1", "前任監査人が閲覧の対象外にできる監査調書の例（2つ）")],
 1: [("答練1", "重要性の基準値・手続実施上の重要性を前提に、修繕費の手続実施方針の不適切な点を理由とともに指摘")],
 2: [("過去問 R3", "減損：本社費の配分で考えられる不正とその対応手続"), ("過去問 R3", "減損の兆候の例と、不正による重要な虚偽表示リスク（序章）"),
     ("過去問 R4", "循環取引：正常な取引か判断するために理解すべき事項（2つ）"),
     ("答練3", "特別な検討を必要とするリスクへの監査上の対応（3つ）"), ("答練3", "収益認識が特別な検討を必要とするリスクとなる理由"),
     ("答練3", "収益認識で最も重要なアサーション（理由とともに）と対応手続"), ("答練3", "経営者による内部統制の無効化が全企業でリスクとなる理由"),
     ("答練3", "不正な財務報告の「動機・プレッシャー」の例（2つ）"), ("答練3", "事例から識別すべきリスクと対応手続"),
     ("事例問題", "問題1〜3 不正・循環取引／問題4 リスクの識別と評価／問題5〜7 特別な検討を必要とするリスク／問題17 IT")],
 3: [("過去問 R3", "売上債権の確認：残高に加えて確認対象に含めるべき内容（入金消込）"), ("過去問 R6", "滞留在庫の評価"),
     ("過去問 R6", "会計上の見積りのリスク対応手続の3つのアプローチ（序章）"), ("過去問 R3", "減損：使用価値の割引率の検証で考えられるリスク"),
     ("過去問 R3", "売上割戻しの検証で検討すべき事項と実証手続"), ("過去問 R5", "不適切な売上計上を発見する実証手続"),
     ("過去問 R5", "アサーションに適合した監査手続（語群から）"), ("過去問 R5", "実地棚卸の立会が必要な理由・立会で実施しなければならない手続（2つ）"),
     ("過去問 R5", "期末日前の実地棚卸と立会後の手続"), ("過去問 R2", "確認状の発送除外の依頼と確認差異への対応"),
     ("過去問 R3", "未回収の確認状の代替的な手続、意見表明までに終わらない場合の対応"),
     ("答練1", "修繕費：期間帰属・分類の妥当性で留意すべき事項"), ("答練1", "監査サンプリングと特定項目抽出の相違（虚偽表示を発見した場合）"),
     ("答練1", "サンプリングで合理的な基礎が得られない場合の対応"), ("答練1", "専門家の利用：必要性が高まる例（2つ）・業務が不適切な場合の手続（2つ）"),
     ("答練1", "会社の判断の妥当性を検証する手続（3つ）"), ("答練1", "グループ監査：方針の妥当性・重要性等の2項目・構成単位の監査人への報告依頼事項（3つ）"),
     ("答練3", "棚卸資産：網羅性の手続（2つ）・その理由・カット・オフ情報の目的・期末評価の検討事項・追加手続"),
     ("答練3", "アサーションに適合した監査手続（語群から）"),
     ("不備事例", "前年度の会計上の見積りの検討（資産除去債務・製品保証引当金）"),
     ("事例問題", "問題8〜10 会計上の見積り／問題11〜13 特定項目・項目別監査手続／問題14 確認")],
 4: [("答練1", "監査役等とのコミュニケーション：記載に含める事項（2つ）・会計実務の質的側面（2つ）"),
     ("答練3", "経営者確認書：経営者の責任に関する確認事項（3つ）・相談への回答・無形固定資産の記載内容・未修正の虚偽表示の記載・確認が得られない場合の対応（2つ）"),
     ("対策編1", "訂正報告書：監査契約を締結する場合・解除する場合、監査人が交代している場合の留意事項"),
     ("事例問題", "問題15 訂正報告書に含まれる財務諸表等の監査／問題16 継続企業の前提")],
 5: [("過去問 R4", "その他の記載内容：会社の説明を検討するための手続（3つ）（序章）"),
     ("答練1", "グループ監査で構成単位の監査人の利用を監査報告書に記載することの適否"),
     ("答練3", "KAMとはどのようなものか・利用者の正しい理解のための留意事項（2つ）"),
     ("答練3", "その他の記載内容の一部が監査報告書日までに入手できない場合の対応")],
}
def doc_of(page):
    cur = DOCS[0]
    for d in DOCS:
        if d[0] <= page: cur = d
    return cur
# 問題番号 → PDFページ
qpage = {}
for p in range(9, 101):
    t = re.sub(r"\s", "", MQ[p - 1].get_text())
    for m in re.finditer(r"問題(\S{1,8}?[\-－][0-9]+)", t): qpage.setdefault(m.group(1).replace("－", "-"), p)
rows = {i: {} for i in range(6)}
for qid, q in QS:
    p = qpage.get(qid.replace("－", "-"))
    d = doc_of(p) if p else None
    if not d: continue
    key = d[1].split(" ")[0]
    rows[STAGE_OF[key]].setdefault(d, []).append((qid, LB.get(qid, q[:40]), p))
CSS = """@page { size: 297mm 210mm; margin: 9mm 11mm; } body { font-family:"Noto Sans CJK JP",sans-serif; font-size:9.3pt; line-height:1.42; color:#222; margin:0; }
.pg { break-before:page; } h2 { font-size:15pt; margin:0 0 5pt; color:#fff; background:var(--c); padding:3pt 9pt; border-radius:4pt; }
h2 small { font-size:9pt; font-weight:normal; margin-left:8pt; }
.ex { border:1.4pt solid var(--c); border-radius:4pt; padding:4pt 8pt; margin-bottom:6pt; background:#fffdf6; }
.ex .h { font-weight:bold; color:var(--c); font-size:10.5pt; margin-bottom:2pt; } .ex ul { margin:0; padding-left:12pt; columns:2; column-gap:16pt; } .ex li { margin:1pt 0; break-inside:avoid; }
.tag { display:inline-block; font-size:8pt; font-weight:bold; color:#fff; border-radius:2pt; padding:0 4pt; margin-right:4pt; }
.t-k { background:#c1121f; } .t-a { background:#2a6f97; } .t-j { background:#555; } .t-f { background:#b5651d; }
.grid { display:grid; grid-template-columns:repeat(3,1fr); gap:6pt 10pt; align-items:start; } .sd { break-inside:avoid; border:0.8pt solid #ccc; border-left:3.5pt solid var(--c); border-radius:3pt; padding:3pt 6pt; background:#fafafa; }
.sd .h { font-weight:bold; font-size:10pt; } .sd .h .r { color:#c1121f; font-size:8.5pt; margin-left:4pt; } .sd .h .p { color:#888; font-weight:normal; font-size:8pt; margin-left:4pt; }
.sd ol { margin:1pt 0 0; padding-left:0; list-style:none; } .sd li { margin:1pt 0; } .sd li .n { color:#888; font-size:8pt; display:inline-block; min-width:40pt; }
.lg { font-size:8pt; color:#666; margin:0 0 4pt; }"""
def stage_html(i):
    name, c = STAGES[i]
    ex = "".join(f'<li><span class="tag {"t-k" if s.startswith("過去問") else "t-a" if s.startswith("答練") else "t-f" if s.startswith("不備") or s.startswith("対策") else "t-j"}">{H.escape(s)}</span>{H.escape(t)}</li>' for s, t in EXAM[i])
    sds = []
    for d in sorted(rows[i], key=lambda x: x[0]):
        items = "".join(f'<li><span class="n">{H.escape(q)}</span>{H.escape(l)}</li>' for q, l, p in rows[i][d])
        sds.append(f'<div class="sd"><div class="h">{H.escape(d[1])}<span class="r">重要性{d[2]}</span><span class="p">問題集 p.{d[0]}〜</span></div><ol>{items}</ol></div>')
    return (f'<div class="pg" style="--c:{c}"><h2>{name}<small>この段階で問われた・問われうる論点</small></h2>'
            f'<div class="ex"><div class="h">本番・答練で実際に出た論点</div><ul>{ex}</ul></div>'
            f'<div class="lg">問題集（基準編）の論点：監基報ごとに問題番号つき。重要性は問題集の目次の表示。</div><div class="grid">{"".join(sds)}</div></div>')
html = f'<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}</style></head><body>' + "".join(stage_html(i) for i in range(6)) + "</body></html>"
open(os.path.join(HERE, "_issues.html"), "w").write(html)
def pdf(src, dst):
    subprocess.run([B.CHROME, "--headless", "--disable-gpu", "--no-sandbox", f"--print-to-pdf={dst}", "--no-pdf-header-footer", src], check=True, capture_output=True)
pdf(os.path.join(HERE, "page1_a3.html"), os.path.join(HERE, "_p1.pdf")); pdf(os.path.join(HERE, "_issues.html"), os.path.join(HERE, "_p2.pdf"))
doc = pymupdf.open(os.path.join(HERE, "_p1.pdf")); n1 = doc.page_count; d2 = pymupdf.open(os.path.join(HERE, "_p2.pdf")); doc.insert_pdf(d2)
toc = [[1, "全体図（監基報マップ）", 1]]
for i, (name, c) in enumerate(STAGES):
    for p in range(d2.page_count):
        if d2[p].get_text().strip().startswith(name): toc.append([1, f"{name} の論点", n1 + p + 1]); break
doc.set_toc(toc); doc.save(OUT, garbage=3, deflate=True)
for f in ("_p1.pdf", "_p2.pdf", "_issues.html"): os.remove(os.path.join(HERE, f))
print(OUT, doc.page_count, "pages; toc", toc, "; 問題数", sum(len(v) for r in rows.values() for v in r.values()))
