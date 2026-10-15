from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.rooms.models import Room

from .models import Reservation

S = Reservation.Status
PWD = "MotDePasse!2026"


def make_user(email, staff=False):
    return User.objects.create_user(email, PWD, last_name="Nom", first_name="Prenom", phone="0341234567", is_staff=staff)


class BaseCase(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.room = Room.objects.create(number="101", name="Chambre 101", room_type="double", capacity=2, price_per_night=100000)
        self.alice, self.bob, self.admin = make_user("alice@x.com"), make_user("bob@x.com"), make_user("admin@x.com", staff=True)

    def client_for(self, user):
        c = APIClient()
        c.force_login(user)
        return c

    def d(self, offset):
        return (self.today + timedelta(days=offset)).isoformat()

    def book(self, user, start, end, guests=2, room=None):
        return self.client_for(user).post(
            "/api/reservations/",
            {"room": (room or self.room).pk, "check_in": self.d(start), "check_out": self.d(end), "guests": guests},
            format="json",
        )


class BookingRulesTests(BaseCase):
    def test_creation_calculates_total_on_server_and_is_pending(self):
        r = self.client_for(self.alice).post(
            "/api/reservations/",
            {"room": self.room.pk, "check_in": self.d(10), "check_out": self.d(13), "guests": 2,
             "total_amount": 1, "status": "accepted", "price_per_night": 1},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.content)
        data = r.json()
        self.assertEqual((data["nights"], data["price_per_night"], data["total_amount"]), (3, 100000, 300000))
        self.assertEqual(data["status"], "pending")

    def test_persistence_in_database(self):
        self.book(self.alice, 10, 12)
        saved = Reservation.objects.get(customer=self.alice)
        self.assertEqual(saved.total_amount, 200000)
        self.assertTrue(saved.reference.startswith("RSV-"))

    def test_invalid_dates_rejected(self):
        self.assertEqual(self.book(self.alice, -2, 3).status_code, 400)   # passé
        self.assertEqual(self.book(self.alice, 5, 5).status_code, 400)    # départ = arrivée
        self.assertEqual(self.book(self.alice, 8, 5).status_code, 400)    # départ avant arrivée

    def test_capacity_exceeded_rejected(self):
        r = self.book(self.alice, 10, 12, guests=3)
        self.assertEqual(r.status_code, 400)
        self.assertIn("guests", r.json())

    def test_inactive_room_rejected(self):
        self.room.is_active = False
        self.room.save()
        self.assertEqual(self.book(self.alice, 10, 12).status_code, 400)

    def test_overlapping_reservation_rejected_even_when_pending(self):
        self.assertEqual(self.book(self.alice, 10, 15).status_code, 201)
        self.assertEqual(self.book(self.bob, 12, 17).status_code, 409)
        self.assertEqual(self.book(self.bob, 8, 11).status_code, 409)
        self.assertEqual(self.book(self.bob, 11, 13).status_code, 409)  # incluse dans la période

    def test_consecutive_reservations_allowed(self):
        self.assertEqual(self.book(self.alice, 10, 15).status_code, 201)
        self.assertEqual(self.book(self.bob, 15, 18).status_code, 201)
        self.assertEqual(self.book(self.bob, 5, 10).status_code, 201)

    def test_dates_released_after_refusal_and_cancellation(self):
        first = self.book(self.alice, 10, 15).json()
        self.client_for(self.admin).post(f"/api/admin/reservations/{first['id']}/refuse/")
        second = self.book(self.bob, 10, 15)
        self.assertEqual(second.status_code, 201)
        r = self.client_for(self.bob).post(f"/api/reservations/{second.json()['id']}/cancel/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.book(self.alice, 11, 14).status_code, 201)

    def test_availability_search_excludes_busy_rooms(self):
        other = Room.objects.create(number="102", name="Chambre 102", capacity=2, price_per_night=90000)
        self.book(self.alice, 10, 15)
        url = f"/api/rooms/?check_in={self.d(12)}&check_out={self.d(14)}&guests=2"
        ids = [x["id"] for x in APIClient().get(url).json()["results"]]
        self.assertEqual(ids, [other.pk])

    def test_accept_rechecks_availability(self):
        pending = self.book(self.alice, 10, 15).json()
        # Simule une réservation concurrente qui a occupé la période entre-temps.
        Reservation.objects.create(
            customer=self.bob, room=self.room, check_in=self.today + timedelta(days=12), check_out=self.today + timedelta(days=16),
            guests=1, price_per_night=100000, nights=4, total_amount=400000, status=S.ACCEPTED,
        )
        r = self.client_for(self.admin).post(f"/api/admin/reservations/{pending['id']}/accept/")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Reservation.objects.get(pk=pending["id"]).status, S.PENDING)

    def test_accept_then_cancel_flow(self):
        res = self.book(self.alice, 10, 12).json()
        ok = self.client_for(self.admin).post(f"/api/admin/reservations/{res['id']}/accept/")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["status"], "accepted")
        again = self.client_for(self.admin).post(f"/api/admin/reservations/{res['id']}/accept/")
        self.assertEqual(again.status_code, 409)  # transition interdite
        self.assertEqual(self.client_for(self.alice).post(f"/api/reservations/{res['id']}/cancel/").status_code, 200)

    def test_price_snapshot_is_kept_when_room_price_changes(self):
        res = self.book(self.alice, 10, 12).json()
        self.room.price_per_night = 500000
        self.room.save()
        self.assertEqual(Reservation.objects.get(pk=res["id"]).total_amount, 200000)


class PermissionTests(BaseCase):
    def test_client_cannot_use_admin_endpoints(self):
        res = self.book(self.alice, 10, 12).json()
        c = self.client_for(self.alice)
        for url in ["/api/admin/reservations/", "/api/admin/rooms/", "/api/admin/customers/", "/api/admin/stats/", "/api/admin/services/"]:
            self.assertEqual(c.get(url).status_code, 403, url)
        self.assertEqual(c.post(f"/api/admin/reservations/{res['id']}/accept/").status_code, 403)
        self.assertEqual(c.post("/api/admin/rooms/", {"number": "9"}, format="json").status_code, 403)

    def test_anonymous_cannot_use_admin_or_reserve(self):
        anon = APIClient()
        self.assertIn(anon.get("/api/admin/stats/").status_code, (401, 403))
        self.assertIn(anon.get("/api/reservations/").status_code, (401, 403))

    def test_client_sees_only_own_reservations(self):
        mine = self.book(self.alice, 10, 12).json()
        theirs = self.book(self.bob, 20, 22).json()
        listing = self.client_for(self.alice).get("/api/reservations/").json()
        self.assertEqual([x["id"] for x in listing["results"]], [mine["id"]])
        self.assertEqual(self.client_for(self.alice).get(f"/api/reservations/{theirs['id']}/").status_code, 404)
        self.assertEqual(self.client_for(self.alice).post(f"/api/reservations/{theirs['id']}/cancel/").status_code, 404)

    def test_admin_can_list_and_see_stats(self):
        self.book(self.alice, 10, 12)
        c = self.client_for(self.admin)
        self.assertEqual(c.get("/api/admin/reservations/").json()["count"], 1)
        stats = c.get("/api/admin/stats/").json()
        self.assertEqual((stats["pending"], stats["total_rooms"], stats["customers"]), (1, 1, 2))

    def test_room_with_reservations_cannot_be_deleted(self):
        self.book(self.alice, 10, 12)
        self.assertEqual(self.client_for(self.admin).delete(f"/api/admin/rooms/{self.room.pk}/").status_code, 409)


class PaginationTests(BaseCase):
    def test_room_lists_are_paginated_by_6(self):
        for i in range(14):
            Room.objects.create(number=f"2{i:02d}", name=f"R{i}", capacity=2, price_per_night=50000)
        data = APIClient().get("/api/rooms/").json()
        self.assertEqual(data["count"], 15)
        self.assertEqual(len(data["results"]), 6)
        admin_page = self.client_for(self.admin).get("/api/admin/rooms/?page=3").json()
        self.assertEqual(admin_page["count"], 15)
        self.assertEqual(len(admin_page["results"]), 3)
