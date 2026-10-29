"""搜索结果域名过滤：黑名单 + 竞争对手识别"""
import re
from typing import Dict, Optional

# 非企业站：目录/百科/新闻/地图/B2B平台/政府/社交媒体
DOMAIN_BLACKLIST = (
    # 百科/新闻/文档
    "wikipedia.org", "scribd.com", "oec.world", "bloomberg.com", "reuters.com",
    "nytimes.com", "bbc.com", "cnn.com", "theguardian.com", "forbes.com",
    # B2B 目录/平台
    "exportgenius.", "importgenius.", "tradekey.", "alibaba.", "made-in-china.",
    "globalsources.", "ec21.", "ecvv.", "dhgate.", "exporthub.", "gobizkorea.",
    "kompass.", "yellowpages.", "yelp.", "trustpilot.", "dnb.com", "bloomberg.com/profile",
    # 地图/点评
    "addismap.", "google.com/maps", "maps.google", "openstreetmap.",
    "tripadvisor.", "foursquare.", "yello.", "cylex.", "cybo.",
    # 政府/组织
    ".gov", "un.org", "worldbank.", "wto.org", "unido.", "who.int",
    # 社交/视频
    "facebook.", "twitter.", "x.com", "instagram.", "youtube.", "tiktok.",
    "linkedin.com/feed", "linkedin.com/posts", "reddit.", "pinterest.",
    # 招聘
    "indeed.", "glassdoor.", "linkedin.com/jobs", "linkedin.com/company",
    # 其他噪音
    "amazon.", "ebay.", "walmart.", "statista.", "researchgate.",
    "academia.edu", "slideshare.", "scribd.", "issuu.", "coursehero.",
    "2merkato.com",  # 埃塞分类目录
)

# 啤酒行业国际巨头 + 主要竞争对手（不是潜在客户）
COMPETITOR_BLACKLIST = (
    "heineken", "carlsberg", "ab-inbev", "ab inbev", "anheuser-busch",
    "budweiser", "budvar", "stella artois", "corona", "becks", "becker",
    "molson coors", "coors", "miller", "pabst", "diageo", "guinness",
    "pernod", "pernod-ricard", "asahi", "kirin", "sapporo", "suntory",
    "tsingtao", "qingdao",  # 青岛啤酒自己
    "carlsberggroup", "heinekenethiopia", "bavaria", "grolsch",
    "paulaner", "erdinger", "bitburger", "warsteiner", "krombacher",
    "efes", "anadolu", "sabmiller", "castel", "bgi ethiopia",  # BGI 是埃塞本地大厂
    "dashen",  # 埃塞本地啤酒厂
)

# 域名级别的竞争对手关键词（用来在 website/company_name 上匹配）
_COMP_PAT = re.compile("|".join(re.escape(c) for c in COMPETITOR_BLACKLIST), re.I)


def is_domain_blocked(url: str) -> bool:
    """URL 是否命中域名黑名单"""
    if not url:
        return False
    low = url.lower()
    return any(b in low for b in DOMAIN_BLACKLIST)


def is_competitor(company_name: str = "", website: str = "") -> bool:
    """是否为啤酒行业竞争对手/巨头"""
    text = f"{company_name or ''} {website or ''}".lower()
    return bool(_COMP_PAT.search(text))


def filter_result(row: Dict) -> Optional[str]:
    """
    对单条搜索结果做过滤判断。
    返回 None 表示通过；返回字符串表示被丢弃的原因。
    """
    website = row.get("website", "") or ""
    company = row.get("company_name", "") or ""

    if is_domain_blocked(website):
        return "domain_blacklist"
    if is_competitor(company, website):
        return "competitor"
    return None
