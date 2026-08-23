"""経営実務(IT)の完成版を組む。

書込済PDF(赤ペン+講師インク統合済み)に、講義の配布資料を対応位置へ綴じ込む:
- 初回ガイダンス → 巻頭(第1章の直前)
- 第1〜3回まとめ(注釈済み) → 各回が扱った章の直後
- 第2回の画面イメージ2枚 → 第9章 情報処理統制の直前
- 過去問(本試験問題) → 巻末

使い方: python3 build_keiei_final.py
"""
import os

import pymupdf

SC = os.path.dirname(os.path.abspath(__file__))
RED = (0.82, 0.05, 0.05)
F = "japan"

SRC = f"{SC}/経営実務_IT_書込済.pdf"
OUT = f"{SC}/経営実務_IT_講義反映版.pdf"

# (挿入する元PDF, 挿入先=このページの直後(1-based, 0なら巻頭), バナー文言)
INSERTS = [
    (f"{SC}/guid_annot.pdf", 4,
     "■ 講義資料 初回ガイダンス（青柳講師）"),
    (f"{SC}/sum1_annot.pdf", 33,
     "■ 講義資料 第1回まとめ（第1〜3章の全体像）"),
    (f"{SC}/keiei_pdf/IT_第2回_営業管理画面.pdf", 124,
     "■ 講義資料 営業管理システムの画面イメージ（第9章の説明で使用）"),
    (f"{SC}/keiei_pdf/IT_第2回_経理仕訳画面.pdf", 124,
     "■ 講義資料 経理仕訳作成システムの画面イメージ（第9章の説明で使用）"),
    (f"{SC}/sum2_annot.pdf", 95,
     "■ 講義資料 第2回まとめ（第5〜7章の流れ）"),
    (f"{SC}/sum3_annot.pdf", 151,
     "■ 講義資料 第3回まとめ（第8〜9章の流れ）"),
    (f"{SC}/keiei_pdf/IT_過去問.pdf", 216,
     "■ 参考資料 本試験問題（監査に関する理論及び実務 第三問・第四問）"),
]


def main():
    base = pymupdf.open(SRC)
    ins = {}
    for path, after, banner in INSERTS:
        if os.path.exists(path):
            ins.setdefault(after, []).append((path, banner))
        else:
            print("  skip (not found):", os.path.basename(path))

    ndoc = pymupdf.open()
    ow = base[0].rect.width

    def add(path, banner):
        d = pymupdf.open(path)
        first = ndoc.page_count
        ndoc.insert_pdf(d)
        for i in range(first, ndoc.page_count):
            p = ndoc[i]
            # 教科書と同じ幅に揃っていない資料もあるので左上に赤バナー
            p.insert_text((14, 16), banner, fontname=F, fontsize=9, color=RED)
        d.close()

    for path, banner in ins.get(0, []):
        add(path, banner)
    for p in range(1, base.page_count + 1):
        ndoc.insert_pdf(base, from_page=p - 1, to_page=p - 1)
        for path, banner in ins.get(p, []):
            add(path, banner)

    tmp = OUT + ".tmp"
    ndoc.save(tmp, garbage=4, deflate=True, clean=True)
    ndoc.close()
    d = pymupdf.open(tmp)
    d.save(OUT, garbage=4, deflate=True, clean=True)
    print(f"{os.path.basename(OUT)}: {base.page_count} → {d.page_count} pages, "
          f"{os.path.getsize(OUT)/1e6:.1f} MB")
    d.close()
    os.remove(tmp)
    base.close()


if __name__ == "__main__":
    main()
