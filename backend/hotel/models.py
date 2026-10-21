import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models import F, Q
from django.utils import timezone

phone_validator = RegexValidator(
	regex   = r"\A[0-9]{10}\Z",
	message = "Le numéro de téléphone doit comporter exactement 10 chiffres.",
)

NO_EMAIL_DOMAIN = "sans-email.invalid"

MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


class ErreurMetier(Exception):
	def __init__(self, contenu, statut=400):
		super().__init__(str(contenu))
		self.contenu = contenu
		self.statut  = statut


def en_ariary(montant):
	return f"{int(montant):,}".replace(",", " ") + " Ar"


def url_fichier(fichier, requete=None):
	if not fichier:
		return None
	return requete.build_absolute_uri(fichier.url) if requete else fichier.url


def lignes(texte):
	return [ligne.strip() for ligne in (texte or "").splitlines() if ligne.strip()]


class UserManager(BaseUserManager):
	use_in_migrations = True

	def _create_user(self, email, password, **extra):
		if not email:
			raise ValueError("L'adresse e-mail est obligatoire.")
		user = self.model(email=self.normalize_email(email).lower(), **extra)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email, password=None, **extra):
		extra.setdefault("is_staff", False)
		extra.setdefault("is_superuser", False)
		return self._create_user(email, password, **extra)

	def create_superuser(self, email, password=None, **extra):
		extra["is_staff"]     = True
		extra["is_superuser"] = True
		return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
	email       = models.EmailField("e-mail", unique=True)
	last_name   = models.CharField("nom", max_length=100)
	first_name  = models.CharField("prénom", max_length=100)
	phone       = models.CharField("téléphone", max_length=10, validators=[phone_validator])
	is_active   = models.BooleanField("compte actif", default=True)
	is_staff    = models.BooleanField("administrateur", default=False)
	date_joined = models.DateTimeField("date de création", default=timezone.now)

	objects        = UserManager()
	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = ["last_name", "first_name", "phone"]

	class Meta:
		ordering = ["-date_joined"]

	def __str__(self):
		return f"{self.first_name} {self.last_name} <{self.email}>"

	@property
	def contact_email(self):
		return "" if self.email.endswith("@" + NO_EMAIL_DOMAIN) else self.email

	@property
	def full_name(self):
		return f"{self.first_name} {self.last_name}".strip()

	def en_json(self):
		return {
			"id"         : self.id,
			"email"      : self.email,
			"last_name"  : self.last_name,
			"first_name" : self.first_name,
			"phone"      : self.phone,
			"is_staff"   : self.is_staff,
			"date_joined": timezone.localtime(self.date_joined).isoformat(),
		}

	def en_json_client(self):
		nombre = getattr(self, "reservations_count", None)
		if nombre is None:
			nombre = self.reservations.count()
		return {
			"id"                : self.id,
			"email"             : self.contact_email,
			"last_name"         : self.last_name,
			"first_name"        : self.first_name,
			"phone"             : self.phone,
			"is_active"         : self.is_active,
			"date_joined"       : timezone.localtime(self.date_joined).isoformat(),
			"reservations_count": nombre,
		}


class Room(models.Model):
	class RoomType(models.TextChoices):
		SINGLE = "simple", "Simple"
		DOUBLE = "double", "Double"
		FAMILY = "familiale", "Familiale"
		SUITE  = "suite", "Suite"

	number            = models.CharField("numéro", max_length=20, unique=True)
	name              = models.CharField("nom", max_length=150)
	room_type         = models.CharField("type", max_length=20, choices=RoomType.choices, default=RoomType.DOUBLE)
	short_description = models.CharField("description courte", max_length=255, blank=True)
	description       = models.TextField("description complète", blank=True)
	capacity          = models.PositiveSmallIntegerField("capacité maximale", validators=[MinValueValidator(1)])
	price_per_night   = models.PositiveIntegerField("prix par nuit (Ar)", validators=[MinValueValidator(1)])
	image             = models.ImageField("photo principale", upload_to="rooms/", blank=True, null=True)
	amenities         = models.TextField("équipements (un par ligne)", blank=True)
	included_services = models.TextField("services inclus (un par ligne)", blank=True)
	is_active         = models.BooleanField("active", default=True)
	created_at        = models.DateTimeField(auto_now_add=True)
	updated_at        = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["number"]

	def __str__(self):
		return f"{self.number} - {self.name}"

	def en_json(self, requete=None):
		return {
			"id"               : self.id,
			"number"           : self.number,
			"name"             : self.name,
			"room_type"        : self.room_type,
			"room_type_display": self.get_room_type_display(),
			"short_description": self.short_description,
			"description"      : self.description,
			"capacity"         : self.capacity,
			"price_per_night"  : self.price_per_night,
			"image"            : url_fichier(self.image, requete),
			"images"           : [{"id": i.id, "image": url_fichier(i.image, requete)} for i in self.images.all()],
			"amenities"        : self.amenities,
			"amenities_list"   : lignes(self.amenities),
			"included_services": self.included_services,
			"services_list"    : lignes(self.included_services),
			"is_active"        : self.is_active,
			"created_at"       : timezone.localtime(self.created_at).isoformat(),
		}

	def en_json_libre(self):
		return {
			"id"               : self.id,
			"number"           : self.number,
			"name"             : self.name,
			"room_type_display": self.get_room_type_display(),
			"capacity"         : self.capacity,
			"price_per_night"  : self.price_per_night,
		}


class RoomImage(models.Model):
	room       = models.ForeignKey("Room", on_delete=models.CASCADE, related_name="images")
	image      = models.ImageField(upload_to="rooms/gallery/")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["id"]


class HotelService(models.Model):
	class Kind(models.TextChoices):
		SERVICE  = "service", "Service"
		ACTIVITY = "activity", "Activité"

	kind        = models.CharField("catégorie", max_length=10, choices=Kind.choices, default=Kind.SERVICE)
	name        = models.CharField("nom", max_length=150)
	description = models.TextField("description", blank=True)
	image       = models.ImageField("photo", upload_to="services/", blank=True, null=True)
	is_active   = models.BooleanField("actif", default=True)
	created_at  = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["kind", "name"]

	def __str__(self):
		return self.name

	def en_json(self, requete=None):
		return {
			"id"          : self.id,
			"kind"        : self.kind,
			"kind_display": self.get_kind_display(),
			"name"        : self.name,
			"description" : self.description,
			"image"       : url_fichier(self.image, requete),
			"is_active"   : self.is_active,
			"created_at"  : timezone.localtime(self.created_at).isoformat(),
		}


def generate_reference():
	return "RSV-" + uuid.uuid4().hex[:8].upper()


class Reservation(models.Model):
	class Status(models.TextChoices):
		PENDING   = "pending", "En attente"
		ACCEPTED  = "accepted", "Acceptée"
		REFUSED   = "refused", "Refusée"
		CANCELLED = "cancelled", "Annulée"
		COMPLETED = "completed", "Terminée"

	reference       = models.CharField("référence", max_length=20, unique=True, default=generate_reference, editable=False)
	customer        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservations")
	room            = models.ForeignKey("Room", on_delete=models.PROTECT, related_name="reservations")
	check_in        = models.DateField("date d'arrivée")
	check_out       = models.DateField("date de départ")
	guests          = models.PositiveSmallIntegerField("nombre de personnes")
	price_per_night = models.PositiveIntegerField("prix par nuit (Ar)")
	nights          = models.PositiveSmallIntegerField("nombre de nuits")
	total_amount    = models.PositiveBigIntegerField("montant total (Ar)")
	status          = models.CharField("statut", max_length=12, choices=Status.choices, default=Status.PENDING)
	comment         = models.TextField("commentaire", blank=True)
	created_at      = models.DateTimeField(auto_now_add=True)
	updated_at      = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["room", "status", "check_in", "check_out"], name="resa_room_period_idx"),
			models.Index(fields=["status", "created_at"], name="resa_status_created_idx"),
		]
		constraints = [
			models.CheckConstraint(check=Q(check_out__gt=F("check_in")), name="resa_checkout_after_checkin"),
		]

	def __str__(self):
		return f"{self.reference} ({self.get_status_display()})"

	def en_json(self, requete=None):
		client = self.customer
		chambre = self.room
		return {
			"id"             : self.id,
			"reference"      : self.reference,
			"customer"       : {"id": client.id, "full_name": client.full_name, "email": client.contact_email, "phone": client.phone},
			"room"           : {
				"id": chambre.id, "number": chambre.number, "name": chambre.name,
				"room_type": chambre.room_type, "image": url_fichier(chambre.image, requete),
			},
			"check_in"       : self.check_in.isoformat(),
			"check_out"      : self.check_out.isoformat(),
			"guests"         : self.guests,
			"price_per_night": self.price_per_night,
			"nights"         : self.nights,
			"total_amount"   : self.total_amount,
			"status"         : self.status,
			"status_display" : self.get_status_display(),
			"comment"        : self.comment,
			"amount_paid"    : self.montant_paye,
			"balance"        : self.reste_a_payer,
			"payment_status" : self.statut_paiement,
			"payments"       : [p.en_json() for p in self.payments.all()],
			"actions"        : self.actions_permises(requete.user) if requete else [],
			"created_at"     : timezone.localtime(self.created_at).isoformat(),
			"updated_at"     : timezone.localtime(self.updated_at).isoformat(),
		}

	@property
	def numero_facture(self):
		return "FAC-" + self.reference.split("-", 1)[-1]

	def en_json_facture(self):
		paiements = list(self.payments.all())
		client = self.customer
		chambre = self.room
		return {
			"number"        : self.numero_facture,
			"issued_at"     : timezone.localtime(paiements[-1].created_at).isoformat() if paiements else None,
			"reference"     : self.reference,
			"status"        : self.status,
			"customer"      : {"full_name": client.full_name, "email": client.contact_email, "phone": client.phone},
			"room"          : {"number": chambre.number, "name": chambre.name, "room_type": chambre.get_room_type_display()},
			"check_in"      : self.check_in.isoformat(),
			"check_out"     : self.check_out.isoformat(),
			"guests"        : self.guests,
			"nights"        : self.nights,
			"price_per_night": self.price_per_night,
			"total_amount"  : self.total_amount,
			"amount_paid"   : self.montant_paye,
			"balance"       : self.reste_a_payer,
			"payment_status": self.statut_paiement,
			"payments"      : [p.en_json() for p in paiements],
		}

	def details(self):
		return (
			f"Chambre n° {self.room.number} ({self.room.name}), du {self.check_in:%d/%m/%Y} au {self.check_out:%d/%m/%Y} "
			f"({self.nights} nuit(s)), {self.guests} personne(s), prix par nuit {en_ariary(self.price_per_night)}, "
			f"total {en_ariary(self.total_amount)}."
		)

	@property
	def montant_paye(self):
		return sum(p.amount for p in self.payments.all())

	@property
	def reste_a_payer(self):
		return max(self.total_amount - self.montant_paye, 0)

	@property
	def statut_paiement(self):
		paye = self.montant_paye
		if paye <= 0:
			return "unpaid"
		return "paid" if paye >= self.total_amount else "partial"

	@classmethod
	def chevauchantes(cls, room_id, check_in, check_out, exclure=None):
		resultat = cls.objects.filter(
			room_id=room_id, status__in=BLOQUANTS, check_in__lt=check_out, check_out__gt=check_in,
		)
		if exclure is not None:
			resultat = resultat.exclude(pk=exclure)
		return resultat

	@classmethod
	def chambre_disponible(cls, room_id, check_in, check_out, exclure=None):
		return not cls.chevauchantes(room_id, check_in, check_out, exclure).exists()

	@classmethod
	def chambres_libres(cls, chambres, check_in, check_out):
		occupees = cls.objects.filter(
			status__in=BLOQUANTS, check_in__lt=check_out, check_out__gt=check_in,
		).values("room_id")
		return chambres.exclude(pk__in=occupees)

	@classmethod
	def terminer_passees(cls):
		aujourdhui = timezone.localdate()
		return cls.objects.filter(status=cls.Status.ACCEPTED, check_out__lte=aujourdhui).update(status=cls.Status.COMPLETED)

	@classmethod
	@transaction.atomic
	def creer(cls, *, client, room_id, check_in, check_out, guests, comment="", par_admin=False):
		try:
			chambre = Room.objects.select_for_update().get(pk=room_id)
		except Room.DoesNotExist:
			raise ErreurMetier({"room": ["Cette chambre n'existe pas."]})
		if not chambre.is_active:
			raise ErreurMetier({"room": ["Cette chambre n'est pas disponible à la réservation."]})
		if check_in < timezone.localdate():
			raise ErreurMetier({"check_in": ["La date d'arrivée ne peut pas être dans le passé."]})
		if check_out <= check_in:
			raise ErreurMetier({"check_out": ["La date de départ doit être postérieure à la date d'arrivée."]})
		if guests > chambre.capacity:
			raise ErreurMetier({"guests": [f"Cette chambre accueille au maximum {chambre.capacity} personne(s)."]})
		if not cls.chambre_disponible(chambre.pk, check_in, check_out):
			raise ErreurMetier(
				{"detail": "Cette chambre n'est pas disponible pour les dates choisies. Choisissez d'autres dates ou une autre chambre."},
				409,
			)
		nuits = (check_out - check_in).days
		reservation = cls.objects.create(
			customer=client, room=chambre, check_in=check_in, check_out=check_out, guests=guests,
			price_per_night=chambre.price_per_night, nights=nuits, total_amount=nuits * chambre.price_per_night,
			status=cls.Status.ACCEPTED if par_admin else cls.Status.PENDING, comment=comment or "",
		)
		if not par_admin:
			Notification.nouvelle_reservation(reservation)
		return reservation

	@classmethod
	@transaction.atomic
	def encaisser(cls, *, reservation_id, montant, note, acteur):
		try:
			reservation = cls.objects.select_for_update().get(pk=reservation_id)
		except cls.DoesNotExist:
			raise ErreurMetier({"detail": "Réservation introuvable."}, 404)
		if reservation.status not in (cls.Status.ACCEPTED, cls.Status.COMPLETED):
			raise ErreurMetier(
				{"detail": "Un paiement ne peut être enregistré que pour une réservation acceptée ou terminée."}, 409,
			)
		reste = reservation.reste_a_payer
		if reste <= 0:
			raise ErreurMetier({"detail": "Cette réservation est déjà payée en totalité."}, 409)
		if montant > reste:
			raise ErreurMetier({"amount": [f"Le montant dépasse le reste à payer ({en_ariary(reste)})."]})
		paiement = Payment.objects.create(reservation=reservation, amount=montant, note=note or "", received_by=acteur)
		reservation = cls.objects.prefetch_related("payments").select_related("room", "customer").get(pk=reservation.pk)
		Notification.paiement(reservation, paiement)
		return reservation

	def actions_permises(self, utilisateur):
		aujourdhui = timezone.localdate()
		if self.status == self.Status.PENDING:
			return ["accept", "refuse", "cancel"] if utilisateur.is_staff else ["cancel"]
		if self.status == self.Status.ACCEPTED:
			if utilisateur.is_staff:
				return ["cancel"]
			return ["cancel"] if self.check_in > aujourdhui else []
		return []

	@classmethod
	@transaction.atomic
	def appliquer(cls, *, reservation_id, action, acteur):
		S = cls.Status
		cibles = {"accept": S.ACCEPTED, "refuse": S.REFUSED, "cancel": S.CANCELLED}
		transitions = {
			S.PENDING  : {S.ACCEPTED, S.REFUSED, S.CANCELLED},
			S.ACCEPTED : {S.CANCELLED, S.COMPLETED},
			S.REFUSED  : set(),
			S.CANCELLED: set(),
			S.COMPLETED: set(),
		}
		cible = cibles.get(action)
		if cible is None:
			raise ErreurMetier({"detail": "Action inconnue."})
		try:
			reservation = cls.objects.select_for_update().get(pk=reservation_id)
		except cls.DoesNotExist:
			raise ErreurMetier({"detail": "Réservation introuvable."}, 404)
		Room.objects.select_for_update().get(pk=reservation.room_id)
		if cible == S.CANCELLED and not acteur.is_staff and reservation.montant_paye > 0:
			raise ErreurMetier(
				{"detail": "Un paiement a déjà été enregistré pour cette réservation : contactez l'hôtel pour l'annuler."}, 409,
			)
		if action not in reservation.actions_permises(acteur) or cible not in transitions[reservation.status]:
			raise ErreurMetier(
				{"detail": f"Impossible de passer une réservation « {reservation.get_status_display()} » à l'action « {action} »."},
				409,
			)
		if cible == S.ACCEPTED:
			if reservation.check_in < timezone.localdate():
				raise ErreurMetier({"detail": "La date d'arrivée est dépassée : cette demande ne peut plus être acceptée."}, 409)
			if not cls.chambre_disponible(reservation.room_id, reservation.check_in, reservation.check_out, exclure=reservation.pk):
				raise ErreurMetier({"detail": "Une autre réservation occupe déjà cette chambre sur cette période : acceptation impossible."}, 409)
		reservation.status = cible
		reservation.save(update_fields=["status", "updated_at"])
		if acteur.is_staff:
			Notification.decision_admin(reservation, cible)
		else:
			Notification.annulation_client(reservation)
		return reservation


BLOQUANTS = [Reservation.Status.PENDING, Reservation.Status.ACCEPTED]


class Payment(models.Model):
	reservation = models.ForeignKey("Reservation", on_delete=models.CASCADE, related_name="payments")
	amount      = models.PositiveBigIntegerField("montant payé (Ar)", validators=[MinValueValidator(1)])
	note        = models.CharField("note", max_length=255, blank=True)
	received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments_received")
	created_at  = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["created_at", "id"]

	def __str__(self):
		return f"{self.reservation.reference} - {en_ariary(self.amount)}"

	def en_json(self):
		return {
			"id"        : self.id,
			"receipt"   : f"REC-{self.id:06d}",
			"amount"    : self.amount,
			"method"    : "Espèces",
			"note"      : self.note,
			"created_at": timezone.localtime(self.created_at).isoformat(),
		}


class Notification(models.Model):
	class Kind(models.TextChoices):
		NEW_RESERVATION = "new_reservation", "Nouvelle demande"
		ACCEPTED        = "accepted", "Réservation acceptée"
		REFUSED         = "refused", "Réservation refusée"
		CANCELLED       = "cancelled", "Réservation annulée"
		PAYMENT         = "payment", "Paiement enregistré"

	user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
	kind        = models.CharField(max_length=20, choices=Kind.choices)
	title       = models.CharField(max_length=150)
	message     = models.TextField()
	reservation = models.ForeignKey("Reservation", null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications")
	is_read     = models.BooleanField(default=False)
	created_at  = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at", "-id"]
		indexes = [models.Index(fields=["user", "is_read"], name="notif_user_read_idx")]

	def __str__(self):
		return f"{self.user_id} - {self.title}"

	def en_json(self):
		return {
			"id"         : self.id,
			"kind"       : self.kind,
			"title"      : self.title,
			"message"    : self.message,
			"reservation": self.reservation_id,
			"is_read"    : self.is_read,
			"created_at" : timezone.localtime(self.created_at).isoformat(),
		}

	@classmethod
	def vers_administrateurs(cls, reservation, kind, titre, texte):
		cls.objects.bulk_create([
			cls(user=a, kind=kind, title=titre, message=texte, reservation=reservation)
			for a in User.objects.filter(is_staff=True, is_active=True)
		])

	@classmethod
	def nouvelle_reservation(cls, r):
		texte = f"{r.customer.full_name} a demandé la réservation {r.reference}. {r.details()}"
		cls.vers_administrateurs(r, cls.Kind.NEW_RESERVATION, "Nouvelle demande de réservation", texte)

	@classmethod
	def annulation_client(cls, r):
		texte = f"{r.customer.full_name} a annulé la réservation {r.reference}. {r.details()}"
		cls.vers_administrateurs(r, cls.Kind.CANCELLED, "Réservation annulée par le client", texte)

	@classmethod
	def paiement(cls, r, paiement):
		if r.reste_a_payer <= 0:
			fin = "Votre réservation est payée en totalité."
		else:
			fin = f"Reste à payer : {en_ariary(r.reste_a_payer)}."
		texte = f"Paiement en espèces de {en_ariary(paiement.amount)} reçu pour la réservation {r.reference}. {fin}"
		cls.objects.create(user=r.customer, kind=cls.Kind.PAYMENT, title="Paiement enregistré", message=texte, reservation=r)

	@classmethod
	def decision_admin(cls, r, statut):
		if statut == "accepted":
			kind, titre = cls.Kind.ACCEPTED, "Réservation acceptée"
			texte = f"L'administrateur a accepté votre demande de réservation {r.reference}. {r.details()}"
		elif statut == "refused":
			kind, titre = cls.Kind.REFUSED, "Réservation refusée"
			texte = f"L'administrateur a refusé votre demande de réservation {r.reference}. {r.details()}"
		else:
			kind, titre = cls.Kind.CANCELLED, "Réservation annulée"
			texte = f"L'administrateur a annulé votre réservation {r.reference}. {r.details()}"
		cls.objects.create(user=r.customer, kind=kind, title=titre, message=texte, reservation=r)
