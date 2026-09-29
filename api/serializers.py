from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import User, DatePlan, DateActivity, ACTIVITY_CHOICES


# ─── Users ───────────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ["id", "username", "email_partner1", "email_partner2", "avatar", "created_at"]

    def get_avatar(self, user):
        """URL absolue de l'avatar (le front et l'API ne sont pas sur le même domaine)."""
        if not user.avatar:
            return None
        request = self.context.get("request")
        url = user.avatar.url
        return request.build_absolute_uri(url) if request else url


class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ["username", "password", "password_confirm", "email_partner1", "email_partner2"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class UpdateProfileSerializer(serializers.ModelSerializer):
    """PATCH /api/auth/me/ — modifier nom, emails, avatar"""
    class Meta:
        model  = User
        fields = ["username", "email_partner1", "email_partner2", "avatar"]
        extra_kwargs = {field: {"required": False} for field in fields}

    def validate_username(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def validate_avatar(self, value):
        if value and value.size > settings.AVATAR_MAX_SIZE:
            max_mb = settings.AVATAR_MAX_SIZE // (1024 * 1024)
            raise serializers.ValidationError(f"L'image ne doit pas dépasser {max_mb} Mo.")
        return value

    def update(self, instance, validated_data):
        old_avatar = instance.avatar.name if "avatar" in validated_data and instance.avatar else None
        instance = super().update(instance, validated_data)
        # Supprime l'ancien fichier une fois le nouveau enregistré.
        if old_avatar and old_avatar != instance.avatar.name:
            instance.avatar.storage.delete(old_avatar)
        return instance


# ─── Date plans ──────────────────────────────────────────────────────────────

class DateActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model  = DateActivity
        fields = ["id", "activity"]


class DatePlanSerializer(serializers.ModelSerializer):
    activities    = DateActivitySerializer(many=True, read_only=True)
    activity_keys = serializers.ListField(
        child=serializers.ChoiceField(choices=[c[0] for c in ACTIVITY_CHOICES]),
        write_only=True,
        required=False,
    )

    class Meta:
        model  = DatePlan
        fields = [
            "id", "date", "time", "location", "excitement",
            "activities", "activity_keys",
            "email_sent", "email_sent_at", "created_at", "updated_at",
        ]
        read_only_fields = ["email_sent", "email_sent_at", "created_at", "updated_at"]

    @staticmethod
    def _set_activities(plan, keys):
        plan.activities.all().delete()
        DateActivity.objects.bulk_create(
            DateActivity(date_plan=plan, activity=key) for key in dict.fromkeys(keys)
        )

    @transaction.atomic
    def create(self, validated_data):
        activity_keys = validated_data.pop("activity_keys", [])
        plan = DatePlan.objects.create(**validated_data)
        self._set_activities(plan, activity_keys)
        return plan

    @transaction.atomic
    def update(self, instance, validated_data):
        activity_keys = validated_data.pop("activity_keys", None)
        instance = super().update(instance, validated_data)
        if activity_keys is not None:
            self._set_activities(instance, activity_keys)
        return instance
