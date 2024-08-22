from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag

from recipe.serializers import TagSerializer


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
