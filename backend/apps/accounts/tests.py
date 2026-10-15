from django.test import TestCase
from rest_framework.test import APIClient

from .models import User

VALID = {
    "email": "Jean@Example.com", "last_name": "Rakoto", "first_name": "Jean", "phone": "0341234567",
    "password": "MotDePasse!2026", "password_confirm": "MotDePasse!2026",
}


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_with_hashed_password(self):
        r = self.client.post("/api/auth/register/", VALID, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        user = User.objects.get(email="jean@example.com")
        self.assertNotEqual(user.password, VALID["password"])
        self.assertTrue(user.check_password(VALID["password"]))
        self.assertFalse(user.is_staff)

    def test_register_rejects_bad_phone(self):
        for phone in ["034123456", "03412345678", "03412345ab", ""]:
            r = self.client.post("/api/auth/register/", {**VALID, "phone": phone}, format="json")
            self.assertEqual(r.status_code, 400, phone)
            self.assertIn("phone", r.json())

    def test_register_rejects_duplicate_email(self):
        self.client.post("/api/auth/register/", VALID, format="json")
        r = self.client.post("/api/auth/register/", {**VALID, "email": "jean@example.com"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("email", r.json())

    def test_register_rejects_password_mismatch(self):
        r = self.client.post("/api/auth/register/", {**VALID, "password_confirm": "autre"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_login_and_me(self):
        User.objects.create_user("a@b.com", "MotDePasse!2026", last_name="A", first_name="B", phone="0341234567")
        bad = self.client.post("/api/auth/login/", {"email": "a@b.com", "password": "faux"}, format="json")
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post("/api/auth/login/", {"email": "A@B.com", "password": "MotDePasse!2026"}, format="json")
        self.assertEqual(ok.status_code, 200)
        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.json()["email"], "a@b.com")

    def test_inactive_account_cannot_login(self):
        User.objects.create_user("x@y.com", "MotDePasse!2026", last_name="X", first_name="Y", phone="0341234567", is_active=False)
        r = self.client.post("/api/auth/login/", {"email": "x@y.com", "password": "MotDePasse!2026"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_me_requires_authentication(self):
        self.assertIn(self.client.get("/api/auth/me/").status_code, (401, 403))


class AdminCustomerCreationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin@x.com", "MotDePasse!2026", last_name="A", first_name="B", phone="0341234567", is_staff=True)
        self.client_user = User.objects.create_user("c@x.com", "MotDePasse!2026", last_name="C", first_name="D", phone="0341234567")

    def payload(self, **over):
        return {"email": "walkin@x.com", "last_name": "Rabe", "first_name": "Paul", "phone": "0321234567",
                "password": "MotDePasse!2026", "password_confirm": "MotDePasse!2026", **over}

    def test_admin_creates_customer_without_being_logged_in_as_them(self):
        c = APIClient()
        c.force_login(self.admin)
        r = c.post("/api/admin/customers/", self.payload(), format="json")
        self.assertEqual(r.status_code, 201, r.content)
        created = User.objects.get(email="walkin@x.com")
        self.assertFalse(created.is_staff)
        self.assertTrue(created.check_password("MotDePasse!2026"))
        self.assertEqual(c.get("/api/auth/me/").json()["email"], "admin@x.com")

    def test_admin_creation_validates_phone_and_duplicates(self):
        c = APIClient()
        c.force_login(self.admin)
        self.assertEqual(c.post("/api/admin/customers/", self.payload(phone="123"), format="json").status_code, 400)
        self.assertEqual(c.post("/api/admin/customers/", self.payload(email="c@x.com"), format="json").status_code, 400)

    def test_client_cannot_create_customers(self):
        c = APIClient()
        c.force_login(self.client_user)
        self.assertEqual(c.post("/api/admin/customers/", self.payload(), format="json").status_code, 403)

    def test_customer_list_is_paginated_by_6(self):
        for i in range(8):
            User.objects.create_user(f"u{i}@x.com", "MotDePasse!2026", last_name="N", first_name="P", phone="0341234567")
        c = APIClient()
        c.force_login(self.admin)
        data = c.get("/api/admin/customers/").json()
        self.assertEqual((data["count"], len(data["results"])), (9, 6))
