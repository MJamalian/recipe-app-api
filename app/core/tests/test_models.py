"""Tests for models"""


from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import (
    Recipe,
    Tag,
    Ingredient,
    recipe_image_file_path,
)

from decimal import Decimal

from unittest.mock import patch


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

    def test_create_recipe(self):
        """Test create new recipe"""

        user = get_user_model().objects.create_user(
            email="test@example.com",
            password="test123",
        )

        recipe = Recipe.objects.create(
            user=user,
            title="some recipe",
            price=Decimal("5.56"),
            description="This is a great recipe",
            time_to_get_ready=5,
        )

        self.assertTrue(Recipe.objects.all().exists())
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):

        user = get_user_model().objects.create_user(
            email="test@example.com",
            password="test123",
        )

        tag = Tag.objects.create(user=user, name="tag1")

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredients(self):

        user = get_user_model().objects.create_user(
            email="test@exmaple.com",
            password="testpass123",
        )

        ingredient = Ingredient.objects.create(
            user=user,
            name="tomato",
        )

        self.assertEqual(str(ingredient), ingredient.name)
        self.assertTrue(Ingredient.objects.all().exists())

    @patch("uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        uuid = "test-uuid"
        mock_uuid.return_value = uuid

        file_path = recipe_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
