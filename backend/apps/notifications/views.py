from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """Les 30 dernières notifications de l'utilisateur connecté + nombre de non lues."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user)
        return Response(
            {
                "unread_count": qs.filter(is_read=False).count(),
                "results": NotificationSerializer(qs[:30], many=True).data,
            }
        )


class MarkReadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        updated = Notification.objects.filter(user=request.user, pk=pk).update(is_read=True)
        if not updated:
            return Response({"detail": "Notification introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
