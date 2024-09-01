from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

from decimal import Decimal


TAG_LIST_URL = reverse("recipe:tag-list")


def detail_tag_url(id):
    return reverse("recipe:tag-detail", args=[id])


def create_tag(user, name="vegan"):

    return Tag.objects.create(
        user=user,
        name=name,
    )


class PublicTagAPITest(TestCase):
    """Test Tag APIs unauthenticated."""

    def setUp(self):
        self.client = APIClient()

    def test_tag_list_unauthenticated_error(self):
        res = self.client.get(TAG_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITest(TestCase):
    """Test authenticated tag APIs"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="test1234",
        )
        self.client.force_authenticate(self.user)

    def test_get_tag_list(self):
        create_tag(self.user)
        create_tag(self.user, "dessert")

        res = self.client.get(TAG_LIST_URL)

        tags = Tag.objects.all().filter(user=self.user).order_by("-name")

        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_tag_list_only_for_user(self):
        tag = create_tag(self.user)

        another_user = get_user_model().objects.create_user(
            email="test2@email.com",
            password="testpass1234",
        )

        create_tag(another_user, "dessert")

        res = self.client.get(TAG_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        tag = create_tag(self.user)

        tag_update = {"name": "dessert"}

        res = self.client.patch(detail_tag_url(tag.id), tag_update)

        tag.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, tag_update["name"])

    def test_delete_tag(self):
        tag = create_tag(self.user)

        res = self.client.delete(detail_tag_url(tag.id))

        tags = Tag.objects.filter(user=self.user)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(tags.exists())

    def test_filter_tags_by_assigned_to_recipe(self):
        tag1 = create_tag(self.user)
        tag2 = create_tag(self.user, name="lunch")

        recipe = Recipe.objects.create(
            user=self.user,
            title="some food",
            description="some description",
            time_to_get_ready=5,
            price=Decimal("5.25"),
        )
        recipe.tags.add(tag1)

        res = self.client.get(
            TAG_LIST_URL,
            {"assigned_only": 1}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self):
        tag = create_tag(self.user)

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

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(
            TAG_LIST_URL,
            {"assigned_only": 1}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
