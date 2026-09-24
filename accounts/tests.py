from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountWorkflowTests(TestCase):
    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("account:index"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_authenticated_user_can_view_profile(self):
        user = get_user_model().objects.create_user(
            username="profile-user",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("account:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile-user")

    def test_registration_page_renders_bound_fields(self):
        response = self.client.get(reverse("account:register"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password1"')

    def test_registration_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("account:register"),
            {
                "username": "new-user",
                "password1": "Strong-Test-Password-123!",
                "password2": "Strong-Test-Password-123!",
            },
        )

        self.assertRedirects(response, reverse("dashboard:index"))
        user = get_user_model().objects.get(username="new-user")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_login_and_post_logout_workflow(self):
        user = get_user_model().objects.create_user(
            username="login-user",
            password="test-password",
        )

        login_response = self.client.post(
            reverse("login"),
            {
                "username": "login-user",
                "password": "test-password",
            },
        )
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

        logout_response = self.client.post(reverse("logout"))

        self.assertRedirects(logout_response, reverse("dashboard:index"))
        self.assertNotIn("_auth_user_id", self.client.session)
