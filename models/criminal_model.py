# models/criminal_model.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Criminal Model
# ─────────────────────────────────────────────

from utils.helpers import execute_query
from typing import Optional


class CriminalModel:
    """CRUD + queries for the `criminals` table."""

    # ── Read ─────────────────────────────────────────────────────
    @staticmethod
    def get_all() -> list:
        return execute_query(
            "SELECT * FROM criminals ORDER BY full_name", fetch=True
        )

    @staticmethod
    def get_by_id(criminal_id: int) -> Optional[dict]:
        return execute_query(
            "SELECT * FROM criminals WHERE criminal_id = %s",
            (criminal_id,), fetch_one=True
        )

    @staticmethod
    def search(query: str) -> list:
        like = f"%{query}%"
        return execute_query(
            """SELECT * FROM criminals
               WHERE full_name LIKE %s OR alias LIKE %s OR id_proof_no LIKE %s""",
            (like, like, like), fetch=True
        )

    @staticmethod
    def get_wanted() -> list:
        return execute_query(
            "SELECT * FROM criminals WHERE is_wanted = 1 ORDER BY arrest_count DESC",
            fetch=True
        )

    @staticmethod
    def get_repeat_offenders(min_arrests: int = 2) -> list:
        return execute_query(
            "SELECT * FROM criminals WHERE arrest_count >= %s ORDER BY arrest_count DESC",
            (min_arrests,), fetch=True
        )

    @staticmethod
    def get_fir_history(criminal_id: int) -> list:
        return execute_query(
            """SELECT f.fir_number, f.offense_type, f.incident_date, f.status,
                      o.full_name AS officer_name
               FROM firs f LEFT JOIN officers o ON f.officer_id = o.officer_id
               WHERE f.criminal_id = %s ORDER BY f.incident_date DESC""",
            (criminal_id,), fetch=True
        )

    # ── Create ───────────────────────────────────────────────────
    @staticmethod
    def create(data: dict) -> int:
        return execute_query(
            """INSERT INTO criminals
               (full_name, alias, dob, gender, nationality, address, phone,
                id_proof_type, id_proof_no, blood_group, physical_desc, is_wanted)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                data["full_name"], data.get("alias"), data.get("dob"),
                data.get("gender"), data.get("nationality", "Indian"),
                data.get("address"), data.get("phone"),
                data.get("id_proof_type"), data.get("id_proof_no"),
                data.get("blood_group"), data.get("physical_desc"),
                int(data.get("is_wanted", 0)),
            )
        )

    # ── Update ───────────────────────────────────────────────────
    @staticmethod
    def update(criminal_id: int, data: dict) -> None:
        execute_query(
            """UPDATE criminals SET
               full_name=%s, alias=%s, dob=%s, gender=%s, nationality=%s,
               address=%s, phone=%s, id_proof_type=%s, id_proof_no=%s,
               blood_group=%s, physical_desc=%s, is_wanted=%s
               WHERE criminal_id=%s""",
            (
                data["full_name"], data.get("alias"), data.get("dob"),
                data.get("gender"), data.get("nationality", "Indian"),
                data.get("address"), data.get("phone"),
                data.get("id_proof_type"), data.get("id_proof_no"),
                data.get("blood_group"), data.get("physical_desc"),
                int(data.get("is_wanted", 0)),
                criminal_id
            )
        )

    @staticmethod
    def increment_arrest_count(criminal_id: int) -> None:
        execute_query(
            "UPDATE criminals SET arrest_count = arrest_count + 1 WHERE criminal_id = %s",
            (criminal_id,)
        )

    # ── Delete ───────────────────────────────────────────────────
    @staticmethod
    def delete(criminal_id: int) -> None:
        execute_query("DELETE FROM criminals WHERE criminal_id = %s", (criminal_id,))
