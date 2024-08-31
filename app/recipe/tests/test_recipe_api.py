"""Test recipe APIs."""

from rest_framework.test import APIClient
from rest_framework import status

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)

import os
import tempfile

from PIL import Image

RECIPE_LIST_URL = reverse("recipe:recipe-list")


def image_upload_url(id):
    return reverse("recipe:recipe-upload-image", args=[id])


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

    def test_create_recipe_with_new_tag(self):
        recipe_detail = {
            "title": "some title",
            "price": 5,
            "time_to_get_ready": 5,
            "description": "some description",
            "link": "www.example.com/hello",
            "tags": [
                {"name": "dessert"},
                {"name": "dinner"},
            ]
        }

        res = self.client.post(RECIPE_LIST_URL, recipe_detail, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in recipe_detail["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):

        tag = Tag.objects.create(user=self.user, name="dessert")

        recipe_detail = {
            "title": "some title",
            "price": 5,
            "time_to_get_ready": 5,
            "description": "some description",
            "link": "www.example.com/hello",
            "tags": [
                {"name": "dessert"},
                {"name": "dinner"},
            ]
        }

        res = self.client.post(RECIPE_LIST_URL, recipe_detail, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())

        tags = Tag.objects.filter(user=self.user)
        self.assertEqual(tags.count(), 2)

        for tag in recipe_detail["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_update_tags_of_recipe(self):
        recipe = create_recipe(self.user)

        tags_detail = {"tags": [{"name": "lunch"}]}

        res = self.client.patch(
            recipe_detail_url(recipe.id),
            tags_detail,
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(name="lunch", user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_tag_with_existing_tag(self):
        tag = Tag.objects.create(user=self.user, name="dessert")

        recipe = create_recipe(self.user)
        recipe.tags.add(tag)

        new_tag = Tag.objects.create(user=self.user, name="lunch")

        tags_detail = {"tags": [{"name": new_tag.name}]}

        res = self.client.patch(
            recipe_detail_url(recipe.id),
            tags_detail,
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(new_tag, recipe.tags.all())
        self.assertNotIn(tag, recipe.tags.all())

    def test_clear_tags_for_recipe(self):
        tag = Tag.objects.create(user=self.user, name="dessert")

        recipe = create_recipe(self.user)
        recipe.tags.add(tag)

        tags_detail = {"tags": []}

        res = self.client.patch(
            recipe_detail_url(recipe.id),
            tags_detail,
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        recipe_detail = {
            "title": "some title",
            "price": 5,
            "time_to_get_ready": 5,
            "description": "some description",
            "link": "www.example.com/hello",
            "ingredients": [
                {"name": "potato"},
                {"name": "milk"},
            ]
        }

        res = self.client.post(RECIPE_LIST_URL, recipe_detail, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in recipe_detail["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):

        ingredient = Ingredient.objects.create(user=self.user, name="potato")

        recipe_detail = {
            "title": "some_title",
            "price": 5,
            "time_to_get_ready": 5,
            "description": "some description",
            "link": "www.example.com/hello",
            "ingredients": [
                {"name": "potato"},
                {"name": "milk"},
            ]
        }

        res = self.client.post(RECIPE_LIST_URL, recipe_detail, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertEqual(ingredients.count(), 2)

        for ing in recipe_detail["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ing["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_update_ingredients_of_recipe(self):
        recipe = create_recipe(self.user)

        ingredients_detail = {"ingredients": [{"name": "potato"}]}

        res = self.client.patch(
            recipe_detail_url(recipe.id),
            ingredients_detail,
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(name="potato", user=self.user)
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_ingredient_with_existing_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="potato")

        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingredient)

        new_ingredient = Ingredient.objects.create(user=self.user, name="milk")

        ingredients_detail = {"ingredients": [{"name": new_ingredient.name}]}

        res = self.client.patch(
            recipe_detail_url(recipe.id),
            ingredients_detail,
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(new_ingredient, recipe.ingredients.all())
        self.assertNotIn(ingredient, recipe.ingredients.all())

    def test_clear_ingredients_for_recipe(self):
        ingredient = Ingredient.objects.create(user=self.user, name="potato")

        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingredient)

        ingredients_detail = {"ingredients": []}

        res = self.client.patch(
            recipe_detail_url(recipe.id),
            ingredients_detail,
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadAPITest(TestCase):
    """Test class for testing upload image functionality."""

    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpass1234",
        )
        self.client.force_authenticate(self.user)

        self.recipe = create_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_bad_image_error(self):
        url = image_upload_url(self.recipe.id)
        payload = {"image": "some image"}

        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
