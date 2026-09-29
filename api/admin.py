from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from .models import User, DatePlan, DateActivity


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model  = User
        fields = ["username", "email_partner1", "email_partner2"]


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model  = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form            = UserChangeForm
    add_form        = UserCreationForm
    ordering        = ["-created_at"]
    list_display    = ["username", "email_partner1", "email_partner2", "is_active", "is_staff", "created_at"]
    list_filter     = ["is_active", "is_staff"]
    search_fields   = ["username", "email_partner1", "email_partner2"]
    readonly_fields = ["created_at", "last_login"]
    fieldsets = [
        (None,          {"fields": ["username", "password"]}),
        ("Partenaires", {"fields": ["email_partner1", "email_partner2", "avatar"]}),
        ("Permissions", {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
        ("Dates",       {"fields": ["created_at", "last_login"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["username", "email_partner1", "email_partner2", "password1", "password2"]}),
    ]


class DateActivityInline(admin.TabularInline):
    model = DateActivity
    extra = 0


@admin.register(DatePlan)
class DatePlanAdmin(admin.ModelAdmin):
    list_display  = ["id", "user", "date", "time", "location", "excitement", "email_sent", "created_at"]
    list_filter   = ["email_sent", "date"]
    search_fields = ["user__username", "location"]
    inlines       = [DateActivityInline]
