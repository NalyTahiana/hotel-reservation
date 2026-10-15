from rest_framework.routers import SimpleRouter

from .views import AdminReservationViewSet

router = SimpleRouter()
router.register("reservations", AdminReservationViewSet, basename="admin-reservations")
urlpatterns = router.urls
