"""
青岛啤酒 · 全球客户开拓系统 — 应用入口
运行: python -m streamlit run app.py
"""
import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core import db  # noqa: E402
from views import common, registry  # noqa: E402
from views import home, settings, customers  # noqa: E402

st.set_page_config(
    page_title="青岛啤酒 · 全球客户开拓",
    page_icon="assets/tsingtao_mark.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

common.init_session_state()
db.init_db()

BASE_CSS = """
<style>
:root {
  /* TSINGTAO 品牌蓝主题（严格 Blue/Cyan 系，无紫色） */
  --ink: #0B1C3F;          /* 深墨蓝，正文 */
  --ink-soft: #1B2F5C;     /* 次深蓝 */
  --muted: #5B7AA8;        /* 柔和蓝，辅助文字 */
  --b1: #00508C;           /* 品牌蓝（logo 主色） */
  --b2: #0B2C6B;           /* 深蓝 */
  --b3: #1A7FC8;           /* 亮蓝 */
  --b4: #00B4D8;           /* 科技青 */
  --b5: #8AB4E5;           /* 极亮蓝 */
  --paper: #EEF4FD;        /* 冷白纸色 */
  --glass: rgba(255,255,255,.55);
  --stroke: rgba(255,255,255,.88);
}

html, body, [class*="st-"] {
  font-family: "SF Pro Display", "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
  color: var(--ink);
}
#MainMenu, footer, header[data-testid="stHeader"] { display: none; }

/* ===== 页面背景：冷白 + 蓝青透视渐变 + 科技网格 ===== */
.stApp {
  background:
    radial-gradient(940px 640px at -8% -10%, rgba(0,80,140,.22), transparent 62%),
    radial-gradient(900px 600px at 108% -4%, rgba(0,180,216,.14), transparent 64%),
    radial-gradient(860px 580px at 92% 108%, rgba(11,44,107,.18), transparent 66%),
    radial-gradient(980px 680px at 8% 112%, rgba(138,180,229,.45), transparent 72%),
    linear-gradient(168deg, #F3F7FF 0%, #E8F0FC 28%, #EEF4FD 52%, #F5F9FE 76%, #F0F5FD 100%);
  background-attachment: fixed;
}
[data-testid="stAppViewContainer"] { background: transparent; }
[data-testid="stAppViewContainer"]::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(rgba(11,44,107,.075) 1px, transparent 1px),
    linear-gradient(90deg, rgba(11,44,107,.075) 1px, transparent 1px);
  background-size: 46px 46px;
  -webkit-mask-image: radial-gradient(circle at 50% 22%, #000 0%, transparent 74%);
  mask-image: radial-gradient(circle at 50% 22%, #000 0%, transparent 74%);
}
/* 底层渐变光（模拟透视地平线） */
[data-testid="stAppViewContainer"]::after {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(1200px 820px at 50% 32%, transparent 50%, rgba(0,80,140,.08) 100%),
    radial-gradient(900px 600px at 50% 120%, rgba(0,180,216,.10), transparent 72%);
}
.block-container {
  padding-top: 1rem; padding-bottom: 2rem;
  max-width: 1560px;
  padding-left: 1.9rem; padding-right: 1.9rem;
  position: relative; z-index: 1;
}
[data-testid="stVerticalBlock"] { gap: 0.85rem; }

/* ===== 左上角品牌区 ===== */
.st-key-brand_logo { gap: 0 !important; }
.st-key-brand_logo [data-testid="stImage"] {
  background: rgba(255,255,255,.62);
  -webkit-backdrop-filter: blur(16px) saturate(150%);
  backdrop-filter: blur(16px) saturate(150%);
  border: 1px solid rgba(255,255,255,.95);
  border-radius: 15px;
  padding: 6px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10px 26px rgba(11,44,107,.16),
              inset 0 1px 0 rgba(255,255,255,.98),
              0 0 0 1px rgba(0,80,140,.14);
}
.st-key-brand_logo [data-testid="stImage"] img {
  border-radius: 50%;
  filter: drop-shadow(0 2px 6px rgba(0,80,140,.20));
}
.brand-cn {
  font-size: 16.5px; font-weight: 800; color: #0B1C3F;
  letter-spacing: .8px; line-height: 1.15;
}
.brand-en {
  font-size: 10.5px; font-weight: 800; color: #00508C;
  letter-spacing: 3.6px; line-height: 1.2; margin-top: 3px;
}

/* ===== 顶部导航按钮 ===== */
.st-key-nav_settings button, .st-key-nav_customers button,
.st-key-nav_home button, .st-key-nav_home_2 button, .st-key-nav_settings_2 button {
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,.95);
  background: rgba(255,255,255,.62);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
  color: #1B2F5C; font-weight: 700; font-size: 13px; height: 38px;
  box-shadow: 0 6px 18px rgba(11,44,107,.10);
  transition: all .18s ease;
}
.st-key-nav_settings button:hover, .st-key-nav_customers button:hover,
.st-key-nav_home button:hover, .st-key-nav_home_2 button:hover,
.st-key-nav_settings_2 button:hover {
  background: #FFFFFF; color: #00508C;
  border-color: rgba(0,80,140,.30);
  box-shadow: 0 10px 24px rgba(0,80,140,.17);
  transform: translateY(-1px);
}

/* ===== 首页：多语言大按钮（品牌红） ===== */
.st-key-hero_cta {
  position: relative !important;
  max-width: 620px; margin: 0 auto; gap: 0 !important;
}
.st-key-hero_cta [data-testid="stElementContainer"] { margin: 0 !important; }
.st-key-hero_cta [data-testid="stElementContainer"]:first-child,
.st-key-hero_cta [data-testid="stElementContainer"]:has(.cta-overlay) {
  position: absolute; top: 0; left: 0; width: 100%; height: 82px;
  z-index: 6; pointer-events: none;
  display: flex; align-items: center; justify-content: center;
}
.st-key-run_today button {
  width: 100%; height: 82px; border: none; border-radius: 20px;
  background: linear-gradient(105deg,
      rgba(11,44,107,.92) 0%, rgba(0,80,140,.88) 38%,
      rgba(26,127,200,.86) 66%, rgba(0,180,216,.82) 100%);
  background-size: 190% 100%;
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  backdrop-filter: blur(14px) saturate(160%);
  box-shadow: 0 14px 34px rgba(0,80,140,.26),
              inset 0 1px 0 rgba(255,255,255,.34),
              0 0 0 1px rgba(255,255,255,.55),
              0 0 60px rgba(0,180,216,.18);
  transition: transform .18s ease, box-shadow .18s ease;
  animation: ctaShift 10s ease-in-out infinite;
}
.st-key-run_today button:hover {
  transform: translateY(-3px);
  box-shadow: 0 22px 48px rgba(0,80,140,.36),
              inset 0 1px 0 rgba(255,255,255,.44),
              0 0 0 1px rgba(255,255,255,.78),
              0 0 80px rgba(0,180,216,.28);
}
.st-key-run_today button:active { transform: translateY(0); }
.st-key-run_today button p { opacity: 0 !important; }

/* 运行中：同位置的停止按钮（暖灰玻璃，与开始明确区分） */
.st-key-stop_search button {
  width: 100%; height: 82px; border: none; border-radius: 20px;
  background: linear-gradient(100deg, #1A2548 0%, #2A3A68 46%, #7A95BF 100%);
  background-size: 190% 100%;
  box-shadow: 0 18px 44px rgba(58,46,49,.28),
              inset 0 1px 0 rgba(255,255,255,.30);
  transition: transform .18s ease, box-shadow .18s ease;
  animation: ctaShift 6s ease-in-out infinite;
}
.st-key-stop_search button:hover {
  transform: translateY(-3px);
  box-shadow: 0 26px 58px rgba(58,46,49,.38),
              inset 0 1px 0 rgba(255,255,255,.38);
}
.st-key-stop_search button:active { transform: translateY(0); }
.st-key-stop_search button p { opacity: 0 !important; }

@keyframes ctaShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.cta-overlay {
  position: relative; width: 100%; height: 82px;
  display: flex; align-items: center; justify-content: center;
}
.cta-overlay span {
  position: absolute; left: 0; right: 0; top: 0; bottom: 0;
  display: flex; align-items: center; justify-content: center;
  margin: 0; padding: 0; border: 0;
  font-size: 25px; font-weight: 800; letter-spacing: 0; color: #FFFFFF;
  text-align: center; line-height: 1;
  text-shadow: 0 2px 14px rgba(80,8,20,.30);
  opacity: 0; white-space: nowrap;
  animation: langFade 20s infinite;
}
.cta-overlay span.always { opacity: 1; animation: none; }
@keyframes langFade {
  0%    { opacity: 0; transform: translateY(9px); }
  1.8%  { opacity: 1; transform: translateY(0); }
  10.2% { opacity: 1; transform: translateY(0); }
  12%   { opacity: 0; transform: translateY(-9px); }
  100%  { opacity: 0; }
}

/* ===== 首页：地球 + 统计玻璃卡（透明渐变） ===== */
.st-key-hero_card {
  max-width: 1320px; margin: 0 auto;
  background: linear-gradient(135deg,
      rgba(255,255,255,.46) 0%,
      rgba(255,255,255,.20) 42%,
      rgba(255,255,255,.08) 66%,
      rgba(255,245,244,.26) 100%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  backdrop-filter: blur(20px) saturate(150%);
  border: 1px solid rgba(255,255,255,.62);
  border-radius: 34px;
  padding: 20px 34px 18px 26px;
  box-shadow: 0 26px 70px rgba(11,44,107,.09),
              inset 0 1px 0 rgba(255,255,255,.80),
              0 0 0 1px rgba(247,245,238,.55);
}

/* 真实地球：等距圆柱贴图横向滚动模拟自转 */
.globe-stage {
  position: relative; width: 100%; max-width: 520px; aspect-ratio: 1 / 1;
  margin: 0 auto;
  display: flex; align-items: center; justify-content: center;
}
.globe-stage::before {
  content: ""; position: absolute; width: 114%; height: 114%; left: -7%; top: -7%;
  border-radius: 50%; pointer-events: none;
  background:
    radial-gradient(circle, rgba(0,180,216,.22) 38%, rgba(0,80,140,.14) 56%, transparent 72%),
    radial-gradient(circle at 50% 50%, transparent 58%, rgba(0,180,216,.08) 68%, transparent 80%);
  filter: blur(18px);
  animation: haloPulse 8s ease-in-out infinite;
}
@keyframes haloPulse {
  0%, 100% { transform: scale(1); opacity: .85; }
  50%      { transform: scale(1.05); opacity: 1; }
}
.earth {
  position: relative; width: 100%; height: 100%; border-radius: 50%;
  background-image: url("/app/static/earth.jpg");
  background-size: 200% 100%;
  background-repeat: repeat-x;
  background-position: 0% 50%;
  animation: earthSpin 34s linear infinite;
  box-shadow:
    inset -40px -30px 88px rgba(2,10,30,.86),
    inset -12px -8px 46px rgba(2,10,30,.50),
    inset 30px 34px 96px rgba(150,200,255,.22),
    0 0 90px rgba(0,80,140,.24);
}
@keyframes earthSpin {
  from { background-position: 0% 50%; }
  to   { background-position: -200% 50%; }
}
/* 大气层边缘光 */
.earth::before {
  content: ""; position: absolute; inset: -2.2%; border-radius: 50%;
  background: radial-gradient(circle at 50% 50%,
      rgba(80,160,255,0) 58%,
      rgba(90,170,255,.30) 70%,
      rgba(120,190,255,.16) 78%,
      transparent 84%);
  filter: blur(5px);
  pointer-events: none;
}
/* 光照高光 + 背光暗部 */
.earth::after {
  content: ""; position: absolute; inset: 0; border-radius: 50%;
  background:
    radial-gradient(circle at 28% 22%, rgba(255,255,255,.30), rgba(255,255,255,0) 38%),
    radial-gradient(circle at 76% 72%, rgba(2,8,24,.62), rgba(2,8,24,0) 56%);
  pointer-events: none;
}

/* 统计：与地球并排 2×2 */
.stat-grid {
  display: grid; grid-template-columns: repeat(2, minmax(150px, 1fr));
  gap: 14px 14px;
}
.stat-cell {
  padding: 16px 20px 15px;
  border-radius: 18px;
  background: linear-gradient(140deg, rgba(255,255,255,.62), rgba(255,255,255,.14));
  border: 1px solid rgba(255,255,255,.60);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.85);
}
.stat-num {
  font-size: clamp(40px, 3.6vw, 58px); font-weight: 800; line-height: 1; color: var(--ink);
  letter-spacing: -1.2px; font-variant-numeric: tabular-nums;
  background: linear-gradient(100deg, var(--b2) 4%, var(--b1) 50%, var(--b3) 80%, var(--b4) 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
.stat-num em {
  font-style: normal; font-size: 15px; font-weight: 800; margin-left: 5px;
  letter-spacing: 0;
  -webkit-text-fill-color: #7A95BF;
}
.stat-label {
  font-size: 13.5px; color: #5B7AA8; margin-top: 9px;
  letter-spacing: .8px; font-weight: 650;
}

/* ===== 分区标题 ===== */
.sec-title {
  display: flex; align-items: center; gap: 9px;
  font-size: 14px; font-weight: 800; color: #1A2548;
  margin: 6px 0 2px; letter-spacing: .4px;
}
.sec-title::before {
  content: ""; width: 4px; height: 15px; border-radius: 3px;
  background: linear-gradient(180deg, #00508C, #7A95BF);
  box-shadow: 0 0 12px rgba(0,80,140,.38);
}
.sec-title.sub {
  font-size: 12.5px; font-weight: 700; color: #5B7AA8;
  margin: 10px 0 0; letter-spacing: .3px;
}
.sec-title.sub::before {
  width: 3px; height: 12px;
  background: linear-gradient(180deg, rgba(0,80,140,.62), rgba(138,127,139,.62));
  box-shadow: none;
}

/* ===== 控件外观统一 ===== */
[data-testid="stWidgetLabel"] p { color: #1B2F5C !important; font-weight: 650; font-size: 12.8px; }
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  background: rgba(255,255,255,.74) !important;
  border-radius: 11px !important;
  border-color: rgba(214,203,203,.9) !important;
}
[data-testid="stExpander"] { background: rgba(255,255,255,.55); border-radius: 16px; }

/* 客户列表页指标卡 */
[data-testid="stMetric"] {
  background: rgba(255,255,255,.58);
  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,.92);
  border-radius: 18px;
  padding: 15px 18px;
  box-shadow: 0 10px 28px rgba(11,44,107,.10);
}
[data-testid="stMetricValue"] { color: #0B1C3F; font-weight: 800; }
[data-testid="stMetricLabel"] p { color: #5B7AA8 !important; font-weight: 650; font-size: 12.5px; }
[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; }

/* 主按钮 */
.stButton button[kind="primary"] {
  border-radius: 12px;
  background: linear-gradient(100deg, #0B2C6B, #00508C);
  border: none;
  box-shadow: 0 10px 26px rgba(0,80,140,.26);
}

/* ===== 首页：国家选择卡 + 搜索池 ===== */
.st-key-country_adder [data-baseweb="select"] > div {
  background: rgba(255,255,255,.82);
  border-radius: 16px;
  border: 1px solid rgba(0,80,140,.26);
  box-shadow: 0 10px 28px rgba(11,44,107,.09);
  padding: 6px 8px;
  min-height: 52px;
  transition: border-color .18s ease, box-shadow .18s ease;
}
.st-key-country_adder [data-baseweb="select"] > div:hover {
  border-color: rgba(0,80,140,.55);
  box-shadow: 0 14px 34px rgba(0,80,140,.14);
}

/* 搜索池：整个框（标题 + 标签）一体化 */
.st-key-country_pool {
  gap: .2rem !important;
  margin-top: 2px;
  background:
    linear-gradient(135deg, rgba(0,80,140,.065), rgba(247,245,238,.55) 52%, rgba(138,127,139,.075)),
    rgba(255,255,255,.58);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
  backdrop-filter: blur(18px) saturate(150%);
  border: 1.5px dashed rgba(0,80,140,.30);
  border-radius: 22px;
  padding: 14px 18px 10px 18px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.95), 0 12px 30px rgba(11,44,107,.07);
}
.st-key-country_pool [data-testid="stElementContainer"] { margin: 0 !important; }
.st-key-country_pool [data-baseweb="select"] > div {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  min-height: 34px;
  align-content: flex-start;
  padding: 0 !important;
}
.st-key-country_pool [data-baseweb="select"] input { display: none; }
.st-key-country_pool [data-testid="stWidgetLabel"] { display: none; }

/* 池内「清空」按钮：小胶囊 */
.st-key-country_pool .stButton button {
  height: 28px; min-height: 28px; padding: 0 12px;
  border-radius: 999px; font-size: 12px; font-weight: 700;
  color: #0B2C6B; background: rgba(255,255,255,.72);
  border: 1px solid rgba(0,80,140,.28);
  box-shadow: none; transition: all .15s ease;
}
.st-key-country_pool .stButton button:hover {
  background: #FFFFFF; border-color: rgba(0,80,140,.55);
  color: #00508C; box-shadow: 0 4px 12px rgba(0,80,140,.16);
}
.pool-head {
  display: flex; align-items: center; gap: 8px;
  font-size: 13.5px; font-weight: 800; color: #0B1C3F; letter-spacing: .3px;
  padding-bottom: 4px;
}
.pool-sub { font-size: 10.5px; font-weight: 700; color: #7A95BF; letter-spacing: 1.4px; }
.pool-count {
  margin-left: auto; font-size: 11px; font-weight: 700; color: #00508C;
  background: rgba(0,80,140,.09);
  border: 1px solid rgba(0,80,140,.20);
  border-radius: 999px; padding: 2px 10px;
}

/* 池内国家标签 */
.st-key-country_pool [data-baseweb="tag"] {
  background: linear-gradient(100deg, rgba(0,80,140,.11), rgba(247,245,238,.92)) !important;
  border: 1px solid rgba(0,80,140,.24) !important;
  border-radius: 999px !important;
  color: #4A2A2E !important;
  font-weight: 700 !important;
  font-size: 12.5px !important;
  height: 30px !important;
  padding: 0 10px !important;
  margin: 3px 4px 3px 0 !important;
  box-shadow: 0 3px 10px rgba(11,44,107,.08), inset 0 1px 0 rgba(255,255,255,.85);
  transition: all .15s ease;
}
.st-key-country_pool [data-baseweb="tag"]:hover {
  border-color: rgba(0,80,140,.55) !important;
  box-shadow: 0 6px 16px rgba(0,80,140,.18);
}
.st-key-country_pool [data-baseweb="tag"] svg {
  opacity: .85 !important;
  fill: #00508C !important;
  cursor: pointer;
  transition: transform .15s ease, opacity .15s ease;
}
.st-key-country_pool [data-baseweb="tag"]:hover svg { opacity: 1 !important; transform: scale(1.18); }

/* 进度条 */
[data-testid="stProgress"] > div > div > div > div {
  background: linear-gradient(90deg, #0B2C6B, #00508C, #1A7FC8);
}

/* ===== 首页底部品牌落款（大场景：带狮徽标） ===== */
.brand-footer {
  display: flex; align-items: center; justify-content: center; gap: 38px;
  max-width: 1320px; margin: 26px auto 6px;
  padding: 22px 40px;
  border-radius: 28px;
  background: linear-gradient(118deg, #0B2C6B 0%, #00508C 40%, #0078B8 72%, #00B4D8 100%);
  box-shadow: 0 22px 56px rgba(11,44,107,.28),
              inset 0 1px 0 rgba(255,255,255,.18),
              inset 0 -1px 0 rgba(0,0,0,.18),
              0 0 0 1px rgba(255,255,255,.06);
  position: relative; overflow: hidden;
}
.brand-footer::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(680px 280px at 26% 120%, rgba(255,255,255,.18), transparent 70%),
    radial-gradient(520px 220px at 80% -10%, rgba(0,180,216,.20), transparent 70%);
}
.brand-footer::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(108deg, transparent 0%, rgba(255,255,255,.06) 50%, transparent 100%);
  animation: footerShift 8s ease-in-out infinite;
}
@keyframes footerShift {
  0%, 100% { transform: translateX(-30%); }
  50%      { transform: translateX(30%); }
}
.brand-footer img {
  width: 268px; max-width: 60%; height: auto;
  position: relative; z-index: 1;
  filter: drop-shadow(0 8px 22px rgba(0,0,0,.22));
}
.bf-text { display: flex; flex-direction: column; gap: 3px; position: relative; z-index: 1; }
.bf-cn {
  font-size: 27px; font-weight: 800; color: #FFFFFF;
  letter-spacing: 3px; line-height: 1.15;
  text-shadow: 0 2px 14px rgba(90,6,12,.35);
}
.bf-en {
  font-size: 15px; font-weight: 800; color: #F6D79B;
  letter-spacing: 7px; line-height: 1.2;
}
.bf-tag {
  margin-top: 6px; font-size: 11.5px; font-weight: 600; color: rgba(255,255,255,.72);
  letter-spacing: 1.6px;
}
</style>
"""

# 地球贴图内嵌为 data URI（Streamlit Cloud 不开放 /app/static/ 静态目录）
BASE_CSS = BASE_CSS.replace(
    'url("/app/static/earth.jpg")',
    f'url("{common.img_data_uri(os.path.join(ROOT, "assets", "earth.jpg"))}")',
)

st.markdown(BASE_CSS, unsafe_allow_html=True)

home_page = st.Page(home.render, title="首页", icon="🍺", default=True)
settings_page = st.Page(settings.render, title="设置", icon="⚙️", url_path="settings")
customers_page = st.Page(customers.render, title="客户列表", icon="📋", url_path="customers")

registry.PAGES.update(
    {"home": home_page, "settings": settings_page, "customers": customers_page}
)

st.navigation([home_page, settings_page, customers_page], position="hidden").run()
