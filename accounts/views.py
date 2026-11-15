from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.views import PasswordChangeView
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from accounts.models import UserProfile
from accounts.permissions import admin_required
from records.services import log_activity

class CrimeTrackPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = "/accounts/password/done/"
    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request.user, "PASSWORD_CHANGED", details="Account password changed", request=self.request)
        messages.success(self.request, "Password changed successfully.")
        return response

@login_required
def password_change(request):
    return CrimeTrackPasswordChangeView.as_view()(request)

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        user = authenticate(request, username=username, password=request.POST.get("password", ""))
        if user is not None and user.is_active:
            login(request, user)
            log_activity(user, "LOGIN", details="Successful sign in", request=request)
            next_url = request.GET.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect("dashboard")
        messages.error(request, "The username or password was not accepted.")
    return render(request, "login.html")

@login_required
@require_POST
def logout_view(request):
    log_activity(request.user, "LOGOUT", details="Signed out", request=request)
    logout(request)
    return redirect("login")

@login_required
@admin_required
def user_list(request):
    return render(request, "accounts/user_list.html", {"users": User.objects.select_related("profile").order_by("username")})

@login_required
@admin_required
def user_create(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", UserProfile.Role.OFFICER)
        if not username or role not in UserProfile.Role.values:
            messages.error(request, "Enter a username and choose a valid role.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username already exists.")
        else:
            candidate = User(username=username)
            try:
                validate_password(password, candidate)
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                user = User.objects.create_user(username=username, password=password)
                UserProfile.objects.create(user=user, role=role)
                log_activity(request.user, "USER_CREATED", "auth_user", user.pk, username, request)
                messages.success(request, "User account created.")
                return redirect("user_list")
    return render(request, "accounts/user_form.html")

@login_required
@admin_required
@require_POST
def user_toggle(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.pk == request.user.pk:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        log_activity(request.user, "USER_STATUS_CHANGED", "auth_user", user.pk, f"active={user.is_active}", request)
        messages.success(request, "Account status updated.")
    return redirect("user_list")

@login_required
@admin_required
def user_update(request, user_id):
    account = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(
        user=account,
        defaults={"role": UserProfile.Role.ADMIN if account.is_superuser else UserProfile.Role.OFFICER},
    )
    if request.method == "POST":
        role = request.POST.get("role", "")
        if role not in UserProfile.Role.values:
            messages.error(request, "Choose a valid account role.")
        elif account.pk == request.user.pk and role != UserProfile.Role.ADMIN:
            messages.error(request, "Keep your own account as an administrator to avoid locking yourself out.")
        else:
            profile.role = role
            profile.save(update_fields=["role"])
            log_activity(request.user, "USER_ROLE_CHANGED", "auth_user", account.pk, role, request)
            messages.success(request, "Account role updated.")
            return redirect("user_list")
    return render(request, "accounts/user_edit.html", {"account": account, "profile": profile})

@login_required
@admin_required
def user_password_reset(request, user_id):
    account = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        password = request.POST.get("password", "")
        try:
            validate_password(password, account)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            account.set_password(password)
            account.save(update_fields=["password"])
            log_activity(request.user, "USER_PASSWORD_RESET", "auth_user", account.pk, account.username, request)
            messages.success(request, "Password set. Activate this account from the user list when appropriate.")
            return redirect("user_list")
    return render(request, "accounts/user_password.html", {"account": account})
