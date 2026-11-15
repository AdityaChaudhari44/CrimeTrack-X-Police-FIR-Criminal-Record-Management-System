# models/fir_model.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  FIR Model
# ─────────────────────────────────────────────

from utils.helpers import execute_query
from typing import Optional


_FIR_SELECT = """
    SELECT f.*,
           o.full_name  AS officer_name,
           o.badge_number,
           c.full_name  AS criminal_name,
           u.username   AS registered_by_user
    FROM firs f
    LEFT JOIN officers o  ON f.officer_id  = o.officer_id
    LEFT JOIN criminals c ON f.criminal_id = c.criminal_id
    LEFT JOIN users u     ON f.registered_by = u.user_id
"""


class FIRModel:
    """CRUD + search for the `firs` table."""

    # ── Read ─────────────────────────────────────────────────────
    @staticmethod
    def get_all() -> list:
        return execute_query(
            _FIR_SELECT + " ORDER BY f.registered_at DESC", fetch=True
        )

    @staticmethod
    def get_by_id(fir_id: int) -> Optional[dict]:
        return execute_query(
            _FIR_SELECT + " WHERE f.fir_id = %s",
            (fir_id,), fetch_one=True
        )

    @staticmethod
    def get_by_fir_number(fir_number: str) -> Optional[dict]:
        return execute_query(
            _FIR_SELECT + " WHERE f.fir_number = %s",
            (fir_number,), fetch_one=True
        )

    @staticmethod
    def search(query: str) -> list:
        like = f"%{query}%"
        return execute_query(
            _FIR_SELECT + """
            WHERE f.fir_number LIKE %s
               OR f.complainant LIKE %s
               OR f.offense_type LIKE %s
               OR f.location LIKE %s
               OR c.full_name LIKE %s
            ORDER BY f.registered_at DESC""",
            (like, like, like, like, like), fetch=True
        )

    @staticmethod
    def search_by_date(date_str: str) -> list:
        return execute_query(
            _FIR_SELECT + " WHERE f.incident_date = %s ORDER BY f.registered_at DESC",
            (date_str,), fetch=True
        )

    @staticmethod
    def search_by_status(status: str) -> list:
        return execute_query(
            _FIR_SELECT + " WHERE f.status = %s ORDER BY f.registered_at DESC",
            (status,), fetch=True
        )

    @staticmethod
    def get_by_officer(officer_id: int) -> list:
        return execute_query(
            _FIR_SELECT + " WHERE f.officer_id = %s ORDER BY f.registered_at DESC",
            (officer_id,), fetch=True
        )

    # ── Stats ─────────────────────────────────────────────────────
    @staticmethod
    def monthly_stats(year: int) -> list:
        return execute_query(
            """SELECT MONTH(incident_date) AS month,
                      COUNT(*) AS total,
                      SUM(status='Closed') AS closed
               FROM firs WHERE YEAR(incident_date) = %s
               GROUP BY MONTH(incident_date) ORDER BY month""",
            (year,), fetch=True
        )

    @staticmethod
    def offense_breakdown() -> list:
        return execute_query(
            """SELECT offense_type, COUNT(*) AS total
               FROM firs GROUP BY offense_type ORDER BY total DESC""",
            fetch=True
        )

    # ── Create ───────────────────────────────────────────────────
    @staticmethod
    def create(data: dict) -> int:
        return execute_query(
            """INSERT INTO firs
               (fir_number, complainant, complainant_ph, incident_date, incident_time,
                location, offense_type, ipc_sections, description, status,
                officer_id, criminal_id, registered_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                data["fir_number"], data["complainant"], data.get("complainant_ph"),
                data["incident_date"], data.get("incident_time"),
                data["location"], data["offense_type"], data.get("ipc_sections"),
                data.get("description"), data.get("status", "Registered"),
                data.get("officer_id"), data.get("criminal_id"), data["registered_by"]
            )
        )

    # ── Update ───────────────────────────────────────────────────
    @staticmethod
    def update(fir_id: int, data: dict) -> None:
        execute_query(
            """UPDATE firs SET
               complainant=%s, complainant_ph=%s, incident_date=%s,
               incident_time=%s, location=%s, offense_type=%s,
               ipc_sections=%s, description=%s, status=%s,
               officer_id=%s, criminal_id=%s
               WHERE fir_id=%s""",
            (
                data["complainant"], data.get("complainant_ph"),
                data["incident_date"], data.get("incident_time"),
                data["location"], data["offense_type"], data.get("ipc_sections"),
                data.get("description"), data["status"],
                data.get("officer_id"), data.get("criminal_id"),
                fir_id
            )
        )

    @staticmethod
    def update_status(fir_id: int, status: str) -> None:
        execute_query(
            "UPDATE firs SET status = %s WHERE fir_id = %s",
            (status, fir_id)
        )

    @staticmethod
    def assign_officer(fir_id: int, officer_id: int) -> None:
        execute_query(
            "UPDATE firs SET officer_id = %s WHERE fir_id = %s",
            (officer_id, fir_id)
        )

    # ── Delete ───────────────────────────────────────────────────
    @staticmethod
    def delete(fir_id: int) -> None:
        execute_query("DELETE FROM firs WHERE fir_id = %s", (fir_id,))
