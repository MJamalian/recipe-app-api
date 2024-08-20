from django.test import TestCase, Client

from django.contrib.auth import get_user_model

from django.urls import reverse


class AdminTest(TestCase):
    """Test admin functionality."""

    def setUp(self):
        """Set up fake user and superuser to test admin functionality"""

        self.client = Client()
        self.superuser = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="admin123"
        )

        self.client.force_login(self.superuser)
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            name="user",
            password="user123"
        )

    def test_admin_show_users_list(self):
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_admin_update_users_page(self):
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_admin_add_user(self):
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
