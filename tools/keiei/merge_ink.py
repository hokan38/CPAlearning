"""教科書PDFに、講義資料(講師の書き込み入り版)の色付きインクだけを重ねた版を作る。

資料は教科書ページを別倍率・別余白で刷り直したものなので、ページごとに
「黒文字部分の外接矩形」を突き合わせて座標変換を推定してから重ねる。

使い方: python3 merge_ink.py 出力.pdf 教科書.pdf 資料.pdf:マップJSON [資料2.pdf:マップ2 ...]
マップJSONは {"資料ページ": 教科書ページ} (どちらも1始まり)
"""
import json
import sys

import numpy as np
import pymupdf

SAT_TH = 40        # これ以上の彩度 = 講師の書き込み
DARK_TH = 140      # これ以下の明度 = 印刷された黒文字
RENDER_W = 620     # 変換推定用のレンダ幅(px)
INK_SCALE = 2.6    # インク画像の解像度


def _render(page, width=RENDER_W):
    r = page.rect
    m = pymupdf.Matrix(width / r.width, width / r.width)
    pm = page.get_pixmap(matrix=m)
    a = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, :3].astype(np.int16)
    return a


def _text_bbox(a):
    """黒文字(色でない暗い画素)の外接矩形。(x0,y0,x1,y1) or None"""
    sat = a.max(2) - a.min(2)
    dark = (a.mean(2) < DARK_TH) & (sat <= SAT_TH)
    if dark.sum() < 200:
        return None
    rows = np.where(dark.sum(1) > 0.4)[0]
    cols = np.where(dark.sum(0) > 0.4)[0]
    if len(rows) < 2 or len(cols) < 2:
        return None
    return float(cols[0]), float(rows[0]), float(cols[-1]), float(rows[-1])


def transform(src_page, base_page, fallback=None):
    """資料ページ上の相対座標 → 教科書ページ上の相対座標 に変換する係数を返す。"""
    sa, ba = _render(src_page), _render(base_page)
    sb, bb = _text_bbox(sa), _text_bbox(ba)
    hs, ws = sa.shape[:2]
    hb, wb = ba.shape[:2]
    if sb and bb:
        sx = (bb[2] - bb[0]) / max(sb[2] - sb[0], 1)
        sy = (bb[3] - bb[1]) / max(sb[3] - sb[1], 1)
        if 0.7 < sx < 1.45 and 0.7 < sy < 1.45:
            # 資料px → 教科書px
            def fwd(x, y):
                return (bb[0] + (x - sb[0]) * sx, bb[1] + (y - sb[1]) * sy)
            return fwd, (ws, hs), (wb, hb)
    if fallback:
        return fallback, (ws, hs), (wb, hb)
    scale_x, scale_y = wb / ws, hb / hs
    return (lambda x, y: (x * scale_x, y * scale_y)), (ws, hs), (wb, hb)


def ink_image(page, scale=INK_SCALE):
    pm = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
    a = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, :3].astype(np.int16)
    mask = (a.max(2) - a.min(2)) > SAT_TH
    if mask.sum() < 60:
        return None
    rows = np.where(mask.any(1))[0]
    cols = np.where(mask.any(0))[0]
    y0, y1, x0, x1 = int(rows[0]), int(rows[-1]) + 1, int(cols[0]), int(cols[-1]) + 1
    sub = a[y0:y1, x0:x1]
    m = mask[y0:y1, x0:x1]
    rgb = np.where(m[:, :, None], sub, 255).astype(np.uint8)
    alpha = np.where(m, 255, 0).astype(np.uint8)
    h, w, _ = rgb.shape
    px = pymupdf.Pixmap(pymupdf.csRGB, w, h, np.dstack([rgb, alpha]).tobytes(), True)
    # 資料レンダ(RENDER_W基準)での座標へ換算するための係数
    k = RENDER_W / pm.width
    return px, (x0 * k, y0 * k, x1 * k, y1 * k)


def main():
    out, base_path, *specs = sys.argv[1:]
    base = pymupdf.open(base_path)
    applied = skipped = 0
    for spec in specs:
        src_path, map_path = spec.rsplit(":", 1)
        src = pymupdf.open(src_path)
        mapping = json.load(open(map_path))
        for sp, bp in sorted(((int(k), v) for k, v in mapping.items())):
            if not (1 <= bp <= base.page_count and 1 <= sp <= src.page_count):
                continue
            got = ink_image(src[sp - 1])
            if got is None:
                skipped += 1
                continue
            px, (ix0, iy0, ix1, iy1) = got
            fwd, (ws, hs), (wb, hb) = transform(src[sp - 1], base[bp - 1])
            X0, Y0 = fwd(ix0, iy0)
            X1, Y1 = fwd(ix1, iy1)
            r = base[bp - 1].rect
            rect = pymupdf.Rect(X0 / wb * r.width, Y0 / hb * r.height,
                                X1 / wb * r.width, Y1 / hb * r.height)
            if rect.is_empty or rect.width <= 0 or rect.height <= 0:
                skipped += 1
                continue
            base[bp - 1].insert_image(rect, pixmap=px, overlay=True)
            applied += 1
        src.close()
    base.save(out, garbage=4, deflate=True, clean=True)
    print(f"ink overlaid: {applied} pages (skipped {skipped}) → {out}")


if __name__ == "__main__":
    main()
