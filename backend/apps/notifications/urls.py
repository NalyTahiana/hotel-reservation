from django.urls import path

from .views import MarkAllReadView, MarkReadView, NotificationListView

urlpatterns = [
    path("", NotificationListView.as_view()),
    path("read-all/", MarkAllReadView.as_view()),
    path("<int:pk>/read/", MarkReadView.as_view()),
]
