"""JSON注釈プランをtext1.pdfに適用するスクリプト。

プラン形式(1行1オブジェクトのJSONL、または配列JSON):
{
  "page": 71,                  # PDFページ番号(1始まり)
  "type": "highlight",         # highlight | underline | badge | note | margin
  "search": "純資産の部の表示", # ページ内で検索するアンカー文字列(必須)
  "occurrence": 0,             # 0=最初のヒット, -1=全ヒット, n=n番目(0始まり)
  "text": "...",               # badge/note/margin用の文字列
  "color": "yellow"            # yellow|green|red|blue|orange|gray
}
使い方: python3 apply_annots.py plan1.json plan2.json ... out.pdf
"""
import json
import sys

import pymupdf

COLORS = {
    "yellow": (1, 0.92, 0.23),
    "green": (0.56, 0.93, 0.56),
    "red": (0.85, 0.1, 0.1),
    "blue": (0.15, 0.35, 0.85),
    "orange": (1, 0.55, 0),
    "gray": (0.45, 0.45, 0.5),
}

# 赤ペン仕上げ: ユーザー指定によりライン=赤マーカー、文字=赤に統一
RED_MARKER = (1, 0.62, 0.62)   # ハイライト用の薄い赤
RED_INK = (0.82, 0.05, 0.05)   # 文字・下線用の赤
RED_MODE = True

def wrap(text, n=13):
    lines = []
    for para in text.split("\n"):
        while len(para) > n:
            lines.append(para[:n])
            para = para[n:]
        lines.append(para)
    return lines

def apply(doc, a, stats):
    page = doc[a["page"] - 1]
    hits = page.search_for(a["search"])
    if not hits:
        stats["miss"].append((a["page"], a["search"][:30], a["type"]))
        return
    occ = a.get("occurrence", 0)
    rects = hits if occ == -1 else [hits[min(occ, len(hits) - 1)]]
    t = a["type"]
    if RED_MODE:
        color = RED_MARKER if t == "highlight" else RED_INK
    else:
        color = COLORS.get(a.get("color", ""), None)
    if t == "highlight":
        for r in rects:
            an = page.add_highlight_annot(r)
            if color:
                an.set_colors(stroke=color)
                an.update()
    elif t == "underline":
        for r in rects:
            an = page.add_underline_annot(r)
            an.set_colors(stroke=color or COLORS["red"])
            an.update()
    elif t == "badge":
        r = rects[0]
        txt = a["text"]
        w = pymupdf.get_text_length(txt, fontname="japan", fontsize=8)
        pw = page.rect.width
        c = color or COLORS["red"]
        right_zone = pymupdf.Rect(r.x1, r.y0, min(pw, r.x1 + 6 + w), r.y1)
        occupied = bool(page.get_text(clip=right_zone).strip())
        if not occupied and r.x1 + 4 + w < pw - 8:
            pos = (r.x1 + 4, r.y1 - 1.5)
        else:
            pos = (r.x0, r.y0 - 3)
        page.insert_text(pos, txt, fontname="japan", fontsize=8, color=c)
    elif t == "note":
        r = rects[0]
        x = page.rect.width - 22
        an = page.add_text_annot((x, r.y0 - 2), a["text"], icon="Comment")
        an.set_colors(stroke=color or COLORS["orange"])
        an.update(opacity=0.9)
    elif t == "margin":
        r = rects[0]
        c = color or COLORS["blue"]
        lines = wrap(a["text"], a.get("wrap", 13))
        fs = a.get("fontsize", 6.5)
        pw = page.rect.width
        # 右余白に入るなら右、無理なら行の下に
        maxw = max(pymupdf.get_text_length(l, fontname="japan", fontsize=fs) for l in lines)
        if r.x1 + 6 + maxw < pw - 4:
            x, y = r.x1 + 6, r.y0 + 5
        else:
            x, y = max(8, pw - maxw - 10), r.y1 + 8
        for i, l in enumerate(lines):
            page.insert_text((x, y + i * (fs + 1.5)), l, fontname="japan", fontsize=fs, color=c)
    stats["ok"] += 1

def main():
    *plans, out = sys.argv[1:]
    doc = pymupdf.open("text1.pdf")
    stats = {"ok": 0, "miss": []}
    for pf in plans:
        raw = open(pf).read().strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = [
                json.loads(s.rstrip(","))
                for s in (l.strip() for l in raw.splitlines())
                if s.startswith("{")
            ]
        for a in data:
            try:
                apply(doc, a, stats)
            except Exception as e:
                stats["miss"].append((a.get("page"), a.get("search", "")[:30], f"ERR:{e}"))
    doc.save(out, garbage=3, deflate=True)
    print(f"applied: {stats['ok']}, missed: {len(stats['miss'])}")
    for m in stats["miss"]:
        print("  MISS", m)

if __name__ == "__main__":
    main()
