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


class TicketKnowledgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Group
        from django.core.management import call_command
        from io import StringIO
        from issues.models import Issue, Priority
        call_command('setup_roles', stdout=StringIO())
        cls.user = get_user_model().objects.create_user(username='technician')
        cls.user.groups.add(Group.objects.get(name='Help Desk'))
        cls.issue = Issue.objects.create(requestor_name='requestor', summary='Recurring VPN failure',
            description=('Full diagnostic detail. ' * 20).rstrip(),
            priority=Priority.objects.create(name='Normal'), pub_date=timezone.now())

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse('knowledgebase:from_ticket', args=[self.issue.pk])
        self.payload = {'description': self.issue.summary, 'problem': self.issue.description,
                        'solution': 'Restart the VPN service.\nVerify the connection.', 'keywords': 'vpn'}

    def test_prefill_copies_full_ticket_details_without_publishing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['description'], self.issue.summary)
        self.assertEqual(response.context['form'].initial['problem'], self.issue.description)
        self.assertEqual(Article.objects.count(), 0)
        self.assertContains(self.client.get(reverse('issues:issue', args=[self.issue.pk])), self.url)
        self.assertContains(self.client.get(reverse('issues:issue_edit', args=[self.issue.pk])), self.url)

    def test_publish_preserves_full_content_authorship_and_source_without_modifying_ticket(self):
        self.payload.update(author='Forged author', source_issue=999999, solution=('Tested step. ' * 300).rstrip())
        response = self.client.post(self.url, self.payload)
        article = Article.objects.get(source_issue=self.issue)
        self.assertRedirects(response, reverse('knowledgebase:detail', args=[article.pk]))
        self.assertEqual(article.author, self.user.username)
        self.assertEqual(article.problem, self.issue.description)
        self.assertEqual(article.solution, self.payload['solution'])
        self.issue.refresh_from_db()
        self.assertTrue(self.issue.issue_open)
        self.assertEqual(self.issue.description, self.payload['problem'])
        detail = self.client.get(reverse('issues:issue', args=[self.issue.pk]))
        self.assertContains(detail, 'View knowledge article')
        self.assertNotContains(detail, 'Create knowledge article')

    def test_repeated_submission_reuses_article_without_overwriting_solution(self):
        self.client.post(self.url, self.payload)
        article = Article.objects.get(source_issue=self.issue)
        self.client.post(self.url, dict(self.payload, solution='Do not overwrite'))
        article.refresh_from_db()
        self.assertEqual(Article.objects.count(), 1)
        self.assertEqual(article.solution, self.payload['solution'])
        self.assertRedirects(self.client.get(self.url), reverse('knowledgebase:detail', args=[article.pk]))

    def test_solution_required_and_invalid_form_retains_problem(self):
        response = self.client.post(self.url, dict(self.payload, solution=''))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'solution', 'This field is required.')
        self.assertContains(response, self.issue.description)
        self.assertEqual(Article.objects.count(), 0)

    def test_authentication_and_both_permissions_are_required(self):
        from django.contrib.auth.models import Permission
        self.client.logout()
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])
        for codename, app in [('add_article', 'knowledgebase'), ('view_issue', 'issues')]:
            user = get_user_model().objects.create_user(username=codename)
            user.user_permissions.add(Permission.objects.get(content_type__app_label=app, codename=codename))
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.client.post(self.url, self.payload).status_code, 403)
            detail = self.client.get(reverse('issues:issue', args=[self.issue.pk]))
            self.assertNotContains(detail, self.url, status_code=200 if codename == 'view_issue' else 403)
        self.assertEqual(Article.objects.count(), 0)

    def test_missing_ticket_and_unsupported_methods(self):
        url = reverse('knowledgebase:from_ticket', args=[999999])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, self.payload).status_code, 404)
        self.assertEqual(self.client.put(self.url).status_code, 405)

    def test_solution_is_escaped_searchable_and_survives_ticket_deletion(self):
        self.client.post(self.url, dict(self.payload, solution='<script>unsafe</script>\nReset tunnel'))
        article = Article.objects.get(source_issue=self.issue)
        response = self.client.get(reverse('knowledgebase:detail', args=[article.pk]))
        self.assertContains(response, '&lt;script&gt;unsafe&lt;/script&gt;')
        self.assertNotContains(response, '<script>unsafe</script>')
        response = self.client.get(reverse('knowledgebase:search'), {'q': 'Reset tunnel'})
        self.assertIn(article, response.context['knowledgebase_list'])
        self.issue.delete()
        article.refresh_from_db()
        self.assertIsNone(article.source_issue)
        self.assertIn('Reset tunnel', article.solution)

    def test_conversion_requires_csrf_token(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, self.payload).status_code, 403)
        self.assertEqual(Article.objects.count(), 0)
