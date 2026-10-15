from django.urls import path

from .views import ClientReservationCancelView, ClientReservationDetailView, ClientReservationListCreateView

urlpatterns = [
    path("", ClientReservationListCreateView.as_view()),
    path("<int:pk>/", ClientReservationDetailView.as_view()),
    path("<int:pk>/cancel/", ClientReservationCancelView.as_view()),
]
