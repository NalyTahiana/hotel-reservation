from rest_framework import generics, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser

from .models import HotelService
from .serializers import HotelServiceSerializer


class PublicServiceListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = HotelServiceSerializer
    pagination_class = None

    def get_queryset(self):
        qs = HotelService.objects.filter(is_active=True)
        kind = self.request.query_params.get("kind")
        return qs.filter(kind=kind) if kind else qs


class AdminServiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = HotelServiceSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = HotelService.objects.all()
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        kind = self.request.query_params.get("kind")
        return qs.filter(kind=kind) if kind else qs
