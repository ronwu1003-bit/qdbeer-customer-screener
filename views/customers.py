"""客户列表页：筛选、查看、导出（后续继续优化）"""
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from core import db
from views import common, registry


def _header():
    c1, c2, c3 = st.columns([6.5, 1.2, 1.2], vertical_alignment="center")
    with c1:
        common.header("客户列表", "已采集的潜在客户与联系方式", "📋")
    with c2:
        if st.button("← 返回首页", key="nav_home_2", width="stretch"):
            st.switch_page(registry.PAGES["home"])
    with c3:
        if st.button("⚙️ 设置", key="nav_settings_2", width="stretch"):
            st.switch_page(registry.PAGES["settings"])


def _to_excel_bytes(rows: list) -> bytes:
    buf = BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def render():
    _header()
    st.write("")

    s = db.get_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("客户总数", f"{s['total']:,}")
    c2.metric("有邮箱", f"{s['with_email']:,}")
    c3.metric("覆盖国家", s["countries"])
    c4.metric("白名单客户", f"{s['whitelist']:,}")

    st.write("")
    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        need_email = st.toggle("只看有邮箱", value=True)
    with f2:
        wl_only = st.toggle("只看白名单市场", value=False)
    with f3:
        search = st.text_input("搜索公司名 / 邮箱", placeholder="输入关键词过滤", label_visibility="collapsed")

    rows = db.get_filtered_customers(require_email=need_email, whitelist_only=wl_only, exclude_existing=False)
    if search:
        low = search.strip().lower()
        rows = [r for r in rows
                if low in (r.get("company_name") or "").lower()
                or low in (r.get("email") or "").lower()]

    if not rows:
        st.info("暂无匹配的客户，回首页点「开始今日搜索」采集一批。")
        return

    st.caption(f"共 {len(rows):,} 条")

    df = pd.DataFrame([
        {
            "公司名称": r.get("company_name", ""),
            "国家": common.COUNTRY_CN.get(r.get("country"), r.get("country") or ""),
            "邮箱": r.get("email", ""),
            "邮箱可信度": {"2": "强有效", "1": "弱有效"}.get(str(r.get("email_valid", 0)), "未验证"),
            "官网": r.get("website", ""),
            "来源": r.get("search_source", ""),
            "白名单": "是" if r.get("is_whitelist") else "",
        }
        for r in rows
    ])

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        height=460,
        column_config={
            "官网": st.column_config.LinkColumn("官网", display_text="打开"),
            "邮箱": st.column_config.TextColumn("邮箱", width="medium"),
        },
    )

    st.download_button(
        "⬇️ 导出 Excel",
        data=_to_excel_bytes(rows),
        file_name=f"qdbeer_customers_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
