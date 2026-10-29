"""从带狮版 PDF 提取品牌蓝色主色"""
import numpy as np
import pymupdf
from PIL import Image

PDF = r"c:\Users\11865\Desktop\TSINGTAO logo文件\250303_logo_with_lion_red&green_CMYK.pdf"
doc = pymupdf.open(PDF)
page = doc[0]
pix = page.get_pixmap(dpi=200, alpha=False)
arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).astype(np.float32)
# 非红、非白、非金的颜色里，找蓝
not_red = np.sqrt(((arr - np.array([219, 39, 45]))**2).sum(axis=2)) > 50
not_white = arr.sum(axis=2) < 700
not_gold = ~((arr[:, :, 0] > 200) & (arr[:, :, 1] > 150) & (arr[:, :, 2] < 200))
cand = not_red & not_white & not_gold
ys, xs = np.nonzero(cand)
print("cand pixels:", len(xs))
# 按 R 分桶
bins = {}
for i in np.random.RandomState(42).choice(len(xs), min(40000, len(xs)), replace=False):
    r, g, b = arr[ys[i], xs[i]].astype(int)
    k = (r//16, g//16, b//16)
    bins[k] = bins.get(k, 0) + 1
top = sorted(bins.items(), key=lambda x: -x[1])[:12]
for (br, bg, bb), cnt in top:
    r,g,b = br*16, bg*16, bb*16
    print(f"#{r:02X}{g:02X}{b:02X} cnt={cnt}")

# 再打印蓝球区域的精确颜色
blue_mask = (arr[:,:,2] > arr[:,:,0] + 50) & (arr[:,:,2] > arr[:,:,1] + 25) & (arr[:,:,2] > 110)
ys, xs = np.nonzero(blue_mask)
print("blue pixels:", len(xs))
if len(xs):
    sample = arr[ys[::20], xs[::20]].astype(int)
    print("mean:", sample.mean(axis=0).astype(int))
    print("unique top:", [(f"#{r:02X}{g:02X}{b:02X}", c) for (r,g,b), c in 
        zip(*np.unique(sample, axis=0, return_counts=True))][:8])
