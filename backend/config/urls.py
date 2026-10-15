from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/rooms/", include("apps.rooms.urls")),
    path("api/reservations/", include("apps.reservations.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/catalog/", include("apps.services.urls")),
    path("api/admin/", include("apps.accounts.admin_urls")),
    path("api/admin/", include("apps.rooms.admin_urls")),
    path("api/admin/", include("apps.reservations.admin_urls")),
    path("api/admin/", include("apps.services.admin_urls")),
    path("api/admin/", include("apps.dashboard.urls")),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
