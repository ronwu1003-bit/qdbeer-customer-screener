"""用 logo 提取的蓝色主题色，把 app.py 里所有红色系 CSS 值替换成严格蓝青色系"""
import re
import pathlib

APP = pathlib.Path(r"C:\Users\11865\Documents\Trae-CN\default\qdbeer-customer-screener\app.py")
text = APP.read_text(encoding="utf-8")

# Logo 蓝色 token（从 PDF 提取）
# 深 → 中 → 亮 → 极亮 → 点缀
BLUE_TOKENS = {
    # 红色 → 蓝色一一对应（HSL 关系保持，整体亮度不变）
    "#8E1119": "#0B2C6B",   # 深红 → 深蓝
    "#CD1A21": "#00508C",   # 品牌红 → 品牌蓝（logo 主色）
    "#E2504C": "#1A7FC8",   # 亮红 → 亮蓝
    "#DB272D": "#004480",   # 横幅红 → 横幅蓝
}

for old, new in BLUE_TOKENS.items():
    text = text.replace(old, new)

# rgba 红色 → rgba 蓝色
# rgba(205,26,33,X) → rgba(0,80,140,X)
# rgba(142,17,25,X) → rgba(11,44,107,X)
# rgba(226,80,76,X) → rgba(26,127,200,X)
rgba_map = [
    (r"rgba\(\s*205\s*,\s*26\s*,\s*33\s*,\s*([0-9.]+)\)", r"rgba(0,80,140,\1)"),
    (r"rgba\(\s*142\s*,\s*17\s*,\s*25\s*,\s*([0-9.]+)\)", r"rgba(11,44,107,\1)"),
    (r"rgba\(\s*226\s*,\s*80\s*,\s*76\s*,\s*([0-9.]+)\)", r"rgba(26,127,200,\1)"),
    (r"rgba\(\s*219\s*,\s*39\s*,\s*45\s*,\s*([0-9.]+)\)", r"rgba(0,68,128,\1)"),
    (r"rgba\(\s*179\s*,\s*20\s*,\s*28\s*,\s*([0-9.]+)\)", r"rgba(0,56,108,\1)"),
]
for pat, rep in rgba_map:
    text = re.sub(pat, rep, text)

# 品牌相关：#F6D79B (金色) → 保留，但品牌 logo 里的金色本身是金色，不要动
# 检查：看看还有没有红色残留
import re as _re
red_hex_left = [c for c in set(_re.findall(r"#[0-9A-Fa-f]{6}", text))
                if c.upper() in {"8E1119","CD1A21","E2504C","DB272D","B3141C","7C0E15","AE1E26"}]
print("剩余红色 hex:", red_hex_left)

APP.write_text(text, encoding="utf-8")
print("app.py 已写入")

# common.py 里的 footer 也处理一下（那是 HTML 字符串，里面有 #DB272D）
COMMON = pathlib.Path(r"C:\Users\11865\Documents\Trae-CN\default\qdbeer-customer-screener\views\common.py")
ct = COMMON.read_text(encoding="utf-8")
for old, new in BLUE_TOKENS.items():
    ct = ct.replace(old, new)
COMMON.write_text(ct, encoding="utf-8")
print("common.py 已写入")
