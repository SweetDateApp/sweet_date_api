from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import send_invitation_emails
from .models import User, DatePlan
from .serializers import DatePlanSerializer, RegisterSerializer, UpdateProfileSerializer, UserSerializer


def auth_payload(user, request):
    refresh = RefreshToken.for_user(user)
    return {
        "user":   UserSerializer(user, context={"request": request}).data,
        "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
    }


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/  — Créer un compte avec 2 emails partenaires"""
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(auth_payload(user, request), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/  — Connexion, retourne JWT"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))

        if not username or not password:
            return Response({"detail": "Identifiant et mot de passe requis."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(username=username).first()
        if user is None or not user.check_password(password):
            return Response({"detail": "Identifiant ou mot de passe incorrect."},
                            status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({"detail": "Compte désactivé."}, status=status.HTTP_403_FORBIDDEN)

        return Response(auth_payload(user, request))


class MeView(generics.RetrieveUpdateAPIView):
    """GET /api/auth/me/    — Profil de l'utilisateur connecté
       PATCH /api/auth/me/  — Modifier nom, emails, avatar (multipart/form-data pour l'avatar)"""
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        return UpdateProfileSerializer if self.request.method == "PATCH" else UserSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context=self.get_serializer_context()).data)


# ─── DatePlan ────────────────────────────────────────────────────────────────

class DatePlanQuerysetMixin:
    serializer_class = DatePlanSerializer

    def get_queryset(self):
        return DatePlan.objects.filter(user=self.request.user).prefetch_related("activities")


class DatePlanListCreateView(DatePlanQuerysetMixin, generics.ListCreateAPIView):
    """GET /api/dates/   — Lister ses plans
       POST /api/dates/  — Créer un plan (avec activity_keys)"""

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DatePlanDetailView(DatePlanQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    """GET / PATCH / DELETE /api/dates/<id>/"""
    http_method_names = ["get", "patch", "delete", "head", "options"]


class SendInvitationView(DatePlanQuerysetMixin, generics.GenericAPIView):
    """POST /api/dates/<id>/send/  — Envoyer l'invitation email aux 2 partenaires"""

    def post(self, request, pk):
        plan = self.get_object()
        user = request.user

        if plan.email_sent:
            return Response({
                "detail":  "L'invitation a déjà été envoyée.",
                "plan":    DatePlanSerializer(plan).data,
                "sent_to": [user.email_partner1, user.email_partner2],
            })

        if not send_invitation_emails(plan):
            return Response(
                {"detail": "Erreur lors de l'envoi de l'email. Vérifiez la configuration SMTP."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({
            "detail":  "Invitation envoyée avec succès aux 2 partenaires 💗",
            "plan":    DatePlanSerializer(plan).data,
            "sent_to": [user.email_partner1, user.email_partner2],
        })
