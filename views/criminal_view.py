# views/criminal_view.py
# ─────────────────────────────────────────────
#  CrimeTrack-X  |  Criminal View
#  All display logic specific to criminal records
# ─────────────────────────────────────────────

from tabulate import tabulate
from colorama import Fore, Back, Style
from views.menu_view import (
    print_section_header, print_table, print_divider, Colors
)


def display_criminal_list(criminals: list) -> None:
    """Render a styled criminal roster with WANTED highlighting."""
    if not criminals:
        print(Colors.warning("  No criminal records found.\n"))
        return

    rows = []
    for c in criminals:
        wanted_tag = (
            f"{Fore.RED}{Style.BRIGHT} ★WANTED{Style.RESET_ALL}"
            if c.get("is_wanted") else ""
        )
        rows.append([
            c["criminal_id"],
            f"{c['full_name']}{wanted_tag}",
            c.get("alias") or "—",
            c.get("gender") or "—",
            str(c.get("dob") or "—"),
            c.get("nationality") or "—",
            c.get("arrest_count", 0),
        ])
    print(f"\n{Fore.CYAN}")
    print(tabulate(
        rows,
        headers=["ID", "Full Name", "Alias", "Gender", "DOB", "Nationality", "Arrests"],
        tablefmt="rounded_outline"
    ))
    print(Style.RESET_ALL)


def display_criminal_profile(criminal: dict) -> None:
    """
    Full criminal profile card — personal details + physical description.
    """
    print_section_header(f"CRIMINAL PROFILE — {criminal['full_name']}", width=60)

    wanted = criminal.get("is_wanted", 0)
    if wanted:
        print(f"  {Back.RED}{Fore.WHITE}{Style.BRIGHT}"
              f"  ★  THIS INDIVIDUAL IS ON THE WANTED LIST  ★  "
              f"{Style.RESET_ALL}\n")

    personal = [
        ("Criminal ID",   criminal["criminal_id"]),
        ("Full Name",     criminal["full_name"]),
        ("Alias",         criminal.get("alias") or "—"),
        ("Gender",        criminal.get("gender") or "—"),
        ("Date of Birth", str(criminal.get("dob") or "—")),
        ("Nationality",   criminal.get("nationality") or "—"),
        ("Blood Group",   criminal.get("blood_group") or "—"),
        ("Phone",         criminal.get("phone") or "—"),
        ("ID Proof",
         f"{criminal.get('id_proof_type') or ''} "
         f"{criminal.get('id_proof_no') or ''}".strip() or "—"),
        ("Address",       criminal.get("address") or "—"),
        ("Physical Desc", criminal.get("physical_desc") or "—"),
        ("Arrest Count",  criminal.get("arrest_count", 0)),
    ]
    for label, value in personal:
        color = Fore.RED if label == "Arrest Count" and int(criminal.get("arrest_count", 0)) >= 3 \
                else Fore.CYAN
        print(f"  {color}{label:<18}{Style.RESET_ALL}: {value}")
    print()


def display_fir_history(fir_history: list, criminal_name: str) -> None:
    """Show all FIRs linked to a specific criminal."""
    print(f"\n  {Colors.header(f'── FIR History for {criminal_name} ──────────────')}")
    if not fir_history:
        print(Colors.warning("  No FIR history found.\n"))
        return
    print_table(
        fir_history,
        ["fir_number", "offense_type", "incident_date", "status", "officer_name"],
        ["FIR No.", "Offense", "Date", "Status", "Officer"]
    )


def display_wanted_banner(criminals: list) -> None:
    """Bold formatted WANTED list for reporting."""
    print(f"\n  {Fore.RED}{Style.BRIGHT}{'═' * 60}")
    print(f"  {'★  MOST WANTED LIST  ★':^58}")
    print(f"  {'═' * 60}{Style.RESET_ALL}\n")

    for idx, c in enumerate(criminals, 1):
        print(f"  {Fore.YELLOW}{Style.BRIGHT}#{idx:02d}{Style.RESET_ALL}  "
              f"{Fore.WHITE}{Style.BRIGHT}{c['full_name']}{Style.RESET_ALL}"
              f"  {Fore.RED}(Alias: {c.get('alias') or 'None'}){Style.RESET_ALL}"
              f"  Arrests: {Fore.RED}{c.get('arrest_count', 0)}{Style.RESET_ALL}")
    print()
