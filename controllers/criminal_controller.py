# controllers/criminal_controller.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Criminal Controller
# ─────────────────────────────────────────────

from models.criminal_model import CriminalModel
from utils.security import current_session
from utils.helpers import audit_log
from utils.validators import (
    prompt_required, prompt_optional, prompt_int, prompt_choice,
    validate_phone, validate_date
)
from views.criminal_view import (
    display_criminal_list, display_criminal_profile,
    display_fir_history, display_wanted_banner
)
from views.menu_view import (
    print_section_header, print_success, print_error, print_info,
    print_table, print_menu, press_enter, confirm, paginate_display,
    clear_screen, Colors
)
from colorama import Fore, Style


CRIM_COLS    = ["criminal_id","full_name","alias","gender","dob","nationality","is_wanted","arrest_count"]
CRIM_HEADERS = ["ID","Full Name","Alias","Gender","DOB","Nationality","Wanted","Arrests"]


class CriminalController:
    """Manages criminal record CRUD."""

    # ── List ──────────────────────────────────────────────────────
    @staticmethod
    def list_criminals() -> None:
        clear_screen()
        print_section_header("CRIMINAL RECORDS")
        data = CriminalModel.get_all()
        paginate_display(data, CRIM_COLS, CRIM_HEADERS)

    # ── View ──────────────────────────────────────────────────────
    @staticmethod
    def view_criminal() -> None:
        clear_screen()
        print_section_header("CRIMINAL PROFILE")
        cid = prompt_int("  Criminal ID: ", min_val=1)
        c = CriminalModel.get_by_id(cid)
        if not c:
            print_error(f"Criminal ID {cid} not found.")
            press_enter()
            return
        history = CriminalModel.get_fir_history(cid)
        display_criminal_profile(c)
        display_fir_history(history, c["full_name"])
        press_enter()

    # ── Add ───────────────────────────────────────────────────────
    @staticmethod
    def add_criminal() -> None:
        clear_screen()
        print_section_header("ADD CRIMINAL RECORD")

        full_name    = prompt_required("  Full Name       : ")
        alias        = prompt_optional("  Alias           : ")
        gender       = prompt_choice("  Gender (Male/Female/Other): ", ["Male","Female","Other"])
        dob          = prompt_optional("  Date of Birth (YYYY-MM-DD): ")
        if dob and not validate_date(dob):
            print_error("Invalid DOB format. Field left blank.")
            dob = None
        nationality  = prompt_optional("  Nationality     [Indian]: ") or "Indian"
        address      = prompt_optional("  Address         : ")
        phone        = prompt_optional("  Phone           : ")
        if phone and not validate_phone(phone):
            print_error("Invalid phone. Field left blank.")
            phone = None
        id_type      = prompt_optional("  ID Proof Type (Aadhaar/PAN/Passport): ")
        id_no        = prompt_optional("  ID Proof Number : ")
        blood_group  = prompt_optional("  Blood Group     : ")
        physical     = prompt_optional("  Physical Desc   : ")
        is_wanted    = confirm("  Mark as WANTED? (y/n): ")

        data = {
            "full_name": full_name, "alias": alias or None, "dob": dob,
            "gender": gender, "nationality": nationality, "address": address,
            "phone": phone, "id_proof_type": id_type or None,
            "id_proof_no": id_no or None, "blood_group": blood_group or None,
            "physical_desc": physical or None, "is_wanted": is_wanted,
        }
        cid = CriminalModel.create(data)
        audit_log(current_session.user_id, "CRIMINAL_CREATED", "criminals", cid, full_name)
        print_success(f"Criminal '{full_name}' added. (ID: {cid})")
        press_enter()

    # ── Edit ──────────────────────────────────────────────────────
    @staticmethod
    def edit_criminal() -> None:
        clear_screen()
        print_section_header("EDIT CRIMINAL RECORD")
        cid = prompt_int("  Criminal ID: ", min_val=1)
        c = CriminalModel.get_by_id(cid)
        if not c:
            print_error(f"Criminal ID {cid} not found.")
            press_enter()
            return
        print_info("Press ENTER to keep current value.")

        full_name   = prompt_optional(f"  Full Name  [{c['full_name']}]: ") or c["full_name"]
        alias       = prompt_optional(f"  Alias      [{c['alias'] or ''}]: ") or c.get("alias")
        gender      = prompt_optional(f"  Gender     [{c['gender'] or ''}]: ") or c.get("gender")
        dob         = prompt_optional(f"  DOB        [{c['dob'] or ''}]: ") or c.get("dob")
        nationality = prompt_optional(f"  Nationality[{c['nationality'] or ''}]: ") or c.get("nationality")
        address     = prompt_optional(f"  Address    [{c['address'] or ''}]: ") or c.get("address")
        phone       = prompt_optional(f"  Phone      [{c['phone'] or ''}]: ") or c.get("phone")
        is_wanted_s = prompt_optional(f"  Wanted 1/0 [{c['is_wanted']}]: ") or str(c["is_wanted"])
        is_wanted   = is_wanted_s in ("1","yes","true","y")

        CriminalModel.update(cid, {
            "full_name": full_name, "alias": alias, "dob": dob,
            "gender": gender, "nationality": nationality, "address": address,
            "phone": phone, "id_proof_type": c.get("id_proof_type"),
            "id_proof_no": c.get("id_proof_no"), "blood_group": c.get("blood_group"),
            "physical_desc": c.get("physical_desc"), "is_wanted": is_wanted,
        })
        audit_log(current_session.user_id, "CRIMINAL_UPDATED", "criminals", cid)
        print_success(f"Criminal '{full_name}' updated.")
        press_enter()

    # ── Search ────────────────────────────────────────────────────
    @staticmethod
    def search_criminals() -> None:
        clear_screen()
        print_section_header("SEARCH CRIMINALS")
        query = prompt_required("  Search (name / alias / ID proof): ")
        results = CriminalModel.search(query)
        if not results:
            print_info("No matches found.")
        else:
            print_table(results, CRIM_COLS, CRIM_HEADERS)
        press_enter()

    # ── Most Wanted ───────────────────────────────────────────────
    @staticmethod
    def most_wanted() -> None:
        clear_screen()
        print_section_header("MOST WANTED LIST")
        data = CriminalModel.get_wanted()
        if not data:
            print_info("No wanted criminals on record.")
        else:
            display_wanted_banner(data)
            print_table(data, CRIM_COLS, CRIM_HEADERS)
        press_enter()

    # ── Repeat Offenders ──────────────────────────────────────────
    @staticmethod
    def repeat_offenders() -> None:
        clear_screen()
        print_section_header("REPEAT OFFENDERS")
        min_a = prompt_int("  Minimum arrests to filter by [2]: ", min_val=1)
        data  = CriminalModel.get_repeat_offenders(min_a)
        if not data:
            print_info(f"No criminals with {min_a}+ arrests.")
        else:
            print_table(data, CRIM_COLS, CRIM_HEADERS)
        press_enter()

    # ── Delete ────────────────────────────────────────────────────
    @staticmethod
    def delete_criminal() -> None:
        if not current_session.require_admin():
            print_error("Admin access required.")
            press_enter()
            return
        clear_screen()
        print_section_header("DELETE CRIMINAL RECORD")
        cid = prompt_int("  Criminal ID: ", min_val=1)
        c = CriminalModel.get_by_id(cid)
        if not c:
            print_error(f"Criminal ID {cid} not found.")
            press_enter()
            return
        if confirm(f"  Delete '{c['full_name']}'? (y/n): "):
            CriminalModel.delete(cid)
            audit_log(current_session.user_id, "CRIMINAL_DELETED", "criminals", cid)
            print_success("Criminal record deleted.")
        else:
            print_info("Cancelled.")
        press_enter()

    # ── Menu ──────────────────────────────────────────────────────
    @staticmethod
    def menu() -> None:
        while True:
            clear_screen()
            print_menu("CRIMINAL RECORDS", [
                ("1", "List All Criminals"),
                ("2", "View Criminal Profile"),
                ("3", "Add Criminal Record"),
                ("4", "Edit Criminal Record"),
                ("5", "Search Criminals"),
                ("6", "Most Wanted List"),
                ("7", "Repeat Offenders"),
                ("8", "Delete Criminal Record"),
                ("0", "Back"),
            ])
            choice = input("  Select option: ").strip()
            if choice == "1": CriminalController.list_criminals()
            elif choice == "2": CriminalController.view_criminal()
            elif choice == "3": CriminalController.add_criminal()
            elif choice == "4": CriminalController.edit_criminal()
            elif choice == "5": CriminalController.search_criminals()
            elif choice == "6": CriminalController.most_wanted()
            elif choice == "7": CriminalController.repeat_offenders()
            elif choice == "8": CriminalController.delete_criminal()
            elif choice == "0": break
            else: print_error("Invalid option.")
