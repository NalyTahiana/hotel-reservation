from django.urls import path

from .views import PublicServiceListView

urlpatterns = [path("services/", PublicServiceListView.as_view())]
