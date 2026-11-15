# models/officer_model.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Officer Model
# ─────────────────────────────────────────────

from utils.helpers import execute_query
from typing import Optional


class OfficerModel:
    """CRUD + queries for the `officers` table."""

    # ── Read ─────────────────────────────────────────────────────
    @staticmethod
    def get_all(active_only: bool = False) -> list:
        sql = "SELECT o.*, u.username FROM officers o LEFT JOIN users u ON o.user_id = u.user_id"
        if active_only:
            sql += " WHERE o.is_active = 1"
        sql += " ORDER BY o.full_name"
        return execute_query(sql, fetch=True)

    @staticmethod
    def get_by_id(officer_id: int) -> Optional[dict]:
        return execute_query(
            """SELECT o.*, u.username
               FROM officers o LEFT JOIN users u ON o.user_id = u.user_id
               WHERE o.officer_id = %s""",
            (officer_id,), fetch_one=True
        )

    @staticmethod
    def get_by_badge(badge: str) -> Optional[dict]:
        return execute_query(
            "SELECT * FROM officers WHERE badge_number = %s",
            (badge.upper(),), fetch_one=True
        )

    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[dict]:
        return execute_query(
            "SELECT * FROM officers WHERE user_id = %s",
            (user_id,), fetch_one=True
        )

    @staticmethod
    def search(query: str) -> list:
        like = f"%{query}%"
        return execute_query(
            """SELECT o.*, u.username FROM officers o
               LEFT JOIN users u ON o.user_id = u.user_id
               WHERE o.full_name LIKE %s OR o.badge_number LIKE %s OR o.`rank` LIKE %s""",
            (like, like, like), fetch=True
        )

    # ── Performance stats ─────────────────────────────────────────
    @staticmethod
    def get_performance(officer_id: int) -> dict:
        """Return dict with total_firs, total_cases, solved_cases."""
        firs = execute_query(
            "SELECT COUNT(*) AS cnt FROM firs WHERE officer_id = %s",
            (officer_id,), fetch_one=True
        ) or {"cnt": 0}
        total = execute_query(
            "SELECT COUNT(*) AS cnt FROM cases WHERE assigned_to = %s",
            (officer_id,), fetch_one=True
        ) or {"cnt": 0}
        solved = execute_query(
            "SELECT COUNT(*) AS cnt FROM cases WHERE assigned_to = %s AND status = 'Closed'",
            (officer_id,), fetch_one=True
        ) or {"cnt": 0}
        return {
            "total_firs":   firs["cnt"],
            "total_cases":  total["cnt"],
            "solved_cases": solved["cnt"],
        }

    # ── Create ───────────────────────────────────────────────────
    @staticmethod
    def create(data: dict) -> int:
        return execute_query(
            """INSERT INTO officers
               (user_id, badge_number, full_name, `rank`, department, phone, email, station, date_joined)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                data.get("user_id"),
                data["badge_number"].upper(),
                data["full_name"],
                data["rank"],
                data.get("department"),
                data.get("phone"),
                data.get("email"),
                data.get("station"),
                data.get("date_joined"),
            )
        )

    # ── Update ───────────────────────────────────────────────────
    @staticmethod
    def update(officer_id: int, data: dict) -> None:
        execute_query(
            """UPDATE officers SET
               full_name=%s, `rank`=%s, department=%s, phone=%s,
               email=%s, station=%s, is_active=%s
               WHERE officer_id=%s""",
            (
                data["full_name"], data["rank"], data.get("department"),
                data.get("phone"), data.get("email"), data.get("station"),
                int(data.get("is_active", 1)), officer_id
            )
        )

    # ── Delete ───────────────────────────────────────────────────
    @staticmethod
    def delete(officer_id: int) -> None:
        execute_query("DELETE FROM officers WHERE officer_id = %s", (officer_id,))
