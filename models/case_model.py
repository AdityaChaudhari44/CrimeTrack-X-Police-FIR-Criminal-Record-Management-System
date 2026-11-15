# models/case_model.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Case Model
# ─────────────────────────────────────────────

from utils.helpers import execute_query
from typing import Optional


_CASE_SELECT = """
    SELECT cs.*,
           f.fir_number,
           f.offense_type,
           o.full_name AS officer_name,
           o.badge_number
    FROM cases cs
    LEFT JOIN firs f    ON cs.fir_id      = f.fir_id
    LEFT JOIN officers o ON cs.assigned_to = o.officer_id
"""


class CaseModel:
    """CRUD for cases + investigation notes + evidence."""

    # ── Cases ────────────────────────────────────────────────────
    @staticmethod
    def get_all() -> list:
        return execute_query(_CASE_SELECT + " ORDER BY cs.opened_at DESC", fetch=True)

    @staticmethod
    def get_by_id(case_id: int) -> Optional[dict]:
        return execute_query(
            _CASE_SELECT + " WHERE cs.case_id = %s",
            (case_id,), fetch_one=True
        )

    @staticmethod
    def get_by_fir(fir_id: int) -> Optional[dict]:
        return execute_query(
            _CASE_SELECT + " WHERE cs.fir_id = %s",
            (fir_id,), fetch_one=True
        )

    @staticmethod
    def get_by_status(status: str) -> list:
        return execute_query(
            _CASE_SELECT + " WHERE cs.status = %s ORDER BY cs.opened_at DESC",
            (status,), fetch=True
        )

    @staticmethod
    def get_by_officer(officer_id: int) -> list:
        return execute_query(
            _CASE_SELECT + " WHERE cs.assigned_to = %s ORDER BY cs.opened_at DESC",
            (officer_id,), fetch=True
        )

    @staticmethod
    def create(data: dict) -> int:
        return execute_query(
            """INSERT INTO cases
               (case_number, fir_id, title, status, priority, assigned_to, court_date)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (
                data["case_number"], data["fir_id"], data["title"],
                data.get("status", "Open"), data.get("priority", "Medium"),
                data.get("assigned_to"), data.get("court_date")
            )
        )

    @staticmethod
    def update(case_id: int, data: dict) -> None:
        execute_query(
            """UPDATE cases SET
               title=%s, status=%s, priority=%s, assigned_to=%s,
               court_date=%s, verdict=%s,
               closed_at = CASE WHEN %s='Closed' THEN NOW() ELSE closed_at END
               WHERE case_id=%s""",
            (
                data["title"], data["status"], data.get("priority", "Medium"),
                data.get("assigned_to"), data.get("court_date"), data.get("verdict"),
                data["status"], case_id
            )
        )

    @staticmethod
    def update_status(case_id: int, status: str) -> None:
        if status == "Closed":
            execute_query(
                "UPDATE cases SET status=%s, closed_at=NOW() WHERE case_id=%s",
                (status, case_id)
            )
        else:
            execute_query(
                "UPDATE cases SET status=%s WHERE case_id=%s",
                (status, case_id)
            )

    @staticmethod
    def delete(case_id: int) -> None:
        execute_query("DELETE FROM cases WHERE case_id = %s", (case_id,))

    # ── Investigation Notes ───────────────────────────────────────
    @staticmethod
    def get_notes(case_id: int) -> list:
        return execute_query(
            """SELECT n.*, o.full_name AS officer_name
               FROM investigation_notes n
               LEFT JOIN officers o ON n.officer_id = o.officer_id
               WHERE n.case_id = %s ORDER BY n.created_at""",
            (case_id,), fetch=True
        )

    @staticmethod
    def add_note(case_id: int, officer_id: int, note_text: str) -> int:
        return execute_query(
            "INSERT INTO investigation_notes (case_id, officer_id, note_text) VALUES (%s,%s,%s)",
            (case_id, officer_id, note_text)
        )

    # ── Evidence ─────────────────────────────────────────────────
    @staticmethod
    def get_evidence(case_id: int) -> list:
        return execute_query(
            """SELECT e.*, o.full_name AS collected_by_name
               FROM evidence e
               LEFT JOIN officers o ON e.collected_by = o.officer_id
               WHERE e.case_id = %s ORDER BY e.collected_at""",
            (case_id,), fetch=True
        )

    @staticmethod
    def add_evidence(case_id: int, data: dict) -> int:
        return execute_query(
            """INSERT INTO evidence
               (case_id, evidence_type, description, location, collected_by, status)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (
                case_id, data["evidence_type"], data.get("description"),
                data.get("location"), data.get("collected_by"),
                data.get("status", "Collected")
            )
        )

    @staticmethod
    def update_evidence_status(evidence_id: int, status: str) -> None:
        execute_query(
            "UPDATE evidence SET status=%s WHERE evidence_id=%s",
            (status, evidence_id)
        )

    # ── Stats ─────────────────────────────────────────────────────
    @staticmethod
    def get_summary_stats() -> dict:
        row = execute_query(
            """SELECT
               COUNT(*) AS total,
               SUM(status='Open') AS open_cases,
               SUM(status='Under Investigation') AS under_inv,
               SUM(status='Closed') AS closed,
               SUM(status='Pending') AS pending,
               SUM(status='Cold') AS cold
               FROM cases""",
            fetch_one=True
        )
        return row or {}
