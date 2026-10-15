from django.contrib import admin

from .models import Room, RoomImage


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 0


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "room_type", "capacity", "price_per_night", "is_active")
    list_filter = ("room_type", "is_active")
    search_fields = ("number", "name")
    inlines = [RoomImageInline]
