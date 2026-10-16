from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

phone_validator = RegexValidator(
    regex=r"\A[0-9]{10}\Z",
    message="Le numéro de téléphone doit comporter exactement 10 chiffres.",
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        # E-mail optionnel : un client venu à l'hôtel est enregistré sans e-mail ni mot de passe.
        email = self.normalize_email(email).lower() if email else None
        if (extra.get("is_staff") or extra.get("is_superuser")) and not email:
            raise ValueError("L'adresse e-mail est obligatoire pour un administrateur.")
        user = self.model(email=email, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # compte sans connexion possible
        user.save(using=self._db)
        return user

    def create_walkin_customer(self, *, last_name, first_name, phone, email=None):
        """Client enregistré à la réception : e-mail facultatif, jamais de mot de passe."""
        return self._create_user(email or None, None, last_name=last_name, first_name=first_name, phone=phone)

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra["is_staff"] = True
        extra["is_superuser"] = True
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Client (is_staff=False) ou administrateur (is_staff=True)."""

    # Unique mais facultatif (NULL autorisé plusieurs fois) : clients enregistrés à la réception.
    email = models.EmailField("e-mail", unique=True, null=True, blank=True)
    last_name = models.CharField("nom", max_length=100)
    first_name = models.CharField("prénom", max_length=100)
    phone = models.CharField("téléphone", max_length=10, validators=[phone_validator])
    is_active = models.BooleanField("compte actif", default=True)
    is_staff = models.BooleanField("administrateur", default=False)
    date_joined = models.DateTimeField("date de création", default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["last_name", "first_name", "phone"]

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>" if self.email else f"{self.first_name} {self.last_name} ({self.phone})"

    @property
    def can_login(self):
        return bool(self.email) and self.has_usable_password()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
