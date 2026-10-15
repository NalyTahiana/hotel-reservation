from rest_framework import serializers

from .models import HotelService


class HotelServiceSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = HotelService
        fields = ["id", "kind", "kind_display", "name", "description", "image", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
