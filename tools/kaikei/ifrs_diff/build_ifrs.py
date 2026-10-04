"""会計基準差異対照表(IFRS-JGAAP)の論述ドリルを見開きPDFにする。"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drill"))
import build_all as B
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "ifrs_drill.html")
OUT_PDF = os.path.join(HERE, "会計基準差異対照表_論述ドリル.pdf")

def main():
    frag = open(os.path.join(HERE, "frag_ifrs.html")).read()
    n = len(re.findall(r'<div class="item">', frag))
    body = B.to_spread(frag)
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>会計基準差異対照表 論述ドリル</title><style>{B.CSS}</style></head><body>
<h1 class="cover">会計基準差異対照表 論述ドリル</h1>
<div class="cover-sub">IFRSと日本基準との主要な差異｜CPA会計学院 補助教材（令和7年12月）準拠｜Tier S・A・B 全{n}問</div>
<div class="cover-wrap"><div class="lead"><b>使い方</b><br>
⓪見開き構成。左ページが問題、右ページが解答例。右を隠して左だけ読み、書いてから右を開く。<br>
①答案は必ず「IFRS＝○○／日本基準＝○○／理由（考え方の違い）」の3点で書く。基準番号は書けなくてよい。<br>
②Tier Sの5つは実務対応報告18号の修正5項目そのもの。連結の問題で「修正の要否」を問われたときはB-10で確認する。<br>
③Tier Cの7項目（仕入割引、補助金、有給休暇引当金、金融資産の3分類、市場価格のない株式、ヘッジの分類、振当処理・特例処理）は原本では「眺める程度」とされているため収録していない。</div></div>
{body}
<p class="foot">出典：CPA会計学院「財務会計論 補助教材 会計基準差異対照表」（令和7年12月27日）。解答例の基準番号は同資料の記載による。</p>
</body></html>"""
    open(OUT_HTML, "w").write(html)
    subprocess.run([B.CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    f"--print-to-pdf={OUT_PDF}", "--no-pdf-header-footer", OUT_HTML], check=True, capture_output=True)
    d = pymupdf.open(OUT_PDF)
    B.stamp_page_numbers(d)
    d.save(OUT_PDF + ".tmp", garbage=3, deflate=True); d.close(); os.replace(OUT_PDF + ".tmp", OUT_PDF)
    d = pymupdf.open(OUT_PDF)
    print("items", n, "pages", d.page_count, "MB", round(os.path.getsize(OUT_PDF)/1e6, 2))

if __name__ == "__main__":
    main()
