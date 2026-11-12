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

    def test_search_matches_description_keywords_and_author(self):
        Article.objects.create(
            author="Network Team",
            description="Configure wireless access",
            keywords="wifi,network",
            pub_date=timezone.now(),
        )

        by_description = self.client.get(
            reverse("knowledgebase:search"),
            {"q": "locked"},
        )
        self.assertEqual(
            list(by_description.context["knowledgebase_list"]),
            [self.article],
        )

        by_keywords = self.client.get(
            reverse("knowledgebase:search"),
            {"q": "network"},
        )
        self.assertEqual(by_keywords.status_code, 200)
        self.assertContains(by_keywords, "Configure wireless access")

        by_author = self.client.get(
            reverse("knowledgebase:search"),
            {"q": "support"},
        )
        self.assertEqual(
            list(by_author.context["knowledgebase_list"]),
            [self.article],
        )

    def test_empty_search_returns_empty_result(self):
        response = self.client.get(reverse("knowledgebase:search"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["knowledgebase_list"]), [])

    def test_author_can_edit_article(self):
        owned = Article.objects.create(
            author=self.user.username,
            description="Original description",
            keywords="original",
            pub_date=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("knowledgebase:edit", args=[owned.pk]),
            {
                "description": "Updated description",
                "keywords": "updated",
            },
        )

        self.assertRedirects(
            response,
            reverse("knowledgebase:detail", args=[owned.pk]),
        )
        owned.refresh_from_db()
        self.assertEqual(owned.description, "Updated description")
        self.assertEqual(owned.keywords, "updated")

    def test_non_author_cannot_edit_article(self):
        other = get_user_model().objects.create_user(
            username="other-kb-user",
            password="test-password",
        )
        owned = Article.objects.create(
            author=self.user.username,
            description="Owned article",
            keywords="owner",
            pub_date=timezone.now(),
        )
        self.client.force_login(other)

        response = self.client.get(
            reverse("knowledgebase:edit", args=[owned.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_can_edit_article(self):
        staff = get_user_model().objects.create_user(
            username="kb-staff",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse("knowledgebase:edit", args=[self.article.pk]),
            {
                "description": "Staff updated article",
                "keywords": "staff",
            },
        )

        self.assertRedirects(
            response,
            reverse("knowledgebase:detail", args=[self.article.pk]),
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.description, "Staff updated article")

    def test_delete_requires_post(self):
        owned = Article.objects.create(
            author=self.user.username,
            description="Delete me",
            keywords="delete",
            pub_date=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("knowledgebase:delete", args=[owned.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Article.objects.filter(pk=owned.pk).exists())

    def test_author_can_delete_article(self):
        owned = Article.objects.create(
            author=self.user.username,
            description="Delete me",
            keywords="delete",
            pub_date=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("knowledgebase:delete", args=[owned.pk])
        )

        self.assertRedirects(response, reverse("knowledgebase:index"))
        self.assertFalse(Article.objects.filter(pk=owned.pk).exists())

    def test_non_author_cannot_delete_article(self):
        other = get_user_model().objects.create_user(
            username="other-delete-user",
            password="test-password",
        )
        owned = Article.objects.create(
            author=self.user.username,
            description="Protected article",
            keywords="protected",
            pub_date=timezone.now(),
        )
        self.client.force_login(other)

        response = self.client.post(
            reverse("knowledgebase:delete", args=[owned.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Article.objects.filter(pk=owned.pk).exists())


class ArticlePaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.articles = [Article.objects.create(
            author='Support', description=f'Network & access {number}',
            keywords='network,vpn', pub_date=now,
        ) for number in range(34)]
        Article.objects.create(author='Other', description='Unrelated', keywords='other', pub_date=now)

    def test_every_article_is_reachable_in_stable_newest_first_order(self):
        ids = []
        for number in (1, 2, 3):
            response = self.client.get(reverse('knowledgebase:index'), {'page': number})
            self.assertEqual(response.status_code, 200)
            ids.extend(item.pk for item in response.context['knowledgebase_list'])
        self.assertEqual(ids, list(Article.objects.order_by('-pub_date', '-pk').values_list('pk', flat=True)))
        self.assertEqual(len(ids), len(set(ids)))

    def test_search_preserves_encoded_query_and_does_not_include_nonmatches(self):
        ids = []
        for number in (1, 2, 3):
            response = self.client.get(reverse('knowledgebase:search'), {
                'q': ' Network & access ', 'page': number,
            })
            self.assertContains(response, 'q=Network%20%26%20access')
            self.assertEqual(response.context['query'], 'Network & access')
            ids.extend(item.pk for item in response.context['knowledgebase_list'])
        self.assertEqual(ids, [item.pk for item in reversed(self.articles)])

    def test_invalid_pages_fall_back_safely(self):
        for value, expected in [('bad', 1), ('9999', 3), ('0', 3)]:
            response = self.client.get(reverse('knowledgebase:index'), {'page': value})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page_obj'].number, expected)

    def test_empty_search_and_no_matches_have_no_pagination(self):
        for query in ('', '   ', 'not-present'):
            response = self.client.get(reverse('knowledgebase:search'), {'q': query, 'page': 99})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page_obj'].paginator.count, 0)
            self.assertContains(response, 'No knowledge base articles are available.')
            self.assertNotContains(response, 'aria-label="Article pages"')
