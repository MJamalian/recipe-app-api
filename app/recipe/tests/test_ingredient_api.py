from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENT_LIST_URL = reverse("recipe:ingredient-list")


def ingredient_detail_url(id):
    return reverse("recipe:ingredient-detail", args=[id])


def create_ingredient(user, name="tomato"):
    return Ingredient.objects.create(
        user=user,
        name=name,
    )


class PublicIngredientsAPITest(TestCase):
    """Test ingredients APIs when unauthenticated."""

    def setUp(self):
        self.client = APIClient()

    def test_get_ingredients_list_unauthenticated(self):

        res = self.client.get(INGREDIENT_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITest(TestCase):
    """Test ingredients APIs when authenticated."""

    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpass1234"
        )

        self.client.force_authenticate(self.user)

    def test_get_ingredients_list_successful(self):
        create_ingredient(self.user)
        create_ingredient(self.user, "potato")

        res = self.client.get(INGREDIENT_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.filter(
            user=self.user
        ).order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(len(res.data), 2)
        self.assertEqual(serializer.data, serializer.data)

    def test_get_only_user_ingredients(self):
        another_user = get_user_model().objects.create_user(
            email="test2@example.com",
            password="anotherpass123",
        )

        create_ingredient(another_user)
        ingredient = create_ingredient(self.user, "cabbage")

        res = self.client.get(INGREDIENT_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.filter(
            user=self.user
        ).order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "cabbage")
        self.assertEqual(res.data[0]["id"], ingredient.id)
        self.assertEqual(res.data, serializer.data)

    def test_update_tag(self):
        ingredient = create_ingredient(self.user)

        ingredient_update = {"name": "potato"}

        res = self.client.patch(
            ingredient_detail_url(ingredient.id),
            ingredient_update
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, ingredient_update["name"])

    def test_delete_tag(self):
        ingredient = create_ingredient(self.user)

        res = self.client.delete(ingredient_detail_url(ingredient.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
