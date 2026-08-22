"""完全版v3: 書込済v4(バッジ無し・軽い過去問解答は本文余白に記載済み)に対して
- 講義スライド(画面集)の各ページを、対応する教科書ページの直後に挿入
- 解答量の多い過去問ページ(qa_pages.json)の直後に解答例ページを挿入
(章末の解答例まとめページは廃止 — 解答は問題掲載ページに紐づける)

使い方: python3 build_final3.py
"""
import json
import os

import pymupdf

import build_final as bf
import build_final2 as bf2

SC = bf.SC
RED = bf.RED
INK = bf.INK
GRAY = bf.GRAY
F = bf.F

BOOKS = [
    (f"{SC}/会計実務_テキスト1_書込済_v4.pdf", f"{SC}/会計実務_テキスト1_完全版v3.pdf", 1,
     {1: (10, 21), 2: (22, 45), 3: (46, 69), 4: (70, 105), 5: (106, 154)}),
    (f"{SC}/会計実務_テキスト2_書込済_v4.pdf", f"{SC}/会計実務_テキスト2_完全版v3.pdf", 2,
     {6: (6, 39), 7: (40, 70)}),
    (f"{SC}/会計実務_テキスト3_書込済_v4.pdf", f"{SC}/会計実務_テキスト3_完全版v3.pdf", 3,
     {8: (12, 21), 9: (22, 35), 10: (36, 51), 11: (52, 63), 12: (64, 71),
      13: (72, 79), 14: (80, 115), 15: (116, 127), 16: (128, 137), 17: (138, 145),
      18: (146, 167), 19: (168, 181), 20: (182, 225), 21: (226, 235),
      22: (236, 259), 23: (260, 267), 24: (268, 304)}),
]


def make_qa_pages_ref(doc, ref, items, w, h):
    """特定ページ(ref)の過去問解答例ページを doc 末尾に作る。build_final.make_qa_pages の題名違い。"""
    ml, mr, mt, mb = 42, 40, 52, 44
    fs = 9.2
    lh = fs * 1.42
    gap = 10
    scratch = pymupdf.open()
    page = None
    y = 0

    def new_page(cont=False):
        nonlocal page, y
        page = doc.new_page(width=w, height=h)
        title = f"過去問check 解答例（前ページ p.{ref} 掲載分）"
        if cont:
            title += "（続き）"
        page.insert_text((ml, mt - 22), title, fontname=F, fontsize=10.5, color=RED)
        page.draw_line((ml, mt - 14), (w - mr, mt - 14), color=RED, width=0.8)
        page.insert_text((ml, h - 24),
                         "※ 教科書掲載の過去問に対する解答例（本試験の公式解答ではない）",
                         fontname=F, fontsize=7.5, color=GRAY)
        y = mt

    def block(q, a, y_top, dry):
        tgt = scratch.new_page(width=w, height=h) if dry else page
        yy = y_top
        r1 = pymupdf.Rect(ml, yy, w - mr, h - mb)
        if r1.height < lh:
            if dry: scratch.delete_page(tgt.number)
            return None
        rc = tgt.insert_textbox(r1, q, fontname=F, fontsize=fs - 0.4,
                                color=RED, lineheight=1.38, align=0)
        if rc < 0:
            if dry: scratch.delete_page(tgt.number)
            return None
        yy += r1.height - rc + 2
        r2 = pymupdf.Rect(ml + 12, yy, w - mr, h - mb)
        if r2.height < lh:
            if dry: scratch.delete_page(tgt.number)
            return None
        rc2 = tgt.insert_textbox(r2, a, fontname=F, fontsize=fs,
                                 color=INK, lineheight=1.42, align=0)
        if rc2 < 0:
            if dry: scratch.delete_page(tgt.number)
            return None
        yy += r2.height - rc2
        if dry: scratch.delete_page(tgt.number)
        return yy - y_top

    new_page()
    for it in items:
        q, a = it["q"], it["a"]
        used = block(q, a, y, dry=True)
        if used is None:
            new_page(cont=True)
            used = block(q, a, y, dry=True)
            if used is None:
                r = pymupdf.Rect(ml, y, w - mr, h - mb)
                page.insert_textbox(r, f"{q}\n{a}", fontname=F,
                                    fontsize=fs - 1.4, color=INK, lineheight=1.34)
                y = h - mb
                continue
        block(q, a, y, dry=False)
        y += used + gap


def main():
    heavy = json.load(open(f"{SC}/qa_pages.json", encoding="utf-8"))
    for src, out, book_no, chmap in BOOKS:
        base = pymupdf.open(src)
        w, h = base[0].rect.width, base[0].rect.height

        # スライド挿入マップ(build_final2と同じロジック)
        ins = {}
        slide_docs = {}
        for ch in sorted(chmap):
            sl_path = f"{SC}/slides/画面集_第{ch:02d}章.pdf"
            if not os.path.exists(sl_path):
                continue
            sd = pymupdf.open(sl_path)
            slide_docs[ch] = sd
            mapping = bf2.load_jsonl(f"{SC}/slide_map_ch{ch:02d}.json")
            cs, ce = chmap[ch]
            assigned = set()
            for m in mapping:
                sp = m.get("slide_page")
                pg = bf2.ref_to_page(m.get("after_ref"), ch)
                if not sp or sp < 1 or sp > sd.page_count:
                    continue
                if pg is None or not (cs <= pg <= ce):
                    pg = cs
                ins.setdefault(pg, []).append((ch, sp, m.get("after_ref")))
                assigned.add(sp)
            for sp in range(1, sd.page_count + 1):
                if sp not in assigned:
                    ins.setdefault(cs, []).append((ch, sp, None))

        # 解答例ページ(重いページ分)を一時ドキュメントに生成
        supp = pymupdf.open()
        qa_after = {}   # 元PDFページ番号 → (supp開始, supp終了)
        for hv in heavy:
            if hv["book"] != book_no:
                continue
            start = supp.page_count
            make_qa_pages_ref(supp, hv["ref"], hv["items"], w, h)
            qa_after[hv["page"]] = (start, supp.page_count - 1)

        ndoc = pymupdf.open()
        for p in range(1, base.page_count + 1):
            ndoc.insert_pdf(base, from_page=p - 1, to_page=p - 1)
            # 過去問解答例ページを問題ページの直後に
            if p in qa_after:
                s0, s1 = qa_after[p]
                ndoc.insert_pdf(supp, from_page=s0, to_page=s1)
            # 対応スライドをその後に
            for (ch, sp, ref) in ins.get(p, []):
                sd = slide_docs[ch]
                first = ndoc.page_count
                ndoc.insert_pdf(sd, from_page=sp - 1, to_page=sp - 1)
                tag = f"(p.{ref})" if ref else ""
                ndoc[first].insert_text(
                    (14, 16),
                    f"■ 講義スライド（画面集） 第{ch}章 — 前の教科書ページ{tag}の内容に対応",
                    fontname=F, fontsize=9, color=RED)
            
        tmp = out + ".tmp"
        ndoc.save(tmp, garbage=4, deflate=True, clean=True)
        ndoc.close()
        d = pymupdf.open(tmp)
        d.save(out, garbage=4, deflate=True, clean=True)
        d.close()
        os.remove(tmp)
        print(f"{os.path.basename(out)}: {base.page_count} → done")
        for sd in slide_docs.values():
            sd.close()
        supp.close()
        base.close()


if __name__ == "__main__":
    main()
