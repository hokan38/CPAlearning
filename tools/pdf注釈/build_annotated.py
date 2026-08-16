"""赤ペン直書き版の書き込み済みPDFを生成する。

各ページの右側にコメント帯(WIDE pt)を拡張し、コメントは紙面に赤文字で直接記載する。
付箋(note)は使わない。旧プランのnoteはcommentに自動変換(「講師メモ(…): 」等の前置きを除去)。

プラン形式(JSONL or 配列JSON):
{"page": 71, "type": "highlight|underline|badge|margin|comment|note",
 "search": "アンカー文字列", "occurrence": 0, "text": "...", "wrap": 13}

使い方: python3 build_annotated.py 元.pdf 出力.pdf plan1.json [plan2.json ...]
"""
import json
import re
import sys

import pymupdf

WIDE = 175           # 右コメント帯の幅(pt)
RED_MARKER = (1, 0.62, 0.62)
RED_INK = (0.82, 0.05, 0.05)
FS_COMMENT = 6.8     # コメント文字サイズ
FS_BADGE = 8

def load_plan(pf):
    raw = open(pf).read().strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [
            json.loads(s.rstrip(","))
            for s in (l.strip() for l in raw.splitlines())
            if s.startswith("{")
        ]

def clean_comment(text):
    # 旧形式の前置き・タイムスタンプを除去
    text = re.sub(r"^講師メモ\s*[（(][^）)]*[）)]\s*[:：]\s*", "", text)
    text = re.sub(r"^講師メモ\s*[:：]\s*", "", text)
    text = re.sub(r"[（(]\d+_\d+\s+\d+:\d\d:\d\d[）)]", "", text)
    text = re.sub(r"[・、,\s]*\d+:\d\d:\d\d\s*", "", text)
    return text.strip()

def wrap_jp(text, width_pt, fs):
    # 全角基準の簡易折り返し
    n = max(6, int(width_pt / fs))
    lines = []
    for para in text.split("\n"):
        while len(para) > n:
            lines.append(para[:n])
            para = para[n:]
        if para:
            lines.append(para)
    return lines

def main():
    src, out, *plan_files = sys.argv[1:]
    sdoc = pymupdf.open(src)
    ndoc = pymupdf.open()
    ow = sdoc[0].rect.width
    # 元ページを左に配置した拡張ページを作る
    for sp in sdoc:
        r = sp.rect
        np = ndoc.new_page(width=r.width + WIDE, height=r.height)
        np.show_pdf_page(pymupdf.Rect(0, 0, r.width, r.height), sdoc, sp.number)
        np.draw_line((r.width + 2, 8), (r.width + 2, r.height - 8),
                     color=(0.88, 0.82, 0.82), width=0.5)

    annots = []
    for pf in plan_files:
        annots.extend(load_plan(pf))

    # ページごとのコメント帯カーソル(縦位置の衝突回避)
    cursors = {}
    stats = {"ok": 0, "miss": []}
    # コメントはy順に置くと自然なので、事前にページ内アンカー位置を解決してソート
    resolved = []
    for a in annots:
        page = ndoc[a["page"] - 1]
        hits = page.search_for(a["search"], clip=pymupdf.Rect(0, 0, ow, page.rect.height))
        if not hits:
            stats["miss"].append((a["page"], a["search"][:30], a["type"]))
            continue
        occ = a.get("occurrence", 0)
        rects = hits if occ == -1 else [hits[min(occ, len(hits) - 1)]]
        resolved.append((a, rects))
    order = {"highlight": 0, "underline": 0, "badge": 1, "margin": 2, "note": 3, "comment": 3}
    resolved.sort(key=lambda x: (x[0]["page"], order.get(x[0]["type"], 9), x[1][0].y0))

    resolved_extra = []
    for a, rects in resolved:
        page = ndoc[a["page"] - 1]
        t = a["type"]
        try:
            if t == "highlight":
                for r in rects:
                    an = page.add_highlight_annot(r)
                    an.set_colors(stroke=RED_MARKER)
                    an.update()
            elif t == "underline":
                for r in rects:
                    an = page.add_underline_annot(r)
                    an.set_colors(stroke=RED_INK)
                    an.update()
            elif t == "badge":
                r = rects[0]
                txt = a["text"]
                w = pymupdf.get_text_length(txt, fontname="japan", fontsize=FS_BADGE)
                zone_r = pymupdf.Rect(r.x1 + 2, r.y0, min(ow, r.x1 + 8 + w), r.y1)
                zone_a = pymupdf.Rect(r.x0, r.y0 - FS_BADGE - 4, r.x0 + w + 4, r.y0 - 1)
                if not page.get_text(clip=zone_r).strip() and r.x1 + 4 + w < ow - 8:
                    page.insert_text((r.x1 + 4, r.y1 - 1.5), txt,
                                     fontname="japan", fontsize=FS_BADGE, color=RED_INK)
                elif not page.get_text(clip=zone_a).strip() and zone_a.y0 > 4:
                    page.insert_text((r.x0, r.y0 - 3), txt,
                                     fontname="japan", fontsize=FS_BADGE, color=RED_INK)
                else:
                    a2 = dict(a); a2["type"] = "comment"
                    resolved_extra.append((a2, rects))
            elif t == "margin":
                r = rects[0]
                lines = wrap_jp(a["text"], 90, 6.5)
                maxw = max(pymupdf.get_text_length(l, fontname="japan", fontsize=6.5) for l in lines)
                h = len(lines) * 8 + 2
                placed = False
                zone1 = pymupdf.Rect(r.x1 + 4, r.y0 - 1, r.x1 + 8 + maxw, r.y0 + h)
                if zone1.x1 < ow - 4 and not page.get_text(clip=zone1).strip():
                    x, y, placed = r.x1 + 6, r.y0 + 4.5, True
                else:
                    zone2 = pymupdf.Rect(max(8, ow - maxw - 12), r.y1 + 2,
                                         max(8, ow - maxw - 12) + maxw + 4, r.y1 + 4 + h)
                    if zone2.y1 < page.rect.height - 24 and not page.get_text(clip=zone2).strip():
                        x, y, placed = zone2.x0 + 2, r.y1 + 8, True
                if placed:
                    for i, l in enumerate(lines):
                        page.insert_text((x, y + i * 8), l, fontname="japan", fontsize=6.5, color=RED_INK)
                else:
                    a2 = dict(a); a2["type"] = "comment"
                    resolved_extra.append((a2, rects))
            elif t in ("comment", "note"):
                r = rects[0]
                txt = clean_comment(a["text"])
                lines = wrap_jp(txt, WIDE - 14, FS_COMMENT)
                y = max(cursors.get(a["page"], 14), r.y0 + 4)
                block_h = len(lines) * (FS_COMMENT + 1.8) + 6
                if y + block_h > page.rect.height - 10:
                    y = max(10, page.rect.height - 10 - block_h)
                x = ow + 8
                # アンカーへの赤い接続マーク(既存文字と交差しない起点を選ぶ)
                gap = pymupdf.Rect(r.x1 + 1, r.y0, ow, r.y1)
                sx = r.x1 + 1 if not page.get_text(clip=gap).strip() else ow - 4
                page.draw_line((sx, (r.y0 + r.y1) / 2), (ow + 5, y + 3),
                               color=RED_INK, width=0.6)
                for i, l in enumerate(lines):
                    page.insert_text((x, y + 4 + i * (FS_COMMENT + 1.8)), l,
                                     fontname="japan", fontsize=FS_COMMENT, color=RED_INK)
                cursors[a["page"]] = y + block_h + 4
            stats["ok"] += 1
        except Exception as e:
            stats["miss"].append((a.get("page"), a.get("search", "")[:30], f"ERR:{e}"))

    # 退避分(badge/marginがコメント帯へ)を処理
    for a, rects in resolved_extra:
        page = ndoc[a["page"] - 1]
        try:
            r = rects[0]
            txt = clean_comment(a["text"])
            lines = wrap_jp(txt, WIDE - 14, FS_COMMENT)
            y = max(cursors.get(a["page"], 14), r.y0 + 4)
            block_h = len(lines) * (FS_COMMENT + 1.8) + 6
            if y + block_h > page.rect.height - 10:
                y = max(10, page.rect.height - 10 - block_h)
            gap = pymupdf.Rect(r.x1 + 1, r.y0, ow, r.y1)
            sx = r.x1 + 1 if not page.get_text(clip=gap).strip() else ow - 4
            page.draw_line((sx, (r.y0 + r.y1) / 2), (ow + 5, y + 3), color=RED_INK, width=0.6)
            for i, l in enumerate(lines):
                page.insert_text((ow + 8, y + 4 + i * (FS_COMMENT + 1.8)), l,
                                 fontname="japan", fontsize=FS_COMMENT, color=RED_INK)
            cursors[a["page"]] = y + block_h + 4
            stats["ok"] += 1
        except Exception as e:
            stats["miss"].append((a.get("page"), a.get("search", "")[:30], f"ERR:{e}"))

    ndoc.save(out, garbage=3, deflate=True)
    print(f"applied: {stats['ok']}, missed: {len(stats['miss'])}")
    for m in stats["miss"]:
        print("  MISS", m)

if __name__ == "__main__":
    main()
