#!/usr/bin/env python3
"""
scripts/seed_admin.py
─────────────────────────────────────────────
Utility to (re)create the default admin user with a fresh bcrypt hash.
Run this after loading schema.sql or whenever you want to reset the admin password.

Usage:
    python scripts/seed_admin.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.security import PasswordManager
from utils.helpers import execute_query, get_connection


def seed_admin() -> None:
    print("\n  CrimeTrack-X  —  Admin Seed Utility")
    print("  " + "─" * 42)

    username = input("  Admin username [admin]: ").strip() or "admin"
    import getpass
    password = getpass.getpass("  New admin password: ")

    ok, reason = PasswordManager.is_strong_password(password)
    if not ok:
        print(f"\n  ✘  Weak password: {reason}")
        sys.exit(1)

    confirm = getpass.getpass("  Confirm password  : ")
    if password != confirm:
        print("\n  ✘  Passwords do not match.")
        sys.exit(1)

    hashed = PasswordManager.hash_password(password)

    # Check connection
    try:
        conn = get_connection()
        conn.close()
    except Exception as e:
        print(f"\n  ✘  DB connection failed: {e}")
        sys.exit(1)

    # Upsert the admin user
    existing = execute_query(
        "SELECT user_id FROM users WHERE username = %s",
        (username,), fetch_one=True
    )

    if existing:
        execute_query(
            "UPDATE users SET password_hash = %s, role = 'admin', is_active = 1 WHERE username = %s",
            (hashed, username)
        )
        print(f"\n  ✔  Password updated for existing user '{username}'.")
    else:
        uid = execute_query(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'admin')",
            (username, hashed)
        )
        print(f"\n  ✔  Admin user '{username}' created (ID: {uid}).")

    print(f"  Hash: {hashed[:30]}…\n")


if __name__ == "__main__":
    seed_admin()
