# utils/security.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Security Utilities
#  bcrypt password hashing + session handling
# ─────────────────────────────────────────────

import bcrypt
import hashlib
import secrets
import datetime
from typing import Optional


class PasswordManager:
    """Secure password hashing and verification using bcrypt."""

    ROUNDS = 12  # work factor

    @staticmethod
    def hash_password(plain_text: str) -> str:
        """Hash a plain-text password; returns UTF-8 decoded hash string."""
        salt = bcrypt.gensalt(rounds=PasswordManager.ROUNDS)
        hashed = bcrypt.hashpw(plain_text.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_text: str, hashed: str) -> bool:
        """Return True if plain_text matches the stored hash."""
        try:
            return bcrypt.checkpw(
                plain_text.encode("utf-8"),
                hashed.encode("utf-8")
            )
        except Exception:
            return False

    @staticmethod
    def is_strong_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        Returns (True, '') on success or (False, reason) on failure.
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters."
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter."
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter."
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit."
        specials = "!@#$%^&*()_+-=[]{}|;:',.<>?/"
        if not any(c in specials for c in password):
            return False, "Password must contain at least one special character."
        return True, ""


class Session:
    """In-memory session for the currently authenticated user."""

    def __init__(self):
        self._user: Optional[dict] = None
        self._token: Optional[str] = None
        self._login_time: Optional[datetime.datetime] = None

    # ── authentication ──────────────────────────────────────────
    def create(self, user: dict) -> None:
        """Establish a new session for the given user dict."""
        self._user = user
        self._token = secrets.token_hex(16)
        self._login_time = datetime.datetime.now()

    def destroy(self) -> None:
        """Clear the current session."""
        self._user = None
        self._token = None
        self._login_time = None

    # ── accessors ───────────────────────────────────────────────
    @property
    def is_authenticated(self) -> bool:
        return self._user is not None

    @property
    def user(self) -> Optional[dict]:
        return self._user

    @property
    def user_id(self) -> Optional[int]:
        return self._user.get("user_id") if self._user else None

    @property
    def username(self) -> Optional[str]:
        return self._user.get("username") if self._user else None

    @property
    def role(self) -> Optional[str]:
        return self._user.get("role") if self._user else None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def login_time(self) -> Optional[datetime.datetime]:
        return self._login_time

    def require_auth(self) -> bool:
        """Return True if authenticated; callers should exit menu if False."""
        return self.is_authenticated

    def require_admin(self) -> bool:
        """Return True if user is admin."""
        return self.is_authenticated and self.is_admin


# Module-level singleton – imported everywhere
current_session = Session()
