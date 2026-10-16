import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q


def generate_reference():
    return "RSV-" + uuid.uuid4().hex[:8].upper()


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        ACCEPTED = "accepted", "Acceptée"
        REFUSED = "refused", "Refusée"
        CANCELLED = "cancelled", "Annulée"
        COMPLETED = "completed", "Terminée"

    reference = models.CharField("référence", max_length=20, unique=True, default=generate_reference, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservations")
    room = models.ForeignKey("rooms.Room", on_delete=models.PROTECT, related_name="reservations")
    check_in = models.DateField("date d'arrivée")
    check_out = models.DateField("date de départ")
    guests = models.PositiveSmallIntegerField("nombre de personnes")
    # Copie du tarif au moment de la réservation : l'historique ne change pas si le prix de la chambre change.
    price_per_night = models.PositiveIntegerField("prix par nuit (Ar)")
    nights = models.PositiveSmallIntegerField("nombre de nuits")
    total_amount = models.PositiveBigIntegerField("montant total (Ar)")
    # Montant déjà encaissé (réservation prise à la réception, ou acompte). Reste à payer = total - payé.
    amount_paid = models.PositiveBigIntegerField("montant payé (Ar)", default=0)
    status = models.CharField("statut", max_length=12, choices=Status.choices, default=Status.PENDING)
    comment = models.TextField("commentaire", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["room", "status", "check_in", "check_out"], name="resa_room_period_idx"),
            models.Index(fields=["status", "created_at"], name="resa_status_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=Q(check_out__gt=F("check_in")), name="resa_checkout_after_checkin"),
            models.CheckConstraint(check=Q(amount_paid__lte=F("total_amount")), name="resa_paid_lte_total"),
        ]

    @property
    def balance_due(self):
        return max(self.total_amount - self.amount_paid, 0)

    def __str__(self):
        return f"{self.reference} ({self.get_status_display()})"
