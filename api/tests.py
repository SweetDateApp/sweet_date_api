import io
import shutil
import tempfile

from django.core import mail
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase as BaseAPITestCase

from .models import DatePlan, User

PASSWORD = "Sweet-Test-2026!"
MEDIA_ROOT = tempfile.mkdtemp()


# Avec DEBUG=false (CI, prod), SECURE_SSL_REDIRECT redirige les requêtes HTTP du client de test en 301.
@override_settings(SECURE_SSL_REDIRECT=False)
class APITestCase(BaseAPITestCase):
    pass


def make_user(username="alice", **extra):
    return User.objects.create_user(
        username=username, password=PASSWORD,
        email_partner1=f"{username}1@example.com", email_partner2=f"{username}2@example.com", **extra,
    )


def png_file(name="avatar.png"):
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buf, "PNG")
    buf.seek(0)
    buf.name = name
    return buf


class AuthTests(APITestCase):
    def test_register_returns_user_and_tokens(self):
        res = self.client.post("/api/auth/register/", {
            "username": "bob", "password": PASSWORD, "password_confirm": PASSWORD,
            "email_partner1": "a@example.com", "email_partner2": "b@example.com",
        }, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["user"]["username"], "bob")
        self.assertIn("access", res.data["tokens"])
        self.assertTrue(User.objects.get(username="bob").check_password(PASSWORD))

    def test_register_rejects_mismatched_passwords(self):
        res = self.client.post("/api/auth/register/", {
            "username": "bob", "password": PASSWORD, "password_confirm": "other-password",
            "email_partner1": "a@example.com", "email_partner2": "b@example.com",
        }, format="json")
        self.assertEqual(res.status_code, 400)

    def test_login(self):
        make_user()
        ok = self.client.post("/api/auth/login/", {"username": "alice", "password": PASSWORD}, format="json")
        bad = self.client.post("/api/auth/login/", {"username": "alice", "password": "nope"}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertIn("refresh", ok.data["tokens"])
        self.assertEqual(bad.status_code, 401)

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ProfileTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(self.user)

    def test_update_profile_fields(self):
        res = self.client.patch("/api/auth/me/", {"username": "alice2"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["username"], "alice2")

    def test_username_must_be_unique(self):
        make_user("taken")
        res = self.client.patch("/api/auth/me/", {"username": "taken"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_avatar_upload_returns_absolute_url_and_replaces_old_file(self):
        first = self.client.patch("/api/auth/me/", {"avatar": png_file("Copie d'écran.png")}, format="multipart")
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.data["avatar"].startswith("http://testserver/media/avatars/"))
        old_name = User.objects.get(pk=self.user.pk).avatar.name

        second = self.client.patch("/api/auth/me/", {"avatar": png_file()}, format="multipart")
        self.assertEqual(second.status_code, 200)
        user = User.objects.get(pk=self.user.pk)
        self.assertNotEqual(user.avatar.name, old_name)
        self.assertFalse(user.avatar.storage.exists(old_name))

        self.assertTrue(user.avatar.storage.exists(user.avatar.name))

    def test_avatar_rejects_non_image(self):
        bad = io.BytesIO(b"not an image")
        bad.name = "evil.png"
        res = self.client.patch("/api/auth/me/", {"avatar": bad}, format="multipart")
        self.assertEqual(res.status_code, 400)


class DatePlanTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(self.user)

    def create_plan(self, **data):
        payload = {"date": "2026-11-20", "time": "18:45", "location": "Lac Anosy",
                   "excitement": 80, "activity_keys": ["movie", "meal", "movie"], **data}
        return self.client.post("/api/dates/", payload, format="json")

    def test_create_plan_with_activities(self):
        res = self.create_plan()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(sorted(a["activity"] for a in res.data["activities"]), ["meal", "movie"])
        self.assertEqual(res.data["excitement"], 80)

    def test_create_plan_minimal(self):
        res = self.client.post("/api/dates/", {"date": "2026-11-20"}, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertIsNone(res.data["time"])

    def test_invalid_activity_and_excitement_rejected(self):
        self.assertEqual(self.create_plan(activity_keys=["skydiving"]).status_code, 400)
        self.assertEqual(self.create_plan(excitement=150).status_code, 400)

    def test_update_replaces_activities(self):
        plan_id = self.create_plan().data["id"]
        res = self.client.patch(f"/api/dates/{plan_id}/", {"activity_keys": ["walk"]}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual([a["activity"] for a in res.data["activities"]], ["walk"])

    def test_update_without_activity_keys_keeps_activities(self):
        plan_id = self.create_plan().data["id"]
        res = self.client.patch(f"/api/dates/{plan_id}/", {"location": "Ivato"}, format="json")
        self.assertEqual(len(res.data["activities"]), 2)

    def test_users_only_see_their_own_plans(self):
        plan_id = self.create_plan().data["id"]
        self.client.force_authenticate(make_user("eve"))
        self.assertEqual(self.client.get("/api/dates/").data, [])
        self.assertEqual(self.client.get(f"/api/dates/{plan_id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/dates/{plan_id}/").status_code, 404)

    def test_delete_plan(self):
        plan_id = self.create_plan().data["id"]
        self.assertEqual(self.client.delete(f"/api/dates/{plan_id}/").status_code, 204)
        self.assertFalse(DatePlan.objects.filter(pk=plan_id).exists())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class InvitationTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_authenticate(self.user)
        self.plan_id = self.client.post("/api/dates/", {
            "date": "2026-11-20", "time": "18:45", "location": "<b>Lac</b>", "activity_keys": ["walk"],
        }, format="json").data["id"]

    def test_send_invitation_to_both_partners_once(self):
        res = self.client.post(f"/api/dates/{self.plan_id}/send/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["plan"]["email_sent"])
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ["alice1@example.com", "alice2@example.com"])
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn("Vendredi 20 novembre 2026", html)
        self.assertIn("&lt;b&gt;Lac&lt;/b&gt;", html)

        again = self.client.post(f"/api/dates/{self.plan_id}/send/")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_HOST="invalid.localhost", EMAIL_PORT=1, EMAIL_TIMEOUT=1)
    def test_send_failure_reports_error_and_keeps_plan_unsent(self):
        res = self.client.post(f"/api/dates/{self.plan_id}/send/")
        self.assertEqual(res.status_code, 502)
        self.assertFalse(DatePlan.objects.get(pk=self.plan_id).email_sent)
