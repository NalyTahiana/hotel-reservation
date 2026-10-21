import json
import uuid
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import BigIntegerField, Count, F, ProtectedError, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse, JsonResponse
from django.http.multipartparser import MultiPartParser
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from hotel.forms import *
from hotel.models import *


class VueApi(View):
	connexion      = False
	administrateur = False

	def dispatch(self, request, *args, **kwargs):
		try:
			if (self.connexion or self.administrateur) and not request.user.is_authenticated:
				raise ErreurMetier({"detail": "Authentification requise."}, 403)
			if self.administrateur and not request.user.is_staff:
				raise ErreurMetier({"detail": "Vous n'avez pas la permission d'effectuer cette action."}, 403)
			return super().dispatch(request, *args, **kwargs)
		except ErreurMetier as erreur:
			return JsonResponse(erreur.contenu, status=erreur.statut, safe=False)

	def reponse(self, contenu, statut=200):
		return JsonResponse(contenu, status=statut, safe=False)

	def vide(self):
		return HttpResponse(status=204)

	def lire(self, request):
		type_contenu = request.content_type
		if type_contenu == "application/json":
			try:
				contenu = json.loads(request.body or b"{}")
			except ValueError:
				raise ErreurMetier({"detail": "Le corps de la requête n'est pas un JSON valide."})
			if not isinstance(contenu, dict):
				raise ErreurMetier({"detail": "Le corps de la requête doit être un objet JSON."})
			return contenu, {}
		if type_contenu == "multipart/form-data" and request.method != "POST":
			return MultiPartParser(request.META, request, request.upload_handlers, request.encoding).parse()
		return request.POST, request.FILES

	def valider(self, formulaire):
		if not formulaire.is_valid():
			raise ErreurMetier(erreurs_formulaire(formulaire))
		return formulaire.cleaned_data

	def enregistrer(self, formulaire):
		if not formulaire.is_valid():
			raise ErreurMetier(erreurs_formulaire(formulaire))
		return formulaire.save()

	def paginer(self, request, liste, taille, convertir):
		paginateur = Paginator(liste, taille)
		try:
			page = paginateur.page(request.GET.get("page", 1))
		except (PageNotAnInteger, EmptyPage):
			raise ErreurMetier({"detail": "Page invalide."}, 404)
		return {"count": paginateur.count, "results": [convertir(element) for element in page.object_list]}

	def introuvable(self, texte):
		return ErreurMetier({"detail": texte}, 404)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class Csrf(VueApi):
	def get(self, request):
		return self.reponse({"detail": "Cookie CSRF défini."})


class Inscription(VueApi):
	def post(self, request):
		donnees, _ = self.lire(request)
		propres = self.valider(FormulaireInscription(donnees))
		utilisateur = User.objects.create_user(
			propres["email"], propres["password"],
			last_name=propres["last_name"], first_name=propres["first_name"], phone=propres["phone"],
		)
		login(request, utilisateur, backend="django.contrib.auth.backends.ModelBackend")
		return self.reponse(utilisateur.en_json(), 201)


class Connexion(VueApi):
	def post(self, request):
		donnees, _ = self.lire(request)
		propres = self.valider(FormulaireConnexion(donnees))
		utilisateur = authenticate(request, username=propres["email"].strip().lower(), password=propres["password"])
		if utilisateur is None:
			raise ErreurMetier({"detail": "Adresse e-mail ou mot de passe incorrect, ou compte désactivé."})
		login(request, utilisateur)
		return self.reponse(utilisateur.en_json())


class Deconnexion(VueApi):
	def post(self, request):
		logout(request)
		return self.vide()


class Moi(VueApi):
	connexion = True

	def get(self, request):
		return self.reponse(request.user.en_json())

	def patch(self, request):
		donnees, _ = self.lire(request)
		valeurs = {champ: donnees.get(champ, getattr(request.user, champ)) for champ in ("last_name", "first_name", "phone")}
		propres = self.valider(FormulaireProfil(valeurs))
		for champ, valeur in propres.items():
			setattr(request.user, champ, valeur)
		request.user.save(update_fields=list(propres))
		return self.reponse(request.user.en_json())


class ChambreListe(VueApi):
	def get(self, request):
		propres  = self.valider(FormulaireDisponibilite(request.GET))
		chambres = Room.objects.filter(is_active=True).prefetch_related("images")
		type_chambre = request.GET.get("room_type")
		if type_chambre:
			chambres = chambres.filter(room_type=type_chambre)
		if propres.get("guests"):
			chambres = chambres.filter(capacity__gte=propres["guests"])
		if propres.get("check_in"):
			chambres = Reservation.chambres_libres(chambres, propres["check_in"], propres["check_out"])
		return self.reponse(self.paginer(request, chambres, 6, lambda c: c.en_json(request)))


class ChambreDetail(VueApi):
	def get(self, request, pk):
		chambre = Room.objects.filter(pk=pk, is_active=True).prefetch_related("images").first()
		if chambre is None:
			raise self.introuvable("Chambre introuvable.")
		contenu = chambre.en_json(request)
		propres = self.valider(FormulaireDisponibilite(request.GET))
		if propres.get("check_in"):
			contenu["available"] = Reservation.chambre_disponible(chambre.pk, propres["check_in"], propres["check_out"])
		else:
			contenu["available"] = None
		return self.reponse(contenu)


class ServiceListe(VueApi):
	def get(self, request):
		services = HotelService.objects.filter(is_active=True)
		kind = request.GET.get("kind")
		if kind:
			services = services.filter(kind=kind)
		return self.reponse([s.en_json(request) for s in services])


def reservations_de_base():
	return Reservation.objects.select_related("room", "customer").prefetch_related("payments")


class ReservationListe(VueApi):
	connexion = True

	def get(self, request):
		Reservation.terminer_passees()
		reservations = reservations_de_base().filter(customer=request.user)
		statut = request.GET.get("status")
		if statut:
			reservations = reservations.filter(status=statut)
		return self.reponse(self.paginer(request, reservations, 10, lambda r: r.en_json(request)))

	def post(self, request):
		donnees, _ = self.lire(request)
		propres = self.valider(FormulaireReservation(donnees))
		reservation = Reservation.creer(
			client=request.user, room_id=propres["room"], check_in=propres["check_in"], check_out=propres["check_out"],
			guests=propres["guests"], comment=propres.get("comment", ""),
		)
		return self.reponse(reservation.en_json(request), 201)


class ReservationDetail(VueApi):
	connexion = True

	def get(self, request, pk):
		Reservation.terminer_passees()
		reservation = reservations_de_base().filter(customer=request.user, pk=pk).first()
		if reservation is None:
			raise self.introuvable("Réservation introuvable.")
		return self.reponse(reservation.en_json(request))


class ReservationAnnulation(VueApi):
	connexion = True

	def post(self, request, pk):
		propre = Reservation.objects.filter(customer=request.user, pk=pk).first()
		if propre is None:
			raise self.introuvable("Réservation introuvable.")
		Reservation.appliquer(reservation_id=propre.pk, action="cancel", acteur=request.user)
		return self.reponse(reservations_de_base().get(pk=pk).en_json(request))


def reponse_facture(vue, reservation):
	if reservation is None:
		raise vue.introuvable("Réservation introuvable.")
	if not reservation.payments.all():
		raise ErreurMetier({"detail": "Aucune facture : aucun paiement n'a encore été enregistré pour cette réservation."}, 409)
	return vue.reponse(reservation.en_json_facture())


class ReservationFacture(VueApi):
	connexion = True

	def get(self, request, pk):
		return reponse_facture(self, reservations_de_base().filter(customer=request.user, pk=pk).first())


class NotificationListe(VueApi):
	connexion = True

	def get(self, request):
		notifications = Notification.objects.filter(user=request.user)
		return self.reponse({
			"unread_count": notifications.filter(is_read=False).count(),
			"results"     : [n.en_json() for n in notifications[:30]],
		})


class NotificationLecture(VueApi):
	connexion = True

	def post(self, request, pk):
		modifiees = Notification.objects.filter(user=request.user, pk=pk).update(is_read=True)
		if not modifiees:
			raise self.introuvable("Notification introuvable.")
		return self.vide()


class NotificationToutLire(VueApi):
	connexion = True

	def post(self, request):
		Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
		return self.vide()


class AdminChambreListe(VueApi):
	administrateur = True

	def get(self, request):
		chambres = Room.objects.prefetch_related("images").order_by("number")
		q = request.GET.get("q", "").strip()
		if q:
			chambres = chambres.filter(Q(name__icontains=q) | Q(number__icontains=q))
		type_chambre = request.GET.get("room_type")
		if type_chambre:
			chambres = chambres.filter(room_type=type_chambre)
		actif = request.GET.get("is_active")
		if actif in ("true", "false"):
			chambres = chambres.filter(is_active=(actif == "true"))
		return self.reponse(self.paginer(request, chambres, 6, lambda c: c.en_json(request)))

	def post(self, request):
		donnees, fichiers = self.lire(request)
		chambre = self.enregistrer(FormulaireChambre(valeurs_formulaire(FormulaireChambre, donnees), fichiers))
		return self.reponse(chambre.en_json(request), 201)


class AdminChambreDetail(VueApi):
	administrateur = True

	def chambre(self, pk):
		chambre = Room.objects.prefetch_related("images").filter(pk=pk).first()
		if chambre is None:
			raise self.introuvable("Chambre introuvable.")
		return chambre

	def get(self, request, pk):
		return self.reponse(self.chambre(pk).en_json(request))

	def patch(self, request, pk):
		chambre = self.chambre(pk)
		donnees, fichiers = self.lire(request)
		formulaire = FormulaireChambre(valeurs_formulaire(FormulaireChambre, donnees, chambre), fichiers, instance=chambre)
		return self.reponse(self.enregistrer(formulaire).en_json(request))

	def delete(self, request, pk):
		try:
			self.chambre(pk).delete()
		except ProtectedError:
			raise ErreurMetier(
				{"detail": "Cette chambre a un historique de réservations et ne peut pas être supprimée. Désactivez-la à la place."},
				409,
			)
		return self.vide()


class AdminChambreImages(VueApi):
	administrateur = True

	def post(self, request, pk):
		chambre = Room.objects.filter(pk=pk).first()
		if chambre is None:
			raise self.introuvable("Chambre introuvable.")
		_, fichiers = self.lire(request)
		images = fichiers.getlist("images") if hasattr(fichiers, "getlist") else []
		if not images:
			raise ErreurMetier({"detail": "Aucune image envoyée."})
		for image in images:
			formulaire = FormulaireImage({}, {"image": image})
			if not formulaire.is_valid():
				raise ErreurMetier({"detail": " ".join(erreurs_formulaire(formulaire)["image"])})
		for image in images:
			RoomImage.objects.create(room=chambre, image=image)
		chambre = Room.objects.prefetch_related("images").get(pk=pk)
		return self.reponse(chambre.en_json(request), 201)


class AdminChambreImage(VueApi):
	administrateur = True

	def delete(self, request, pk, image_id):
		chambre = Room.objects.filter(pk=pk).first()
		if chambre is None:
			raise self.introuvable("Chambre introuvable.")
		supprimees, _ = RoomImage.objects.filter(room=chambre, pk=image_id).delete()
		if not supprimees:
			raise self.introuvable("Image introuvable.")
		return self.vide()


class AdminServiceListe(VueApi):
	administrateur = True

	def get(self, request):
		services = HotelService.objects.all()
		q = request.GET.get("q", "").strip()
		if q:
			services = services.filter(name__icontains=q)
		kind = request.GET.get("kind")
		if kind:
			services = services.filter(kind=kind)
		return self.reponse(self.paginer(request, services, 10, lambda s: s.en_json(request)))

	def post(self, request):
		donnees, fichiers = self.lire(request)
		service = self.enregistrer(FormulaireService(valeurs_formulaire(FormulaireService, donnees), fichiers))
		return self.reponse(service.en_json(request), 201)


class AdminServiceDetail(VueApi):
	administrateur = True

	def service(self, pk):
		service = HotelService.objects.filter(pk=pk).first()
		if service is None:
			raise self.introuvable("Service introuvable.")
		return service

	def get(self, request, pk):
		return self.reponse(self.service(pk).en_json(request))

	def patch(self, request, pk):
		service = self.service(pk)
		donnees, fichiers = self.lire(request)
		formulaire = FormulaireService(valeurs_formulaire(FormulaireService, donnees, service), fichiers, instance=service)
		return self.reponse(self.enregistrer(formulaire).en_json(request))

	def delete(self, request, pk):
		self.service(pk).delete()
		return self.vide()


class AdminReservationListe(VueApi):
	administrateur = True

	def get(self, request):
		Reservation.terminer_passees()
		reservations = reservations_de_base()
		statut = request.GET.get("status")
		if statut:
			reservations = reservations.filter(status=statut)
		for mot in request.GET.get("q", "").split():
			reservations = reservations.filter(
				Q(reference__icontains=mot) | Q(customer__first_name__icontains=mot)
				| Q(customer__last_name__icontains=mot) | Q(customer__email__icontains=mot)
			)
		paiement = request.GET.get("payment")
		if paiement in ("unpaid", "partial", "paid"):
			paye = Coalesce(Sum("payments__amount"), Value(0), output_field=BigIntegerField())
			reservations = reservations.filter(status__in=[Reservation.Status.ACCEPTED, Reservation.Status.COMPLETED]).annotate(paye=paye).order_by("-created_at", "-id")
			if paiement == "unpaid":
				reservations = reservations.filter(paye=0)
			elif paiement == "partial":
				reservations = reservations.filter(paye__gt=0, paye__lt=F("total_amount"))
			else:
				reservations = reservations.filter(paye__gte=F("total_amount"))
		dates = self.valider(FormulaireFiltreDates(request.GET))
		if dates.get("date_from"):
			reservations = reservations.filter(check_out__gte=dates["date_from"])
		if dates.get("date_to"):
			reservations = reservations.filter(check_in__lte=dates["date_to"])
		return self.reponse(self.paginer(request, reservations, 5, lambda r: r.en_json(request)))


class AdminReservationDetail(VueApi):
	administrateur = True

	def get(self, request, pk):
		Reservation.terminer_passees()
		reservation = reservations_de_base().filter(pk=pk).first()
		if reservation is None:
			raise self.introuvable("Réservation introuvable.")
		return self.reponse(reservation.en_json(request))


class AdminReservationAction(VueApi):
	administrateur = True

	def post(self, request, pk, action):
		Reservation.terminer_passees()
		if not Reservation.objects.filter(pk=pk).exists():
			raise self.introuvable("Réservation introuvable.")
		Reservation.appliquer(reservation_id=pk, action=action, acteur=request.user)
		return self.reponse(reservations_de_base().get(pk=pk).en_json(request))


class AdminReservationFacture(VueApi):
	administrateur = True

	def get(self, request, pk):
		return reponse_facture(self, reservations_de_base().filter(pk=pk).first())


class AdminReservationPaiement(VueApi):
	administrateur = True

	def post(self, request, pk):
		Reservation.terminer_passees()
		donnees, _ = self.lire(request)
		propres = self.valider(FormulairePaiement(donnees))
		Reservation.encaisser(reservation_id=pk, montant=propres["amount"], note=propres.get("note", ""), acteur=request.user)
		return self.reponse(reservations_de_base().get(pk=pk).en_json(request), 201)


class AdminClientListe(VueApi):
	administrateur = True

	def get(self, request):
		clients = User.objects.filter(is_staff=False).annotate(reservations_count=Count("reservations")).order_by("-date_joined")
		for mot in request.GET.get("q", "").split():
			clients = clients.filter(
				Q(first_name__icontains=mot) | Q(last_name__icontains=mot) | Q(email__icontains=mot) | Q(phone__icontains=mot)
			)
		actif = request.GET.get("is_active")
		if actif in ("true", "false"):
			clients = clients.filter(is_active=(actif == "true"))
		return self.reponse(self.paginer(request, clients, 6, lambda c: c.en_json_client()))

	def post(self, request):
		donnees, _ = self.lire(request)
		propres = self.valider(FormulaireClientHotel(donnees))
		with transaction.atomic():
			client = User.objects.create_user(
				f"client-{uuid.uuid4().hex[:12]}@{NO_EMAIL_DOMAIN}", None,
				last_name=propres["last_name"], first_name=propres["first_name"], phone=propres["phone"],
			)
			reservation = Reservation.creer(
				client=client, room_id=propres["room"], check_in=propres["check_in"], check_out=propres["check_out"],
				guests=propres.get("guests") or 1, par_admin=True,
			)
		client.reservations_count = 1
		return self.reponse({"customer": client.en_json_client(), "reservation": reservation.en_json(request)}, 201)


class AdminClientDetail(VueApi):
	administrateur = True

	def client(self, pk):
		client = User.objects.filter(pk=pk, is_staff=False).annotate(reservations_count=Count("reservations")).first()
		if client is None:
			raise self.introuvable("Client introuvable.")
		return client

	def get(self, request, pk):
		client = self.client(pk)
		contenu = client.en_json_client()
		reservations = client.reservations.select_related("room", "customer").order_by("-created_at")
		contenu["reservations"] = [r.en_json(request) for r in reservations]
		return self.reponse(contenu)

	def patch(self, request, pk):
		client = self.client(pk)
		donnees, _ = self.lire(request)
		if "is_active" not in donnees:
			raise ErreurMetier({"is_active": ["Ce champ est obligatoire."]})
		propres = self.valider(FormulaireStatut({"is_active": donnees.get("is_active")}))
		client.is_active = propres["is_active"]
		client.save(update_fields=["is_active"])
		return self.reponse({"is_active": client.is_active})


class AdminClientChambresLibres(VueApi):
	administrateur = True

	def get(self, request):
		propres = self.valider(FormulaireDisponibilite(request.GET))
		if not propres.get("check_in"):
			raise ErreurMetier({"check_in": ["Indiquez la date d'arrivée et la date de départ."]})
		if propres["check_in"] < timezone.localdate():
			raise ErreurMetier({"check_in": ["La date d'arrivée ne peut pas être dans le passé."]})
		chambres = Reservation.chambres_libres(Room.objects.filter(is_active=True).order_by("number"), propres["check_in"], propres["check_out"])
		return self.reponse([c.en_json_libre() for c in chambres])


def derniers_mois(aujourdhui, nombre=6):
	annee, mois = aujourdhui.year, aujourdhui.month
	resultat = []
	for _ in range(nombre):
		resultat.append((annee, mois))
		mois -= 1
		if mois == 0:
			annee, mois = annee - 1, 12
	return list(reversed(resultat))


class AdminTableauDeBord(VueApi):
	administrateur = True

	def get(self, request):
		Reservation.terminer_passees()
		S = Reservation.Status
		aujourdhui = timezone.localdate()
		par_statut = dict(Reservation.objects.values_list("status").annotate(n=Count("id")))
		occupees = set(
			Reservation.objects.filter(status=S.ACCEPTED, check_in__lte=aujourdhui, check_out__gt=aujourdhui).values_list("room_id", flat=True)
		)
		actives   = Room.objects.filter(is_active=True)
		occupe    = actives.filter(pk__in=occupees).count()
		mois      = derniers_mois(aujourdhui)
		premier   = aujourdhui.replace(year=mois[0][0], month=mois[0][1], day=1)
		mensuel   = {}
		lignes = (
			Reservation.objects.filter(check_in__gte=premier)
			.annotate(month=TruncMonth("check_in"))
			.values("month", "status")
			.annotate(n=Count("id"), total=Sum("total_amount"))
		)
		for ligne in lignes:
			cle  = (ligne["month"].year, ligne["month"].month)
			case = mensuel.setdefault(cle, {"count": 0, "revenue": 0})
			if ligne["status"] in (S.PENDING, S.ACCEPTED, S.COMPLETED):
				case["count"] += ligne["n"]
			if ligne["status"] == S.COMPLETED:
				case["revenue"] += ligne["total"] or 0
		return self.reponse({
			"total_rooms"    : Room.objects.count(),
			"active_rooms"   : actives.count(),
			"occupied_rooms" : occupe,
			"available_rooms": actives.count() - occupe,
			"customers"      : User.objects.filter(is_staff=False).count(),
			"pending"        : par_statut.get(S.PENDING, 0),
			"accepted"       : par_statut.get(S.ACCEPTED, 0),
			"refused"        : par_statut.get(S.REFUSED, 0),
			"cancelled"      : par_statut.get(S.CANCELLED, 0),
			"completed"      : par_statut.get(S.COMPLETED, 0),
			"revenue"        : Reservation.objects.filter(status=S.COMPLETED).aggregate(t=Sum("total_amount"))["t"] or 0,
			"collected"      : Payment.objects.aggregate(t=Sum("amount"))["t"] or 0,
			"balance_due"    : max(
				(Reservation.objects.filter(status__in=[S.ACCEPTED, S.COMPLETED]).aggregate(t=Sum("total_amount"))["t"] or 0)
				- (Payment.objects.filter(reservation__status__in=[S.ACCEPTED, S.COMPLETED]).aggregate(t=Sum("amount"))["t"] or 0), 0,
			),
			"monthly"        : [
				{"label": f"{MOIS[m - 1]} {a}", **mensuel.get((a, m), {"count": 0, "revenue": 0})} for a, m in mois
			],
		})
