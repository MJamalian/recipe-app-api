from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

from decimal import Decimal


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

    def test_update_ingredient(self):
        ingredient = create_ingredient(self.user)

        ingredient_update = {"name": "potato"}

        res = self.client.patch(
            ingredient_detail_url(ingredient.id),
            ingredient_update
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, ingredient_update["name"])

    def test_delete_ingredient(self):
        ingredient = create_ingredient(self.user)

        res = self.client.delete(ingredient_detail_url(ingredient.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_by_assigned_to_recipe(self):
        ingredient1 = create_ingredient(self.user)
        ingredient2 = create_ingredient(self.user, name="milk")

        recipe = Recipe.objects.create(
            user=self.user,
            title="some food",
            description="some description",
            time_to_get_ready=5,
            price=Decimal("5.25"),
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(
            INGREDIENT_LIST_URL,
            {"assigned_only": 1}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = IngredientSerializer(ingredient1)
        s2 = IngredientSerializer(ingredient2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_unique(self):
        ingredient = create_ingredient(self.user)

        recipe1 = Recipe.objects.create(
            user=self.user,
            title="some food",
            description="some description",
            time_to_get_ready=5,
            price=Decimal("5.25"),
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="another food",
            description="another description",
            time_to_get_ready=10,
            price=Decimal("3.25"),
        )

        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        res = self.client.get(
            INGREDIENT_LIST_URL,
            {"assigned_only": 1}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
