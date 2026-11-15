# controllers/officer_controller.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Officer Controller
# ─────────────────────────────────────────────

from models.officer_model import OfficerModel
from models.user_model import UserModel
from utils.security import current_session, PasswordManager
from utils.helpers import audit_log
from utils.validators import (
    prompt_required, prompt_optional, prompt_int,
    validate_phone, validate_email, validate_date, validate_badge_number
)
from views.menu_view import (
    print_section_header, print_success, print_error, print_info,
    print_table, print_menu, press_enter, confirm, paginate_display,
    clear_screen, Colors
)
from views.officer_view import (
    display_officer_list, display_officer_profile, display_officer_cases
)
from colorama import Fore, Style


OFFICER_COLUMNS   = ["officer_id","badge_number","full_name","rank","department","station","phone","is_active"]
OFFICER_HEADERS   = ["ID","Badge","Name","Rank","Department","Station","Phone","Active"]


class OfficerController:
    """Manages officer CRUD and display."""

    # ── List all ─────────────────────────────────────────────────
    @staticmethod
    def list_officers() -> None:
        clear_screen()
        print_section_header("ALL OFFICERS")
        data = OfficerModel.get_all()
        paginate_display(data, OFFICER_COLUMNS, OFFICER_HEADERS)

    # ── View details ──────────────────────────────────────────────
    @staticmethod
    def view_officer() -> None:
        clear_screen()
        oid = prompt_int("  Enter Officer ID: ", min_val=1)
        officer = OfficerModel.get_by_id(oid)
        if not officer:
            print_error(f"Officer ID {oid} not found.")
            press_enter()
            return
        perf = OfficerModel.get_performance(oid)
        from models.case_model import CaseModel
        cases = CaseModel.get_by_officer(oid)
        display_officer_profile(officer, perf)
        if cases:
            print(f"  {Colors.header('─── Assigned Cases ───')}")
            display_officer_cases(cases)
        press_enter()

    # ── Add officer ───────────────────────────────────────────────
    @staticmethod
    def add_officer() -> None:
        if not current_session.require_admin():
            print_error("Admin access required.")
            press_enter()
            return
        clear_screen()
        print_section_header("ADD NEW OFFICER")

        badge = prompt_required(
            "  Badge Number (e.g. MH-001): ",
            validator=lambda v: validate_badge_number(v),
            error_msg="Format: 2-5 uppercase letters, hyphen, 3-6 digits (e.g. MH-001)."
        ).upper()
        if OfficerModel.get_by_badge(badge):
            print_error(f"Badge '{badge}' already registered.")
            press_enter()
            return

        full_name  = prompt_required("  Full Name       : ")
        rank       = prompt_required("  Rank            : ")
        department = prompt_optional("  Department      : ")
        station    = prompt_optional("  Station         : ")
        phone      = prompt_optional("  Phone           : ")
        if phone and not validate_phone(phone):
            print_error("Invalid phone number. Record saved without it.")
            phone = None
        email = prompt_optional("  Email           : ")
        if email and not validate_email(email):
            print_error("Invalid email. Record saved without it.")
            email = None
        date_joined = prompt_optional("  Date Joined (YYYY-MM-DD): ")
        if date_joined and not validate_date(date_joined):
            print_error("Invalid date. Field left blank.")
            date_joined = None

        # Optionally create a login account
        create_login = confirm("  Create login account for this officer? (y/n): ")
        user_id = None
        if create_login:
            uname = prompt_required("  Username: ")
            if UserModel.get_by_username(uname):
                print_error(f"Username '{uname}' already exists. Skipping login creation.")
            else:
                import getpass
                pwd = getpass.getpass(f"  {Fore.YELLOW}Password: {Style.RESET_ALL}")
                ok, reason = PasswordManager.is_strong_password(pwd)
                if not ok:
                    print_error(f"Weak password ({reason}). Skipping login creation.")
                else:
                    user_id = UserModel.create(uname, PasswordManager.hash_password(pwd), "officer")

        data = {
            "user_id": user_id, "badge_number": badge, "full_name": full_name,
            "rank": rank, "department": department, "station": station,
            "phone": phone, "email": email, "date_joined": date_joined or None,
        }
        oid = OfficerModel.create(data)
        audit_log(current_session.user_id, "OFFICER_CREATED", "officers", oid, full_name)
        print_success(f"Officer '{full_name}' added successfully! (ID: {oid})")
        press_enter()

    # ── Edit officer ──────────────────────────────────────────────
    @staticmethod
    def edit_officer() -> None:
        if not current_session.require_admin():
            print_error("Admin access required.")
            press_enter()
            return
        clear_screen()
        print_section_header("EDIT OFFICER")
        oid = prompt_int("  Enter Officer ID: ", min_val=1)
        officer = OfficerModel.get_by_id(oid)
        if not officer:
            print_error(f"Officer ID {oid} not found.")
            press_enter()
            return

        print_info(f"Editing: {officer['full_name']} ({officer['badge_number']})")
        print_info("Press ENTER to keep current value.")

        full_name  = prompt_optional(f"  Full Name   [{officer['full_name']}]: ") or officer["full_name"]
        rank       = prompt_optional(f"  Rank        [{officer['rank']}]: ") or officer["rank"]
        department = prompt_optional(f"  Department  [{officer['department'] or ''}]: ") or officer.get("department")
        station    = prompt_optional(f"  Station     [{officer['station'] or ''}]: ") or officer.get("station")
        phone      = prompt_optional(f"  Phone       [{officer['phone'] or ''}]: ") or officer.get("phone")
        email      = prompt_optional(f"  Email       [{officer['email'] or ''}]: ") or officer.get("email")
        active_str = prompt_optional(f"  Active 1/0  [{officer['is_active']}]: ") or str(officer["is_active"])
        is_active  = active_str in ("1", "yes", "true")

        OfficerModel.update(oid, {
            "full_name": full_name, "rank": rank, "department": department,
            "station": station, "phone": phone, "email": email, "is_active": is_active,
        })
        audit_log(current_session.user_id, "OFFICER_UPDATED", "officers", oid)
        print_success(f"Officer '{full_name}' updated.")
        press_enter()

    # ── Search ────────────────────────────────────────────────────
    @staticmethod
    def search_officers() -> None:
        clear_screen()
        print_section_header("SEARCH OFFICERS")
        query = prompt_required("  Search (name / badge / rank): ")
        results = OfficerModel.search(query)
        if not results:
            print_info("No officers matched your query.")
        else:
            print_table(results, OFFICER_COLUMNS, OFFICER_HEADERS)
        press_enter()

    # ── Delete ────────────────────────────────────────────────────
    @staticmethod
    def delete_officer() -> None:
        if not current_session.require_admin():
            print_error("Admin access required.")
            press_enter()
            return
        clear_screen()
        print_section_header("DELETE OFFICER")
        oid = prompt_int("  Enter Officer ID to delete: ", min_val=1)
        officer = OfficerModel.get_by_id(oid)
        if not officer:
            print_error(f"Officer ID {oid} not found.")
            press_enter()
            return
        if confirm(f"  Delete '{officer['full_name']}'? This cannot be undone. (y/n): "):
            OfficerModel.delete(oid)
            audit_log(current_session.user_id, "OFFICER_DELETED", "officers", oid)
            print_success("Officer deleted.")
        else:
            print_info("Cancelled.")
        press_enter()

    # ── Menu ──────────────────────────────────────────────────────
    @staticmethod
    def menu() -> None:
        while True:
            clear_screen()
            print_menu("OFFICER MANAGEMENT", [
                ("1", "List All Officers"),
                ("2", "View Officer Details"),
                ("3", "Add New Officer"),
                ("4", "Edit Officer"),
                ("5", "Search Officers"),
                ("6", "Delete Officer"),
                ("0", "Back"),
            ])
            choice = input("  Select option: ").strip()
            if choice == "1": OfficerController.list_officers()
            elif choice == "2": OfficerController.view_officer()
            elif choice == "3": OfficerController.add_officer()
            elif choice == "4": OfficerController.edit_officer()
            elif choice == "5": OfficerController.search_officers()
            elif choice == "6": OfficerController.delete_officer()
            elif choice == "0": break
            else: print_error("Invalid option.")
