from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    """Application role attached to Django's securely hashed user account."""
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        OFFICER = "officer", "Police Officer"
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.OFFICER)
    legacy_user_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
