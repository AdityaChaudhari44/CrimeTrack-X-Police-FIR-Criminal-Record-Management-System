from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(getattr(user, "profile", None), "role", None) == "admin")

def admin_required(view):
    """Require a signed-in administrator and return 403 for other signed-in users."""
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped
