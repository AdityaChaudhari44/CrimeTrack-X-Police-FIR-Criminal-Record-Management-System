# utils/helpers.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Helpers
#  DB connection pool, logging, pagination,
#  export utilities, FIR/Case ID generators
# ─────────────────────────────────────────────

import mysql.connector
from mysql.connector import Error as MySQLError
import logging
import os
import csv
import datetime
from typing import Optional, List, Dict, Any
from config.db_config import DB_CONFIG, APP_CONFIG


# ── Logging setup ────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=APP_CONFIG["log_file"],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("CrimeTrackX")


# ── Database Connection ──────────────────────────────────────────
def get_connection():
    """
    Return a new MySQL connection using DB_CONFIG.
    Raises ConnectionError on failure.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except MySQLError as e:
        logger.error(f"DB connection failed: {e}")
        raise ConnectionError(f"Cannot connect to database: {e}")


def execute_query(
    sql: str,
    params: tuple = (),
    fetch: bool = False,
    fetch_one: bool = False,
    commit: bool = True,
) -> Any:
    """
    Generic query executor.

    Parameters
    ----------
    sql       : SQL string (use %s placeholders)
    params    : tuple of parameters
    fetch     : if True, return all rows as list[dict]
    fetch_one : if True, return single row as dict
    commit    : if True, commit after DML

    Returns
    -------
    list[dict] | dict | int (lastrowid) | None
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    result = None
    try:
        cursor.execute(sql, params)
        if fetch:
            result = cursor.fetchall()
        elif fetch_one:
            result = cursor.fetchone()
        else:
            if commit:
                conn.commit()
            result = cursor.lastrowid
    except MySQLError as e:
        conn.rollback()
        logger.error(f"Query error: {e} | SQL: {sql}")
        raise
    finally:
        cursor.close()
        conn.close()
    return result


# ── FIR / Case number generators ────────────────────────────────
def generate_fir_number() -> str:
    """
    Generate next FIR number: FIR-YYYY-NNNNNN
    Reads current max sequence from DB.
    """
    year = datetime.date.today().year
    row = execute_query(
        "SELECT fir_number FROM firs WHERE fir_number LIKE %s ORDER BY fir_id DESC LIMIT 1",
        (f"FIR-{year}-%",), fetch_one=True
    )
    if row:
        last_seq = int(row["fir_number"].split("-")[-1])
        return f"FIR-{year}-{last_seq + 1:06d}"
    return f"FIR-{year}-000001"


def generate_case_number() -> str:
    """Generate next Case number: CASE-YYYY-NNNNNN"""
    year = datetime.date.today().year
    row = execute_query(
        "SELECT case_number FROM cases WHERE case_number LIKE %s ORDER BY case_id DESC LIMIT 1",
        (f"CASE-{year}-%",), fetch_one=True
    )
    if row:
        last_seq = int(row["case_number"].split("-")[-1])
        return f"CASE-{year}-{last_seq + 1:06d}"
    return f"CASE-{year}-000001"


# ── Pagination ───────────────────────────────────────────────────
class Paginator:
    """Simple cursor-based paginator over a list."""

    def __init__(self, data: List[Any], page_size: int = None):
        self.data = data
        self.page_size = page_size or APP_CONFIG["page_size"]
        self.total = len(data)
        self.total_pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        self.current_page = 1

    def get_page(self, page: int) -> List[Any]:
        self.current_page = max(1, min(page, self.total_pages))
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.data[start:end]

    def next_page(self) -> List[Any]:
        return self.get_page(self.current_page + 1)

    def prev_page(self) -> List[Any]:
        return self.get_page(self.current_page - 1)

    @property
    def page_info(self) -> str:
        return f"Page {self.current_page}/{self.total_pages}  ({self.total} records)"


# ── Export Utilities ─────────────────────────────────────────────
def export_to_csv(filename: str, data: List[Dict], fieldnames: List[str]) -> str:
    """Export list-of-dicts to CSV. Returns the full path."""
    os.makedirs(APP_CONFIG["export_dir"], exist_ok=True)
    path = os.path.join(APP_CONFIG["export_dir"], filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
    return path


def export_to_txt(filename: str, content: str) -> str:
    """Export text content to a .txt file. Returns the full path."""
    os.makedirs(APP_CONFIG["export_dir"], exist_ok=True)
    path = os.path.join(APP_CONFIG["export_dir"], filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ── Audit logger helper ──────────────────────────────────────────
def audit_log(user_id: Optional[int], action: str,
              table_name: str = None, record_id: int = None,
              details: str = None) -> None:
    """Insert an audit trail record (fire-and-forget; never raises)."""
    try:
        execute_query(
            """INSERT INTO audit_logs (user_id, action, table_name, record_id, details)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, action, table_name, record_id, details)
        )
    except Exception:
        pass  # audit failure must never crash main flow
