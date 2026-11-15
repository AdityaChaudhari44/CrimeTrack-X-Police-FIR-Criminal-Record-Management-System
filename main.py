#!/usr/bin/env python3
"""Start the CrimeTrack-X Django web app and open it in the browser."""

import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

WEB_URL = "http://127.0.0.1:8000/"


def _open_web_app_when_ready() -> None:
    """Open the app once Django's local development server responds."""
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(WEB_URL, timeout=1):
                webbrowser.open(WEB_URL)
                return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)


def main() -> int:
    manage_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manage.py")
    if not os.path.isfile(manage_py):
        print(f"Could not find Django entry point: {manage_py}", file=sys.stderr)
        return 1

    print(f"CrimeTrack-X web app: {WEB_URL}", flush=True)
    print("Starting the web server. Press Ctrl+C in this terminal to stop it.", flush=True)
    threading.Thread(target=_open_web_app_when_ready, daemon=True).start()
    try:
        return subprocess.call([sys.executable, manage_py, "runserver", "127.0.0.1:8000"])
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
