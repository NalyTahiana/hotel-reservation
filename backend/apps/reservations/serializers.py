from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import phone_validator

from .models import Reservation
from .services import allowed_actions


class ReservationCreateSerializer(serializers.Serializer):
    room = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guests = serializers.IntegerField(min_value=1)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        if attrs["check_in"] < timezone.localdate():
            raise serializers.ValidationError({"check_in": "La date d'arrivée ne peut pas être dans le passé."})
        if attrs["check_in"] >= attrs["check_out"]:
            raise serializers.ValidationError({"check_out": "La date de départ doit être postérieure à la date d'arrivée."})
        return attrs


class AdminReservationCreateSerializer(serializers.Serializer):
    """Réservation saisie par l'administrateur pour un client présent à l'hôtel."""

    last_name = serializers.CharField(max_length=100)
    first_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=10)
    room = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guests = serializers.IntegerField(min_value=1)
    amount_paid = serializers.IntegerField(min_value=0, required=False, default=0)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate_phone(self, value):
        phone_validator(value)
        return value

    def validate(self, attrs):
        if attrs["check_in"] < timezone.localdate():
            raise serializers.ValidationError({"check_in": "La date d'arrivée ne peut pas être dans le passé."})
        if attrs["check_in"] >= attrs["check_out"]:
            raise serializers.ValidationError({"check_out": "La date de départ doit être postérieure à la date d'arrivée."})
        return attrs


class PaymentSerializer(serializers.Serializer):
    amount_paid = serializers.IntegerField(min_value=0)


class ReservationSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    room = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    balance_due = serializers.IntegerField(read_only=True)
    actions = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            "id", "reference", "customer", "room", "check_in", "check_out", "guests", "price_per_night",
            "nights", "total_amount", "amount_paid", "balance_due", "status", "status_display", "comment", "actions", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_customer(self, obj):
        c = obj.customer
        return {"id": c.id, "full_name": c.full_name, "email": c.email or "", "phone": c.phone}

    def get_room(self, obj):
        r = obj.room
        request = self.context.get("request")
        image = None
        if r.image:
            image = request.build_absolute_uri(r.image.url) if request else r.image.url
        return {"id": r.id, "number": r.number, "name": r.name, "room_type": r.room_type, "image": image}

    def get_actions(self, obj):
        request = self.context.get("request")
        return allowed_actions(obj, request.user) if request else []
