from django.urls import path

from .views import PublicRoomDetailView, PublicRoomListView

urlpatterns = [
    path("", PublicRoomListView.as_view()),
    path("<int:pk>/", PublicRoomDetailView.as_view()),
]
