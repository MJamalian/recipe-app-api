"""Test recipe APIs."""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import Recipe
from recipe.serializers import RecipeSerializer

RECIPE_LIST_URL = reverse("recipe:recipe-list")


def create_recipe(user, payload={}):
    recipe_detail = {
        "user": user,
        "title": "some title",
        "price": 5,
        "time_to_get_ready": 5,
        "description": "some description",
    }

    recipe_detail.update(payload)
    return Recipe.objects.create(**recipe_detail)


class PublicRecipeAPITest(TestCase):
    """Test recipe APIs without authentication."""

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_recipe_list(self):

        get_user_model().objects.create_user(
            email="test@example.com",
            password="testpass1234",
        )

        res = self.client.get(RECIPE_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    """Test recipe APIs with authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpass1234",
        )

        self.client.force_authenticate(self.user)

    def test_get_recipe_list_successful(self):

        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPE_LIST_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_list_only_for_user(self):
        create_recipe(self.user)

        another_user = get_user_model().objects.create_user(
            email="test2@example.com",
            password="testpass12345",
        )

        create_recipe(another_user)

        res = self.client.get(RECIPE_LIST_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
