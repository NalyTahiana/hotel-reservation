from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APIClient

from apps.reservations.tests import BaseCase

from .models import Notification


class NotificationTests(BaseCase):
    def test_admin_notified_of_new_reservation(self):
        self.book(self.alice, 10, 12)
        n = Notification.objects.get(user=self.admin)
        self.assertEqual(n.kind, "new_reservation")
        self.assertIn("101", n.message)
        self.assertFalse(Notification.objects.filter(user=self.alice).exists())

    def test_customer_notified_with_details_on_accept_and_refuse(self):
        res = self.book(self.alice, 10, 12).json()
        admin = self.client_for(self.admin)
        admin.post(f"/api/admin/reservations/{res['id']}/accept/")
        n = Notification.objects.get(user=self.alice, kind="accepted")
        start = (timezone.localdate() + timedelta(days=10)).strftime("%d/%m/%Y")
        self.assertIn("Chambre n° 101", n.message)
        self.assertIn(start, n.message)
        self.assertIn("2 nuit(s)", n.message)
        res2 = self.book(self.bob, 20, 22).json()
        admin.post(f"/api/admin/reservations/{res2['id']}/refuse/")
        self.assertTrue(Notification.objects.filter(user=self.bob, kind="refused").exists())

    def test_list_and_mark_read_are_private(self):
        self.book(self.alice, 10, 12)
        admin = self.client_for(self.admin)
        data = admin.get("/api/notifications/").json()
        self.assertEqual(data["unread_count"], 1)
        nid = data["results"][0]["id"]
        self.assertEqual(self.client_for(self.bob).post(f"/api/notifications/{nid}/read/").status_code, 404)
        self.assertEqual(admin.post(f"/api/notifications/{nid}/read/").status_code, 204)
        self.assertEqual(admin.get("/api/notifications/").json()["unread_count"], 0)

    def test_requires_login(self):
        self.assertIn(APIClient().get("/api/notifications/").status_code, (401, 403))
