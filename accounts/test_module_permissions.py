"""Request-level boundaries for the project and knowledge domains."""
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority
from knowledgebase.models import Article
from projects.models import Project


class ProjectKnowledgePermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('setup_roles', stdout=StringIO())
        cls.users = {}
        for role in ('Infrastructure Team', 'Help Desk', 'Project Manager'):
            user = get_user_model().objects.create_user(username=role.replace(' ', '-'))
            user.groups.add(Group.objects.get(name=role))
            cls.users[role] = user
        cls.no_role = get_user_model().objects.create_user(username='no-role', is_staff=True)
        cls.project = Project.objects.create(requestor_name='Private requestor',
            summary='Private project marker', description='Private project body',
            assigned=cls.no_role, pub_date=timezone.now())
        cls.article = Article.objects.create(author=cls.no_role.username,
            description='Private article marker', keywords='Private',
            solution='Private solution body', pub_date=timezone.now())
        cls.ticket = Issue.objects.create(requestor_name='Requestor', summary='Source',
            description='Source body', priority=Priority.objects.create(name='Normal'),
            pub_date=timezone.now())

    def grant(self, user, app, *codes):
        user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label=app, codename__in=codes))

    def reads(self):
        return [reverse('projects:' + name) for name in
                ('index', 'my_projects', 'unassigned_projects', 'search')] + [
                    reverse('projects:project', args=[self.project.pk]),
                    reverse('knowledgebase:index'), reverse('knowledgebase:search'),
                    reverse('knowledgebase:detail', args=[self.article.pk])]

    def writes(self):
        return [reverse('projects:project_new'), reverse('knowledgebase:new'),
                reverse('knowledgebase:edit', args=[self.article.pk]),
                reverse('knowledgebase:delete', args=[self.article.pk]),
                reverse('knowledgebase:from_ticket', args=[self.ticket.pk])]

    def test_all_direct_reads_require_login_and_explicit_grants(self):
        for url in self.reads():
            self.assertEqual(self.client.get(url, {'q': 'Private'}).status_code, 302)
        self.client.force_login(self.no_role)
        for url in self.reads():
            response = self.client.get(url, {'q': 'Private'})
            self.assertEqual(response.status_code, 403)
            self.assertNotContains(response, 'Private project marker', status_code=403)
            self.assertNotContains(response, 'Private article marker', status_code=403)
        for url in [reverse('projects:project', args=[999999]),
                    reverse('knowledgebase:detail', args=[999999])]:
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_denied_writes_do_not_construct_forms_or_mutate_records(self):
        for url in self.writes():
            self.assertEqual(self.client.post(url, {'description': 'Tampered'}).status_code, 302)
        self.client.force_login(self.no_role)
        with patch('projects.views.ProjectForm') as project_form, patch('knowledgebase.views.ArticleForm') as article_form:
            for url in self.writes():
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {'description': 'Tampered'}).status_code, 403)
            project_form.assert_not_called()
            article_form.assert_not_called()
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Article.objects.count(), 1)
        self.article.refresh_from_db()
        self.assertEqual(self.article.description, 'Private article marker')

    def test_roles_read_both_domains_and_only_project_manager_creates_projects(self):
        for role, user in self.users.items():
            self.client.force_login(user)
            for url in self.reads():
                self.assertEqual(self.client.get(url).status_code, 200)
            url = reverse('projects:project_new')
            self.assertEqual(self.client.get(url).status_code, 200 if role == 'Project Manager' else 403)
            count = Project.objects.count()
            result = self.client.post(url, {'summary': 'Role project', 'description': 'Body'})
            self.assertEqual(result.status_code, 302 if role == 'Project Manager' else 403)
            self.assertEqual(Project.objects.count(), count + (role == 'Project Manager'))
            page = self.client.get(reverse('projects:index'))
            if role == 'Project Manager':
                self.assertContains(page, 'href="' + url)
            else:
                self.assertNotContains(page, 'href="' + url)

    def test_all_roles_publish_articles_but_authorship_does_not_grant_management(self):
        for role, user in self.users.items():
            self.client.force_login(user)
            result = self.client.post(reverse('knowledgebase:new'), {
                'description': 'Role article', 'keywords': 'test', 'solution': 'Solution',
                'author': 'spoofed',
            })
            self.assertEqual(result.status_code, 302)
            article = Article.objects.latest('pk')
            self.assertEqual(article.author, user.username)
            for action in ('edit', 'delete'):
                url = reverse('knowledgebase:' + action, args=[article.pk])
                self.assertEqual(self.client.post(url, {'description': 'Tampered'}).status_code, 403)
                self.assertNotContains(self.client.get(result['Location']), 'href="' + url)
            self.assertNotContains(self.client.get(result['Location']), '>Delete</button>')

    def test_article_model_grants_preserve_owner_or_staff_boundary(self):
        user = self.users['Help Desk']
        self.grant(user, 'knowledgebase', 'change_article', 'delete_article')
        self.client.force_login(user)
        edit = reverse('knowledgebase:edit', args=[self.article.pk])
        delete = reverse('knowledgebase:delete', args=[self.article.pk])
        self.assertEqual(self.client.get(edit).status_code, 403)
        self.assertEqual(self.client.post(delete).status_code, 403)
        self.article.author = user.username
        self.article.save()
        response = self.client.post(edit, {'description': 'Edited safely', 'keywords': 'edited',
                                           'author': 'spoofed'})
        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertEqual(self.article.author, user.username)
        page = self.client.get(response['Location'])
        self.assertContains(page, 'href="' + edit)
        self.assertContains(page, '>Delete</button>')
        self.assertEqual(self.client.get(delete).status_code, 405)
        self.assertEqual(self.client.post(delete).status_code, 302)
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())

    def test_create_and_conversion_require_destination_view_grants(self):
        self.grant(self.no_role, 'projects', 'add_project')
        self.grant(self.no_role, 'knowledgebase', 'add_article', 'change_article', 'delete_article')
        self.grant(self.no_role, 'issues', 'view_issue')
        self.client.force_login(self.no_role)
        for url in self.writes():
            self.assertEqual(self.client.post(url, {'description': 'Blocked'}).status_code, 403)
        source = self.client.get(reverse('issues:issue', args=[self.ticket.pk]))
        self.assertNotContains(source, reverse('knowledgebase:from_ticket', args=[self.ticket.pk]))

    def test_dashboard_and_search_do_not_disclose_denied_domains(self):
        # Give access to tickets so global search works without either target grant.
        self.grant(self.no_role, 'issues', 'view_issue')
        self.client.force_login(self.no_role)
        with CaptureQueriesContext(connection) as queries:
            page = self.client.get(reverse('dashboard:index'))
            search = self.client.get(reverse('watson:search'), {'q': 'Private'})
        self.assertEqual(page.context['num_open_projects'], 0)
        self.assertFalse(any('"projects_project"' in q['sql'] or '"knowledgebase_article"' in q['sql']
                             for q in queries))
        for url in self.reads() + self.writes():
            self.assertNotContains(page, 'href="' + url)
        self.assertNotContains(search, 'Private project marker')
        self.assertNotContains(search, 'Private article marker')

    def test_revocation_and_multiple_roles_take_effect_next_request(self):
        user = self.users['Help Desk']
        self.client.force_login(user)
        create = reverse('projects:project_new')
        self.assertEqual(self.client.get(create).status_code, 403)
        user.groups.add(Group.objects.get(name='Project Manager'))
        self.assertEqual(self.client.get(create).status_code, 200)
        user.groups.remove(Group.objects.get(name='Project Manager'))
        self.assertEqual(self.client.get(create).status_code, 403)
        user.groups.clear()
        for url in self.reads():
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertNotContains(self.client.get(reverse('dashboard:index')), 'href="' + reverse('knowledgebase:index'))

    def test_staff_article_controls_require_each_model_grant_independently(self):
        self.grant(self.no_role, 'knowledgebase', 'view_article', 'change_article')
        self.client.force_login(self.no_role)
        detail = reverse('knowledgebase:detail', args=[self.article.pk])
        edit = reverse('knowledgebase:edit', args=[self.article.pk])
        self.assertContains(self.client.get(detail), 'href="' + edit)
        self.assertNotContains(self.client.get(detail), '>Delete</button>')
        self.grant(self.no_role, 'knowledgebase', 'delete_article')
        self.no_role.user_permissions.remove(Permission.objects.get(
            content_type__app_label='knowledgebase', codename='change_article'))
        self.assertNotContains(self.client.get(detail), 'href="' + edit)
        self.assertContains(self.client.get(detail), '>Delete</button>')
        self.assertEqual(self.client.post(edit, {'description': 'Blocked'}).status_code, 403)

    def test_csrf_protects_authorized_writes_and_create_methods_are_restricted(self):
        user = self.users['Project Manager']
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        for url in [reverse('projects:project_new'), reverse('knowledgebase:new'),
                    reverse('knowledgebase:from_ticket', args=[self.ticket.pk])]:
            self.assertEqual(client.post(url, {'description': 'Blocked'}).status_code, 403)
            client.get(url)
            self.assertEqual(client.delete(url, HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value).status_code, 405)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Article.objects.count(), 1)

    def test_superuser_recovers_all_routes_without_role_membership(self):
        user = get_user_model().objects.create_superuser(username='recovery', password='test-only')
        self.client.force_login(user)
        for url in self.reads() + self.writes():
            expected = 405 if url == reverse('knowledgebase:delete', args=[self.article.pk]) else 200
            self.assertEqual(self.client.get(url).status_code, expected)
