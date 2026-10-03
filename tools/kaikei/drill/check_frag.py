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
# 長さチェック（圧縮版用）
LIM={"A":260,"B":180,"C":90}; over=[]; lens=[]
def strip(h): return re.sub(r'\s+','',re.sub(r'<[^>]+>','',h))
for m in re.finditer(r'<div class="th">([ABC])-(\d+)(.*?)</div>.*?<div class="a">(.*?)(?=<div class="pt">|</div>\s*(?:<div class="item">|<h2|</section>))',s,re.S):
    r,n,a=m.group(1),m.group(2),strip(m.group(4)).replace("解答例","",1)
    lim=LIM[r]
    if r=="A" and re.search(r'[①②]|\(a\)|\(b\)|の場合',m.group(4)): lim=320
    lens.append(len(a))
    if len(a)>lim: over.append(f"{r}-{n} {len(a)}字 (上限{lim})")
avg=int(sum(lens)/len(lens)) if lens else 0
print(f"{p}: items={len(items)} errors={len(err)} 平均{avg}字 長さ超過={len(over)}")
for o in over: print("   長さ超過:",o)
for e in err: print(" -",e)
sys.exit(1 if err else 0)
