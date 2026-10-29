"""
命令行批量搜索（后台静默运行，不弹窗）
用法示例：
  python run_batch.py --engine serper --countries whitelist --max 10 --enrich 40
  python run_batch.py --engine all --countries whitelist --max 10
"""
import os
import sys
import argparse
import logging
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import db
from core.exporter import export_to_excel
from core.searchers.engines import build_searcher
from core.filters.config_manager import (
    apply_env_overrides, load_keywords_config, load_whitelist_countries, normalize_country,
)
from core.filters.email_validator import validate_email
from core.filters.email_finder import find_emails

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG_DIR = os.path.join(ROOT, "config")
OUT_DIR = os.path.join(ROOT, "data", "output")

logging.basicConfig(level=logging.WARNING, format="%(message)s")


def load_yaml(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="serper", help="serper / bing_api / google / linkedin / all")
    ap.add_argument("--countries", default="whitelist", help="whitelist 或逗号分隔的国家名")
    ap.add_argument("--max", type=int, default=10, help="每个关键词最多取几条")
    ap.add_argument("--kw-limit", type=int, default=3, help="每个国家最多用几个关键词")
    ap.add_argument("--enrich", type=int, default=40, help="本轮最多为多少个官网挖掘邮箱，0=不挖")
    ap.add_argument("--no-export", action="store_true")
    args = ap.parse_args()

    cfg = apply_env_overrides(load_yaml(os.path.join(CFG_DIR, "search_config.yaml")))
    kw_cfg = load_keywords_config(os.path.join(CFG_DIR, "keywords.yaml"))
    proxy = (cfg.get("network", {}) or {}).get("proxy", "")

    if args.countries == "whitelist":
        countries = [normalize_country(c) for c in sorted(load_whitelist_countries(
            os.path.join(CFG_DIR, "whitelist_countries.txt")))]
    else:
        countries = [normalize_country(c.strip()) for c in args.countries.split(",") if c.strip()]

    engines = ["serper", "bing_api", "google", "linkedin"] if args.engine == "all" else [args.engine]
    base_kws = kw_cfg.get("global", [])
    by_country = kw_cfg.get("by_country", {})

    db.init_db()
    total_found, total_new = 0, 0

    for engine in engines:
        try:
            searcher = build_searcher(engine, cfg, proxy)
        except ValueError as e:
            print(f"[跳过] {engine}: {e}")
            continue

        # 检查 Key 是否为空
        if engine in ("serper", "bing_api") and not cfg.get(engine, {}).get("api_key"):
            print(f"[跳过] {engine}: 未配置 API Key")
            continue
        if engine == "google" and not cfg.get("google", {}).get("api_key"):
            print("[跳过] google: 未配置 API Key")
            continue

        print(f"\n=== 渠道 {engine} | 国家 {len(countries)} 个 ===")
        for country in countries:
            kws = list(dict.fromkeys(list(by_country.get(country, [])) + base_kws))[:args.kw_limit]
            found_this = 0
            for kw in kws:
                try:
                    rows = searcher.search(kw, country=country, max_results=args.max)
                except Exception as e:
                    print(f"  [{country}] {kw} 失败: {e}")
                    continue

                cleaned = []
                seen = set()
                for r in rows:
                    key = (r["company_name"].strip().lower(), country)
                    if not r["company_name"] or key in seen:
                        continue
                    seen.add(key)
                    r["country"] = normalize_country(r["country"] or country)
                    r["is_whitelist"] = 1 if r["country"].lower() in {
                        c.lower() for c in countries} else 0
                    cleaned.append(r)

                new_cnt = db.bulk_insert_customers(cleaned)
                db.record_search_run(engine, kw, country, len(cleaned))
                found_this += len(cleaned)
                total_found += len(cleaned)
                total_new += new_cnt
                print(f"  [{country}] {kw}: 搜到 {len(cleaned)} / 新增 {new_cnt}")

            print(f"  -> {country} 合计 {found_this} 条")

    # 官网挖邮箱
    if args.enrich > 0:
        rows = [r for r in db.get_all_customers() if not r["email"] and r["website"]]
        rows = rows[:args.enrich]
        if rows:
            print(f"\n=== 官网邮箱挖掘（{len(rows)} 个站点）===")
            with ThreadPoolExecutor(max_workers=6) as ex:
                futures = {ex.submit(find_emails, r["website"]): r for r in rows}
                for i, fut in enumerate(as_completed(futures), 1):
                    r = futures[fut]
                    try:
                        emails = fut.result()
                    except Exception:
                        emails = []
                    if emails:
                        conn = db.get_conn()
                        conn.execute("UPDATE customers SET email=?, email_valid=? WHERE id=?",
                                     (emails[0], 2, r["id"]))
                        conn.commit()
                        conn.close()
                        print(f"  {r['company_name'][:30]}: {emails[0]}")
            print("邮箱挖掘完成")

    # 校验已有邮箱
    conn = db.get_conn()
    pending = conn.execute("SELECT id, email FROM customers WHERE email != '' AND email_valid = 0").fetchall()
    conn.close()
    for p in pending:
        score, _ = validate_email(p["email"], do_mx_check=True)
        db.update_email_valid(p["id"], score)

    stats = db.get_stats()
    print(f"\n=== 本轮汇总 ===")
    print(f"搜到 {total_found} 条，新增入库 {total_new} 条")
    print(f"库内合计 {stats['total']} 条 | 有邮箱 {stats['with_email']} | 邮箱强有效 {stats['valid_email']} | 白名单 {stats['whitelist']}")

    if not args.no_export:
        ready = db.get_filtered_customers(require_email=True, exclude_existing=True, min_email_valid=1)
        if ready:
            path = export_to_excel(ready, OUT_DIR)
            print(f"待发清单已导出: {path}（{len(ready)} 条）")
        else:
            print("暂无可导出的有效客户（需有有效邮箱）")


if __name__ == "__main__":
    main()
