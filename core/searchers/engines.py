"""搜索引擎：API 优先（Serper / Bing API / Google CSE），网页抓取兜底"""
import re
import time
import logging
import urllib.parse
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

# 白名单市场对应的国家代码（Serper 用 gl，Bing API 用 mkt）
COUNTRY_CODES = {
    "Ethiopia": ("et", "en-ET"),
    "Cameroon": ("cm", "fr-CM"),
    "Angola": ("ao", "pt-AO"),
    "Paraguay": ("py", "es-PY"),
    "Chile": ("cl", "es-CL"),
    "Ecuador": ("ec", "es-EC"),
    "Croatia": ("hr", "hr-HR"),
    "Bosnia and Herzegovina": ("ba", "en-US"),
    "Lithuania": ("lt", "lt-LT"),
    "Latvia": ("lv", "lv-LV"),
    "Bulgaria": ("bg", "bg-BG"),
}

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


class BaseSearcher(ABC):
    """搜索引擎基类：统一会话、代理、延时"""

    SOURCE = "base"

    def __init__(self, proxy: str = ""):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.delay = 1.5
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    @abstractmethod
    def search(self, keyword: str, country: str = "", max_results: int = 20) -> List[Dict]:
        pass

    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        time.sleep(self.delay)
        kwargs.setdefault("timeout", 25)
        try:
            resp = self.session.request(method, url, **kwargs)
            return resp
        except Exception as e:
            logger.warning(f"请求失败 {url[:60]}: {e}")
            return None

    @staticmethod
    def extract_domain(url: str) -> str:
        match = re.search(r'https?://([^/]+)', url or "")
        return match.group(1).lower().lstrip("www.") if match else ""

    @staticmethod
    def guess_company_name(title: str, domain: str) -> str:
        title = (title or "").strip()
        for sep in [" - ", " | ", " – ", ": ", " » ", "｜"]:
            if sep in title:
                title = title.split(sep)[0]
                break
        title = title.strip()
        if len(title) < 3 or len(title) > 80:
            first = (domain or "").split(".")[0]
            title = first.replace("-", " ").replace("_", " ").title()
        return title

    @staticmethod
    def extract_email(text: str) -> str:
        for m in EMAIL_RE.findall(text or ""):
            low = m.lower()
            if not low.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
                return low
        return ""

    def _build_row(self, title, link, snippet, country, keyword):
        domain = self.extract_domain(link)
        return {
            "company_name": self.guess_company_name(title, domain),
            "website": link or (f"https://{domain}" if domain else ""),
            "email": self.extract_email(snippet),
            "country": country,
            "search_source": self.SOURCE,
            "keywords_matched": keyword,
        }


class SerperSearcher(BaseSearcher):
    """Serper.dev —— 返回 Google 搜索结果，国内网络可直连，免费 2500 次"""

    SOURCE = "serper"
    URL = "https://google.serper.dev/search"

    def __init__(self, api_key: str, proxy: str = ""):
        super().__init__(proxy)
        self.api_key = api_key

    def search(self, keyword: str, country: str = "", max_results: int = 20) -> List[Dict]:
        if not self.api_key:
            raise ValueError("缺少 Serper API Key")

        query = f"{keyword} {country}".strip()
        gl, _ = COUNTRY_CODES.get(country, ("", ""))
        results = []
        pages = max(1, (max_results + 9) // 10)

        for page in range(1, pages + 1):
            payload = {"q": query, "num": min(10, max_results), "page": page, "hl": "en"}
            if gl:
                payload["gl"] = gl
            resp = self._request(
                "POST", self.URL, json=payload,
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            )
            if not resp or resp.status_code != 200:
                if resp is not None:
                    logger.warning(f"Serper 返回 {resp.status_code}: {resp.text[:120]}")
                break
            data = resp.json()
            for item in data.get("organic", []):
                results.append(self._build_row(
                    item.get("title", ""), item.get("link", ""),
                    item.get("snippet", ""), country, keyword,
                ))
            if len(results) >= max_results:
                break
        return results[:max_results]


class BingApiSearcher(BaseSearcher):
    """Bing Web Search API —— Azure 免费 1000 次/月"""

    SOURCE = "bing_api"
    URL = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self, api_key: str, proxy: str = ""):
        super().__init__(proxy)
        self.api_key = api_key

    def search(self, keyword: str, country: str = "", max_results: int = 20) -> List[Dict]:
        if not self.api_key:
            raise ValueError("缺少 Bing API Key")

        query = f"{keyword} {country}".strip()
        _, mkt = COUNTRY_CODES.get(country, ("", "en-US"))
        results = []
        offset = 0
        while len(results) < max_results:
            resp = self._request("GET", self.URL, headers={"Ocp-Apim-Subscription-Key": self.api_key}, params={
                "q": query, "count": min(50, max_results - len(results)),
                "offset": offset, "mkt": mkt, "setLang": "en", "responseFilter": "Webpages",
            })
            if not resp or resp.status_code != 200:
                if resp is not None:
                    logger.warning(f"Bing API 返回 {resp.status_code}: {resp.text[:120]}")
                break
            items = resp.json().get("webPages", {}).get("value", [])
            if not items:
                break
            for it in items:
                results.append(self._build_row(
                    it.get("name", ""), it.get("url", ""), it.get("snippet", ""), country, keyword,
                ))
            offset += len(items)
        return results[:max_results]


class GoogleSearcher(BaseSearcher):
    """Google Custom Search API（国外网络可用；国内需代理）"""

    SOURCE = "google"
    URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str = "", cx_id: str = "", proxy: str = ""):
        super().__init__(proxy)
        self.api_key = api_key
        self.cx_id = cx_id

    def search(self, keyword: str, country: str = "", max_results: int = 20) -> List[Dict]:
        if not (self.api_key and self.cx_id):
            raise ValueError("缺少 Google API Key 或 CX ID")

        query = f"{keyword} {country}".strip()
        gl, _ = COUNTRY_CODES.get(country, ("", ""))
        results = []
        for start in range(1, max_results, 10):
            params = {"key": self.api_key, "cx": self.cx_id, "q": query, "num": 10, "start": start}
            if gl:
                params["gl"] = gl
            resp = self._request("GET", self.URL, params=params)
            if not resp or resp.status_code != 200:
                if resp is not None:
                    logger.warning(f"Google API 返回 {resp.status_code}: {resp.text[:120]}")
                break
            for item in resp.json().get("items", []) or []:
                results.append(self._build_row(
                    item.get("title", ""), item.get("link", ""), item.get("snippet", ""),
                    country, keyword,
                ))
        return results[:max_results]


class BingSearcher(BaseSearcher):
    """Bing 网页版抓取（国内网络结果不可用，需代理；保留作兜底）"""

    SOURCE = "bing"

    def search(self, keyword: str, country: str = "", max_results: int = 20) -> List[Dict]:
        query = f"{keyword} {country}".strip()
        results = []
        for page in range(max(1, (max_results + 9) // 10)):
            url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&first={page * 10 + 1}&ensearch=1"
            resp = self._request("GET", url, headers={
                "User-Agent": self.ua.random,
                "Accept-Language": "en-US,en;q=0.9",
            })
            if not resp:
                break
            soup = BeautifulSoup(resp.text, "lxml")
            for li in soup.select("li.b_algo"):
                h2 = li.find("h2")
                a = h2.find("a") if h2 else None
                if not a:
                    continue
                snippet_el = li.find("p")
                results.append(self._build_row(
                    a.get_text(strip=True), a.get("href", ""),
                    snippet_el.get_text(strip=True) if snippet_el else "", country, keyword,
                ))
            if len(results) >= max_results:
                break
        return results[:max_results]


class LinkedInPublicSearcher(BaseSearcher):
    """领英公开公司搜索页（不登录，只取公开可见信息）"""

    SOURCE = "linkedin"

    def search(self, keyword: str, country: str = "", max_results: int = 20) -> List[Dict]:
        query = f"{keyword} {country}".strip()
        url = f"https://www.linkedin.com/search/results/companies/?keywords={urllib.parse.quote(query)}"
        resp = self._request("GET", url, headers={
            "User-Agent": self.ua.random,
            "Accept-Language": "en-US,en;q=0.9",
        })
        if not resp:
            return []

        results = []
        try:
            soup = BeautifulSoup(resp.text, "lxml")
            for result in soup.select("li.search-result"):
                head = result.find("h3") or result.find(class_="name")
                if not head:
                    continue
                link = result.find("a", href=True)
                results.append({
                    "company_name": head.get_text(strip=True),
                    "website": link["href"] if link else "",
                    "email": "",
                    "country": country,
                    "search_source": self.SOURCE,
                    "keywords_matched": keyword,
                })
        except Exception as e:
            logger.warning(f"领英解析异常: {e}")

        return results[:max_results]


def build_searcher(engine: str, cfg: dict, proxy: str = "") -> BaseSearcher:
    """按渠道名创建搜索器"""
    engine = (engine or "").lower()
    if engine == "serper":
        return SerperSearcher(cfg.get("serper", {}).get("api_key", ""), proxy)
    if engine in ("bing_api", "bingapi"):
        return BingApiSearcher(cfg.get("bing_api", {}).get("api_key", ""), proxy)
    if engine == "google":
        g = cfg.get("google", {})
        return GoogleSearcher(g.get("api_key", ""), g.get("cx_id", ""), proxy)
    if engine == "linkedin":
        return LinkedInPublicSearcher(proxy)
    if engine == "bing":
        return BingSearcher(proxy)
    raise ValueError(f"未知渠道: {engine}")
