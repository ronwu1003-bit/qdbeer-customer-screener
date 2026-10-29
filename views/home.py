"""首页：一键今日搜索（可中途停止）+ 旋转地球与全局进度 + 搜索参数 + 目标市场"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from core import db
from core.filters.config_manager import expand_keywords, normalize_country
from core.filters.domain_filter import filter_result
from core.filters.email_finder import find_emails
from core.filters.email_validator import validate_email
from core.searchers.engines import build_searcher
from views import common, registry

# 大按钮上循环出现的多语种文案
CTA_LANGS = [
    "开始今日搜索",
    "Start Today's Search",
    "Iniciar la búsqueda de hoy",
    "今日の検索を開始",
    "Поиск на сегодня",
    "Recherche du jour",
    "Heutige Suche starten",
    "Inizia la ricerca di oggi",
    "Começar a busca de hoje",
    "ابدأ بحث اليوم",
]

ENGINES = {
    "serper": "Serper",
    "bing_api": "Bing API",
    "google": "Google CSE",
    "linkedin": "领英",
}

GLOBE_HTML = """
<div class="globe-stage"><div class="earth"></div></div>
"""


def _flat(html: str) -> str:
    """去掉每行缩进，避免被 Markdown 识别为代码块"""
    return "".join(line.strip() for line in html.strip().splitlines())


def _cta_overlay() -> str:
    spans = "".join(
        f'<span style="animation-delay:-{i * 2}s">{t}</span>'
        for i, t in enumerate(CTA_LANGS)
    )
    return _flat(f'<div class="cta-overlay">{spans}</div>')


def _stop_overlay() -> str:
    return _flat('<div class="cta-overlay"><span class="always">停止搜索</span></div>')


def _stats_html(s: dict) -> str:
    return _flat(f"""
    <div class="stat-grid">
      <div class="stat-cell">
        <div class="stat-num">{s['searches']:,}<em>次</em></div>
        <div class="stat-label">已完成搜索</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num">{s['total']:,}</div>
        <div class="stat-label">累计客户</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num">{s['countries']}<em>国</em></div>
        <div class="stat-label">覆盖国家</div>
      </div>
      <div class="stat-cell">
        <div class="stat-num">{s['whitelist']:,}</div>
        <div class="stat-label">白名单市场客户</div>
      </div>
    </div>
    """)


def _mark_pending():
    st.session_state.pending_run = True


def _mark_stop():
    job = st.session_state.get("job")
    if job:
        job["cancel"].set()
        job["state"]["stopping"] = True


def _job_running() -> bool:
    job = st.session_state.get("job")
    return bool(job) and not job["state"]["finished"]


def _topbar():
    left, mid, right = st.columns([9, 1.45, 1.3], vertical_alignment="center")
    with left:
        cl, ct = st.columns([0.42, 4], vertical_alignment="center")
        with cl:
            with st.container(key="brand_logo"):
                st.image(common.LOGO_PATH, width=34)
        with ct:
            st.markdown(common.brand_text(), unsafe_allow_html=True)
    with mid:
        if st.button("📋 客户列表", key="nav_customers", width="stretch"):
            st.switch_page(registry.PAGES["customers"])
    with right:
        if st.button("⚙️ 设置", key="nav_settings", width="stretch"):
            st.switch_page(registry.PAGES["settings"])


def _cta_button():
    """同一位置：空闲显示「开始今日搜索」，运行中切换为「停止搜索」"""
    with st.container(key="hero_cta"):
        if _job_running():
            st.markdown(_stop_overlay(), unsafe_allow_html=True)
            st.button("停止搜索", key="stop_search", width="stretch", on_click=_mark_stop)
        else:
            st.markdown(_cta_overlay(), unsafe_allow_html=True)
            st.button("开始今日搜索", key="run_today", width="stretch", on_click=_mark_pending)


def _progress_block(state: dict):
    total = state.get("total") or 0
    val = min(state.get("done", 0) / max(total, 1) * 0.9, 0.9) if total else 0.0
    extra = {"enrich": 0.93, "mx": 0.97, "insert": 1.0}.get(state.get("phase"))
    if extra:
        val = max(val, extra)
    st.progress(val)
    if state.get("stopping"):
        st.info("正在停止…已采集的客户会先保存")
    else:
        msg = state.get("msg") or "准备中…"
        if total:
            msg = f"{msg}　({state['done']}/{total})"
        st.info(msg)


def _summary_block(state: dict):
    if state.get("error"):
        st.error(f"搜索中断：{state['error']}")
        return
    if state.get("cancelled"):
        st.warning(
            f"已停止：本次新增 **{state.get('inserted', 0)}** 家客户，"
            f"其中 **{state.get('with_email', 0)}** 家带邮箱。"
        )
    else:
        st.success(
            f"今日搜索完成：新增 **{state.get('inserted', 0)}** 家客户，"
            f"其中 **{state.get('with_email', 0)}** 家带邮箱，"
            f"覆盖 **{state.get('country_count', 0)}** 个市场。"
        )
    if st.button("查看客户列表 →", key="goto_list"):
        st.switch_page(registry.PAGES["customers"])


def _hero_card():
    s = db.get_stats()
    with st.container(key="hero_card"):
        c1, c2 = st.columns([1.2, 1], vertical_alignment="center", gap="large")
        with c1:
            st.markdown(_flat(GLOBE_HTML), unsafe_allow_html=True)
        with c2:
            st.markdown(_stats_html(s), unsafe_allow_html=True)


def _search_params() -> dict:
    st.markdown('<div class="sec-title">搜索参数</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1], vertical_alignment="top")
    with c1:
        max_results = st.slider("每关键词最大结果数", 5, 50, 20, 5)
    with c2:
        add_synonyms = st.toggle("自动扩展同义词", value=True,
                                 help="把 importer 扩展为 import company 等变体")
        do_mx = st.toggle("MX 邮件服务器检查", value=True,
                          help="验证邮箱域名是否真实可收信")
    with c3:
        do_enrich = st.toggle("自动抓取官网邮箱", value=True,
                              help="结果没有邮箱时去官网联系页挖掘")
        enrich_limit = st.slider("每轮最多抓取站点数", 0, 100, 40, 10,
                                 disabled=not do_enrich)
    return {
        "max_results": max_results,
        "add_synonyms": add_synonyms,
        "do_mx": do_mx,
        "do_enrich": do_enrich,
        "enrich_limit": enrich_limit,
    }


def _merge_adder():
    """把下拉里选中的国家并入搜索池，并清空下拉"""
    pool = list(st.session_state.get("pool") or [])
    add = list(st.session_state.get("adder") or [])
    st.session_state.pool = [normalize_country(c) for c in dict.fromkeys(pool + add)]
    st.session_state.adder = []


def _clear_pool():
    st.session_state.pool = []


def _country_options(wl: list) -> list:
    conn = db.get_conn()
    known = {
        r[0] for r in conn.execute(
            "SELECT DISTINCT country FROM customers WHERE country IS NOT NULL AND country != ''"
        )
    }
    conn.close()
    by_country = st.session_state.keywords_config.get("by_country", {}) or {}
    extra = set(st.session_state.get("pool") or []) | set(st.session_state.get("adder") or [])
    return sorted({c for c in (set(wl) | known | set(by_country) | extra) if c})


def _country_picker() -> list:
    wl = common.whitelist_list()
    if "pool" not in st.session_state:
        st.session_state.pool = list(wl)

    options = _country_options(wl)
    fmt = common.label

    st.markdown('<div class="sec-title">目标市场 / Target Markets</div>', unsafe_allow_html=True)

    # 独立一项：下拉添加国家
    st.markdown('<div class="sec-title sub">添加国家 / Add Country</div>', unsafe_allow_html=True)
    with st.container(key="country_adder"):
        st.multiselect(
            "添加国家",
            options=options,
            key="adder",
            default=[],
            accept_new_options=True,
            format_func=fmt,
            label_visibility="collapsed",
            placeholder="搜索或输入国家名，回车加入下方搜索池 / Search or type a country",
            on_change=_merge_adder,
        )

    # 搜索池：标题 + 已选国家标签都在这一个框里
    with st.container(key="country_pool"):
        head, tail = st.columns([7, 1.1], vertical_alignment="center")
        with head:
            n = len(st.session_state.get("pool") or [])
            st.markdown(
                common.flat(f"""
                <div class="pool-head">
                  搜索国家 <span class="pool-sub">Search Pool</span>
                  <span class="pool-count">{n} 个市场 / markets</span>
                </div>
                """),
                unsafe_allow_html=True,
            )
        with tail:
            st.button("清空 Clear", key="clear_pool", on_click=_clear_pool, width="stretch")

        st.multiselect(
            "搜索国家",
            options=options,
            key="pool",
            format_func=fmt,
            accept_new_options=True,
            label_visibility="collapsed",
            placeholder="池中暂无国家，请在上方下拉中选择 / Pool is empty",
        )

    return [normalize_country(c) for c in (st.session_state.get("pool") or []) if c]


def _worker(state, cancel, cfg, plan, params, whitelist, proxy, engines):
    """后台线程执行搜索；不触碰 st，只更新 state 字典"""
    try:
        state["total"] = sum(len(k) for _, k in plan) * len(engines)
        rows_all = []

        for engine in engines:
            if cancel.is_set():
                break
            searcher = build_searcher(engine, cfg, proxy)
            for country, kws in plan:
                if cancel.is_set():
                    break
                for kw in kws:
                    if cancel.is_set():
                        break
                    state["msg"] = f"🔍 {ENGINES[engine]} · {common.label(country)} · {kw}"
                    try:
                        rows = searcher.search(kw, country=country,
                                               max_results=params["max_results"])
                        for r in rows:
                            if filter_result(r) is not None:
                                continue
                            r["country"] = normalize_country(r.get("country") or country)
                            r["is_whitelist"] = 1 if r["country"].lower() in whitelist else 0
                            rows_all.append(r)
                        db.record_search_run(engine, kw, country, len(rows))
                    except Exception:  # noqa: BLE001
                        state["errors"] = state.get("errors", 0) + 1
                    state["done"] += 1
                    time.sleep(0.25)

        if not cancel.is_set() and params["do_enrich"] and params["enrich_limit"] and rows_all:
            state["phase"] = "enrich"
            targets = [r for r in rows_all if not r.get("email") and r.get("website")]
            targets = targets[: params["enrich_limit"]]
            if targets:
                state["msg"] = f"📮 抓取 {len(targets)} 个官网的邮箱…"
                with ThreadPoolExecutor(max_workers=6) as ex:
                    futures = [(ex.submit(find_emails, r["website"]), r) for r in targets]
                    for fut, row in futures:
                        if cancel.is_set():
                            break
                        try:
                            found = fut.result(timeout=30)
                        except Exception:  # noqa: BLE001
                            found = []
                        if found:
                            row["email"] = found[0]
                            row["email_valid"] = 2

        if not cancel.is_set() and params["do_mx"]:
            state["phase"] = "mx"
            state["msg"] = "📧 校验邮箱有效性…"
            for r in rows_all:
                if cancel.is_set():
                    break
                if r.get("email") and not r.get("email_valid"):
                    score, _ = validate_email(r["email"], do_mx_check=True)
                    r["email_valid"] = score

        state["phase"] = "insert"
        state["msg"] = "💾 写入数据库…"
        state["inserted"] = db.bulk_insert_customers(rows_all)
        state["with_email"] = sum(1 for r in rows_all if r.get("email"))
        state["country_count"] = len({r["country"] for r in rows_all if r.get("country")})
    except Exception as e:  # noqa: BLE001
        state["error"] = str(e)
    finally:
        state["cancelled"] = cancel.is_set()
        state["stopping"] = False
        state["msg"] = ""
        state["finished"] = True


def _start_job(countries: list, params: dict):
    cfg = st.session_state.search_config
    proxy = cfg.get("network", {}).get("proxy", "") or ""
    kw_cfg = st.session_state.keywords_config
    by_country = kw_cfg.get("by_country", {}) or {}
    base_kw = expand_keywords(kw_cfg.get("global", []), add_synonyms=params["add_synonyms"])

    engines = []
    for name in ENGINES:
        sect = cfg.get(name, {}) or {}
        if not sect.get("enabled", False):
            continue
        if name in ("serper", "bing_api", "google") and not sect.get("api_key"):
            continue
        engines.append(name)

    if not engines:
        st.error("没有可用的搜索渠道，请到「⚙️ 设置」启用并填写 API Key。")
        return

    plan = [(c, list(dict.fromkeys(base_kw + list(by_country.get(c, []))))) for c in countries]
    state = {
        "phase": "search", "done": 0, "total": 0, "msg": "准备中…",
        "finished": False, "cancelled": False, "stopping": False, "error": "",
        "inserted": 0, "with_email": 0, "country_count": 0, "errors": 0,
    }
    cancel = threading.Event()
    st.session_state.job = {"state": state, "cancel": cancel}
    threading.Thread(
        target=_worker,
        args=(state, cancel, dict(cfg), plan, dict(params),
              set(st.session_state.whitelist), proxy, engines),
        daemon=True,
    ).start()


def render():
    _topbar()

    st.write("")
    _hero_card()

    st.write("")
    _cta_button()

    job = st.session_state.get("job")
    if job:
        if job["state"]["finished"]:
            _summary_block(job["state"])
        else:
            _progress_block(job["state"])

    st.write("")
    params = _search_params()

    st.write("")
    countries = _country_picker()

    if st.session_state.pop("pending_run", False):
        if not countries:
            st.warning("搜索池为空，请先在上方下拉中选择国家")
        else:
            _start_job(countries, params)

    if _job_running():
        time.sleep(0.7)
        st.rerun()

    st.markdown(common.brand_footer(), unsafe_allow_html=True)
