from django.contrib import admin

from .models import HotelService


@admin.register(HotelService)
class HotelServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("name",)
