import csv
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.db.models.functions import ExtractMonth
from accounts.permissions import admin_required, is_admin
from records.models import ActivityLog, FIR, Criminal, Officer, Case

@login_required
def report_home(request):
    year_text = request.GET.get("year", str(date.today().year))
    year = int(year_text) if year_text.isdigit() and 2000 <= int(year_text) <= 2100 else date.today().year
    cases = Case.objects.all()
    if not is_admin(request.user):
        officer = getattr(request.user, "officer_profile", None)
        cases = cases.filter(assigned_to=officer) if officer else cases.none()
    monthly = {row["month"]: row["total"] for row in
               FIR.objects.filter(incident_date__year=year).annotate(month=ExtractMonth("incident_date")).values("month").annotate(total=Count("pk"))}
    officer_stats = Officer.objects.annotate(
        fir_total=Count("firs", distinct=True),
        case_total=Count("cases", distinct=True),
        closed_total=Count("cases", filter=Q(cases__status=Case.Status.CLOSED), distinct=True),
    ).order_by("-case_total", "full_name")
    return render(request, "reports/home.html", {
        "fir_total": FIR.objects.count(), "criminal_total": Criminal.objects.count(),
        "officer_total": Officer.objects.count(), "case_total": cases.count(),
        "open_cases": cases.exclude(status=Case.Status.CLOSED).count(),
        "wanted_people": Criminal.objects.filter(is_wanted=True).order_by("full_name")[:8],
        "repeat_people": Criminal.objects.filter(arrest_count__gte=2).order_by("-arrest_count", "full_name")[:8],
        "officer_stats": officer_stats, "year": year,
        "monthly": [{"month": n, "label": date(year, n, 1).strftime("%b"), "total": monthly.get(n, 0)} for n in range(1, 13)],
    })

def _csv_response(filename, header):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    return response, writer

@login_required
def fir_csv(request):
    response, writer = _csv_response("crime-track-x-firs.csv",
        ["FIR number", "Complainant", "Incident date", "Offense", "Status", "Officer"])
    qs = FIR.objects.select_related("complainant", "officer").order_by("fir_number")
    year = request.GET.get("year", "")
    if year.isdigit() and 2000 <= int(year) <= 2100: qs = qs.filter(incident_date__year=int(year))
    start_date, end_date = parse_date(request.GET.get("from", "")), parse_date(request.GET.get("to", ""))
    if start_date: qs = qs.filter(incident_date__gte=start_date)
    if end_date: qs = qs.filter(incident_date__lte=end_date)
    for fir in qs:
        writer.writerow([fir.fir_number, fir.complainant.full_name, fir.incident_date,
                         fir.offense_type, fir.status, fir.officer.full_name if fir.officer else ""])
    return response

@login_required
@admin_required
def criminal_csv(request):
    response, writer = _csv_response("crime-track-x-person-records.csv",
        ["Profile ID", "Name", "Alias", "Date of birth", "Wanted flag", "Recorded arrest count"])
    for person in Criminal.objects.order_by("full_name"):
        writer.writerow([person.pk, person.full_name, person.alias, person.date_of_birth,
                         "Yes" if person.is_wanted else "No", person.arrest_count])
    return response

@login_required
def case_csv(request):
    response, writer = _csv_response("crime-track-x-investigations.csv",
        ["Case number", "FIR number", "Title", "Status", "Priority", "Assigned officer", "Opened"])
    qs = Case.objects.select_related("fir", "assigned_to").order_by("case_number")
    if not is_admin(request.user):
        officer = getattr(request.user, "officer_profile", None)
        qs = qs.filter(assigned_to=officer) if officer else qs.none()
    for case in qs:
        writer.writerow([case.case_number, case.fir.fir_number, case.title, case.status,
                         case.priority, case.assigned_to.full_name if case.assigned_to else "", case.opened_at])
    return response

@login_required
@admin_required
def officer_csv(request):
    response, writer = _csv_response("crime-track-x-officer-summary.csv",
        ["Officer", "Badge", "Rank", "Station", "FIR count", "Case count", "Closed cases"])
    qs = Officer.objects.select_related("station").annotate(
        fir_total=Count("firs", distinct=True),
        case_total=Count("cases", distinct=True),
        closed_total=Count("cases", filter=Q(cases__status=Case.Status.CLOSED), distinct=True),
    ).order_by("full_name")
    for officer in qs:
        writer.writerow([officer.full_name, officer.badge_number, officer.rank,
                         officer.station.name if officer.station else officer.legacy_station,
                         officer.fir_total, officer.case_total, officer.closed_total])
    return response

@login_required
@admin_required
def audit_list(request):
    logs = ActivityLog.objects.select_related("user").all()[:250]
    return render(request, "reports/audit.html", {"logs": logs})
