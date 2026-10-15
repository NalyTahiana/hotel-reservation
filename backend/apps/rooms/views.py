from django.db.models import ProtectedError, Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from config.pagination import SixPerPage

from apps.reservations.services import filter_available_rooms, is_room_available

from .models import Room, RoomImage
from .serializers import AvailabilityQuerySerializer, RoomSerializer


class PublicRoomListView(generics.ListAPIView):
    """Chambres actives. Avec des dates, seules les chambres libres sont renvoyées."""

    permission_classes = [AllowAny]
    serializer_class = RoomSerializer
    pagination_class = SixPerPage

    def get_queryset(self):
        params = AvailabilityQuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data
        qs = Room.objects.filter(is_active=True).prefetch_related("images")
        room_type = self.request.query_params.get("room_type")
        if room_type:
            qs = qs.filter(room_type=room_type)
        if data.get("guests"):
            qs = qs.filter(capacity__gte=data["guests"])
        if data.get("check_in"):
            qs = filter_available_rooms(qs, data["check_in"], data["check_out"])
        return qs


class PublicRoomDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RoomSerializer
    queryset = Room.objects.filter(is_active=True).prefetch_related("images")

    def retrieve(self, request, *args, **kwargs):
        room = self.get_object()
        data = self.get_serializer(room).data
        params = AvailabilityQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        dates = params.validated_data
        if dates.get("check_in"):
            data["available"] = is_room_available(room.pk, dates["check_in"], dates["check_out"])
        else:
            data["available"] = None  # dates non précisées
        return Response(data)


class AdminRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = RoomSerializer
    pagination_class = SixPerPage
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Room.objects.prefetch_related("images").order_by("number")
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(number__icontains=q))
        room_type = self.request.query_params.get("room_type")
        if room_type:
            qs = qs.filter(room_type=room_type)
        active = self.request.query_params.get("is_active")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        return qs

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()
        try:
            room.delete()
        except ProtectedError:
            return Response(
                {"detail": "Cette chambre a un historique de réservations et ne peut pas être supprimée. Désactivez-la à la place."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="images")
    def add_images(self, request, pk=None):
        room = self.get_object()
        files = request.FILES.getlist("images")
        if not files:
            return Response({"detail": "Aucune image envoyée."}, status=status.HTTP_400_BAD_REQUEST)
        for f in files:
            RoomImage.objects.create(room=room, image=f)
        room = Room.objects.prefetch_related("images").get(pk=room.pk)
        return Response(self.get_serializer(room).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"images/(?P<image_id>[0-9]+)")
    def delete_image(self, request, pk=None, image_id=None):
        room = self.get_object()
        deleted, _ = RoomImage.objects.filter(room=room, pk=image_id).delete()
        if not deleted:
            return Response({"detail": "Image introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
