from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

USER_CREATE_URL = reverse("user:create")
USER_TOKEN_URL = reverse("user:token")
USER_PROFILE_URL = reverse("user:profile")


class PublicUserApiTest(TestCase):
    """Test user APIs that doesn't need authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user_detail = {
            "email": "test@example.com",
            "name": "test name",
            "password": "testpass123"
        }

    def test_create_user_successful(self):

        res = self.client.post(USER_CREATE_URL, self.user_detail)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=self.user_detail["email"])

        self.assertEqual(user.name, self.user_detail["name"])
        self.assertTrue(user.check_password(self.user_detail["password"]))
        self.assertNotIn("password", res.data)

    def test_create_user_with_same_email(self):

        get_user_model().objects.create_user(**self.user_detail)

        user_detail2 = {
            "email": self.user_detail["email"],
            "name": "test name2",
            "password": "testpass1234"
        }

        res2 = self.client.post(USER_CREATE_URL, user_detail2)

        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        new_user_exists = get_user_model().objects.filter(
            name=user_detail2["name"]
        ).exists()

        self.assertFalse(new_user_exists)

    def test_create_user_short_password(self):

        payload = {
            "email": "test@example.com",
            "name": "test name",
            "password": "123"
        }

        res = self.client.post(USER_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            name=payload["email"]
        ).exists()
        self.assertFalse(user_exists)

    def test_get_auth_token_successful(self):

        get_user_model().objects.create_user(**self.user_detail)

        res = self.client.post(USER_TOKEN_URL, {
            "email": self.user_detail["email"],
            "password": self.user_detail["password"]
        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("token", res.data)

    def test_get_auth_token_wrong_credential(self):

        get_user_model().objects.create_user(**self.user_detail)

        res = self.client.post(USER_TOKEN_URL, {
            "email": self.user_detail["email"],
            "password": self.user_detail["password"][1:]
        })
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_auth_token_empty_password(self):

        res = self.client.post(USER_TOKEN_URL, {
            "email": "test@example.com",
            "password": ""
        })

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_profile_unauthorized(self):

        res = self.client.get(USER_PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """Test user APIs that need to be authorized"""

    def setUp(self):

        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            name="test name",
            password="testpass123"
        )

        self.client.force_authenticate(user=self.user)

    def test_get_user_profile(self):
        res = self.client.get(USER_PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            "name": self.user.name,
            "email": self.user.email,
        })

    def test_update_user_profile(self):
        user_detail = {"name": "updated name", "password": "testpass987"}

        res = self.client.patch(USER_PROFILE_URL, user_detail)

        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, user_detail["name"])
        self.assertTrue(self.user.check_password(user_detail["password"]))
