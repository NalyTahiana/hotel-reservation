from django.core.validators import MinValueValidator
from django.db import models


class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = "simple", "Simple"
        DOUBLE = "double", "Double"
        FAMILY = "familiale", "Familiale"
        SUITE = "suite", "Suite"

    number = models.CharField("numéro", max_length=20, unique=True)
    name = models.CharField("nom", max_length=150)
    room_type = models.CharField("type", max_length=20, choices=RoomType.choices, default=RoomType.DOUBLE)
    short_description = models.CharField("description courte", max_length=255, blank=True)
    description = models.TextField("description complète", blank=True)
    capacity = models.PositiveSmallIntegerField("capacité maximale", validators=[MinValueValidator(1)])
    price_per_night = models.PositiveIntegerField("prix par nuit (Ar)", validators=[MinValueValidator(1)])
    image = models.ImageField("photo principale", upload_to="rooms/", blank=True, null=True)
    amenities = models.TextField("équipements (un par ligne)", blank=True)
    included_services = models.TextField("services inclus (un par ligne)", blank=True)
    is_active = models.BooleanField("active", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.name}"


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="rooms/gallery/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
