from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, DatePlan, DateActivity, ACTIVITY_CHOICES


class RegisterSerializer(serializers.ModelSerializer):
    password        = serializers.CharField(write_only=True, validators=[validate_password])
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
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["id", "username", "email_partner1", "email_partner2", "created_at"]


class DateActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model  = DateActivity
        fields = ["id", "activity"]


class DatePlanSerializer(serializers.ModelSerializer):
    activities = DateActivitySerializer(many=True, read_only=True)
    activity_keys = serializers.ListField(
        child=serializers.ChoiceField(choices=[c[0] for c in ACTIVITY_CHOICES]),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model  = DatePlan
        fields = [
            "id", "date", "time", "location", "excitement",
            "activities", "activity_keys",
            "email_sent", "email_sent_at", "created_at", "updated_at",
        ]
        read_only_fields = ["email_sent", "email_sent_at", "created_at", "updated_at"]

    def create(self, validated_data):
        activity_keys = validated_data.pop("activity_keys", [])
        plan = DatePlan.objects.create(**validated_data)
        for key in set(activity_keys):
            DateActivity.objects.create(date_plan=plan, activity=key)
        return plan

    def update(self, instance, validated_data):
        activity_keys = validated_data.pop("activity_keys", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if activity_keys is not None:
            instance.activities.all().delete()
            for key in set(activity_keys):
                DateActivity.objects.create(date_plan=instance, activity=key)
        return instance
