from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.reservations.models import Reservation
from apps.reservations.services import complete_past_reservations
from apps.rooms.models import Room

S = Reservation.Status
MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def _last_months(today, n=6):
    y, m = today.year, today.month
    out = []
    for _ in range(n):
        out.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


class DashboardStatsView(APIView):
    """Indicateurs calculés depuis la base.

    Règle du chiffre d'affaires : somme des montants des réservations « Terminées » (séjour réellement effectué).
    Une réservation acceptée devient « Terminée » automatiquement après sa date de départ.
    Les graphiques regroupent les réservations par mois d'arrivée.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        complete_past_reservations()
        today = timezone.localdate()
        by_status = dict(Reservation.objects.values_list("status").annotate(n=Count("id")))
        occupied_ids = set(
            Reservation.objects.filter(status=S.ACCEPTED, check_in__lte=today, check_out__gt=today).values_list("room_id", flat=True)
        )
        active_rooms = Room.objects.filter(is_active=True)
        occupied = active_rooms.filter(pk__in=occupied_ids).count()
        months = _last_months(today)
        first = today.replace(year=months[0][0], month=months[0][1], day=1)
        monthly = {}
        rows = (
            Reservation.objects.filter(check_in__gte=first)
            .annotate(month=TruncMonth("check_in"))
            .values("month", "status")
            .annotate(n=Count("id"), total=Sum("total_amount"))
        )
        for r in rows:
            key = (r["month"].year, r["month"].month)
            bucket = monthly.setdefault(key, {"count": 0, "revenue": 0})
            if r["status"] in (S.PENDING, S.ACCEPTED, S.COMPLETED):
                bucket["count"] += r["n"]
            if r["status"] == S.COMPLETED:
                bucket["revenue"] += r["total"] or 0
        return Response(
            {
                "total_rooms": Room.objects.count(),
                "active_rooms": active_rooms.count(),
                "occupied_rooms": occupied,
                "available_rooms": active_rooms.count() - occupied,
                "customers": User.objects.filter(is_staff=False).count(),
                "pending": by_status.get(S.PENDING, 0),
                "accepted": by_status.get(S.ACCEPTED, 0),
                "refused": by_status.get(S.REFUSED, 0),
                "cancelled": by_status.get(S.CANCELLED, 0),
                "completed": by_status.get(S.COMPLETED, 0),
                "revenue": Reservation.objects.filter(status=S.COMPLETED).aggregate(t=Sum("total_amount"))["t"] or 0,
                "monthly": [
                    {"label": f"{MONTHS_FR[m - 1]} {y}", **monthly.get((y, m), {"count": 0, "revenue": 0})} for y, m in months
                ],
            }
        )
