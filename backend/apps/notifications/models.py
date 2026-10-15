from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        NEW_RESERVATION = "new_reservation", "Nouvelle demande"
        ACCEPTED = "accepted", "Réservation acceptée"
        REFUSED = "refused", "Réservation refusée"
        CANCELLED = "cancelled", "Réservation annulée"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    title = models.CharField(max_length=150)
    message = models.TextField()
    reservation = models.ForeignKey("reservations.Reservation", null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "is_read"], name="notif_user_read_idx")]

    def __str__(self):
        return f"{self.user_id} - {self.title}"
