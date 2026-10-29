"""视图层共享常量与配置加载"""
import os

import yaml

from core.filters.config_manager import (
    apply_env_overrides,
    load_keywords_config,
    load_whitelist_countries,
    normalize_country,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT, "config")
DATA_DIR = os.path.join(ROOT, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
SEARCH_CONFIG_PATH = os.path.join(CONFIG_DIR, "search_config.yaml")
KEYWORDS_CONFIG_PATH = os.path.join(CONFIG_DIR, "keywords.yaml")
WHITELIST_PATH = os.path.join(CONFIG_DIR, "whitelist_countries.txt")

BRAND = "#1F4E79"
ACCENT = "#E63946"
WHITELIST_COLOR = "#2E7D32"
INK = "#0F172A"
MUTED = "#64748B"

# 白名单国家中文名
COUNTRY_CN = {
    "Ethiopia": "埃塞俄比亚",
    "Cameroon": "喀麦隆",
    "Angola": "安哥拉",
    "Paraguay": "巴拉圭",
    "Chile": "智利",
    "Ecuador": "厄瓜多尔",
    "Croatia": "克罗地亚",
    "Bosnia and Herzegovina": "波黑",
    "Lithuania": "立陶宛",
    "Latvia": "拉脱维亚",
    "Bulgaria": "保加利亚",
}

FLAG = {
    "Ethiopia": "🇪🇹", "Cameroon": "🇨🇲", "Angola": "🇦🇴", "Paraguay": "🇵🇾",
    "Chile": "🇨🇱", "Ecuador": "🇪🇨", "Croatia": "🇭🇷",
    "Bosnia and Herzegovina": "🇧🇦", "Lithuania": "🇱🇹",
    "Latvia": "🇱🇻", "Bulgaria": "🇧🇬",
}


def label(country: str) -> str:
    """国家显示名：中文 + 英文（Windows 下旗帜 emoji 会退化成字母，故不使用）"""
    cn = COUNTRY_CN.get(country)
    return f"{cn} {country}" if cn and cn != country else country


def flat(html: str) -> str:
    """去掉每行缩进，避免被 Markdown 当成代码块渲染"""
    return "".join(line.strip() for line in html.strip().splitlines())


def img_data_uri(path: str) -> str:
    """把本地图片转成 base64 data URI（用于 HTML 内嵌）"""
    import base64

    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


LOGO_PATH = os.path.join(ROOT, "assets", "tsingtao_mark.png")


def brand_text() -> str:
    """品牌中英文名（徽标用 st.image 单独渲染，保证稳定）"""
    return flat("""
    <div style="padding-left:2px;">
      <div class="brand-cn">青岛啤酒</div>
      <div class="brand-en">TSINGTAO</div>
    </div>
    """)


def brand_footer() -> str:
    """首页底部品牌落款：大场景使用带狮徽标"""
    return flat("""
    <div class="brand-footer">
      <img src="/app/static/tsingtao_lion.png" alt="TSINGTAO"/>
      <div class="bf-text">
        <div class="bf-cn">青岛啤酒</div>
        <div class="bf-en">TSINGTAO</div>
        <div class="bf-tag">让世界品味中国 · SINCE 1903</div>
      </div>
    </div>
    """)


def header(title: str, subtitle: str, icon: str):
    """统一页头：图标 + 标题 + 副标题"""
    import streamlit as st

    st.markdown(
        flat(f"""
        <div style="display:flex;align-items:center;gap:11px;">
          <div style="width:36px;height:36px;border-radius:12px;
               background:linear-gradient(135deg,rgba(205,26,33,.10),rgba(247,245,238,.95));
               border:1px solid rgba(255,255,255,.95);
               display:flex;align-items:center;justify-content:center;font-size:18px;
               box-shadow:0 8px 20px rgba(142,17,25,.13);">{icon}</div>
          <div>
            <div style="font-size:17px;font-weight:800;color:#2A1F22;letter-spacing:.3px;">{title}</div>
            <div style="font-size:11.5px;color:#8A7F8B;font-weight:600;letter-spacing:.4px;">{subtitle}</div>
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def load_search_config() -> dict:
    """加载搜索配置：yaml 文件（可不存在）+ 环境变量 / st.secrets 密钥覆盖"""
    cfg = {}
    if os.path.exists(SEARCH_CONFIG_PATH):
        with open(SEARCH_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    return apply_env_overrides(cfg)


def save_search_config(cfg: dict):
    with open(SEARCH_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)


def init_session_state():
    """初始化 Streamlit 会话级配置缓存"""
    import streamlit as st

    if "search_config" not in st.session_state:
        st.session_state.search_config = load_search_config()
    if "keywords_config" not in st.session_state:
        st.session_state.keywords_config = load_keywords_config(KEYWORDS_CONFIG_PATH)
    if "whitelist" not in st.session_state:
        st.session_state.whitelist = load_whitelist_countries(WHITELIST_PATH)


def whitelist_list() -> list:
    """白名单国家（标准化英文名，按 config 中出现顺序）"""
    import streamlit as st

    raw = st.session_state.get("whitelist", set())
    return [normalize_country(c) for c in sorted(raw)]
