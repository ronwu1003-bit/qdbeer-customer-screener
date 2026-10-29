"""白名单国家管理 + 同义词扩展 + 关键词配置"""
import os
import yaml
from typing import List, Dict, Set


# ---- 同义词词库（啤酒行业 + B2B 销售场景）----
SYNONYM_MAP = {
    # 经销商类
    "importer": ["importer", "import company", "importing company", "beer importer"],
    "distributor": ["distributor", "distribution company", "beer distributor", "trade distributor"],
    "wholesale": ["wholesale", "wholesaler", "wholesale company", "bulk supplier"],
    "supplier": ["supplier", "supply company", "trade supplier"],
    # 产品类
    "beer": ["beer", "craft beer", "imported beer", "premium beer"],
    "alcohol": ["alcohol", "alcoholic beverages", "beverage", "liquor"],
    # 场景类
    "restaurant": ["restaurant", "restaurant chain", "pub", "bar", "hotel"],
    "retail": ["retail", "supermarket", "grocery", "convenience store"],
    "trade show": ["trade show", "expo", "fair"],
}


def expand_keywords(base_keywords: List[str], add_synonyms: bool = True) -> List[str]:
    """
    扩展关键词：对基础词组进行同义词组合
    例：["beer importer"] → ["beer importer", "craft beer importer", "beer importing company", ...]
    """
    expanded = list(base_keywords)

    if not add_synonyms:
        return list(set(expanded))

    # 简单扩展：如果基础词里包含 SYNONYM_MAP 里的某个词，替换成所有同义词版本
    extra = set()
    for kw in base_keywords:
        for key, syns in SYNONYM_MAP.items():
            # 如果关键词里包含这个 key
            if key in kw.lower():
                for syn in syns:
                    if syn != key:
                        variant = kw.lower().replace(key, syn)
                        extra.add(variant)

    expanded.extend(extra)
    # 去重，保持原始大小写
    seen = set()
    result = []
    for kw in expanded:
        normalized = kw.lower().strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def load_keywords_config(path: str) -> Dict:
    """加载关键词 YAML 配置"""
    default = {
        "global": [
            "beer importer",
            "beer distributor",
            "wholesale beer supplier",
            "imported beer company",
            "craft beer distributor",
            "alcohol beverage supplier",
        ],
        "by_country": {},
    }
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            default.update(data)
        except Exception as e:
            print(f"加载关键词配置失败: {e}")
    return default


def save_keywords_config(path: str, config: Dict):
    """保存关键词 YAML 配置"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def load_whitelist_countries(path: str) -> Set[str]:
    """加载白名单国家列表"""
    whitelist = set()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    country = line.strip()
                    if country and not country.startswith("#"):
                        whitelist.add(country.lower())
        except Exception as e:
            print(f"加载白名单失败: {e}")
    return whitelist


def save_whitelist_countries(path: str, countries: List[str]):
    """保存白名单国家"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# 青岛啤酒海外目标市场白名单\n")
        f.write("# 每行一个国家名（英文）或 ISO 代码，# 开头为注释\n\n")
        for c in sorted(set(countries)):
            f.write(c.strip() + "\n")


# ---- 密钥管理：优先读环境变量，其次 st.secrets（Streamlit Cloud），最后才用 yaml 里的值 ----
# 环境变量名 → 配置路径
ENV_KEY_MAP = (
    ("SERPER_API_KEY", ("serper", "api_key")),
    ("BING_API_KEY", ("bing_api", "api_key")),
    ("GOOGLE_API_KEY", ("google", "api_key")),
    ("GOOGLE_CX_ID", ("google", "cx_id")),
    ("SEARCH_PROXY", ("network", "proxy")),
)


def get_secret(name: str, default: str = "") -> str:
    """读取密钥：环境变量优先，其次 st.secrets；本地 CLI 环境下安全回退"""
    val = os.environ.get(name, "").strip()
    if val:
        return val
    try:
        import streamlit as st
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def apply_env_overrides(cfg: Dict) -> Dict:
    """把环境变量 / st.secrets 中的密钥覆盖到 yaml 配置上"""
    cfg = cfg or {}
    for env_name, (sect, key) in ENV_KEY_MAP:
        val = get_secret(env_name)
        if val:
            cfg.setdefault(sect, {})[key] = val
    # 已通过密钥注入的渠道默认启用
    for sect in ("serper", "bing_api", "google"):
        if cfg.get(sect, {}).get("api_key"):
            cfg[sect].setdefault("enabled", True)
    return cfg


# ---- 国家 ISO 代码辅助映射（常用）----
ISO_COUNTRY_MAP = {
    "usa": "United States",
    "us": "United States",
    "united states": "United States",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "gb": "United Kingdom",
    "japan": "Japan",
    "jp": "Japan",
    "germany": "Germany",
    "de": "Germany",
    "france": "France",
    "fr": "France",
    "australia": "Australia",
    "au": "Australia",
    "canada": "Canada",
    "ca": "Canada",
    "korea": "South Korea",
    "south korea": "South Korea",
    "kr": "South Korea",
    "singapore": "Singapore",
    "sg": "Singapore",
    "thailand": "Thailand",
    "th": "Thailand",
    "malaysia": "Malaysia",
    "my": "Malaysia",
    "indonesia": "Indonesia",
    "id": "Indonesia",
    "vietnam": "Vietnam",
    "vn": "Vietnam",
    "philippines": "Philippines",
    "ph": "Philippines",
    "netherlands": "Netherlands",
    "nl": "Netherlands",
    "spain": "Spain",
    "es": "Spain",
    "italy": "Italy",
    "it": "Italy",
    "brazil": "Brazil",
    "br": "Brazil",
    "mexico": "Mexico",
    "mx": "Mexico",
    "russia": "Russia",
    "ru": "Russia",
    # ===== 2026 白名单市场 =====
    "ethiopia": "Ethiopia",
    "et": "Ethiopia",
    "埃塞俄比亚": "Ethiopia",
    "埃萨俄比亚": "Ethiopia",
    "cameroon": "Cameroon",
    "cm": "Cameroon",
    "喀麦隆": "Cameroon",
    "angola": "Angola",
    "ao": "Angola",
    "安哥拉": "Angola",
    "paraguay": "Paraguay",
    "py": "Paraguay",
    "巴拉圭": "Paraguay",
    "chile": "Chile",
    "cl": "Chile",
    "智利": "Chile",
    "ecuador": "Ecuador",
    "ec": "Ecuador",
    "厄瓜多尔": "Ecuador",
    "croatia": "Croatia",
    "hr": "Croatia",
    "克罗地亚": "Croatia",
    "bosnia": "Bosnia and Herzegovina",
    "bosnia and herzegovina": "Bosnia and Herzegovina",
    "ba": "Bosnia and Herzegovina",
    "波黑": "Bosnia and Herzegovina",
    "波斯尼亚和黑塞哥维那": "Bosnia and Herzegovina",
    "lithuania": "Lithuania",
    "lt": "Lithuania",
    "立陶宛": "Lithuania",
    "latvia": "Latvia",
    "lv": "Latvia",
    "拉脱维亚": "Latvia",
    "bulgaria": "Bulgaria",
    "bg": "Bulgaria",
    "保加利亚": "Bulgaria",
}


def normalize_country(name: str) -> str:
    """把国家名或 ISO 代码标准化成统一英文名"""
    if not name:
        return ""
    name_lower = name.strip().lower()
    return ISO_COUNTRY_MAP.get(name_lower, name.strip())
