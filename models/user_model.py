# models/user_model.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  User Model
# ─────────────────────────────────────────────

from utils.helpers import execute_query
from typing import Optional


class UserModel:
    """CRUD for the `users` table."""

    # ── Read ─────────────────────────────────────────────────────
    @staticmethod
    def get_by_username(username: str) -> Optional[dict]:
        return execute_query(
            "SELECT * FROM users WHERE username = %s AND is_active = 1",
            (username,), fetch_one=True
        )

    @staticmethod
    def get_by_id(user_id: int) -> Optional[dict]:
        return execute_query(
            "SELECT * FROM users WHERE user_id = %s",
            (user_id,), fetch_one=True
        )

    @staticmethod
    def get_all() -> list:
        return execute_query("SELECT * FROM users ORDER BY created_at DESC", fetch=True)

    # ── Create ───────────────────────────────────────────────────
    @staticmethod
    def create(username: str, password_hash: str, role: str = "officer") -> int:
        return execute_query(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, password_hash, role)
        )

    # ── Update ───────────────────────────────────────────────────
    @staticmethod
    def update_password(user_id: int, new_hash: str) -> None:
        execute_query(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (new_hash, user_id)
        )

    @staticmethod
    def update_last_login(user_id: int) -> None:
        execute_query(
            "UPDATE users SET last_login = NOW() WHERE user_id = %s",
            (user_id,)
        )

    @staticmethod
    def set_active(user_id: int, is_active: bool) -> None:
        execute_query(
            "UPDATE users SET is_active = %s WHERE user_id = %s",
            (int(is_active), user_id)
        )

    # ── Delete ───────────────────────────────────────────────────
    @staticmethod
    def delete(user_id: int) -> None:
        execute_query("DELETE FROM users WHERE user_id = %s", (user_id,))
