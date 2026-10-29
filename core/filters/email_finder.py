"""官网邮箱挖掘：抓取首页与联系页，提取企业邮箱"""
import re
import logging
from typing import List, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

# 常见无效/系统邮箱
BAD_PREFIX = ("noreply", "no-reply", "donotreply", "postmaster", "webmaster",
              "abuse", "hostmaster", "admin@", "example@", "test@")
BAD_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")
# 建站平台残留邮箱
BAD_DOMAINS = ("sentry.io", "wixpress.com", "example.com", "domain.com", "email.com",
               "yourdomain.com", "sentry-next.wixpress.com", "giftnote.com", "shopify.com",
               "squarespace.com", "wix.com", "hubspot.com", "mailchimp.com", "cloudflare.com")

CONTACT_KEYWORDS = ("contact", "kontakt", "contacto", "contact-us", "about", "about-us",
                    "impressum", "联系", "kapcsolat", "kontakti", "контакти")


def _clean(emails: Set[str], site_domain: str) -> List[str]:
    ok = []
    for e in emails:
        low = e.lower().strip(".,;:")
        if any(b in low for b in BAD_SUFFIX):
            continue
        if low.startswith(BAD_PREFIX):
            continue
        if any(d in low for d in BAD_DOMAINS):
            continue
        if len(low) > 60:
            continue
        ok.append(low)

    # 官网同域邮箱优先
    same = [e for e in ok if site_domain and site_domain.split(".")[0] in e.split("@")[-1]]
    rest = [e for e in ok if e not in same]
    # 优先 sales/info/contact 类
    priority = ("sales", "info", "contact", "import", "export", "office", "hello")
    same.sort(key=lambda e: next((i for i, p in enumerate(priority) if e.startswith(p)), 99))
    return list(dict.fromkeys(same + rest))


def find_emails(website: str, max_pages: int = 3, timeout: int = 10) -> List[str]:
    """从公司官网抓取邮箱，返回候选邮箱列表（同域优先）"""
    if not website:
        return []
    if not website.startswith("http"):
        website = "https://" + website

    parsed = urlparse(website)
    site_domain = parsed.netloc.lower().replace("www.", "")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    emails: Set[str] = set()
    pages_tried = 0
    contact_links: List[str] = []

    try:
        resp = requests.get(website, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            pages_tried += 1
            html = resp.text
            emails.update(EMAIL_RE.findall(html))
            # mailto 链接最可靠
            soup = BeautifulSoup(html, "lxml")
            for a in soup.select('a[href^="mailto:"]'):
                addr = a["href"].split("mailto:")[-1].split("?")[0]
                if "@" in addr:
                    emails.add(addr)
            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                if any(k in href for k in CONTACT_KEYWORDS) and len(contact_links) < 3:
                    contact_links.append(urljoin(website, a["href"]))
    except Exception as e:
        logger.debug(f"官网抓取失败 {website}: {e}")

    for link in contact_links[:max_pages - pages_tried]:
        try:
            r = requests.get(link, headers=headers, timeout=timeout)
            if r.status_code == 200:
                emails.update(EMAIL_RE.findall(r.text))
                soup = BeautifulSoup(r.text, "lxml")
                for a in soup.select('a[href^="mailto:"]'):
                    addr = a["href"].split("mailto:")[-1].split("?")[0]
                    if "@" in addr:
                        emails.add(addr)
        except Exception:
            continue

    return _clean(emails, site_domain)
