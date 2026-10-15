from rest_framework.routers import SimpleRouter

from .views import AdminServiceViewSet

router = SimpleRouter()
router.register("services", AdminServiceViewSet, basename="admin-services")
urlpatterns = router.urls
