"""Tests for models"""


from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTest(TestCase):
    """Test models."""

    def test_create_user(self):
        """Test creating a new user with email and password."""

        sample_email = "test@example.com"
        sample_password = "test123"

        user = get_user_model().objects.create_user(
            email=sample_email,
            password=sample_password
        )

        self.assertEqual(user.email, sample_email)
        self.assertTrue(user.check_password(sample_password))

    def test_create_user_normalize_email(self):
        """Test normalizing email when creating user."""

        samples = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["TEST2@example.com", "TEST2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["Test4@example.com", "Test4@example.com"],
        ]

        for email, normalized_email in samples:
            user = get_user_model().objects.create_user(email, "test123")
            self.assertEqual(user.email, normalized_email)

    def test_create_user_with_no_email_failure(self):
        """Test failure of creating user with no email."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_create_superuser(self):
        """Test create superuser successfully."""
        user = get_user_model().objects.create_superuser(
            email="test@example.com",
            password="test1234"
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
