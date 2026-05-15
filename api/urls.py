from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path("auth/register/",  views.RegisterView.as_view(),   name="register"),
    path("auth/login/",     views.LoginView.as_view(),      name="login"),
    path("auth/me/",        views.MeView.as_view(),         name="me"),
    path("auth/refresh/",   TokenRefreshView.as_view(),     name="token_refresh"),

    # DatePlan CRUD
    path("dates/",          views.DatePlanListCreateView.as_view(), name="date-list"),
    path("dates/<int:pk>/", views.DatePlanDetailView.as_view(),     name="date-detail"),
    path("dates/<int:pk>/send/", views.SendInvitationView.as_view(), name="date-send"),
]
