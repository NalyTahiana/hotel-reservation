from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-date_joined",)
    list_display = ("email", "last_name", "first_name", "phone", "is_staff", "is_active")
    search_fields = ("email", "last_name", "first_name", "phone")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identité", {"fields": ("last_name", "first_name", "phone")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "last_name", "first_name", "phone", "password1", "password2")}),
    )
