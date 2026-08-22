"""完全版v2: 書込済PDF(講義コメント統合済み)に対して
- 講義スライド(画面集)の各ページを、対応する教科書ページの直後に挿入
- 章末に過去問check解答例ページを挿入
(章頭スライド・章末講義補足ページは廃止 — 補足はコメント欄に統合済み)

使い方: python3 build_final2.py
"""
import json
import os

import pymupdf

import build_final as bf

SC = bf.SC
RED = bf.RED
F = bf.F

# ref "10-3" → 元PDFページ番号(1-based) のオフセット (page = offset + 章内ページ番号)
OFFSET = {1: 9, 2: 21, 3: 45, 4: 69, 5: 105,
          6: 5, 7: 39,
          8: 11, 9: 21, 10: 35, 11: 51, 12: 63, 13: 71, 14: 79, 15: 115,
          16: 127, 17: 137, 18: 145, 19: 167, 20: 181, 21: 225, 22: 235,
          23: 259, 24: 267}

# 書込済v3(コメント統合済み)→ 出力
BOOKS = [
    (f"{SC}/会計実務_テキスト1_書込済_v3.pdf",
     f"{SC}/会計実務_テキスト1_完全版v2.pdf",
     {1: (10, 21), 2: (22, 45), 3: (46, 69), 4: (70, 105), 5: (106, 154)}),
    (f"{SC}/会計実務_テキスト2_書込済_v3.pdf",
     f"{SC}/会計実務_テキスト2_完全版v2.pdf",
     {6: (6, 39), 7: (40, 70)}),
    (f"{SC}/会計実務_テキスト3_書込済_v3.pdf",
     f"{SC}/会計実務_テキスト3_完全版v2.pdf",
     {8: (12, 21), 9: (22, 35), 10: (36, 51), 11: (52, 63), 12: (64, 71),
      13: (72, 79), 14: (80, 115), 15: (116, 127), 16: (128, 137), 17: (138, 145),
      18: (146, 167), 19: (168, 181), 20: (182, 225), 21: (226, 235),
      22: (236, 259), 23: (260, 267), 24: (268, 304)}),
]


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        s = line.strip().rstrip(",")
        if s.startswith("{"):
            try:
                out.append(json.loads(s))
            except json.JSONDecodeError:
                pass
    return out


def ref_to_page(ref, ch):
    try:
        n = int(str(ref).split("-")[1])
    except (IndexError, ValueError):
        return None
    return OFFSET[ch] + n


def main():
    for src, out, chmap in BOOKS:
        base = pymupdf.open(src)
        w, h = None, None

        # スライド挿入マップ: 元PDFページ番号(1-based) → [(章, slide_page, ref), ...]
        ins = {}
        slide_docs = {}
        for ch in sorted(chmap):
            sl_path = f"{SC}/slides/画面集_第{ch:02d}章.pdf"
            if not os.path.exists(sl_path):
                continue
            sd = pymupdf.open(sl_path)
            slide_docs[ch] = sd
            mapping = load_jsonl(f"{SC}/slide_map_ch{ch:02d}.json")
            cs, ce = chmap[ch]
            assigned = set()
            for m in mapping:
                sp = m.get("slide_page")
                pg = ref_to_page(m.get("after_ref"), ch)
                if not sp or sp < 1 or sp > sd.page_count:
                    continue
                if pg is None or not (cs <= pg <= ce):
                    pg = cs  # 範囲外は章の先頭ページ直後へ
                ins.setdefault(pg, []).append((ch, sp, m.get("after_ref")))
                assigned.add(sp)
            # マップ漏れのスライドは章扉の直後へ
            for sp in range(1, sd.page_count + 1):
                if sp not in assigned:
                    ins.setdefault(cs, []).append((ch, sp, None))

        # QAページを一時ドキュメントに生成
        # (書込済v3は横幅拡張済みなのでそのページサイズに合わせる)
        w, h = base[0].rect.width, base[0].rect.height
        supp = pymupdf.open()
        qa_range = {}
        for ch in sorted(chmap):
            qa_items = bf.load_qa(ch)
            if qa_items:
                start = supp.page_count
                bf.make_qa_pages(supp, ch, qa_items, w, h)
                qa_range[ch] = (start, supp.page_count - 1)

        ndoc = pymupdf.open()
        # 章末ページ番号 → 章
        ch_end = {ce: ch for ch, (cs, ce) in chmap.items()}
        for p in range(1, base.page_count + 1):
            ndoc.insert_pdf(base, from_page=p - 1, to_page=p - 1)
            # 対応スライドをこのページの直後に
            for (ch, sp, ref) in ins.get(p, []):
                sd = slide_docs[ch]
                first = ndoc.page_count
                ndoc.insert_pdf(sd, from_page=sp - 1, to_page=sp - 1)
                tag = f"(p.{ref})" if ref else ""
                ndoc[first].insert_text(
                    (14, 16),
                    f"■ 講義スライド（画面集） 第{ch}章 — 前の教科書ページ{tag}の内容に対応",
                    fontname=F, fontsize=9, color=RED)
            # 章末なら解答例ページ
            if p in ch_end and ch_end[p] in qa_range:
                s0, s1 = qa_range[ch_end[p]]
                ndoc.insert_pdf(supp, from_page=s0, to_page=s1)

        ndoc.save(out, garbage=3, deflate=True)
        print(f"{os.path.basename(out)}: {base.page_count} → {ndoc.page_count} pages")
        for sd in slide_docs.values():
            sd.close()
        supp.close()
        base.close()
        ndoc.close()


if __name__ == "__main__":
    main()
