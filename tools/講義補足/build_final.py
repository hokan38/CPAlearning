"""書込済PDFに「章頭の講義スライド」と「章末の講義補足ページ」を綴じ込む。

- 講義スライド: slides/画面集_第NN章.pdf を各章の先頭に挿入
- 講義補足ページ: extra_chNN.json (JSONL: {"ref": "5-13", "text": "..."}) を
  各章の末尾に新規ページとして追加(教科書に記載のない講師の発言集)

使い方: python3 build_final.py
"""
import json
import os

import pymupdf

RED = (0.82, 0.05, 0.05)
INK = (0.12, 0.12, 0.12)
GRAY = (0.45, 0.45, 0.48)
F = "japan"

SC = "/tmp/claude-0/-home-user-CPAlearning/420f084b-6e14-58f9-864c-854f5c1df534/scratchpad"

# (書込済PDF, 出力, {章: (章開始ページ, 章終了ページ)})  ページは1-based
BOOKS = [
    (f"{SC}/会計実務_テキスト1_書込済_v2.pdf",
     f"{SC}/会計実務_テキスト1_完全版.pdf",
     {1: (10, 21), 2: (22, 45), 3: (46, 69), 4: (70, 105), 5: (106, 154)}),
    (f"{SC}/会計実務_テキスト2_書込済.pdf",
     f"{SC}/会計実務_テキスト2_完全版.pdf",
     {6: (6, 39), 7: (40, 70)}),
    (f"{SC}/会計実務_テキスト3_書込済.pdf",
     f"{SC}/会計実務_テキスト3_完全版.pdf",
     {8: (12, 21), 9: (22, 35), 10: (36, 51), 11: (52, 63), 12: (64, 71),
      13: (72, 79), 14: (80, 115), 15: (116, 127), 16: (128, 137), 17: (138, 145),
      18: (146, 167), 19: (168, 181), 20: (182, 225), 21: (226, 235),
      22: (236, 259), 23: (260, 267), 24: (268, 304)}),
]

CH_TITLE = {
    1: "イントロダクション", 2: "制度会計総論", 3: "ＩＦＲＳ総論", 4: "開示関連論点",
    5: "法人税等・税効果会計", 6: "連結財務諸表", 7: "企業結合・事業分離等",
    8: "有形固定資産・投資不動産", 9: "無形資産", 10: "固定資産の減損",
    11: "リース（現行基準）", 12: "棚卸資産", 13: "時価の算定", 14: "金融商品",
    15: "外貨換算", 16: "引当金・偶発債務", 17: "資産除去債務", 18: "退職給付",
    19: "株式報酬", 20: "収益認識", 21: "期中財務諸表", 22: "注記関連論点",
    23: "その他の事項", 24: "リース（新基準）",
}


def load_extra(ch):
    path = f"{SC}/extra_ch{ch:02d}.json"
    if not os.path.exists(path):
        return []
    raw = open(path, encoding="utf-8").read().strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
    except json.JSONDecodeError:
        data = []
        for line in raw.splitlines():
            s = line.strip().rstrip(",")
            if s.startswith("{"):
                try:
                    data.append(json.loads(s))
                except json.JSONDecodeError:
                    pass
    out = []
    for d in data:
        t = (d.get("text") or "").strip()
        if t:
            out.append((str(d.get("ref") or "").strip(), t))
    return out


def make_supplement_pages(doc, ch, items, w, h):
    """補足ページを doc の末尾に作り、作ったページ番号のリストを返す。"""
    made = []
    ml, mr, mt, mb = 42, 40, 52, 44
    fs = 9.2
    lh = fs * 1.42
    ref_w = 66  # ページ参照欄の幅
    gap = 7     # 項目間の余白

    page = None
    y = 0

    def new_page(cont=False):
        nonlocal page, y
        page = doc.new_page(width=w, height=h)
        made.append(page.number)
        title = f"第{ch}章 {CH_TITLE.get(ch, '')} ／ 講義補足（教科書に記載のない講師の発言）"
        if cont:
            title += "（続き）"
        page.insert_text((ml, mt - 22), title, fontname=F, fontsize=10.5, color=RED)
        page.draw_line((ml, mt - 14), (w - mr, mt - 14), color=RED, width=0.8)
        page.insert_text((ml, h - 24), "※ 教科書本文に記載のある内容は省いている（講義音声より）",
                         fontname=F, fontsize=7.5, color=GRAY)
        y = mt

    scratch = pymupdf.open()

    def measure(text, y_top):
        """実際には描かずに使用高さを測る。入りきらなければ None。"""
        rect = pymupdf.Rect(ml + ref_w, y_top, w - mr, h - mb)
        if rect.height < lh:
            return None
        sp = scratch.new_page(width=w, height=h)
        rc = sp.insert_textbox(rect, text, fontname=F, fontsize=fs,
                               color=INK, lineheight=1.42, align=0)
        scratch.delete_page(sp.number)
        return None if rc < 0 else rect.height - rc

    def draw(text, y_top):
        used = measure(text, y_top)
        if used is None:
            return None
        rect = pymupdf.Rect(ml + ref_w, y_top, w - mr, h - mb)
        page.insert_textbox(rect, text, fontname=F, fontsize=fs,
                            color=INK, lineheight=1.42, align=0)
        return used

    new_page()
    for ref, text in items:
        used = draw(text, y)
        if used is None:
            new_page(cont=True)
            used = draw(text, y)
            if used is None:  # 1ページに収まらない長文は縮小して強制描画
                rect = pymupdf.Rect(ml + ref_w, y, w - mr, h - mb)
                page.insert_textbox(rect, text, fontname=F, fontsize=fs - 1.2,
                                    color=INK, lineheight=1.35, align=0)
                used = rect.height
        if ref:
            page.insert_text((ml, y + fs), f"p.{ref}", fontname=F, fontsize=8.4, color=RED)
        y += used + gap
    return made


def main():
    for src, out, chmap in BOOKS:
        base = pymupdf.open(src)
        w, h = base[0].rect.width, base[0].rect.height

        # 各章の補足ページを一時ドキュメントに作る
        supp = pymupdf.open()
        supp_range = {}
        for ch in sorted(chmap):
            items = load_extra(ch)
            if not items:
                continue
            start = supp.page_count
            make_supplement_pages(supp, ch, items, w, h)
            supp_range[ch] = (start, supp.page_count - 1)

        ndoc = pymupdf.open()
        cursor = 0  # base の 0-based 位置
        for ch in sorted(chmap):
            cs, ce = chmap[ch]
            # 章開始前の本文
            if cs - 1 > cursor:
                ndoc.insert_pdf(base, from_page=cursor, to_page=cs - 2)
            # 章頭に講義スライド
            sl_path = f"{SC}/slides/画面集_第{ch:02d}章.pdf"
            if os.path.exists(sl_path):
                sl = pymupdf.open(sl_path)
                first = ndoc.page_count
                ndoc.insert_pdf(sl)
                for i in range(first, ndoc.page_count):
                    ndoc[i].insert_text(
                        (14, 16),
                        f"■ 講義スライド（画面集） 第{ch}章 — この先の教科書ページに対応",
                        fontname=F, fontsize=9, color=RED)
                sl.close()
            # 章本文
            ndoc.insert_pdf(base, from_page=cs - 1, to_page=ce - 1)
            # 章末に補足ページ
            if ch in supp_range:
                s0, s1 = supp_range[ch]
                ndoc.insert_pdf(supp, from_page=s0, to_page=s1)
            cursor = ce
        if cursor < base.page_count:
            ndoc.insert_pdf(base, from_page=cursor, to_page=base.page_count - 1)

        ndoc.save(out, garbage=3, deflate=True)
        print(f"{os.path.basename(out)}: {base.page_count} → {ndoc.page_count} pages")
        supp.close()
        base.close()
        ndoc.close()


if __name__ == "__main__":
    main()
