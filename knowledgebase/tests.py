from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article


class KnowledgeBaseTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="kb-user",
            password="test-password",
        )
        self.article = Article.objects.create(
            author="Support",
            description="Reset a locked account",
            keywords="account,password",
            pub_date=timezone.now(),
        )

    def test_index_lists_articles(self):
        response = self.client.get(reverse("knowledgebase:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["knowledgebase_list"]),
            [self.article],
        )
        self.assertContains(response, "Reset a locked account")
        self.assertContains(response, "account,password")

    def test_article_detail_returns_requested_article(self):
        response = self.client.get(
            reverse("knowledgebase:detail", args=[self.article.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["article"], self.article)
        self.assertContains(response, "Reset a locked account")

    def test_create_article_requires_authentication(self):
        response = self.client.get(reverse("knowledgebase:new"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_authenticated_user_can_create_article(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("knowledgebase:new"),
            {
                "description": "Connect to the corporate VPN",
                "keywords": "vpn,remote",
            },
        )

        created = Article.objects.get(
            description="Connect to the corporate VPN"
        )
        self.assertRedirects(
            response,
            reverse("knowledgebase:detail", args=[created.pk]),
        )
        self.assertEqual(created.author, self.user.username)
        self.assertEqual(created.keywords, "vpn,remote")
