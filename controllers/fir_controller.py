# controllers/fir_controller.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  FIR Controller
# ─────────────────────────────────────────────

from models.fir_model import FIRModel
from models.case_model import CaseModel
from models.officer_model import OfficerModel
from models.criminal_model import CriminalModel
from utils.security import current_session
from utils.helpers import audit_log, generate_fir_number, generate_case_number
from utils.validators import (
    prompt_required, prompt_optional, prompt_int, prompt_choice,
    validate_phone, validate_date
)
from views.fir_view import display_fir_detail, display_fir_list, display_fir_receipt, display_search_results
from views.menu_view import (
    print_section_header, print_success, print_error, print_info,
    print_table, print_menu, press_enter, confirm, paginate_display,
    clear_screen, Colors, print_divider
)
from colorama import Fore, Style

FIR_COLS    = ["fir_id","fir_number","complainant","offense_type","incident_date","status","officer_name"]
FIR_HEADERS = ["ID","FIR No.","Complainant","Offense","Date","Status","Officer"]

FIR_STATUSES = ["Registered","Under Investigation","Charge-Sheeted","Closed","Disposed"]


class FIRController:
    """Manages FIR lifecycle."""

    # ── List ──────────────────────────────────────────────────────
    @staticmethod
    def list_firs() -> None:
        clear_screen()
        print_section_header("ALL FIRs")
        data = FIRModel.get_all()
        paginate_display(data, FIR_COLS, FIR_HEADERS)

    # ── View ──────────────────────────────────────────────────────
    @staticmethod
    def view_fir() -> None:
        clear_screen()
        print_section_header("FIR DETAILS")
        fir_input = input("  Enter FIR ID or FIR Number: ").strip()

        if fir_input.upper().startswith("FIR-"):
            fir = FIRModel.get_by_fir_number(fir_input.upper())
        else:
            try:
                fir = FIRModel.get_by_id(int(fir_input))
            except ValueError:
                print_error("Invalid input.")
                press_enter()
                return

        if not fir:
            print_error("FIR not found.")
            press_enter()
            return

        FIRController._print_fir_detail(fir)
        press_enter()

    @staticmethod
    def _print_fir_detail(fir: dict) -> None:
        display_fir_detail(fir)

    # ── Register FIR ──────────────────────────────────────────────
    @staticmethod
    def register_fir() -> None:
        clear_screen()
        print_section_header("REGISTER NEW FIR")

        complainant   = prompt_required("  Complainant Name     : ")
        comp_ph       = prompt_optional("  Complainant Phone    : ")
        if comp_ph and not validate_phone(comp_ph):
            print_error("Invalid phone. Saved without it.")
            comp_ph = None
        incident_date = prompt_required(
            "  Incident Date (YYYY-MM-DD): ",
            validator=validate_date,
            error_msg="Use YYYY-MM-DD format."
        )
        incident_time = prompt_optional("  Incident Time (HH:MM): ")
        location      = prompt_required("  Incident Location    : ")
        offense_type  = prompt_required("  Offense Type         : ")
        ipc_sections  = prompt_optional("  IPC Sections         : ")
        description   = prompt_optional("  Description          : ")

        # Link to officer
        officer_id = None
        if confirm("  Assign to an officer now? (y/n): "):
            oid = prompt_int("  Officer ID: ", min_val=1)
            if OfficerModel.get_by_id(oid):
                officer_id = oid
            else:
                print_error(f"Officer ID {oid} not found. Proceeding without assignment.")

        # Link to criminal
        criminal_id = None
        if confirm("  Link to a known criminal? (y/n): "):
            cid = prompt_int("  Criminal ID: ", min_val=1)
            c = CriminalModel.get_by_id(cid)
            if c:
                criminal_id = cid
                # Increment arrest count
                CriminalModel.increment_arrest_count(cid)
            else:
                print_error(f"Criminal ID {cid} not found. FIR filed without link.")

        fir_number = generate_fir_number()
        data = {
            "fir_number": fir_number, "complainant": complainant,
            "complainant_ph": comp_ph, "incident_date": incident_date,
            "incident_time": incident_time or None, "location": location,
            "offense_type": offense_type, "ipc_sections": ipc_sections or None,
            "description": description or None, "status": "Registered",
            "officer_id": officer_id, "criminal_id": criminal_id,
            "registered_by": current_session.user_id,
        }
        fir_id = FIRModel.create(data)
        audit_log(current_session.user_id, "FIR_REGISTERED", "firs", fir_id, fir_number)

        # Auto-create a case
        if confirm("  Automatically open a Case for this FIR? (y/n): "):
            case_no = generate_case_number()
            CaseModel.create({
                "case_number": case_no,
                "fir_id": fir_id,
                "title": f"{offense_type} – {location}",
                "status": "Open",
                "priority": "Medium",
                "assigned_to": officer_id,
            })
            print_success(f"FIR {fir_number} registered and Case {case_no} opened!")
        else:
            print_success(f"FIR {fir_number} registered successfully! (ID: {fir_id})")
        press_enter()

    # ── Update FIR ────────────────────────────────────────────────
    @staticmethod
    def update_fir() -> None:
        clear_screen()
        print_section_header("UPDATE FIR")
        fir_id = prompt_int("  FIR ID to update: ", min_val=1)
        fir    = FIRModel.get_by_id(fir_id)
        if not fir:
            print_error("FIR not found.")
            press_enter()
            return

        FIRController._print_fir_detail(fir)
        print_info("Press ENTER to keep current value.")

        complainant   = prompt_optional(f"  Complainant  [{fir['complainant']}]: ") or fir["complainant"]
        comp_ph       = prompt_optional(f"  Phone        [{fir['complainant_ph'] or ''}]: ") or fir.get("complainant_ph")
        incident_date = prompt_optional(f"  Date         [{fir['incident_date']}]: ") or str(fir["incident_date"])
        incident_time = prompt_optional(f"  Time         [{fir['incident_time'] or ''}]: ") or fir.get("incident_time")
        location      = prompt_optional(f"  Location     [{fir['location']}]: ") or fir["location"]
        offense_type  = prompt_optional(f"  Offense      [{fir['offense_type']}]: ") or fir["offense_type"]
        ipc_sections  = prompt_optional(f"  IPC sections [{fir['ipc_sections'] or ''}]: ") or fir.get("ipc_sections")
        description   = prompt_optional(f"  Description  [{(fir['description'] or '')[:40]}]: ") or fir.get("description")

        print(f"\n  Statuses: {', '.join(FIR_STATUSES)}")
        status = prompt_optional(f"  Status  [{fir['status']}]: ") or fir["status"]
        if status not in FIR_STATUSES:
            print_error(f"Invalid status '{status}'. Keeping current.")
            status = fir["status"]

        officer_id  = fir.get("officer_id")
        if confirm("  Change assigned officer? (y/n): "):
            oid = prompt_int("  New Officer ID: ", min_val=1)
            if OfficerModel.get_by_id(oid):
                officer_id = oid
            else:
                print_error("Officer not found. Keeping current.")

        criminal_id = fir.get("criminal_id")
        if confirm("  Change linked criminal? (y/n): "):
            cid_input = input("  Criminal ID (0 to unlink): ").strip()
            try:
                cid = int(cid_input)
                if cid == 0:
                    criminal_id = None
                elif CriminalModel.get_by_id(cid):
                    criminal_id = cid
                else:
                    print_error("Criminal not found. Keeping current.")
            except ValueError:
                print_error("Invalid input. Keeping current.")

        FIRModel.update(fir_id, {
            "complainant": complainant, "complainant_ph": comp_ph,
            "incident_date": incident_date, "incident_time": incident_time,
            "location": location, "offense_type": offense_type,
            "ipc_sections": ipc_sections, "description": description,
            "status": status, "officer_id": officer_id, "criminal_id": criminal_id,
        })
        audit_log(current_session.user_id, "FIR_UPDATED", "firs", fir_id)
        print_success(f"FIR {fir['fir_number']} updated successfully.")
        press_enter()

    # ── Delete FIR ────────────────────────────────────────────────
    @staticmethod
    def delete_fir() -> None:
        if not current_session.require_admin():
            print_error("Admin access required.")
            press_enter()
            return
        clear_screen()
        print_section_header("DELETE FIR")
        fir_id = prompt_int("  FIR ID to delete: ", min_val=1)
        fir    = FIRModel.get_by_id(fir_id)
        if not fir:
            print_error("FIR not found.")
            press_enter()
            return
        if confirm(f"  Delete FIR '{fir['fir_number']}'? This will also delete linked cases. (y/n): "):
            FIRModel.delete(fir_id)
            audit_log(current_session.user_id, "FIR_DELETED", "firs", fir_id, fir["fir_number"])
            print_success("FIR deleted.")
        else:
            print_info("Cancelled.")
        press_enter()

    # ── Assign Officer ────────────────────────────────────────────
    @staticmethod
    def assign_officer() -> None:
        clear_screen()
        print_section_header("ASSIGN OFFICER TO FIR")
        fir_id    = prompt_int("  FIR ID  : ", min_val=1)
        officer_id= prompt_int("  Officer ID: ", min_val=1)
        fir       = FIRModel.get_by_id(fir_id)
        officer   = OfficerModel.get_by_id(officer_id)
        if not fir:
            print_error("FIR not found.")
        elif not officer:
            print_error("Officer not found.")
        else:
            FIRModel.assign_officer(fir_id, officer_id)
            audit_log(current_session.user_id, "FIR_OFFICER_ASSIGNED", "firs", fir_id,
                      f"officer={officer_id}")
            print_success(f"Officer '{officer['full_name']}' assigned to FIR '{fir['fir_number']}'.")
        press_enter()

    # ── Search ────────────────────────────────────────────────────
    @staticmethod
    def search_fir() -> None:
        clear_screen()
        print_menu("SEARCH FIR", [
            ("1", "Search by Keyword (name / offense / location)"),
            ("2", "Search by Date"),
            ("3", "Search by Status"),
        ])
        choice = input("  Choose search type: ").strip()
        if choice == "1":
            q = prompt_required("  Keyword: ")
            results = FIRModel.search(q)
        elif choice == "2":
            d = prompt_required("  Date (YYYY-MM-DD): ", validator=validate_date,
                                error_msg="Use YYYY-MM-DD format.")
            results = FIRModel.search_by_date(d)
        elif choice == "3":
            print(f"  Statuses: {', '.join(FIR_STATUSES)}")
            s = prompt_required("  Status: ")
            results = FIRModel.search_by_status(s)
        else:
            print_error("Invalid choice.")
            press_enter()
            return

        if not results:
            print_info("No FIRs matched your query.")
            press_enter()
            return
        paginate_display(results, FIR_COLS, FIR_HEADERS)

    # ── Menu ──────────────────────────────────────────────────────
    @staticmethod
    def menu() -> None:
        while True:
            clear_screen()
            print_menu("FIR MANAGEMENT", [
                ("1", "List All FIRs"),
                ("2", "View FIR Details"),
                ("3", "Register New FIR"),
                ("4", "Update FIR"),
                ("5", "Delete FIR  (Admin)"),
                ("6", "Assign Officer to FIR"),
                ("7", "Search FIR"),
                ("0", "Back"),
            ])
            choice = input("  Select option: ").strip()
            if   choice == "1": FIRController.list_firs()
            elif choice == "2": FIRController.view_fir()
            elif choice == "3": FIRController.register_fir()
            elif choice == "4": FIRController.update_fir()
            elif choice == "5": FIRController.delete_fir()
            elif choice == "6": FIRController.assign_officer()
            elif choice == "7": FIRController.search_fir()
            elif choice == "0": break
            else: print_error("Invalid option.")
