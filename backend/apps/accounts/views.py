from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.pagination import SixPerPage

from .models import User
from .serializers import (
    CustomerDetailSerializer,
    CustomerListSerializer,
    CustomerStatusSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    WalkInCustomerSerializer,
)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "Cookie CSRF défini."})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"].strip().lower(),
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Adresse e-mail ou mot de passe incorrect, ou compte désactivé."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


class AdminCustomerViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Liste, création, détail et (dés)activation des comptes clients. Les administrateurs sont exclus."""

    permission_classes = [IsAdminUser]
    pagination_class = SixPerPage
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = User.objects.filter(is_staff=False).annotate(reservations_count=Count("reservations")).order_by("-date_joined")
        q = self.request.query_params.get("q", "").strip()
        for token in q.split():
            qs = qs.filter(
                Q(first_name__icontains=token)
                | Q(last_name__icontains=token)
                | Q(email__icontains=token)
                | Q(phone__icontains=token)
            )
        active = self.request.query_params.get("is_active")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        return qs

    def create(self, request, *args, **kwargs):
        """L'administrateur enregistre un client venu à l'hôtel (e-mail facultatif, pas de mot de passe)."""
        serializer = WalkInCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        user = User.objects.create_walkin_customer(
            last_name=d["last_name"], first_name=d["first_name"], phone=d["phone"], email=d.get("email")
        )
        user.reservations_count = 0
        return Response(CustomerListSerializer(user).data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action == "create":
            return WalkInCustomerSerializer
        if self.action == "retrieve":
            return CustomerDetailSerializer
        if self.action in ("update", "partial_update"):
            return CustomerStatusSerializer
        return CustomerListSerializer
