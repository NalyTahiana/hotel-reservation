from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import User, phone_validator


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "last_name", "first_name", "phone", "is_staff", "date_joined"]
        read_only_fields = ["id", "email", "is_staff", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["email", "last_name", "first_name", "phone", "password", "password_confirm"]
        extra_kwargs = {"email": {"validators": []}}

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cette adresse e-mail.")
        return value

    def validate_phone(self, value):
        phone_validator(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        candidate = User(email=attrs["email"], last_name=attrs["last_name"], first_name=attrs["first_name"])
        try:
            password_validation.validate_password(attrs["password"], candidate)
        except Exception as exc:  # django ValidationError -> erreurs DRF
            raise serializers.ValidationError({"password": list(getattr(exc, "messages", [str(exc)]))})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class CustomerListSerializer(serializers.ModelSerializer):
    reservations_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "last_name", "first_name", "phone", "is_active", "date_joined", "reservations_count"]


class CustomerDetailSerializer(CustomerListSerializer):
    reservations = serializers.SerializerMethodField()

    class Meta(CustomerListSerializer.Meta):
        fields = CustomerListSerializer.Meta.fields + ["reservations"]

    def get_reservations(self, obj):
        from apps.reservations.serializers import ReservationSerializer

        qs = obj.reservations.select_related("room", "customer").order_by("-created_at")
        return ReservationSerializer(qs, many=True, context=self.context).data


class CustomerStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["is_active"]
