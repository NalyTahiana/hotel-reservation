from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.utils import timezone
from hotel.models import *


def erreurs_formulaire(formulaire):
	erreurs = {}
	for champ, liste in formulaire.errors.get_json_data().items():
		cle = "non_field_errors" if champ == "__all__" else champ
		erreurs[cle] = [e["message"] for e in liste]
	return erreurs


def valeurs_formulaire(classe, donnees, instance=None):
	champs  = [c for c in classe.base_fields if c != "image"]
	valeurs = model_to_dict(instance, fields=champs) if instance else {}
	for champ in champs:
		if champ in donnees:
			valeurs[champ] = donnees.get(champ)
	if instance is None and "is_active" in classe.base_fields:
		valeurs.setdefault("is_active", True)
	return valeurs


class FormulaireInscription(forms.Form):
	email            = forms.EmailField()
	last_name        = forms.CharField(max_length=100)
	first_name       = forms.CharField(max_length=100)
	phone            = forms.CharField(max_length=10, validators=[phone_validator])
	password         = forms.CharField(strip=False)
	password_confirm = forms.CharField(strip=False)

	def clean_email(self):
		email = self.cleaned_data["email"].strip().lower()
		if User.objects.filter(email__iexact=email).exists():
			raise ValidationError("Un compte existe déjà avec cette adresse e-mail.")
		return email

	def clean(self):
		donnees = super().clean()
		mot_de_passe = donnees.get("password")
		if mot_de_passe is None:
			return donnees
		if mot_de_passe != donnees.get("password_confirm"):
			self.add_error("password_confirm", "Les mots de passe ne correspondent pas.")
			return donnees
		candidat = User(email=donnees.get("email", ""), last_name=donnees.get("last_name", ""), first_name=donnees.get("first_name", ""))
		try:
			password_validation.validate_password(mot_de_passe, candidat)
		except ValidationError as erreur:
			self.add_error("password", erreur)
		return donnees


class FormulaireConnexion(forms.Form):
	email    = forms.EmailField()
	password = forms.CharField(strip=False)


class FormulaireFiltreDates(forms.Form):
	date_from = forms.DateField(required=False)
	date_to   = forms.DateField(required=False)


class FormulaireStatut(forms.Form):
	is_active = forms.BooleanField(required=False)


class FormulaireImage(forms.Form):
	image = forms.ImageField()


class FormulaireProfil(forms.Form):
	last_name  = forms.CharField(max_length=100)
	first_name = forms.CharField(max_length=100)
	phone      = forms.CharField(max_length=10, validators=[phone_validator])


class FormulaireChambre(forms.ModelForm):
	class Meta:
		model          = Room
		fields         = [
			"number", "name", "room_type", "short_description", "description", "capacity",
			"price_per_night", "image", "amenities", "included_services", "is_active",
		]
		error_messages = {"number": {"unique": "Une chambre porte déjà ce numéro."}}


class FormulaireService(forms.ModelForm):
	class Meta:
		model  = HotelService
		fields = ["kind", "name", "description", "image", "is_active"]


class FormulaireReservation(forms.Form):
	room      = forms.IntegerField()
	check_in  = forms.DateField()
	check_out = forms.DateField()
	guests    = forms.IntegerField(min_value=1)
	comment   = forms.CharField(required=False, max_length=1000)

	def clean(self):
		donnees = super().clean()
		arrivee, depart = donnees.get("check_in"), donnees.get("check_out")
		if arrivee and arrivee < timezone.localdate():
			self.add_error("check_in", "La date d'arrivée ne peut pas être dans le passé.")
		elif arrivee and depart and arrivee >= depart:
			self.add_error("check_out", "La date de départ doit être postérieure à la date d'arrivée.")
		return donnees


class FormulairePaiement(forms.Form):
	amount = forms.IntegerField(min_value=1)
	note   = forms.CharField(required=False, max_length=255)


class FormulaireClientHotel(forms.Form):
	last_name  = forms.CharField(max_length=100)
	first_name = forms.CharField(max_length=100)
	phone      = forms.CharField(max_length=10, validators=[phone_validator])
	room       = forms.IntegerField()
	check_in   = forms.DateField()
	check_out  = forms.DateField()
	guests     = forms.IntegerField(min_value=1, required=False)

	def clean(self):
		donnees = super().clean()
		arrivee, depart = donnees.get("check_in"), donnees.get("check_out")
		if arrivee and depart and depart <= arrivee:
			self.add_error("check_out", "La date de départ doit être postérieure à la date d'arrivée.")
		return donnees


class FormulaireDisponibilite(forms.Form):
	check_in  = forms.DateField(required=False)
	check_out = forms.DateField(required=False)
	guests    = forms.IntegerField(required=False, min_value=1)

	def clean(self):
		donnees = super().clean()
		arrivee, depart = donnees.get("check_in"), donnees.get("check_out")
		if bool(arrivee) != bool(depart):
			raise ValidationError("Indiquez la date d'arrivée et la date de départ.")
		if arrivee and depart and arrivee >= depart:
			raise ValidationError("La date d'arrivée doit être antérieure à la date de départ.")
		return donnees
