# controllers/auth_controller.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Auth Controller
# ─────────────────────────────────────────────

from models.user_model import UserModel
from models.officer_model import OfficerModel
from utils.security import PasswordManager, current_session
from utils.helpers import audit_log
from views.menu_view import (
    print_banner, print_section_header, print_success,
    print_error, print_info, prompt_password, press_enter,
    Colors, clear_screen
)
from colorama import Fore, Style
import getpass


class AuthController:
    """Handles login, logout, and password change flows."""

    # ── Login ────────────────────────────────────────────────────
    @staticmethod
    def login() -> bool:
        """
        Display login prompt; populate current_session on success.
        Returns True on success, False on failure.
        """
        print_section_header("OFFICER / ADMIN LOGIN", 50)
        username = input(f"  {Fore.YELLOW}Username : {Style.RESET_ALL}").strip()
        if not username:
            print_error("Username cannot be empty.")
            return False

        password = getpass.getpass(f"  {Fore.YELLOW}Password : {Style.RESET_ALL}")

        user = UserModel.get_by_username(username)
        if not user:
            print_error("Invalid credentials. User not found.")
            audit_log(None, f"FAILED_LOGIN: username={username}")
            return False

        if not PasswordManager.verify_password(password, user["password_hash"]):
            print_error("Invalid credentials. Wrong password.")
            audit_log(user["user_id"], "FAILED_LOGIN: wrong password")
            return False

        # success
        current_session.create(user)
        UserModel.update_last_login(user["user_id"])
        audit_log(user["user_id"], "LOGIN_SUCCESS")

        print_success(f"Welcome back, {username}!  Role: {user['role'].upper()}")
        press_enter()
        return True

    # ── Logout ───────────────────────────────────────────────────
    @staticmethod
    def logout() -> None:
        if current_session.is_authenticated:
            audit_log(current_session.user_id, "LOGOUT")
            username = current_session.username
            current_session.destroy()
            print_success(f"Goodbye, {username}! Session closed.")
        else:
            print_info("No active session.")

    # ── Change Password ───────────────────────────────────────────
    @staticmethod
    def change_password() -> None:
        if not current_session.require_auth():
            print_error("Not authenticated.")
            return

        print_section_header("CHANGE PASSWORD", 40)
        current_pw = getpass.getpass(f"  {Fore.YELLOW}Current password : {Style.RESET_ALL}")
        user = UserModel.get_by_id(current_session.user_id)

        if not PasswordManager.verify_password(current_pw, user["password_hash"]):
            print_error("Current password is incorrect.")
            press_enter()
            return

        new_pw = getpass.getpass(f"  {Fore.YELLOW}New password     : {Style.RESET_ALL}")
        ok, reason = PasswordManager.is_strong_password(new_pw)
        if not ok:
            print_error(f"Weak password: {reason}")
            press_enter()
            return

        confirm_pw = getpass.getpass(f"  {Fore.YELLOW}Confirm password : {Style.RESET_ALL}")
        if new_pw != confirm_pw:
            print_error("Passwords do not match.")
            press_enter()
            return

        UserModel.update_password(current_session.user_id, PasswordManager.hash_password(new_pw))
        audit_log(current_session.user_id, "PASSWORD_CHANGED")
        print_success("Password changed successfully!")
        press_enter()

    # ── Register New User (admin only) ────────────────────────────
    @staticmethod
    def register_user() -> None:
        if not current_session.require_admin():
            print_error("Admin access required.")
            press_enter()
            return

        print_section_header("REGISTER NEW USER", 40)
        username = input(f"  {Fore.YELLOW}Username : {Style.RESET_ALL}").strip()
        if not username:
            print_error("Username cannot be empty.")
            press_enter()
            return

        if UserModel.get_by_username(username):
            print_error(f"Username '{username}' already exists.")
            press_enter()
            return

        role_input = input(f"  {Fore.YELLOW}Role (admin/officer) [officer]: {Style.RESET_ALL}").strip().lower()
        role = role_input if role_input in ("admin", "officer") else "officer"

        password = getpass.getpass(f"  {Fore.YELLOW}Password : {Style.RESET_ALL}")
        ok, reason = PasswordManager.is_strong_password(password)
        if not ok:
            print_error(f"Weak password: {reason}")
            press_enter()
            return

        confirm_pw = getpass.getpass(f"  {Fore.YELLOW}Confirm  : {Style.RESET_ALL}")
        if password != confirm_pw:
            print_error("Passwords do not match.")
            press_enter()
            return

        uid = UserModel.create(username, PasswordManager.hash_password(password), role)
        audit_log(current_session.user_id, "USER_CREATED", "users", uid, f"username={username}")
        print_success(f"User '{username}' created with role '{role}'. (ID: {uid})")
        press_enter()
