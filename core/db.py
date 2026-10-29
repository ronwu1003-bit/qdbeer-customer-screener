"""SQLite 数据库操作层"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "customers.db")


def get_conn() -> sqlite3.Connection:
    """获取数据库连接（自动创建文件）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            website TEXT,
            email TEXT,
            country TEXT,
            search_source TEXT,
            keywords_matched TEXT,
            email_valid INTEGER DEFAULT 0,
            is_whitelist INTEGER DEFAULT 0,
            is_existing_client INTEGER DEFAULT 0,
            imported_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_name, country)
        );

        CREATE TABLE IF NOT EXISTS search_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            keyword TEXT,
            country TEXT,
            result_count INTEGER,
            status TEXT,
            run_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_customers_country ON customers(country);
        CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
        CREATE INDEX IF NOT EXISTS idx_customers_whitelist ON customers(is_whitelist);
        CREATE INDEX IF NOT EXISTS idx_customers_source ON customers(search_source);
    """)
    conn.commit()
    conn.close()


def insert_customer(customer: Dict) -> bool:
    """插入一条客户记录（已存在则跳过）"""
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO customers 
            (company_name, website, email, country, search_source, keywords_matched, email_valid, is_whitelist)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer.get("company_name", ""),
            customer.get("website", ""),
            customer.get("email", ""),
            customer.get("country", ""),
            customer.get("search_source", ""),
            customer.get("keywords_matched", ""),
            customer.get("email_valid", 0),
            customer.get("is_whitelist", 0),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"插入客户失败: {e}")
        return False
    finally:
        conn.close()


def bulk_insert_customers(customers: List[Dict]) -> int:
    """批量插入客户，返回成功插入数量"""
    conn = get_conn()
    count = 0
    try:
        for c in customers:
            cur = conn.execute("""
                INSERT OR IGNORE INTO customers 
                (company_name, website, email, country, search_source, keywords_matched, email_valid, is_whitelist)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c.get("company_name", ""),
                c.get("website", ""),
                c.get("email", ""),
                c.get("country", ""),
                c.get("search_source", ""),
                c.get("keywords_matched", ""),
                c.get("email_valid", 0),
                c.get("is_whitelist", 0),
            ))
            if cur.rowcount > 0:
                count += 1
        conn.commit()
    finally:
        conn.close()
    return count


def get_all_customers() -> List[Dict]:
    """获取所有客户"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM customers ORDER BY is_whitelist DESC, country").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_filtered_customers(
    require_email: bool = True,
    whitelist_only: bool = False,
    exclude_existing: bool = True,
    countries: Optional[List[str]] = None,
    min_email_valid: int = 1,
) -> List[Dict]:
    """获取筛选后的客户列表"""
    conn = get_conn()
    query = "SELECT * FROM customers WHERE 1=1"
    params = []

    if require_email:
        query += " AND email IS NOT NULL AND email != ''"
    if whitelist_only:
        query += " AND is_whitelist = 1"
    if exclude_existing:
        query += " AND is_existing_client = 0"
    if min_email_valid:
        query += " AND email_valid >= ?"
        params.append(min_email_valid)
    if countries:
        placeholders = ",".join("?" * len(countries))
        query += f" AND country IN ({placeholders})"
        params.extend(countries)

    query += " ORDER BY is_whitelist DESC, email_valid DESC, country"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_whitelist(country: str, is_whitelist: int):
    """更新某国白名单状态"""
    conn = get_conn()
    conn.execute("UPDATE customers SET is_whitelist = ? WHERE country = ?", (is_whitelist, country))
    conn.commit()
    conn.close()


def update_email_valid(customer_id: int, valid: int):
    """更新邮箱有效性"""
    conn = get_conn()
    conn.execute("UPDATE customers SET email_valid = ? WHERE id = ?", (valid, customer_id))
    conn.commit()
    conn.close()


def mark_existing_client(company_name: str):
    """标记老客户"""
    conn = get_conn()
    conn.execute("UPDATE customers SET is_existing_client = 1 WHERE company_name = ?", (company_name,))
    conn.commit()
    conn.close()


def get_stats() -> Dict:
    """获取统计数据"""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    with_email = conn.execute("SELECT COUNT(*) FROM customers WHERE email IS NOT NULL AND email != ''").fetchone()[0]
    valid_email = conn.execute("SELECT COUNT(*) FROM customers WHERE email_valid >= 1").fetchone()[0]
    whitelist = conn.execute("SELECT COUNT(*) FROM customers WHERE is_whitelist = 1").fetchone()[0]
    countries = conn.execute("SELECT COUNT(DISTINCT country) FROM customers WHERE country IS NOT NULL AND country != ''").fetchone()[0]
    searches = conn.execute("SELECT COUNT(*) FROM search_runs").fetchone()[0]
    conn.close()
    return {
        "total": total,
        "with_email": with_email,
        "valid_email": valid_email,
        "whitelist": whitelist,
        "countries": countries,
        "searches": searches,
    }


def record_search_run(source: str, keyword: str, country: str, count: int, status: str = "ok"):
    """记录一次搜索运行"""
    conn = get_conn()
    conn.execute("""
        INSERT INTO search_runs (source, keyword, country, result_count, status)
        VALUES (?, ?, ?, ?, ?)
    """, (source, keyword, country, count, status))
    conn.commit()
    conn.close()
