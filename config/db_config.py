# config/db_config.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Database Configuration
#  Reads credentials from environment variables
#  or falls back to .env file via python-dotenv
# ─────────────────────────────────────────────

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("CTX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CTX_DB_PORT", "3306")),
    "user":     os.getenv("CTX_DB_USER",     "root"),
    "password": os.getenv("CTX_DB_PASSWORD", ""),
    "database": os.getenv("CTX_DB_NAME",     "crimetrack_x"),
    "autocommit": False,
    "charset": "utf8mb4",
    "use_unicode": True,
    "connection_timeout": 10,
}

APP_CONFIG = {
    "app_name":    "CrimeTrack-X",
    "version":     "1.0.0",
    "page_size":   10,          # rows per paginated listing
    "log_file":    "logs/crimetrack.log",
    "export_dir":  "exports/",
}
