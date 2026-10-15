"""Création des notifications liées aux réservations (appelé depuis apps.reservations.services)."""
from apps.accounts.models import User

from .models import Notification

K = Notification.Kind


def _ar(n):
    return f"{int(n):,}".replace(",", " ") + " Ar"


def _details(r):
    return (
        f"Chambre n° {r.room.number} ({r.room.name}), du {r.check_in:%d/%m/%Y} au {r.check_out:%d/%m/%Y} "
        f"({r.nights} nuit(s)), {r.guests} personne(s), prix par nuit {_ar(r.price_per_night)}, total {_ar(r.total_amount)}."
    )


def new_reservation(r):
    """Prévient tous les administrateurs actifs d'une nouvelle demande."""
    text = f"{r.customer.full_name} a demandé la réservation {r.reference}. {_details(r)}"
    Notification.objects.bulk_create(
        [
            Notification(user=a, kind=K.NEW_RESERVATION, title="Nouvelle demande de réservation", message=text, reservation=r)
            for a in User.objects.filter(is_staff=True, is_active=True)
        ]
    )


def status_changed_by_admin(r, status):
    """Prévient le client de la décision de l'administrateur."""
    if status == "accepted":
        kind, title = K.ACCEPTED, "Réservation acceptée"
        text = f"L'administrateur a accepté votre demande de réservation {r.reference}. {_details(r)}"
    elif status == "refused":
        kind, title = K.REFUSED, "Réservation refusée"
        text = f"L'administrateur a refusé votre demande de réservation {r.reference}. {_details(r)}"
    else:
        kind, title = K.CANCELLED, "Réservation annulée"
        text = f"L'administrateur a annulé votre réservation {r.reference}. {_details(r)}"
    Notification.objects.create(user=r.customer, kind=kind, title=title, message=text, reservation=r)


def cancelled_by_client(r):
    text = f"{r.customer.full_name} a annulé la réservation {r.reference}. {_details(r)}"
    Notification.objects.bulk_create(
        [
            Notification(user=a, kind=K.CANCELLED, title="Réservation annulée par le client", message=text, reservation=r)
            for a in User.objects.filter(is_staff=True, is_active=True)
        ]
    )
