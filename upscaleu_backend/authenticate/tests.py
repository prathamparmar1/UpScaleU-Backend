from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class RegisterAndLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user(self):
        resp = self.client.post(
            "/api/auth/register/",
            {"username": "newstudent", "email": "newstudent@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertTrue(User.objects.filter(username="newstudent").exists())

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(username="taken", password="pass12345")
        resp = self.client.post(
            "/api/auth/register/",
            {"username": "taken", "email": "x@example.com", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_access_and_refresh_tokens(self):
        User.objects.create_user(username="loginuser", password="StrongPass123")
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "loginuser", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_rejects_wrong_password(self):
        User.objects.create_user(username="loginuser2", password="StrongPass123")
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "loginuser2", "password": "WrongPassword"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser", password="pass12345", email="p@example.com"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_profile_requires_auth(self):
        anon_client = APIClient()
        resp = anon_client.get("/api/auth/profile/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_works_without_userprofile_row(self):
        # No UserProfile exists yet for this user (e.g. signal never fired historically).
        # UserProfileAPIView guards with hasattr(), so this should still succeed with
        # career_goal coming back as None rather than 500ing.
        resp = self.client.get("/api/auth/profile/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["username"], "profileuser")
        self.assertIsNone(resp.data["career_goal"])

    def test_update_profile(self):
        resp = self.client.put(
            "/api/auth/profile/update/",
            {"first_name": "Pratham", "last_name": "Parmar", "email": "updated@example.com"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Pratham")
        self.assertEqual(self.user.email, "updated@example.com")


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pwuser", password="OldPass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        resp = self.client.put(
            "/api/auth/change-password/",
            {"old_password": "OldPass123", "new_password": "NewPass456"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456"))

    def test_change_password_rejects_wrong_old_password(self):
        resp = self.client.put(
            "/api/auth/change-password/",
            {"old_password": "WrongOldPassword", "new_password": "NewPass456"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123"))