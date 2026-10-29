"""设置页：搜索渠道、API Key、关键词、白名单（后台功能，与首页交互分离）"""
import os
from datetime import datetime

import streamlit as st

from core import db as _db
from core.filters.config_manager import (
    load_whitelist_countries,
    save_keywords_config,
    save_whitelist_countries,
)
from views import common, registry
from views.common import KEYWORDS_CONFIG_PATH, WHITELIST_PATH


def _header():
    c1, c2 = st.columns([7, 1.3], vertical_alignment="center")
    with c1:
        common.header("系统设置", "渠道、密钥与词库配置", "⚙️")
    with c2:
        if st.button("← 返回首页", key="nav_home", width="stretch"):
            st.switch_page(registry.PAGES["home"])


def _channels(cfg: dict):
    st.markdown('<div class="sec-title">搜索渠道</div>', unsafe_allow_html=True)
    st.caption("启用的渠道会在首页「开始今日搜索」时依次执行")

    rows = [
        ("serper", "Serper（Google 结果）", "注册送 2500 次，国内可直连"),
        ("bing_api", "Bing Web Search API", "Azure 免费 1000 次/月"),
        ("google", "Google CSE", "需代理，每天 100 次免费"),
        ("linkedin", "领英公开搜索", "无需密钥，仅公开公司与链接"),
    ]
    c1, c2 = st.columns(2)
    for i, (key, title, desc) in enumerate(rows):
        with (c1 if i % 2 == 0 else c2):
            cfg.setdefault(key, {})["enabled"] = st.toggle(
                f"{title}　·　{desc}",
                value=cfg.get(key, {}).get("enabled", False),
                key=f"ch_{key}",
            )


def _keys(cfg: dict):
    st.markdown('<div class="sec-title">API 密钥与网络</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        serper_key = st.text_input(
            "Serper API Key",
            value=cfg.get("serper", {}).get("api_key", ""),
            type="password",
            help="google.serper.dev → Dashboard → API Key",
        )
        google_key = st.text_input(
            "Google API Key",
            value=cfg.get("google", {}).get("api_key", ""),
            type="password",
        )
    with c2:
        bing_key = st.text_input(
            "Bing API Key",
            value=cfg.get("bing_api", {}).get("api_key", ""),
            type="password",
            help="Azure → Bing Search v7 → Keys and Endpoint → KEY 1",
        )
        google_cx = st.text_input(
            "Google CX ID",
            value=cfg.get("google", {}).get("cx_id", ""),
        )
    proxy = st.text_input(
        "代理地址（可选）",
        value=cfg.get("network", {}).get("proxy", ""),
        placeholder="http://127.0.0.1:7890",
    )

    if st.button("💾 保存配置", key="save_cfg", type="primary"):
        cfg.setdefault("serper", {})["api_key"] = serper_key.strip()
        cfg.setdefault("bing_api", {})["api_key"] = bing_key.strip()
        cfg.setdefault("google", {})["api_key"] = google_key.strip()
        cfg["google"]["cx_id"] = google_cx.strip()
        cfg.setdefault("network", {})["proxy"] = proxy.strip()
        common.save_search_config(cfg)
        st.session_state.search_config = cfg
        st.success("已保存")


def _keywords():
    st.markdown('<div class="sec-title">搜索关键词</div>', unsafe_allow_html=True)
    cfg = st.session_state.keywords_config
    global_kw = cfg.get("global", [])

    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    with c1:
        new_kw = st.text_input(
            "新增通用关键词（英文或当地语言）",
            placeholder="如: beer wholesaler",
            label_visibility="collapsed",
        )
    with c2:
        if st.button("➕ 添加", key="add_kw", width="stretch") and new_kw.strip():
            kw = new_kw.strip()
            if kw not in global_kw:
                global_kw.append(kw)
                cfg["global"] = global_kw
                save_keywords_config(KEYWORDS_CONFIG_PATH, cfg)
                st.session_state.keywords_config = cfg
                st.rerun()
            else:
                st.warning("关键词已存在")

    to_delete = []
    cols = st.columns(3)
    for i, kw in enumerate(global_kw):
        with cols[i % 3]:
            if st.checkbox(f"❌ {kw}", key=f"del_kw_{kw}"):
                to_delete.append(kw)
    if to_delete and st.button("🗑️ 删除选中关键词", key="del_kw_btn"):
        for kw in to_delete:
            global_kw.remove(kw)
        cfg["global"] = global_kw
        save_keywords_config(KEYWORDS_CONFIG_PATH, cfg)
        st.session_state.keywords_config = cfg
        st.rerun()


def _whitelist():
    st.markdown('<div class="sec-title">白名单市场</div>', unsafe_allow_html=True)
    st.caption("2026 年目标市场，会出现在首页勾选列表的最前面")

    current = load_whitelist_countries(WHITELIST_PATH)
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    with c1:
        new_c = st.text_input(
            "新增国家（英文名）",
            placeholder="如: United States",
            label_visibility="collapsed",
        )
    with c2:
        if st.button("➕ 添加", key="add_c", width="stretch") and new_c.strip():
            current.add(new_c.strip().lower())
            save_whitelist_countries(WHITELIST_PATH, sorted(current))
            st.session_state.whitelist = current
            st.rerun()

    to_remove = []
    cols = st.columns(4)
    for i, c in enumerate(sorted(current)):
        with cols[i % 4]:
            if st.checkbox(f"❌ {c.title()}", key=f"del_c_{c}"):
                to_remove.append(c)
    if to_remove and st.button("🗑️ 删除选中国家", key="del_c_btn"):
        for c in to_remove:
            current.discard(c)
        save_whitelist_countries(WHITELIST_PATH, sorted(current))
        st.session_state.whitelist = current
        st.rerun()


def _backup():
    st.markdown('<div class="sec-title">数据备份与恢复</div>', unsafe_allow_html=True)
    st.caption("线上部署的数据会在重启/重新部署后清空，请定期下载备份；需要恢复时上传备份文件即可")

    c1, c2 = st.columns(2)
    with c1:
        if os.path.exists(_db.DB_PATH):
            with open(_db.DB_PATH, "rb") as f:
                payload = f.read()
            st.download_button(
                f"⬇️ 下载数据备份（{len(payload) / 1024:.0f} KB）",
                data=payload,
                file_name=f"customers_backup_{datetime.now():%Y%m%d_%H%M}.db",
                mime="application/octet-stream",
                width="stretch",
            )
        else:
            st.info("暂无数据可备份")
    with c2:
        up = st.file_uploader("⬆️ 上传备份文件以恢复（会覆盖当前全部数据）", type=["db"])
        if up is not None:
            blob = up.getvalue()
            if not blob.startswith(b"SQLite format 3"):
                st.error("文件无效：不是本系统导出的 SQLite 备份")
            elif st.button("确认恢复并覆盖当前数据", key="restore_db", type="primary"):
                tmp = _db.DB_PATH + ".uploading"
                with open(tmp, "wb") as f:
                    f.write(blob)
                os.replace(tmp, _db.DB_PATH)
                _db.init_db()
                st.success("已恢复备份数据")
                st.rerun()


def render():
    _header()
    st.write("")

    cfg = st.session_state.search_config
    _channels(cfg)
    st.write("")
    _keys(cfg)

    st.divider()
    _keywords()

    st.divider()
    _whitelist()

    st.divider()
    _backup()
