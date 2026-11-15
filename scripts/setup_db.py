#!/usr/bin/env python3
"""
scripts/setup_db.py

One-time database setup helper.
Creates the database and loads schema.sql without needing the mysql CLI.

Usage:
    python scripts/setup_db.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mysql.connector

from config.db_config import DB_CONFIG


def _clean_statement(statement: str) -> str:
    """Remove full-line SQL comments before filtering/executing."""
    lines = []
    for line in statement.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def setup_database() -> None:
    print("\n  CrimeTrack-X  -  Database Setup")
    print("  " + "-" * 42)

    cfg = {
        k: v
        for k, v in DB_CONFIG.items()
        if k not in ("database", "autocommit")
    }

    try:
        conn = mysql.connector.connect(**cfg)
    except Exception as e:
        print(f"\n  [x] Cannot connect to MySQL: {e}")
        print("  Ensure MySQL is running and credentials in .env are correct.\n")
        sys.exit(1)

    cursor = conn.cursor()
    db_name = DB_CONFIG["database"]

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    print(f"  [ok] Database '{db_name}' ready.")

    cursor.execute(f"USE `{db_name}`")

    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    if not os.path.exists(schema_path):
        print(f"  [x] schema.sql not found at: {schema_path}")
        sys.exit(1)

    with open(schema_path, encoding="utf-8") as f:
        raw = f.read()

    statements = []
    for part in raw.split(";"):
        stmt = _clean_statement(part)
        if not stmt:
            continue
        upper = stmt.upper()
        if upper.startswith("CREATE DATABASE") or upper.startswith("USE "):
            continue
        statements.append(stmt)

    errors = 0
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error as e:
            if e.errno == 1062:
                continue
            print(f"  [!] Warning: {e}")
            errors += 1

    conn.commit()
    cursor.close()
    conn.close()

    if errors == 0:
        print("  [ok] Schema and seed data loaded successfully.")
    else:
        print(f"  [!] Schema loaded with {errors} warning(s). Check output above.")

    print("\n  You can now run:  python main.py\n")
    print("  Default login:  admin / Admin@123\n")


if __name__ == "__main__":
    setup_database()
