"""講義資料(講師の書き込み入り)を教科書ページに対応付け、色付きインクだけを抽出して重ねる。

- 対応付け: フッタ「－ ⑥-30 －」のテキスト一致 → 欠落分は近傍からの内挿 + 画像相関で検証
- インク抽出: 彩度の高い画素(講師のマーカー・手書き)のみを透過PNG化して教科書ページに重ねる
"""
import re
import numpy as np
import pymupdf

FOOT = re.compile(r"－\s*([①-⑳])\s*[-‐－]\s*(\d+)\s*－")
SAT_TH = 40          # この彩度以上を「書き込み」とみなす
DPI_SCALE = 2.6      # インク抽出時のレンダ倍率


def footer_map(doc):
    m = {}
    for p in doc:
        f = FOOT.findall(p.get_text())
        if f and f[-1][0] != "⑲":
            m.setdefault(f[-1], p.number + 1)
    return m


def page_sig(page, W=72, H=100):
    r = page.rect
    pm = page.get_pixmap(colorspace=pymupdf.csGRAY,
                         matrix=pymupdf.Matrix(200 / r.width, 200 / r.width))
    a = 255.0 - np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width).astype(np.float32)
    tot = a.sum()
    if tot < 1:
        return None
    rows = np.where(a.sum(1) > tot * 0.0008)[0]
    cols = np.where(a.sum(0) > tot * 0.0008)[0]
    if len(rows) < 5 or len(cols) < 5:
        return None
    a = a[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    ys = np.linspace(0, a.shape[0], H + 1).astype(int)
    xs = np.linspace(0, a.shape[1], W + 1).astype(int)
    o = np.array([[a[ys[i]:ys[i + 1], xs[j]:xs[j + 1]].mean() for j in range(W)] for i in range(H)])
    o = o - o.mean()
    return o / (np.linalg.norm(o) + 1e-6)


def align(src, base, hint_offset=None, window=4):
    """src(資料)の各ページ → base(教科書)のページ番号(1始まり)。"""
    bf = footer_map(base)
    n = src.page_count
    out = {}
    for p in src:
        f = FOOT.findall(p.get_text())
        if f and f[-1][0] != "⑲" and f[-1] in bf:
            out[p.number + 1] = bf[f[-1]]
    known = sorted(out)
    bsig = {}
    for i in range(1, n + 1):
        if i in out:
            continue
        # 近傍から候補位置を推定
        lo = max([k for k in known if k < i], default=None)
        hi = min([k for k in known if k > i], default=None)
        if lo and hi:
            guess = round(out[lo] + (out[hi] - out[lo]) * (i - lo) / (hi - lo))
        elif lo:
            guess = out[lo] + (i - lo)
        elif hi:
            guess = out[hi] - (hi - i)
        elif hint_offset is not None:
            guess = i + hint_offset
        else:
            continue
        v = page_sig(src[i - 1])
        best, bs = guess, -9
        if v is not None:
            for j in range(max(1, guess - window), min(base.page_count, guess + window) + 1):
                if j not in bsig:
                    bsig[j] = page_sig(base[j - 1])
            for j in range(max(1, guess - window), min(base.page_count, guess + window) + 1):
                b = bsig.get(j)
                if b is None:
                    continue
                s = float((v * b).sum())
                if s > bs:
                    bs, best = s, j
        out[i] = best if bs > 0.35 else guess
    return out


def extract_ink(page, scale=DPI_SCALE):
    """彩度の高い画素だけを残した RGB画像 + アルファマスク を返す(なければ None)。"""
    pm = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
    a = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, :3].astype(np.int16)
    sat = a.max(2) - a.min(2)
    mask = sat > SAT_TH
    if mask.sum() < 60:
        return None
    rgb = np.where(mask[:, :, None], a, 255).astype(np.uint8)
    alpha = np.where(mask, 255, 0).astype(np.uint8)
    return rgb, alpha


def ink_pixmap(page, scale=DPI_SCALE):
    got = extract_ink(page, scale)
    if got is None:
        return None
    rgb, alpha = got
    h, w, _ = rgb.shape
    pm = pymupdf.Pixmap(pymupdf.csRGB, w, h, rgb.tobytes(), False)
    pm.set_alpha(alpha.tobytes())
    return pm
