from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "room", "check_in", "check_out", "total_amount", "status")
    list_filter = ("status",)
    search_fields = ("reference", "customer__email", "customer__last_name", "customer__first_name")
    readonly_fields = ("reference", "created_at", "updated_at")
