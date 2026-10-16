"""Règles métier des réservations (disponibilité, création, changements de statut).

Statuts bloquants : « En attente » et « Acceptée ». Refusée, annulée et terminée libèrent la période.
Transitions autorisées :
    En attente -> Acceptée | Refusée | Annulée
    Acceptée   -> Annulée | Terminée (automatique après la date de départ)
    Refusée, Annulée, Terminée : états finaux.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.notifications import services as notify
from apps.rooms.models import Room

from .models import Reservation

S = Reservation.Status
BLOCKING_STATUSES = [S.PENDING, S.ACCEPTED]
ALLOWED_TRANSITIONS = {
    S.PENDING: {S.ACCEPTED, S.REFUSED, S.CANCELLED},
    S.ACCEPTED: {S.CANCELLED, S.COMPLETED},
    S.REFUSED: set(),
    S.CANCELLED: set(),
    S.COMPLETED: set(),
}
ACTION_TARGETS = {"accept": S.ACCEPTED, "refuse": S.REFUSED, "cancel": S.CANCELLED}


class RoomUnavailable(APIException):
    status_code = 409
    default_code = "room_unavailable"
    default_detail = "Cette chambre n'est pas disponible pour les dates choisies. Choisissez d'autres dates ou une autre chambre."


class InvalidTransition(APIException):
    status_code = 409
    default_code = "invalid_transition"
    default_detail = "Ce changement de statut n'est pas autorisé."


def overlapping(room_id, check_in, check_out, exclude_id=None):
    """Réservations bloquantes qui chevauchent [check_in, check_out[ :
    arrivée demandée < départ existant ET départ demandé > arrivée existante."""
    qs = Reservation.objects.filter(
        room_id=room_id, status__in=BLOCKING_STATUSES, check_in__lt=check_out, check_out__gt=check_in
    )
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    return qs


def is_room_available(room_id, check_in, check_out, exclude_id=None):
    return not overlapping(room_id, check_in, check_out, exclude_id).exists()


def filter_available_rooms(queryset, check_in, check_out):
    busy = Reservation.objects.filter(
        status__in=BLOCKING_STATUSES, check_in__lt=check_out, check_out__gt=check_in
    ).values("room_id")
    return queryset.exclude(pk__in=busy)


def complete_past_reservations():
    """Passe en « Terminée » les réservations acceptées dont le départ est atteint."""
    today = timezone.localdate()
    return Reservation.objects.filter(status=S.ACCEPTED, check_out__lte=today).update(status=S.COMPLETED)


@transaction.atomic
def create_reservation(*, customer, room_id, check_in, check_out, guests, comment="", by_admin=False, amount_paid=0):
    """Crée une réservation. Demande client : « En attente » ; saisie par l'administrateur
    (client présent à l'hôtel) : directement « Acceptée », sans notification."""
    # Le verrou sur la ligne de la chambre sérialise les demandes concurrentes pour cette chambre :
    # la vérification de chevauchement qui suit voit donc toutes les demandes déjà validées.
    try:
        room = Room.objects.select_for_update().get(pk=room_id)
    except Room.DoesNotExist:
        raise ValidationError({"room": "Cette chambre n'existe pas."})
    if not room.is_active:
        raise ValidationError({"room": "Cette chambre n'est pas disponible à la réservation."})
    today = timezone.localdate()
    if check_in < today:
        raise ValidationError({"check_in": "La date d'arrivée ne peut pas être dans le passé."})
    if check_out <= check_in:
        raise ValidationError({"check_out": "La date de départ doit être postérieure à la date d'arrivée."})
    if guests > room.capacity:
        raise ValidationError({"guests": f"Cette chambre accueille au maximum {room.capacity} personne(s)."})
    if not is_room_available(room.pk, check_in, check_out):
        raise RoomUnavailable()
    nights = (check_out - check_in).days
    total = nights * room.price_per_night
    if amount_paid > total:
        raise ValidationError({"amount_paid": f"Le montant payé ne peut pas dépasser le total ({total} Ar)."})
    reservation = Reservation.objects.create(
        customer=customer, room=room, check_in=check_in, check_out=check_out, guests=guests,
        price_per_night=room.price_per_night, nights=nights, total_amount=total, amount_paid=amount_paid,
        status=S.ACCEPTED if by_admin else S.PENDING, comment=comment or "",
    )
    if not by_admin:
        notify.new_reservation(reservation)
    return reservation


@transaction.atomic
def create_reservation_for_room_type(*, customer, room_type, check_in, check_out, guests=1, comment="", by_admin=True):
    """Réserve la première chambre active libre du type demandé sur [check_in, check_out[."""
    rooms = filter_available_rooms(Room.objects.filter(is_active=True, room_type=room_type), check_in, check_out)
    for room in rooms.order_by("number"):
        try:
            return create_reservation(
                customer=customer, room_id=room.pk, check_in=check_in, check_out=check_out,
                guests=min(guests, room.capacity), comment=comment, by_admin=by_admin,
            )
        except RoomUnavailable:
            continue  # prise entre-temps par une autre demande : essaie la suivante
    raise RoomUnavailable("Aucune chambre de ce type n'est disponible sur ces dates. Choisissez un autre type ou d'autres dates.")


@transaction.atomic
def set_amount_paid(*, reservation_id, amount_paid):
    """Enregistre le montant total déjà payé (jamais supérieur au total de la réservation)."""
    try:
        reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
    except Reservation.DoesNotExist:
        raise NotFound("Réservation introuvable.")
    if reservation.status in (S.REFUSED, S.CANCELLED):
        raise InvalidTransition("Aucun paiement ne peut être enregistré sur une réservation refusée ou annulée.")
    if amount_paid > reservation.total_amount:
        raise ValidationError({"amount_paid": f"Le montant payé ne peut pas dépasser le total ({reservation.total_amount} Ar)."})
    reservation.amount_paid = amount_paid
    reservation.save(update_fields=["amount_paid", "updated_at"])
    return reservation


def allowed_actions(reservation, user):
    """Actions (accept, refuse, cancel) permises à cet utilisateur sur cette réservation."""
    today = timezone.localdate()
    if reservation.status == S.PENDING:
        return ["accept", "refuse", "cancel"] if user.is_staff else ["cancel"]
    if reservation.status == S.ACCEPTED:
        if user.is_staff:
            return ["cancel"]
        return ["cancel"] if reservation.check_in > today else []
    return []


@transaction.atomic
def apply_action(*, reservation_id, action, actor):
    target = ACTION_TARGETS.get(action)
    if target is None:
        raise ValidationError({"detail": "Action inconnue."})
    # Verrouille d'abord la réservation, puis la chambre (même ordre partout).
    try:
        reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
    except Reservation.DoesNotExist:
        raise NotFound("Réservation introuvable.")
    Room.objects.select_for_update().get(pk=reservation.room_id)
    if action not in allowed_actions(reservation, actor) or target not in ALLOWED_TRANSITIONS[reservation.status]:
        raise InvalidTransition(f"Impossible de passer une réservation « {reservation.get_status_display()} » à l'action « {action} ».")
    if target == S.ACCEPTED:
        today = timezone.localdate()
        if reservation.check_in < today:
            raise InvalidTransition("La date d'arrivée est dépassée : cette demande ne peut plus être acceptée.")
        if not is_room_available(reservation.room_id, reservation.check_in, reservation.check_out, exclude_id=reservation.pk):
            raise RoomUnavailable("Une autre réservation occupe déjà cette chambre sur cette période : acceptation impossible.")
    reservation.status = target
    reservation.save(update_fields=["status", "updated_at"])
    if actor.is_staff:
        notify.status_changed_by_admin(reservation, target)
    else:
        notify.cancelled_by_client(reservation)
    return reservation
