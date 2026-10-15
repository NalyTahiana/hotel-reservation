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
        extra["is_staff"] = True
        extra["is_superuser"] = True
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Client (is_staff=False) ou administrateur (is_staff=True)."""

    email = models.EmailField("e-mail", unique=True)
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
        return f"{self.first_name} {self.last_name} <{self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
