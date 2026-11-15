# controllers/report_controller.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Report Controller
# ─────────────────────────────────────────────

import datetime
from models.fir_model import FIRModel
from models.case_model import CaseModel
from models.criminal_model import CriminalModel
from models.officer_model import OfficerModel
from utils.helpers import execute_query, export_to_csv, export_to_txt, audit_log
from utils.security import current_session
from utils.validators import prompt_int
from views.report_view import (
    display_fir_summary, display_case_stats,
    display_officer_performance_table, display_monthly_stats,
    display_export_success, display_audit_log_table
)
from views.menu_view import (
    print_section_header, print_success, print_error, print_info,
    print_table, print_menu, press_enter, clear_screen, Colors, print_divider
)
from colorama import Fore, Style
from tabulate import tabulate

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]


class ReportController:
    """Generates system-wide reports and exports."""

    # ── Dashboard stats (used by main.py) ─────────────────────────
    @staticmethod
    def get_dashboard_stats() -> dict:
        row = execute_query(
            """SELECT
               (SELECT COUNT(*) FROM firs)                      AS total_firs,
               (SELECT COUNT(*) FROM cases WHERE status='Open') AS open_cases,
               (SELECT COUNT(*) FROM officers WHERE is_active=1)AS active_officers,
               (SELECT COUNT(*) FROM criminals WHERE is_wanted=1)AS wanted_criminals,
               (SELECT COUNT(*) FROM cases WHERE status='Closed') AS solved_cases
            """, fetch_one=True
        )
        return row or {}

    # ── Total FIRs ────────────────────────────────────────────────
    @staticmethod
    def report_total_firs() -> None:
        clear_screen()
        print_section_header("REPORT: TOTAL FIRs")
        data  = FIRModel.get_all()
        total = len(data)

        # breakdown by status
        statuses = {}
        for f in data:
            statuses[f["status"]] = statuses.get(f["status"], 0) + 1

        off_data = FIRModel.offense_breakdown()
        display_fir_summary(total, statuses, off_data)
        press_enter()

    # ── Active cases ──────────────────────────────────────────────
    @staticmethod
    def report_active_cases() -> None:
        clear_screen()
        print_section_header("REPORT: ACTIVE CASES")
        stats = CaseModel.get_summary_stats()
        critical = execute_query(
            """SELECT cs.case_number, cs.title, cs.status, o.full_name AS officer
               FROM cases cs LEFT JOIN officers o ON cs.assigned_to=o.officer_id
               WHERE cs.priority='Critical' AND cs.status != 'Closed'
               ORDER BY cs.opened_at""",
            fetch=True
        )
        display_case_stats(stats, critical or [])
        press_enter()

    # ── Most wanted ───────────────────────────────────────────────
    @staticmethod
    def report_most_wanted() -> None:
        clear_screen()
        print_section_header("REPORT: MOST WANTED CRIMINALS")
        data = CriminalModel.get_wanted()
        if not data:
            print_info("No wanted criminals.")
            press_enter()
            return
        print(f"\n  {Fore.RED}{Style.BRIGHT}⚠  WANTED LIST  ({len(data)} criminals){Style.RESET_ALL}\n")
        print_table(
            data,
            ["criminal_id","full_name","alias","gender","dob","arrest_count"],
            ["ID","Name","Alias","Gender","DOB","Arrests"]
        )
        press_enter()

    # ── Officer performance ───────────────────────────────────────
    @staticmethod
    def report_officer_performance() -> None:
        clear_screen()
        print_section_header("REPORT: OFFICER PERFORMANCE")
        officers = OfficerModel.get_all(active_only=True)
        rows = []
        for o in officers:
            p = OfficerModel.get_performance(o["officer_id"])
            solve_pct = (
                f"{p['solved_cases']/p['total_cases']*100:.0f}%"
                if p["total_cases"] > 0 else "—"
            )
            rows.append({
                "badge":      o["badge_number"],
                "name":       o["full_name"],
                "rank":       o["rank"],
                "firs":       p["total_firs"],
                "cases":      p["total_cases"],
                "solved":     p["solved_cases"],
                "solve_rate": solve_pct,
            })
        display_officer_performance_table(rows)
        press_enter()

    # ── Monthly crime statistics ──────────────────────────────────
    @staticmethod
    def report_monthly_stats() -> None:
        clear_screen()
        print_section_header("REPORT: MONTHLY CRIME STATISTICS")
        year = prompt_int(f"  Year [{datetime.date.today().year}]: ",
                          min_val=2000, max_val=2100)
        data = FIRModel.monthly_stats(year)
        if not data:
            print_info(f"No FIR data for year {year}.")
            press_enter()
            return

        display_monthly_stats(year, data)
        press_enter()

    # ── Export FIRs to CSV ────────────────────────────────────────
    @staticmethod
    def export_firs_csv() -> None:
        clear_screen()
        print_section_header("EXPORT FIRs TO CSV")
        data      = FIRModel.get_all()
        fields    = ["fir_id","fir_number","complainant","offense_type",
                     "incident_date","location","status","officer_name"]
        ts        = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"firs_{ts}.csv"
        path      = export_to_csv(filename, data, fields)
        audit_log(current_session.user_id, "EXPORT_FIRS_CSV")
        display_export_success(path, len(data), "CSV")
        press_enter()

    # ── Export Wanted to TXT ──────────────────────────────────────
    @staticmethod
    def export_wanted_txt() -> None:
        clear_screen()
        print_section_header("EXPORT MOST WANTED TO TXT")
        data  = CriminalModel.get_wanted()
        lines = ["=" * 60, "  CRIMETRACK-X  –  MOST WANTED LIST", "=" * 60, ""]
        for c in data:
            lines.append(f"  ID:       {c['criminal_id']}")
            lines.append(f"  Name:     {c['full_name']}")
            lines.append(f"  Alias:    {c.get('alias') or '—'}")
            lines.append(f"  Gender:   {c.get('gender') or '—'}")
            lines.append(f"  Arrests:  {c['arrest_count']}")
            lines.append(f"  Address:  {c.get('address') or '—'}")
            lines.append("  " + "─" * 40)

        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wanted_{ts}.txt"
        path     = export_to_txt(filename, "\n".join(lines))
        audit_log(current_session.user_id, "EXPORT_WANTED_TXT")
        print_success(f"Exported {len(data)} wanted criminals to: {path}")
        press_enter()

    # ── Audit log viewer ──────────────────────────────────────────
    @staticmethod
    def view_audit_logs() -> None:
        if not current_session.require_admin():
            print_error("Admin access required.")
            press_enter()
            return
        clear_screen()
        print_section_header("AUDIT LOGS  (last 50)")
        data = execute_query(
            """SELECT l.log_id, u.username, l.action, l.table_name,
                      l.record_id, l.logged_at
               FROM audit_logs l LEFT JOIN users u ON l.user_id = u.user_id
               ORDER BY l.logged_at DESC LIMIT 50""",
            fetch=True
        )
        display_audit_log_table(data or [])
        press_enter()

    # ── Menu ──────────────────────────────────────────────────────
    @staticmethod
    def menu() -> None:
        while True:
            clear_screen()
            print_menu("REPORTS & ANALYTICS", [
                ("1", "Total FIRs Report"),
                ("2", "Active Cases Report"),
                ("3", "Most Wanted Criminals"),
                ("4", "Officer Performance"),
                ("5", "Monthly Crime Statistics"),
                ("6", "Export FIRs to CSV"),
                ("7", "Export Most Wanted to TXT"),
                ("8", "View Audit Logs  (Admin)"),
                ("0", "Back"),
            ])
            choice = input("  Select option: ").strip()
            if   choice == "1": ReportController.report_total_firs()
            elif choice == "2": ReportController.report_active_cases()
            elif choice == "3": ReportController.report_most_wanted()
            elif choice == "4": ReportController.report_officer_performance()
            elif choice == "5": ReportController.report_monthly_stats()
            elif choice == "6": ReportController.export_firs_csv()
            elif choice == "7": ReportController.export_wanted_txt()
            elif choice == "8": ReportController.view_audit_logs()
            elif choice == "0": break
            else: print_error("Invalid option.")
