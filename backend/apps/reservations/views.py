from django.db import transaction
from django.db.models import Q
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Reservation
from apps.accounts.models import User

from .serializers import (
    AdminReservationCreateSerializer,
    PaymentSerializer,
    ReservationCreateSerializer,
    ReservationSerializer,
)
from .services import apply_action, complete_past_reservations, create_reservation, set_amount_paid


def _base_queryset():
    return Reservation.objects.select_related("room", "customer")


class ClientReservationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return ReservationCreateSerializer if self.request.method == "POST" else ReservationSerializer

    def get_queryset(self):
        complete_past_reservations()
        qs = _base_queryset().filter(customer=self.request.user)
        st = self.request.query_params.get("status")
        return qs.filter(status=st) if st else qs

    def create(self, request, *args, **kwargs):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        reservation = create_reservation(
            customer=request.user, room_id=d["room"], check_in=d["check_in"], check_out=d["check_out"],
            guests=d["guests"], comment=d.get("comment", ""),
        )
        reservation = _base_queryset().get(pk=reservation.pk)
        return Response(ReservationSerializer(reservation, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ClientReservationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservationSerializer

    def get_queryset(self):
        complete_past_reservations()
        return _base_queryset().filter(customer=self.request.user)


class ClientReservationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        own = generics.get_object_or_404(Reservation.objects.filter(customer=request.user), pk=pk)
        apply_action(reservation_id=own.pk, action="cancel", actor=request.user)
        reservation = _base_queryset().get(pk=pk)
        return Response(ReservationSerializer(reservation, context={"request": request}).data)


class AdminReservationViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = ReservationSerializer

    def get_serializer_class(self):
        return AdminReservationCreateSerializer if self.action == "create" else ReservationSerializer

    def create(self, request, *args, **kwargs):
        """Réservation pour un client présent à l'hôtel : pas d'e-mail ni de mot de passe."""
        serializer = AdminReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        with transaction.atomic():
            # Réutilise le client déjà enregistré (même nom, prénom et téléphone) pour garder son historique.
            customer = User.objects.filter(
                is_staff=False, phone=d["phone"], last_name__iexact=d["last_name"], first_name__iexact=d["first_name"]
            ).first() or User.objects.create_walkin_customer(
                last_name=d["last_name"], first_name=d["first_name"], phone=d["phone"]
            )
            reservation = create_reservation(
                customer=customer, room_id=d["room"], check_in=d["check_in"], check_out=d["check_out"],
                guests=d["guests"], comment=d.get("comment", ""), by_admin=True, amount_paid=d["amount_paid"],
            )
        reservation = _base_queryset().get(pk=reservation.pk)
        return Response(ReservationSerializer(reservation, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def payment(self, request, pk=None):
        obj = self.get_object()
        s = PaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        set_amount_paid(reservation_id=obj.pk, amount_paid=s.validated_data["amount_paid"])
        reservation = _base_queryset().get(pk=obj.pk)
        return Response(ReservationSerializer(reservation, context={"request": request}).data)

    def get_queryset(self):
        complete_past_reservations()
        p = self.request.query_params
        qs = _base_queryset()
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        for token in p.get("q", "").split():
            qs = qs.filter(
                Q(reference__icontains=token) | Q(customer__first_name__icontains=token)
                | Q(customer__last_name__icontains=token) | Q(customer__email__icontains=token)
            )
        if p.get("date_from"):
            qs = qs.filter(check_out__gte=p["date_from"])
        if p.get("date_to"):
            qs = qs.filter(check_in__lte=p["date_to"])
        return qs

    def _act(self, request, pk, name):
        obj = self.get_object()
        apply_action(reservation_id=obj.pk, action=name, actor=request.user)
        reservation = _base_queryset().get(pk=obj.pk)
        return Response(ReservationSerializer(reservation, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return self._act(request, pk, "accept")

    @action(detail=True, methods=["post"])
    def refuse(self, request, pk=None):
        return self._act(request, pk, "refuse")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._act(request, pk, "cancel")
