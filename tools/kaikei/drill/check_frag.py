import sys,re
p=sys.argv[1]; s=open(p).read(); err=[]
if not re.search(r'<section class="chap" id="ch\d\d">',s): err.append("section開始なし")
if not s.rstrip().endswith("</section>"): err.append("</section>で終わっていない")
if not re.search(r'<h1 class="chap">第\d+章',s): err.append("h1.chapなし")
items=re.findall(r'<div class="item">',s)
if not items: err.append("itemなし")
for m in re.finditer(r'<div class="item">(.*?)(?=<div class="item">|<h2|</section>)',s,re.S):
    b=m.group(1)
    if '<div class="q">' not in b: err.append("qなし: "+b[:40])
    if '<div class="a">' not in b: err.append("aなし: "+b[:40])
    if re.search(r'講師メモ|タイムスタンプ|\d:\d\d:\d\d',b): err.append("メタ表現: "+b[:40])
for tag in ("div","ol","ul","p","section"):
    o=len(re.findall(rf'<{tag}[\s>]',s)); c=len(re.findall(rf'</{tag}>',s))
    if o!=c: err.append(f"<{tag}> 開閉不一致 {o}/{c}")
print(f"{p}: items={len(items)} errors={len(err)}")
for e in err: print(" -",e)
sys.exit(1 if err else 0)
