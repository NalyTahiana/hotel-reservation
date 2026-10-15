from rest_framework.routers import SimpleRouter

from .views import AdminCustomerViewSet

router = SimpleRouter()
router.register("customers", AdminCustomerViewSet, basename="admin-customers")
urlpatterns = router.urls
