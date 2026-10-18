from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from hotel.models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	ordering        = ("-date_joined",)
	list_display    = ("email", "last_name", "first_name", "phone", "is_staff", "is_active")
	search_fields   = ("email", "last_name", "first_name", "phone")
	fieldsets       = (
		(None, {"fields": ("email", "password")}),
		("Identité", {"fields": ("last_name", "first_name", "phone")}),
		("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
		("Dates", {"fields": ("last_login", "date_joined")}),
	)
	add_fieldsets   = (
		(None, {"classes": ("wide",), "fields": ("email", "last_name", "first_name", "phone", "password1", "password2")}),
	)


class RoomImageInline(admin.TabularInline):
	model = RoomImage
	extra = 0


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
	list_display  = ("number", "name", "room_type", "capacity", "price_per_night", "is_active")
	list_filter   = ("room_type", "is_active")
	search_fields = ("number", "name")
	inlines       = [RoomImageInline]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
	list_display    = ("reference", "customer", "room", "check_in", "check_out", "total_amount", "status")
	list_filter     = ("status",)
	search_fields   = ("reference", "customer__email", "customer__last_name", "customer__first_name")
	readonly_fields = ("reference", "created_at", "updated_at")


@admin.register(HotelService)
class HotelServiceAdmin(admin.ModelAdmin):
	list_display  = ("name", "kind", "is_active")
	list_filter   = ("kind", "is_active")
	search_fields = ("name",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ("user", "title", "is_read", "created_at")
	list_filter  = ("kind", "is_read")
