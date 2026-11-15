# controllers/case_controller.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Case & Investigation Controller
# ─────────────────────────────────────────────

from models.case_model import CaseModel
from models.fir_model import FIRModel
from models.officer_model import OfficerModel
from utils.security import current_session
from utils.helpers import audit_log, generate_case_number
from utils.validators import (
    prompt_required, prompt_optional, prompt_int, prompt_choice, validate_date
)
from views.menu_view import (
    print_section_header, print_success, print_error, print_info,
    print_table, print_menu, press_enter, confirm, paginate_display,
    clear_screen, Colors, print_divider
)
from colorama import Fore, Style

CASE_COLS    = ["case_id","case_number","title","status","priority","officer_name","fir_number","opened_at"]
CASE_HEADERS = ["ID","Case No.","Title","Status","Priority","Officer","FIR No.","Opened"]

CASE_STATUSES  = ["Open","Pending","Under Investigation","Closed","Cold"]
CASE_PRIORITIES= ["Low","Medium","High","Critical"]
EVID_STATUSES  = ["Collected","In Lab","Processed","Archived"]


class CaseController:
    """Manages cases, investigation notes, and evidence."""

    # ── List ──────────────────────────────────────────────────────
    @staticmethod
    def list_cases() -> None:
        clear_screen()
        print_section_header("ALL CASES")
        data = CaseModel.get_all()
        paginate_display(data, CASE_COLS, CASE_HEADERS)

    # ── View ──────────────────────────────────────────────────────
    @staticmethod
    def view_case() -> None:
        clear_screen()
        print_section_header("CASE DETAILS")
        cid = prompt_int("  Case ID: ", min_val=1)
        case = CaseModel.get_by_id(cid)
        if not case:
            print_error("Case not found.")
            press_enter()
            return
        CaseController._print_case_detail(case)
        press_enter()

    @staticmethod
    def _print_case_detail(case: dict) -> None:
        print(f"\n  {Colors.header('═══ CASE RECORD ════')}")
        fields = [
            ("Case ID",       case["case_id"]),
            ("Case Number",   case["case_number"]),
            ("FIR Number",    case.get("fir_number") or "—"),
            ("Title",         case["title"]),
            ("Status",        case["status"]),
            ("Priority",      case["priority"] or "—"),
            ("Assigned To",   case.get("officer_name") or "Unassigned"),
            ("Court Date",    case.get("court_date") or "—"),
            ("Verdict",       case.get("verdict") or "—"),
            ("Opened At",     str(case["opened_at"])),
            ("Closed At",     str(case["closed_at"]) if case.get("closed_at") else "—"),
        ]
        for label, val in fields:
            print(f"  {Fore.CYAN}{label:<16}{Style.RESET_ALL} : {val}")

        # Notes
        notes = CaseModel.get_notes(case["case_id"])
        if notes:
            print(f"\n  {Colors.header('─── Investigation Notes ───')}")
            for n in notes:
                print(f"  {Style.DIM}[{n['created_at']}]{Style.RESET_ALL}"
                      f" {Fore.CYAN}{n.get('officer_name','—')}{Style.RESET_ALL}: {n['note_text']}")

        # Evidence
        evidence = CaseModel.get_evidence(case["case_id"])
        if evidence:
            print(f"\n  {Colors.header('─── Evidence ───')}")
            print_table(
                evidence,
                ["evidence_id","evidence_type","description","status","collected_by_name"],
                ["ID","Type","Description","Status","Collected By"]
            )

    # ── Open new case ─────────────────────────────────────────────
    @staticmethod
    def open_case() -> None:
        clear_screen()
        print_section_header("OPEN NEW CASE")
        fir_id = prompt_int("  FIR ID to base this case on: ", min_val=1)
        fir    = FIRModel.get_by_id(fir_id)
        if not fir:
            print_error("FIR not found.")
            press_enter()
            return

        existing = CaseModel.get_by_fir(fir_id)
        if existing:
            print_info(f"A case already exists for this FIR: {existing['case_number']}")
            press_enter()
            return

        title = prompt_required(
            "  Case Title: ",
        ) or f"{fir['offense_type']} – {fir['location']}"

        print(f"  Priority options: {', '.join(CASE_PRIORITIES)}")
        priority = prompt_choice("  Priority: ", CASE_PRIORITIES)

        officer_id = fir.get("officer_id")
        if confirm("  Assign a different officer? (y/n): "):
            oid = prompt_int("  Officer ID: ", min_val=1)
            if OfficerModel.get_by_id(oid):
                officer_id = oid
            else:
                print_error("Officer not found. Using FIR's assigned officer.")

        court_date = prompt_optional("  Court Date (YYYY-MM-DD, optional): ")
        if court_date and not validate_date(court_date):
            print_error("Invalid date. Field left blank.")
            court_date = None

        case_no = generate_case_number()
        case_id = CaseModel.create({
            "case_number": case_no, "fir_id": fir_id, "title": title,
            "status": "Open", "priority": priority,
            "assigned_to": officer_id, "court_date": court_date or None,
        })
        audit_log(current_session.user_id, "CASE_OPENED", "cases", case_id, case_no)
        print_success(f"Case '{case_no}' opened! (ID: {case_id})")
        press_enter()

    # ── Update case ───────────────────────────────────────────────
    @staticmethod
    def update_case() -> None:
        clear_screen()
        print_section_header("UPDATE CASE")
        cid  = prompt_int("  Case ID: ", min_val=1)
        case = CaseModel.get_by_id(cid)
        if not case:
            print_error("Case not found.")
            press_enter()
            return

        CaseController._print_case_detail(case)
        print_info("Press ENTER to keep current value.")

        title = prompt_optional(f"  Title    [{case['title']}]: ") or case["title"]
        print(f"  Statuses: {', '.join(CASE_STATUSES)}")
        status = prompt_optional(f"  Status   [{case['status']}]: ") or case["status"]
        if status not in CASE_STATUSES:
            print_error("Invalid status. Keeping current.")
            status = case["status"]

        print(f"  Priorities: {', '.join(CASE_PRIORITIES)}")
        priority = prompt_optional(f"  Priority [{case['priority']}]: ") or case["priority"]
        if priority not in CASE_PRIORITIES:
            priority = case["priority"]

        officer_id = case.get("assigned_to")
        if confirm("  Reassign officer? (y/n): "):
            oid = prompt_int("  Officer ID: ", min_val=1)
            if OfficerModel.get_by_id(oid):
                officer_id = oid
            else:
                print_error("Officer not found. Keeping current.")

        court_date = prompt_optional(f"  Court Date [{case.get('court_date') or ''}]: ")
        if court_date and not validate_date(court_date):
            print_error("Invalid date. Keeping current.")
            court_date = case.get("court_date")
        elif not court_date:
            court_date = case.get("court_date")

        verdict = prompt_optional(f"  Verdict  [{case.get('verdict') or ''}]: ") or case.get("verdict")

        CaseModel.update(cid, {
            "title": title, "status": status, "priority": priority,
            "assigned_to": officer_id, "court_date": court_date, "verdict": verdict,
        })
        audit_log(current_session.user_id, "CASE_UPDATED", "cases", cid)
        print_success(f"Case '{case['case_number']}' updated.")
        press_enter()

    # ── Add investigation note ─────────────────────────────────────
    @staticmethod
    def add_note() -> None:
        clear_screen()
        print_section_header("ADD INVESTIGATION NOTE")
        cid  = prompt_int("  Case ID: ", min_val=1)
        case = CaseModel.get_by_id(cid)
        if not case:
            print_error("Case not found.")
            press_enter()
            return

        note_text = prompt_required("  Note text: ")

        # Determine officer from session
        from models.officer_model import OfficerModel
        officer = OfficerModel.get_by_user_id(current_session.user_id)
        officer_id = officer["officer_id"] if officer else None

        CaseModel.add_note(cid, officer_id, note_text)
        audit_log(current_session.user_id, "NOTE_ADDED", "investigation_notes", cid)
        print_success("Note added to case.")
        press_enter()

    # ── Add evidence ──────────────────────────────────────────────
    @staticmethod
    def add_evidence() -> None:
        clear_screen()
        print_section_header("ADD EVIDENCE")
        cid  = prompt_int("  Case ID: ", min_val=1)
        case = CaseModel.get_by_id(cid)
        if not case:
            print_error("Case not found.")
            press_enter()
            return

        ev_type    = prompt_required("  Evidence Type (Weapon/CCTV/Document/Digital/Other): ")
        desc       = prompt_optional("  Description  : ")
        location   = prompt_optional("  Storage Location: ")
        print(f"  Status options: {', '.join(EVID_STATUSES)}")
        status     = prompt_choice("  Evidence Status: ", EVID_STATUSES)

        officer    = OfficerModel.get_by_user_id(current_session.user_id)
        officer_id = officer["officer_id"] if officer else None

        eid = CaseModel.add_evidence(cid, {
            "evidence_type": ev_type, "description": desc or None,
            "location": location or None, "collected_by": officer_id, "status": status,
        })
        audit_log(current_session.user_id, "EVIDENCE_ADDED", "evidence", eid)
        print_success(f"Evidence item added (ID: {eid}).")
        press_enter()

    # ── Update evidence status ────────────────────────────────────
    @staticmethod
    def update_evidence() -> None:
        clear_screen()
        print_section_header("UPDATE EVIDENCE STATUS")
        eid    = prompt_int("  Evidence ID: ", min_val=1)
        print(f"  Status options: {', '.join(EVID_STATUSES)}")
        status = prompt_choice("  New Status: ", EVID_STATUSES)
        CaseModel.update_evidence_status(eid, status)
        print_success(f"Evidence {eid} status updated to '{status}'.")
        press_enter()

    # ── Filter by status ──────────────────────────────────────────
    @staticmethod
    def filter_by_status() -> None:
        clear_screen()
        print_section_header("FILTER CASES BY STATUS")
        print(f"  Options: {', '.join(CASE_STATUSES)}")
        status = prompt_choice("  Status: ", CASE_STATUSES)
        data   = CaseModel.get_by_status(status)
        if not data:
            print_info(f"No cases with status '{status}'.")
        else:
            paginate_display(data, CASE_COLS, CASE_HEADERS)

    # ── Menu ──────────────────────────────────────────────────────
    @staticmethod
    def menu() -> None:
        while True:
            clear_screen()
            print_menu("CASE TRACKING & INVESTIGATION", [
                ("1", "List All Cases"),
                ("2", "View Case Details (Notes & Evidence)"),
                ("3", "Open New Case"),
                ("4", "Update Case"),
                ("5", "Add Investigation Note"),
                ("6", "Add Evidence"),
                ("7", "Update Evidence Status"),
                ("8", "Filter Cases by Status"),
                ("0", "Back"),
            ])
            choice = input("  Select option: ").strip()
            if   choice == "1": CaseController.list_cases()
            elif choice == "2": CaseController.view_case()
            elif choice == "3": CaseController.open_case()
            elif choice == "4": CaseController.update_case()
            elif choice == "5": CaseController.add_note()
            elif choice == "6": CaseController.add_evidence()
            elif choice == "7": CaseController.update_evidence()
            elif choice == "8": CaseController.filter_by_status()
            elif choice == "0": break
            else: print_error("Invalid option.")
