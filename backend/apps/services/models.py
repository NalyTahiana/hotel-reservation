from django.db import models


class HotelService(models.Model):
    """Service (Wi-Fi, piscine...) ou activité proposé aux clients et affiché sur le site public."""

    class Kind(models.TextChoices):
        SERVICE = "service", "Service"
        ACTIVITY = "activity", "Activité"

    kind = models.CharField("catégorie", max_length=10, choices=Kind.choices, default=Kind.SERVICE)
    name = models.CharField("nom", max_length=150)
    description = models.TextField("description", blank=True)
    image = models.ImageField("photo", upload_to="services/", blank=True, null=True)
    is_active = models.BooleanField("actif", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["kind", "name"]

    def __str__(self):
        return self.name
