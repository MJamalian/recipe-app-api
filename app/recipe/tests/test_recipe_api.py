"""Test recipe APIs."""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_LIST_URL = reverse("recipe:recipe-list")


def recipe_detail_url(id):
    return reverse("recipe:recipe-detail", args=[id])


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

    def test_get_repice_detail(self):
        recipe = create_recipe(self.user)

        res = self.client.get(recipe_detail_url(recipe.id))

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_create_recipe_successful(self):
        recipe_detail = {
            "title": "some_title",
            "price": 5,
            "time_to_get_ready": 5,
            "description": "some description",
            "link": "www.example.com/hello",
        }

        res = self.client.post(RECIPE_LIST_URL, recipe_detail)

        recipe = Recipe.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for k, v in recipe_detail.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)

    def test_delete_recipe_successful(self):
        recipe = create_recipe(self.user)

        res = self.client.delete(recipe_detail_url(recipe.id))

        my_recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(my_recipes.exists())

    def test_delete_another_user_recipe_error(self):
        another_user = get_user_model().objects.create_user(
            email="test2@example.com",
            password="testpass123"
        )

        recipe = create_recipe(another_user)

        res = self.client.delete(recipe_detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            Recipe.objects.all().exists()
        )

    def test_update_recipe_successful(self):
        recipe = create_recipe(self.user)

        update_for_recipe = {
            "title": "another title",
            "description": "another description",
            "price": 100,
        }

        res = self.client.patch(
            recipe_detail_url(recipe.id),
            update_for_recipe
        )

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for k, v in update_for_recipe.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_another_user_recipe_update_error(self):
        another_user = get_user_model().objects.create_user(
            email="test2@example.com",
            password="testpass123"
        )

        recipe = create_recipe(another_user)

        recipe_update = {
            "title": "another title"
        }

        res = self.client.patch(recipe_detail_url(recipe.id), recipe_update)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        recipe.refresh_from_db()
        self.assertNotEqual(recipe.title, recipe_update["title"])
