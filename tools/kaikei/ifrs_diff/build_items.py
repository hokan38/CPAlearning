import pymupdf, json, re, sys
d = pymupdf.open(sys.argv[1])
NOTE_PREFIX = ("ＩＦＲＳと日本基準との主要な差異の中には", "ここでは，日本基準の会計処理と対比", "ＩＦＲＳと日本基準との差異は細部まで")
def rows(pages):
    out = []
    for pno in pages:
        spans = []
        for b in d[pno].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    t = s["text"].strip()
                    if not t: continue
                    x0, y0, x1, y1 = s["bbox"]
                    if y0 < 85 or y0 > 695: continue
                    if y0 < 95 and t in ("項 目", "ＩＦＲＳ", "日本基準", "項目"): continue
                    spans.append((round(y0), x0, x1, t))
        spans.sort()
        for y, x0, x1, t in spans:
            c = "name" if x1 <= 120 else ("ifrs" if x0 >= 118 and x1 <= 300 else ("jp" if x0 >= 298 else "wide"))
            out.append({"p": pno, "y": y, "x0": x0, "c": c, "t": t})
    return out

def join(parts):
    s = ""
    for t in parts:
        if s and (re.match(r"[A-Za-z]", t) or re.search(r"[A-Za-z]$", s)):
            s += " " + t
        else:
            s += t
    return s

def segment(rs, detail=True):
    items, cur, in_comment, in_note = [], None, False, False
    lastp = None
    for r in rs:
        if r["p"] != lastp:
            in_note = False; lastp = r["p"]
        if in_note: continue
        if r["c"] == "wide" and r["t"].startswith(NOTE_PREFIX):
            in_note = True; continue
        if r["c"] == "name" and (cur is None or in_comment or (not detail and cur["ifrs"] and cur["name_done"])):
            cur = {"name": [], "ifrs": [], "jp": [], "comment": [], "name_done": False, "p": r["p"]}
            items.append(cur); in_comment = False
        if cur is None: continue
        if r["c"] == "name":
            cur["name"].append(r["t"]); continue
        cur["name_done"] = True
        if detail and (r["c"] == "wide" or (in_comment and r["c"] == "ifrs")):
            in_comment = True; cur["comment"].append(r["t"]); continue
        # same-row grouping for ifrs/jp
        if r["c"] in ("ifrs", "jp"): cur[r["c"]].append((r["y"], r["t"]))
        else: cur["comment"].append(r["t"])
    for it in items:
        for k in ("ifrs", "jp"):
            byrow = {}
            for y, t in it[k]:
                byrow.setdefault(y, []).append(t)
            it[k] = [join(v) for y, v in sorted(byrow.items())]
        it["name"] = "".join(it["name"])
        it["comment"] = "".join(it["comment"])
    return items

digest = segment(rows([2, 3]), detail=False)
detail = segment(rows(range(4, 11)), detail=True)
print("digest", len(digest), "detail", len(detail))
res = []
for dg, dt in zip(digest, detail):
    def split(summary_lines, all_lines):
        summ = "".join(summary_lines).replace(" ", "")
        acc, i = "", 0
        while i < len(all_lines) and len(acc.replace(" ", "")) < len(summ):
            acc += all_lines[i]; i += 1
        return summary_lines, "".join(all_lines[i:])
    ifs, ifb = split(dg["ifrs"], dt["ifrs"])
    jps, jpb = split(dg["jp"], dt["jp"])
    res.append({"name": dt["name"], "ifrs_sum": ifs, "ifrs_body": ifb, "jp_sum": jps, "jp_body": jpb, "comment": dt["comment"]})
json.dump(res, open("items.json", "w"), ensure_ascii=False, indent=1)
for r in res:
    print("■", r["name"]); print("  IFRS要旨:", " / ".join(r["ifrs_sum"])); print("  IFRS本文:", r["ifrs_body"][:90])
    print("  日本要旨:", " / ".join(r["jp_sum"])); print("  日本本文:", r["jp_body"][:90]); print("  解説:", r["comment"][:90])
