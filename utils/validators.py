# utils/validators.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Input Validators
# ─────────────────────────────────────────────

import re
import datetime


def validate_phone(phone: str) -> bool:
    """Accept 10-digit Indian mobile numbers (optionally with +91 prefix)."""
    cleaned = re.sub(r"[\s\-()]", "", phone)
    return bool(re.fullmatch(r"(\+91)?[6-9]\d{9}", cleaned))


def validate_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


def validate_date(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
    try:
        datetime.datetime.strptime(date_str, fmt)
        return True
    except ValueError:
        return False


def validate_non_empty(value: str) -> bool:
    return bool(value and value.strip())


def validate_positive_int(value: str) -> bool:
    try:
        return int(value) > 0
    except (ValueError, TypeError):
        return False


def validate_badge_number(badge: str) -> bool:
    """Badge format: 2-5 alpha chars, hyphen, 3-6 digits.  e.g. MH-001"""
    return bool(re.fullmatch(r"[A-Z]{2,5}-\d{3,6}", badge.upper()))


def sanitize_input(value: str) -> str:
    """Strip leading/trailing whitespace from user input."""
    return value.strip() if value else ""


def prompt_required(prompt_text: str, validator=None, error_msg: str = "Invalid input.") -> str:
    """
    Repeatedly prompt until the user enters a value that passes `validator`.
    Returns the validated (stripped) string.
    """
    from views.menu_view import Colors
    while True:
        raw = input(prompt_text)
        val = sanitize_input(raw)
        if validator is None:
            if val:
                return val
        else:
            if val and validator(val):
                return val
        print(Colors.error(f"  ✗  {error_msg}"))


def prompt_optional(prompt_text: str, default: str = "") -> str:
    """Prompt for optional input; return default if blank."""
    raw = input(prompt_text)
    val = sanitize_input(raw)
    return val if val else default


def prompt_choice(prompt_text: str, choices: list) -> str:
    """Prompt until user picks one of the allowed choices (case-insensitive)."""
    from views.menu_view import Colors
    choices_lower = [c.lower() for c in choices]
    while True:
        raw = input(prompt_text).strip()
        if raw.lower() in choices_lower:
            return choices[choices_lower.index(raw.lower())]
        print(Colors.error(f"  ✗  Please enter one of: {', '.join(choices)}"))


def prompt_int(prompt_text: str, min_val: int = None, max_val: int = None) -> int:
    """Prompt until user enters a valid integer within optional bounds."""
    from views.menu_view import Colors
    while True:
        raw = input(prompt_text).strip()
        try:
            val = int(raw)
            if (min_val is not None and val < min_val) or (max_val is not None and val > max_val):
                bounds = f"{min_val or ''}–{max_val or ''}"
                print(Colors.error(f"  ✗  Please enter a number in range [{bounds}]."))
                continue
            return val
        except ValueError:
            print(Colors.error("  ✗  Please enter a valid integer."))
