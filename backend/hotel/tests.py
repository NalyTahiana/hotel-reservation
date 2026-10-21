import base64
import shutil
import tempfile
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from django.utils import timezone
from hotel.models import *

MOT_DE_PASSE = "MotDePasse!2026"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

INSCRIPTION = {
	"email": "Jean@Example.com", "last_name": "Rakoto", "first_name": "Jean", "phone": "0341234567",
	"password": MOT_DE_PASSE, "password_confirm": MOT_DE_PASSE,
}


def creer_utilisateur(email, admin=False):
	return User.objects.create_user(email, MOT_DE_PASSE, last_name="Nom", first_name="Prenom", phone="0341234567", is_staff=admin)


def connecte(utilisateur):
	client = Client()
	client.force_login(utilisateur)
	return client


def envoyer(client, url, donnees):
	return client.post(url, donnees, content_type="application/json")


def modifier_formulaire(client, url, donnees):
	return client.patch(url, encode_multipart(BOUNDARY, donnees), content_type=MULTIPART_CONTENT)


class AuthTests(TestCase):
	def setUp(self):
		self.client = Client()

	def test_register_creates_user_with_hashed_password(self):
		r = envoyer(self.client, "/api/auth/register/", INSCRIPTION)
		self.assertEqual(r.status_code, 201, r.content)
		utilisateur = User.objects.get(email="jean@example.com")
		self.assertNotEqual(utilisateur.password, MOT_DE_PASSE)
		self.assertTrue(utilisateur.check_password(MOT_DE_PASSE))
		self.assertFalse(utilisateur.is_staff)

	def test_register_rejects_bad_phone(self):
		for telephone in ["034123456", "03412345678", "03412345ab", ""]:
			r = envoyer(self.client, "/api/auth/register/", {**INSCRIPTION, "phone": telephone})
			self.assertEqual(r.status_code, 400, telephone)
			self.assertIn("phone", r.json())

	def test_register_rejects_duplicate_email(self):
		envoyer(self.client, "/api/auth/register/", INSCRIPTION)
		r = envoyer(self.client, "/api/auth/register/", {**INSCRIPTION, "email": "jean@example.com"})
		self.assertEqual(r.status_code, 400)
		self.assertIn("email", r.json())

	def test_register_rejects_password_mismatch(self):
		r = envoyer(self.client, "/api/auth/register/", {**INSCRIPTION, "password_confirm": "autre"})
		self.assertEqual(r.status_code, 400)
		self.assertIn("password_confirm", r.json())

	def test_login_and_me(self):
		creer_utilisateur("a@b.com")
		mauvais = envoyer(self.client, "/api/auth/login/", {"email": "a@b.com", "password": "faux"})
		self.assertEqual(mauvais.status_code, 400)
		bon = envoyer(self.client, "/api/auth/login/", {"email": "A@B.com", "password": MOT_DE_PASSE})
		self.assertEqual(bon.status_code, 200)
		self.assertEqual(self.client.get("/api/auth/me/").json()["email"], "a@b.com")

	def test_inactive_account_cannot_login(self):
		User.objects.create_user("x@y.com", MOT_DE_PASSE, last_name="X", first_name="Y", phone="0341234567", is_active=False)
		r = envoyer(self.client, "/api/auth/login/", {"email": "x@y.com", "password": MOT_DE_PASSE})
		self.assertEqual(r.status_code, 400)

	def test_me_requires_authentication(self):
		self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)

	def test_me_can_be_updated_partially(self):
		utilisateur = creer_utilisateur("m@x.com")
		client = connecte(utilisateur)
		r = client.patch("/api/auth/me/", {"first_name": "Nouveau"}, content_type="application/json")
		self.assertEqual(r.status_code, 200, r.content)
		utilisateur.refresh_from_db()
		self.assertEqual((utilisateur.first_name, utilisateur.last_name), ("Nouveau", "Nom"))

	def test_logout_returns_204(self):
		client = connecte(creer_utilisateur("l@x.com"))
		self.assertEqual(client.post("/api/auth/logout/").status_code, 204)
		self.assertEqual(client.get("/api/auth/me/").status_code, 403)

	def test_csrf_endpoint_sets_cookie(self):
		r = self.client.get("/api/auth/csrf/")
		self.assertEqual(r.status_code, 200)
		self.assertIn("csrftoken", r.cookies)


class BaseCase(TestCase):
	def setUp(self):
		self.today = timezone.localdate()
		self.room = Room.objects.create(number="101", name="Chambre 101", room_type="double", capacity=2, price_per_night=100000)
		self.alice = creer_utilisateur("alice@x.com")
		self.bob = creer_utilisateur("bob@x.com")
		self.admin = creer_utilisateur("admin@x.com", admin=True)

	def d(self, decalage):
		return (self.today + timedelta(days=decalage)).isoformat()

	def reserver(self, utilisateur, debut, fin, personnes=2, chambre=None):
		return envoyer(connecte(utilisateur), "/api/reservations/", {
			"room": (chambre or self.room).pk, "check_in": self.d(debut), "check_out": self.d(fin), "guests": personnes,
		})


class BookingRulesTests(BaseCase):
	def test_creation_calculates_total_on_server_and_is_pending(self):
		r = envoyer(connecte(self.alice), "/api/reservations/", {
			"room": self.room.pk, "check_in": self.d(10), "check_out": self.d(13), "guests": 2,
			"total_amount": 1, "status": "accepted", "price_per_night": 1,
		})
		self.assertEqual(r.status_code, 201, r.content)
		donnees = r.json()
		self.assertEqual((donnees["nights"], donnees["price_per_night"], donnees["total_amount"]), (3, 100000, 300000))
		self.assertEqual(donnees["status"], "pending")

	def test_persistence_in_database(self):
		self.reserver(self.alice, 10, 12)
		enregistree = Reservation.objects.get(customer=self.alice)
		self.assertEqual(enregistree.total_amount, 200000)
		self.assertTrue(enregistree.reference.startswith("RSV-"))

	def test_invalid_dates_rejected(self):
		self.assertEqual(self.reserver(self.alice, -2, 3).status_code, 400)
		self.assertEqual(self.reserver(self.alice, 5, 5).status_code, 400)
		self.assertEqual(self.reserver(self.alice, 8, 5).status_code, 400)

	def test_capacity_exceeded_rejected(self):
		r = self.reserver(self.alice, 10, 12, personnes=3)
		self.assertEqual(r.status_code, 400)
		self.assertIn("guests", r.json())

	def test_inactive_room_rejected(self):
		self.room.is_active = False
		self.room.save()
		self.assertEqual(self.reserver(self.alice, 10, 12).status_code, 400)

	def test_overlapping_reservation_rejected_even_when_pending(self):
		self.assertEqual(self.reserver(self.alice, 10, 15).status_code, 201)
		self.assertEqual(self.reserver(self.bob, 12, 17).status_code, 409)
		self.assertEqual(self.reserver(self.bob, 8, 11).status_code, 409)
		self.assertEqual(self.reserver(self.bob, 11, 13).status_code, 409)

	def test_consecutive_reservations_allowed(self):
		self.assertEqual(self.reserver(self.alice, 10, 15).status_code, 201)
		self.assertEqual(self.reserver(self.bob, 15, 18).status_code, 201)
		self.assertEqual(self.reserver(self.bob, 5, 10).status_code, 201)

	def test_dates_released_after_refusal_and_cancellation(self):
		premiere = self.reserver(self.alice, 10, 15).json()
		connecte(self.admin).post(f"/api/admin/reservations/{premiere['id']}/refuse/")
		seconde = self.reserver(self.bob, 10, 15)
		self.assertEqual(seconde.status_code, 201)
		r = connecte(self.bob).post(f"/api/reservations/{seconde.json()['id']}/cancel/")
		self.assertEqual(r.status_code, 200)
		self.assertEqual(self.reserver(self.alice, 11, 14).status_code, 201)

	def test_availability_search_excludes_busy_rooms(self):
		autre = Room.objects.create(number="102", name="Chambre 102", capacity=2, price_per_night=90000)
		self.reserver(self.alice, 10, 15)
		url = f"/api/rooms/?check_in={self.d(12)}&check_out={self.d(14)}&guests=2"
		identifiants = [x["id"] for x in Client().get(url).json()["results"]]
		self.assertEqual(identifiants, [autre.pk])

	def test_room_detail_reports_availability(self):
		self.reserver(self.alice, 10, 15)
		occupee = Client().get(f"/api/rooms/{self.room.pk}/?check_in={self.d(11)}&check_out={self.d(12)}").json()
		libre = Client().get(f"/api/rooms/{self.room.pk}/?check_in={self.d(20)}&check_out={self.d(22)}").json()
		sans_dates = Client().get(f"/api/rooms/{self.room.pk}/").json()
		self.assertEqual((occupee["available"], libre["available"], sans_dates["available"]), (False, True, None))

	def test_accept_rechecks_availability(self):
		en_attente = self.reserver(self.alice, 10, 15).json()
		Reservation.objects.create(
			customer=self.bob, room=self.room, check_in=self.today + timedelta(days=12), check_out=self.today + timedelta(days=16),
			guests=1, price_per_night=100000, nights=4, total_amount=400000, status=Reservation.Status.ACCEPTED,
		)
		r = connecte(self.admin).post(f"/api/admin/reservations/{en_attente['id']}/accept/")
		self.assertEqual(r.status_code, 409)
		self.assertEqual(Reservation.objects.get(pk=en_attente["id"]).status, Reservation.Status.PENDING)

	def test_accept_then_cancel_flow(self):
		reservation = self.reserver(self.alice, 10, 12).json()
		admin = connecte(self.admin)
		accepte = admin.post(f"/api/admin/reservations/{reservation['id']}/accept/")
		self.assertEqual(accepte.status_code, 200)
		self.assertEqual(accepte.json()["status"], "accepted")
		self.assertEqual(admin.post(f"/api/admin/reservations/{reservation['id']}/accept/").status_code, 409)
		self.assertEqual(connecte(self.alice).post(f"/api/reservations/{reservation['id']}/cancel/").status_code, 200)

	def test_price_snapshot_is_kept_when_room_price_changes(self):
		reservation = self.reserver(self.alice, 10, 12).json()
		self.room.price_per_night = 500000
		self.room.save()
		self.assertEqual(Reservation.objects.get(pk=reservation["id"]).total_amount, 200000)

	def test_past_accepted_reservations_become_completed(self):
		Reservation.objects.create(
			customer=self.alice, room=self.room, check_in=self.today - timedelta(days=5), check_out=self.today - timedelta(days=2),
			guests=1, price_per_night=100000, nights=3, total_amount=300000, status=Reservation.Status.ACCEPTED,
		)
		connecte(self.alice).get("/api/reservations/")
		self.assertEqual(Reservation.objects.get().status, Reservation.Status.COMPLETED)


class PermissionTests(BaseCase):
	def test_client_cannot_use_admin_endpoints(self):
		reservation = self.reserver(self.alice, 10, 12).json()
		client = connecte(self.alice)
		for url in ["/api/admin/reservations/", "/api/admin/rooms/", "/api/admin/customers/", "/api/admin/stats/", "/api/admin/services/"]:
			self.assertEqual(client.get(url).status_code, 403, url)
		self.assertEqual(client.post(f"/api/admin/reservations/{reservation['id']}/accept/").status_code, 403)
		self.assertEqual(envoyer(client, "/api/admin/rooms/", {"number": "9"}).status_code, 403)

	def test_anonymous_cannot_use_admin_or_reserve(self):
		anonyme = Client()
		self.assertEqual(anonyme.get("/api/admin/stats/").status_code, 403)
		self.assertEqual(anonyme.get("/api/reservations/").status_code, 403)

	def test_client_sees_only_own_reservations(self):
		la_mienne = self.reserver(self.alice, 10, 12).json()
		la_leur = self.reserver(self.bob, 20, 22).json()
		liste = connecte(self.alice).get("/api/reservations/").json()
		self.assertEqual([x["id"] for x in liste["results"]], [la_mienne["id"]])
		self.assertEqual(connecte(self.alice).get(f"/api/reservations/{la_leur['id']}/").status_code, 404)
		self.assertEqual(connecte(self.alice).post(f"/api/reservations/{la_leur['id']}/cancel/").status_code, 404)

	def test_admin_can_list_and_see_stats(self):
		self.reserver(self.alice, 10, 12)
		admin = connecte(self.admin)
		self.assertEqual(admin.get("/api/admin/reservations/").json()["count"], 1)
		stats = admin.get("/api/admin/stats/").json()
		self.assertEqual((stats["pending"], stats["total_rooms"], stats["customers"]), (1, 1, 2))
		self.assertEqual(len(stats["monthly"]), 6)

	def test_room_with_reservations_cannot_be_deleted(self):
		self.reserver(self.alice, 10, 12)
		self.assertEqual(connecte(self.admin).delete(f"/api/admin/rooms/{self.room.pk}/").status_code, 409)


class PaginationTests(BaseCase):
	def test_room_lists_are_paginated_by_6(self):
		for i in range(14):
			Room.objects.create(number=f"2{i:02d}", name=f"R{i}", capacity=2, price_per_night=50000)
		donnees = Client().get("/api/rooms/").json()
		self.assertEqual(donnees["count"], 15)
		self.assertEqual(len(donnees["results"]), 6)
		page_admin = connecte(self.admin).get("/api/admin/rooms/?page=3").json()
		self.assertEqual(page_admin["count"], 15)
		self.assertEqual(len(page_admin["results"]), 3)

	def test_invalid_page_returns_404(self):
		self.assertEqual(Client().get("/api/rooms/?page=9").status_code, 404)

	def test_customer_list_is_paginated_by_6(self):
		for i in range(8):
			creer_utilisateur(f"u{i}@x.com")
		donnees = connecte(self.admin).get("/api/admin/customers/").json()
		self.assertEqual((donnees["count"], len(donnees["results"])), (10, 6))


class NotificationTests(BaseCase):
	def test_admin_notified_of_new_reservation(self):
		self.reserver(self.alice, 10, 12)
		notification = Notification.objects.get(user=self.admin)
		self.assertEqual(notification.kind, "new_reservation")
		self.assertIn("101", notification.message)
		self.assertFalse(Notification.objects.filter(user=self.alice).exists())

	def test_customer_notified_with_details_on_accept_and_refuse(self):
		reservation = self.reserver(self.alice, 10, 12).json()
		admin = connecte(self.admin)
		admin.post(f"/api/admin/reservations/{reservation['id']}/accept/")
		notification = Notification.objects.get(user=self.alice, kind="accepted")
		debut = (timezone.localdate() + timedelta(days=10)).strftime("%d/%m/%Y")
		self.assertIn("Chambre n° 101", notification.message)
		self.assertIn(debut, notification.message)
		self.assertIn("2 nuit(s)", notification.message)
		seconde = self.reserver(self.bob, 20, 22).json()
		admin.post(f"/api/admin/reservations/{seconde['id']}/refuse/")
		self.assertTrue(Notification.objects.filter(user=self.bob, kind="refused").exists())

	def test_admin_notified_when_client_cancels(self):
		reservation = self.reserver(self.alice, 10, 12).json()
		connecte(self.alice).post(f"/api/reservations/{reservation['id']}/cancel/")
		self.assertTrue(Notification.objects.filter(user=self.admin, kind="cancelled").exists())

	def test_list_and_mark_read_are_private(self):
		self.reserver(self.alice, 10, 12)
		admin = connecte(self.admin)
		donnees = admin.get("/api/notifications/").json()
		self.assertEqual(donnees["unread_count"], 1)
		identifiant = donnees["results"][0]["id"]
		self.assertEqual(connecte(self.bob).post(f"/api/notifications/{identifiant}/read/").status_code, 404)
		self.assertEqual(admin.post(f"/api/notifications/{identifiant}/read/").status_code, 204)
		self.assertEqual(admin.get("/api/notifications/").json()["unread_count"], 0)

	def test_mark_all_read(self):
		self.reserver(self.alice, 10, 12)
		self.reserver(self.bob, 20, 22)
		admin = connecte(self.admin)
		self.assertEqual(admin.post("/api/notifications/read-all/").status_code, 204)
		self.assertEqual(admin.get("/api/notifications/").json()["unread_count"], 0)

	def test_requires_login(self):
		self.assertEqual(Client().get("/api/notifications/").status_code, 403)


class ClientHotelTests(BaseCase):
	def donnees(self, **autres):
		return {
			"last_name": "Rabe", "first_name": "Paul", "phone": "0321234567", "room": self.room.pk,
			"check_in": self.today.isoformat(), "check_out": (self.today + timedelta(days=3)).isoformat(), "guests": 2, **autres,
		}

	def test_admin_creates_customer_and_accepted_reservation(self):
		admin = connecte(self.admin)
		r = envoyer(admin, "/api/admin/customers/", self.donnees())
		self.assertEqual(r.status_code, 201, r.content)
		contenu = r.json()
		self.assertEqual(contenu["customer"]["email"], "")
		self.assertEqual(contenu["reservation"]["status"], "accepted")
		self.assertEqual(contenu["reservation"]["nights"], 3)
		self.assertEqual(contenu["reservation"]["total_amount"], 300000)
		cree = User.objects.get(last_name="Rabe")
		self.assertFalse(cree.is_staff)
		self.assertFalse(cree.has_usable_password())
		self.assertEqual(cree.reservations.count(), 1)
		self.assertEqual(admin.get("/api/auth/me/").json()["email"], "admin@x.com")

	def test_guests_defaults_to_one(self):
		donnees = self.donnees()
		del donnees["guests"]
		r = envoyer(connecte(self.admin), "/api/admin/customers/", donnees)
		self.assertEqual(r.status_code, 201, r.content)
		self.assertEqual(r.json()["reservation"]["guests"], 1)

	def test_validation_errors_create_nothing(self):
		admin = connecte(self.admin)
		avant = User.objects.count()
		passe = (self.today - timedelta(days=2)).isoformat()
		for modification in [{"phone": "123"}, {"check_out": self.today.isoformat()}, {"room": 99999}, {"guests": 5}, {"check_in": passe}]:
			self.assertEqual(envoyer(admin, "/api/admin/customers/", self.donnees(**modification)).status_code, 400, modification)
		self.assertEqual(User.objects.count(), avant)

	def test_occupied_room_is_refused_and_no_customer_created(self):
		admin = connecte(self.admin)
		self.assertEqual(envoyer(admin, "/api/admin/customers/", self.donnees()).status_code, 201)
		avant = User.objects.count()
		self.assertEqual(envoyer(admin, "/api/admin/customers/", self.donnees(last_name="Autre")).status_code, 409)
		self.assertEqual(User.objects.count(), avant)

	def test_available_rooms_excludes_occupied_room(self):
		autre = Room.objects.create(number="102", name="Chambre simple", capacity=1, price_per_night=50000)
		admin = connecte(self.admin)
		parametres = f"?check_in={self.today.isoformat()}&check_out={(self.today + timedelta(days=2)).isoformat()}"
		identifiants = [x["id"] for x in admin.get("/api/admin/customers/available-rooms/" + parametres).json()]
		self.assertEqual(identifiants, [self.room.pk, autre.pk])
		envoyer(admin, "/api/admin/customers/", self.donnees())
		identifiants = [x["id"] for x in admin.get("/api/admin/customers/available-rooms/" + parametres).json()]
		self.assertEqual(identifiants, [autre.pk])

	def test_available_rooms_requires_valid_dates(self):
		self.assertEqual(connecte(self.admin).get("/api/admin/customers/available-rooms/").status_code, 400)

	def test_customer_detail_and_deactivation(self):
		admin = connecte(self.admin)
		envoyer(admin, "/api/admin/customers/", self.donnees())
		cree = User.objects.get(last_name="Rabe")
		detail = admin.get(f"/api/admin/customers/{cree.pk}/").json()
		self.assertEqual(len(detail["reservations"]), 1)
		r = admin.patch(f"/api/admin/customers/{cree.pk}/", {"is_active": False}, content_type="application/json")
		self.assertEqual(r.status_code, 200, r.content)
		cree.refresh_from_db()
		self.assertFalse(cree.is_active)

	def test_client_cannot_create_customers_or_list_rooms(self):
		client = connecte(self.alice)
		self.assertEqual(envoyer(client, "/api/admin/customers/", self.donnees()).status_code, 403)
		self.assertEqual(client.get("/api/admin/customers/available-rooms/").status_code, 403)


class AdminChambreTests(BaseCase):
	def setUp(self):
		super().setUp()
		self.dossier = tempfile.mkdtemp()
		self.reglage = override_settings(MEDIA_ROOT=self.dossier)
		self.reglage.enable()
		self.admin_client = connecte(self.admin)

	def tearDown(self):
		self.reglage.disable()
		shutil.rmtree(self.dossier, ignore_errors=True)

	def formulaire(self, **autres):
		return {
			"number": "301", "name": "Suite", "room_type": "suite", "short_description": "", "description": "", "capacity": "4",
			"price_per_night": "250000", "amenities": "Wi-Fi\nTV", "included_services": "", "is_active": "true", **autres,
		}

	def test_create_with_multipart_and_photo(self):
		donnees = self.formulaire(image=SimpleUploadedFile("chambre.png", PNG, content_type="image/png"))
		r = self.admin_client.post("/api/admin/rooms/", donnees)
		self.assertEqual(r.status_code, 201, r.content)
		contenu = r.json()
		self.assertEqual(contenu["amenities_list"], ["Wi-Fi", "TV"])
		self.assertTrue(contenu["image"].startswith("http"))

	def test_duplicate_number_and_missing_price_are_rejected(self):
		r = self.admin_client.post("/api/admin/rooms/", self.formulaire(number="101"))
		self.assertEqual(r.status_code, 400)
		self.assertIn("number", r.json())
		r = self.admin_client.post("/api/admin/rooms/", self.formulaire(price_per_night=""))
		self.assertEqual(r.status_code, 400)
		self.assertIn("price_per_night", r.json())

	def test_patch_multipart_changes_only_sent_fields(self):
		r = modifier_formulaire(self.admin_client, f"/api/admin/rooms/{self.room.pk}/", {"is_active": "false"})
		self.assertEqual(r.status_code, 200, r.content)
		self.room.refresh_from_db()
		self.assertFalse(self.room.is_active)
		self.assertEqual((self.room.name, self.room.price_per_night, self.room.capacity), ("Chambre 101", 100000, 2))
		r = modifier_formulaire(self.admin_client, f"/api/admin/rooms/{self.room.pk}/", {"price_per_night": "120000", "is_active": "true"})
		self.assertEqual(r.status_code, 200, r.content)
		self.room.refresh_from_db()
		self.assertEqual((self.room.is_active, self.room.price_per_night), (True, 120000))

	def test_gallery_upload_and_delete(self):
		fichiers = {"images": [SimpleUploadedFile("a.png", PNG, content_type="image/png"), SimpleUploadedFile("b.png", PNG, content_type="image/png")]}
		r = self.admin_client.post(f"/api/admin/rooms/{self.room.pk}/images/", fichiers)
		self.assertEqual(r.status_code, 201, r.content)
		images = r.json()["images"]
		self.assertEqual(len(images), 2)
		self.assertEqual(self.admin_client.delete(f"/api/admin/rooms/{self.room.pk}/images/{images[0]['id']}/").status_code, 204)
		self.assertEqual(self.admin_client.delete(f"/api/admin/rooms/{self.room.pk}/images/{images[0]['id']}/").status_code, 404)

	def test_gallery_rejects_missing_or_invalid_files(self):
		self.assertEqual(self.admin_client.post(f"/api/admin/rooms/{self.room.pk}/images/", {}).status_code, 400)
		faux = {"images": SimpleUploadedFile("a.png", b"pas une image", content_type="image/png")}
		self.assertEqual(self.admin_client.post(f"/api/admin/rooms/{self.room.pk}/images/", faux).status_code, 400)

	def test_room_without_reservations_can_be_deleted(self):
		vide = Room.objects.create(number="777", name="Libre", capacity=1, price_per_night=1000)
		self.assertEqual(self.admin_client.delete(f"/api/admin/rooms/{vide.pk}/").status_code, 204)
		self.assertFalse(Room.objects.filter(pk=vide.pk).exists())


class AdminServiceTests(BaseCase):
	def test_service_crud_and_public_catalog(self):
		admin = connecte(self.admin)
		r = admin.post("/api/admin/services/", {"kind": "service", "name": "Wi-Fi", "description": "Gratuit", "is_active": "true"})
		self.assertEqual(r.status_code, 201, r.content)
		identifiant = r.json()["id"]
		admin.post("/api/admin/services/", {"kind": "activity", "name": "Excursion", "description": "", "is_active": "false"})
		publics = Client().get("/api/catalog/services/").json()
		self.assertEqual([s["name"] for s in publics], ["Wi-Fi"])
		self.assertEqual(Client().get("/api/catalog/services/?kind=activity").json(), [])
		r = modifier_formulaire(admin, f"/api/admin/services/{identifiant}/", {"is_active": "false"})
		self.assertEqual(r.status_code, 200, r.content)
		self.assertEqual(Client().get("/api/catalog/services/").json(), [])
		self.assertEqual(admin.get("/api/admin/services/").json()["count"], 2)
		self.assertEqual(admin.delete(f"/api/admin/services/{identifiant}/").status_code, 204)
		self.assertEqual(admin.get("/api/admin/services/").json()["count"], 1)


class PaymentTests(BaseCase):
	def accepter(self, debut=10, fin=12):
		reservation = self.reserver(self.alice, debut, fin).json()
		connecte(self.admin).post(f"/api/admin/reservations/{reservation['id']}/accept/")
		return reservation["id"]

	def payer(self, identifiant, montant, utilisateur=None, **extra):
		return envoyer(connecte(utilisateur or self.admin), f"/api/admin/reservations/{identifiant}/payments/", {"amount": montant, **extra})

	def test_new_reservation_is_unpaid(self):
		identifiant = self.accepter()
		donnees = connecte(self.admin).get(f"/api/admin/reservations/{identifiant}/").json()
		self.assertEqual((donnees["amount_paid"], donnees["balance"], donnees["payment_status"]), (0, 200000, "unpaid"))

	def test_partial_then_full_payment(self):
		identifiant = self.accepter()
		r = self.payer(identifiant, 50000, note="Acompte")
		self.assertEqual(r.status_code, 201, r.content)
		self.assertEqual((r.json()["amount_paid"], r.json()["balance"], r.json()["payment_status"]), (50000, 150000, "partial"))
		r = self.payer(identifiant, 150000)
		self.assertEqual((r.json()["balance"], r.json()["payment_status"]), (0, "paid"))
		self.assertEqual(len(r.json()["payments"]), 2)
		self.assertEqual(Payment.objects.filter(reservation_id=identifiant).count(), 2)

	def test_overpayment_and_invalid_amounts_rejected(self):
		identifiant = self.accepter()
		self.assertEqual(self.payer(identifiant, 200001).status_code, 400)
		self.assertEqual(self.payer(identifiant, 0).status_code, 400)
		self.assertEqual(self.payer(identifiant, -5).status_code, 400)
		self.assertEqual(self.payer(identifiant, "abc").status_code, 400)
		self.assertEqual(Payment.objects.count(), 0)

	def test_payment_refused_once_fully_paid(self):
		identifiant = self.accepter()
		self.payer(identifiant, 200000)
		self.assertEqual(self.payer(identifiant, 1).status_code, 409)

	def test_payment_requires_accepted_reservation(self):
		en_attente = self.reserver(self.alice, 10, 12).json()["id"]
		self.assertEqual(self.payer(en_attente, 1000).status_code, 409)

	def test_client_cannot_record_payment(self):
		identifiant = self.accepter()
		self.assertEqual(self.payer(identifiant, 1000, utilisateur=self.alice).status_code, 403)
		self.assertEqual(Payment.objects.count(), 0)

	def test_payment_notifies_customer(self):
		identifiant = self.accepter()
		self.payer(identifiant, 50000)
		notification = Notification.objects.filter(user=self.alice, kind=Notification.Kind.PAYMENT).get()
		self.assertIn("50 000 Ar", notification.message)
		self.assertIn("150 000 Ar", notification.message)

	def test_client_cannot_cancel_after_payment(self):
		identifiant = self.accepter()
		self.payer(identifiant, 50000)
		self.assertEqual(connecte(self.alice).post(f"/api/reservations/{identifiant}/cancel/").status_code, 409)
		self.assertEqual(Reservation.objects.get(pk=identifiant).status, Reservation.Status.ACCEPTED)

	def test_payment_filter_and_dashboard(self):
		paye = self.accepter(10, 12)
		partiel = self.accepter(20, 22)
		self.accepter(30, 32)
		self.payer(paye, 200000)
		self.payer(partiel, 50000)
		admin = connecte(self.admin)
		comptes = {f: admin.get(f"/api/admin/reservations/?payment={f}").json()["count"] for f in ("unpaid", "partial", "paid")}
		self.assertEqual(comptes, {"unpaid": 1, "partial": 1, "paid": 1})
		stats = admin.get("/api/admin/stats/").json()
		self.assertEqual((stats["collected"], stats["balance_due"]), (250000, 350000))


class AdminReservationPaginationTests(BaseCase):
	def test_admin_reservations_are_paginated_by_5(self):
		for i in range(9):
			Reservation.objects.create(
				customer=self.alice, room=self.room, check_in=self.today + timedelta(days=10 + 3 * i), check_out=self.today + timedelta(days=11 + 3 * i),
				guests=1, price_per_night=100000, nights=1, total_amount=100000,
			)
		admin = connecte(self.admin)
		page1 = admin.get("/api/admin/reservations/").json()
		page2 = admin.get("/api/admin/reservations/?page=2").json()
		self.assertEqual((page1["count"], len(page1["results"]), len(page2["results"])), (9, 5, 4))
		self.assertEqual(admin.get("/api/admin/reservations/?page=3").status_code, 404)


class InvoiceTests(BaseCase):
	def reservation_payee(self, montant=50000):
		reservation = self.reserver(self.alice, 10, 12).json()
		connecte(self.admin).post(f"/api/admin/reservations/{reservation['id']}/accept/")
		envoyer(connecte(self.admin), f"/api/admin/reservations/{reservation['id']}/payments/", {"amount": montant})
		return reservation["id"]

	def test_no_invoice_without_payment(self):
		reservation = self.reserver(self.alice, 10, 12).json()["id"]
		self.assertEqual(connecte(self.alice).get(f"/api/reservations/{reservation}/invoice/").status_code, 409)
		self.assertEqual(connecte(self.admin).get(f"/api/admin/reservations/{reservation}/invoice/").status_code, 409)

	def test_client_and_admin_get_the_same_invoice(self):
		identifiant = self.reservation_payee(50000)
		cote_client = connecte(self.alice).get(f"/api/reservations/{identifiant}/invoice/")
		cote_admin = connecte(self.admin).get(f"/api/admin/reservations/{identifiant}/invoice/")
		self.assertEqual(cote_client.status_code, 200, cote_client.content)
		self.assertEqual(cote_client.json(), cote_admin.json())
		facture = cote_admin.json()
		self.assertTrue(facture["number"].startswith("FAC-"))
		self.assertEqual((facture["total_amount"], facture["amount_paid"], facture["balance"], facture["payment_status"]), (200000, 50000, 150000, "partial"))
		self.assertTrue(facture["payments"][0]["receipt"].startswith("REC-"))

	def test_invoice_updates_when_fully_paid(self):
		identifiant = self.reservation_payee(50000)
		envoyer(connecte(self.admin), f"/api/admin/reservations/{identifiant}/payments/", {"amount": 150000})
		facture = connecte(self.admin).get(f"/api/admin/reservations/{identifiant}/invoice/").json()
		self.assertEqual((facture["balance"], facture["payment_status"], len(facture["payments"])), (0, "paid", 2))

	def test_client_cannot_read_someone_elses_invoice(self):
		identifiant = self.reservation_payee()
		self.assertEqual(connecte(self.bob).get(f"/api/reservations/{identifiant}/invoice/").status_code, 404)
		self.assertEqual(connecte(self.bob).get(f"/api/admin/reservations/{identifiant}/invoice/").status_code, 403)
		self.assertEqual(Client().get(f"/api/reservations/{identifiant}/invoice/").status_code, 403)

	def test_walk_in_customer_created_by_admin_has_invoice(self):
		admin = connecte(self.admin)
		r = envoyer(admin, "/api/admin/customers/", {
			"last_name": "Rabe", "first_name": "Jean", "phone": "0341112233",
			"room": self.room.pk, "check_in": self.d(5), "check_out": self.d(7), "guests": 1,
		})
		identifiant = r.json()["reservation"]["id"]
		envoyer(admin, f"/api/admin/reservations/{identifiant}/payments/", {"amount": 200000})
		facture = admin.get(f"/api/admin/reservations/{identifiant}/invoice/").json()
		self.assertEqual((facture["customer"]["full_name"], facture["customer"]["email"], facture["payment_status"]), ("Jean Rabe", "", "paid"))
