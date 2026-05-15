from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, DatePlan
from .serializers import RegisterSerializer, UserSerializer, DatePlanSerializer
from .emails import send_invitation_emails


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/  — Créer un compte avec 2 emails partenaires"""
    queryset         = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user":    UserSerializer(user).data,
            "tokens": {
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
            },
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/  — Connexion, retourne JWT"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not username or not password:
            return Response(
                {"detail": "Identifiant et mot de passe requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"detail": "Identifiant ou mot de passe incorrect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.check_password(password):
            return Response(
                {"detail": "Identifiant ou mot de passe incorrect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"detail": "Compte désactivé."},
                status=status.HTTP_403_FORBIDDEN,
            )
        refresh = RefreshToken.for_user(user)
        return Response({
            "user":   UserSerializer(user).data,
            "tokens": {
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
            },
        })


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/  — Profil de l'utilisateur connecté"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ─── DatePlan ────────────────────────────────────────────────────────────────

class DatePlanListCreateView(generics.ListCreateAPIView):
    """GET /api/dates/        — Lister ses plans
       POST /api/dates/       — Créer un plan"""
    serializer_class   = DatePlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DatePlan.objects.filter(user=self.request.user).prefetch_related("activities")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DatePlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/dates/<id>/"""
    serializer_class   = DatePlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DatePlan.objects.filter(user=self.request.user).prefetch_related("activities")


class SendInvitationView(APIView):
    """POST /api/dates/<id>/send/  — Envoyer l'invitation email aux 2 partenaires"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            plan = DatePlan.objects.prefetch_related("activities").get(pk=pk, user=request.user)
        except DatePlan.DoesNotExist:
            return Response({"detail": "Plan introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if plan.email_sent:
            return Response(
                {"detail": "L'invitation a déjà été envoyée.", "email_sent_at": plan.email_sent_at},
                status=status.HTTP_200_OK,
            )

        success = send_invitation_emails(plan)
        if success:
            return Response({
                "detail": "Invitation envoyée avec succès aux 2 partenaires 💗",
                "sent_to": [request.user.email_partner1, request.user.email_partner2],
            })
        return Response(
            {"detail": "Erreur lors de l'envoi de l'email. Vérifiez la configuration SMTP."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
