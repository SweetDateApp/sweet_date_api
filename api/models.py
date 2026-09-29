from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, username, password, email_partner1, email_partner2, **extra):
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire")
        user = self.model(
            username=username,
            email_partner1=email_partner1,
            email_partner2=email_partner2,
            **extra,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra):
        extra.setdefault("email_partner1", "admin@example.com")
        extra.setdefault("email_partner2", "admin2@example.com")
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    username        = models.CharField(max_length=150, unique=True)
    email_partner1  = models.EmailField(help_text="Email du 1er partenaire")
    email_partner2  = models.EmailField(help_text="Email du 2eme partenaire")
    avatar          = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    is_staff        = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD  = "username"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username


ACTIVITY_CHOICES = [
    ("walk",   "Se promener"),
    ("movie",  "Regarder un film"),
    ("meal",   "Diner ensemble"),
    ("game",   "Jouer ensemble"),
    ("other",  "Autre chose"),
    ("photos", "Prendre des photos"),
]


class DatePlan(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="date_plans")
    date        = models.DateField()
    time        = models.TimeField(null=True, blank=True)
    location    = models.CharField(max_length=255, blank=True)
    excitement  = models.PositiveSmallIntegerField(default=0)
    email_sent  = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "date_plans"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class DateActivity(models.Model):
    date_plan   = models.ForeignKey(DatePlan, on_delete=models.CASCADE, related_name="activities")
    activity    = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)

    class Meta:
        db_table = "date_activities"
        unique_together = ("date_plan", "activity")
