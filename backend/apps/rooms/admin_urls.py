from rest_framework.routers import SimpleRouter

from .views import AdminRoomViewSet

router = SimpleRouter()
router.register("rooms", AdminRoomViewSet, basename="admin-rooms")
urlpatterns = router.urls
