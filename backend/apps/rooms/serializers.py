from rest_framework import serializers

from .models import Room, RoomImage


def _lines(text):
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id", "image"]


class RoomSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    images = RoomImageSerializer(many=True, read_only=True)
    amenities_list = serializers.SerializerMethodField()
    services_list = serializers.SerializerMethodField()
    room_type_display = serializers.CharField(source="get_room_type_display", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "number", "name", "room_type", "room_type_display", "short_description", "description",
            "capacity", "price_per_night", "image", "images", "amenities", "amenities_list",
            "included_services", "services_list", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_amenities_list(self, obj):
        return _lines(obj.amenities)

    def get_services_list(self, obj):
        return _lines(obj.included_services)


class AvailabilityQuerySerializer(serializers.Serializer):
    """Paramètres de recherche de disponibilité (dates et nombre de personnes)."""

    check_in = serializers.DateField(required=False)
    check_out = serializers.DateField(required=False)
    guests = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        check_in, check_out = attrs.get("check_in"), attrs.get("check_out")
        if bool(check_in) != bool(check_out):
            raise serializers.ValidationError("Indiquez la date d'arrivée et la date de départ.")
        if check_in and check_out and check_in >= check_out:
            raise serializers.ValidationError("La date d'arrivée doit être antérieure à la date de départ.")
        return attrs
