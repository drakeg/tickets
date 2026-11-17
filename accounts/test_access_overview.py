from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .roles import ROLE_PERMISSIONS


class AccessOverviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('setup_roles', stdout=StringIO())
        cls.user = get_user_model().objects.create_user(username='reader', email='reader@example.test')
        cls.staff = get_user_model().objects.create_user(username='operator', is_staff=True)
        cls.admin = get_user_model().objects.create_superuser(username='recovery', password='test-only')

    def grant(self, user, *codes):
        user.user_permissions.add(*Permission.objects.filter(content_type__app_label='auth', codename__in=codes))

    def test_role_overview_requires_login_staff_and_explicit_group_view_grant(self):
        url = reverse('account:roles')
        self.assertEqual(self.client.get(url).status_code, 302)
        for user in (self.user, self.staff):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 403)
        self.grant(self.user, 'view_group')
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.grant(self.staff, 'view_group')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertContains(self.client.get(reverse('dashboard:index')), 'href="' + url)

    def test_configured_defaults_custom_grants_and_missing_groups_are_reported_without_writes(self):
        group = Group.objects.get(name='Help Desk')
        group.permissions.remove(Permission.objects.get(content_type__app_label='issues', codename='add_issue'))
        extra = Permission.objects.get(content_type__app_label='knowledgebase', codename='delete_article')
        group.permissions.add(extra)
        Group.objects.get(name='Project Manager').delete()
        custom = Group.objects.create(name='<script>custom</script>')
        custom.permissions.add(extra)
        before = list(group.permissions.order_by('pk').values_list('pk', flat=True))
        self.client.force_login(self.admin)
        response = self.client.get(reverse('account:roles'))
        self.assertContains(response, 'issues.add_issue')
        self.assertContains(response, 'knowledgebase.delete_article')
        self.assertEqual(response.context['missing_groups'], ['Project Manager'])
        row = next(r for r in response.context['role_rows'] if r['group'] == group)
        self.assertEqual(row['missing'], ['issues.add_issue'])
        self.assertEqual(row['additional'], ['knowledgebase.delete_article'])
        self.assertContains(response, '&lt;script&gt;custom&lt;/script&gt;')
        self.assertNotContains(response, '<script>custom</script>')
        self.assertEqual(before, list(group.permissions.order_by('pk').values_list('pk', flat=True)))
        self.assertFalse(Group.objects.filter(name='Project Manager').exists())
        self.assertEqual(Group.objects.count(), 3)
        self.assertFalse(self.user.groups.exists())

    def test_management_links_follow_independent_admin_permissions(self):
        self.grant(self.staff, 'view_group')
        self.client.force_login(self.staff)
        response = self.client.get(reverse('account:roles'))
        group = Group.objects.get(name='Help Desk')
        edit = reverse('admin:auth_group_change', args=[group.pk])
        users = reverse('admin:auth_user_changelist')
        self.assertNotContains(response, edit)
        self.assertNotContains(response, users)
        self.grant(self.staff, 'change_group', 'view_user')
        response = self.client.get(reverse('account:roles'))
        self.assertContains(response, edit)
        self.assertContains(response, users)

    def test_overview_is_read_only_and_superuser_needs_no_groups(self):
        self.client.force_login(self.admin)
        url = reverse('account:roles')
        before = {g.name: set(g.permissions.values_list('pk', flat=True)) for g in Group.objects.all()}
        for method in (self.client.post, self.client.put, self.client.delete):
            self.assertEqual(method(url, {'name': 'Tampered'}).status_code, 405)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(before, {g.name: set(g.permissions.values_list('pk', flat=True)) for g in Group.objects.all()})
        self.assertFalse(self.admin.groups.exists())

    def test_personal_access_combines_groups_and_direct_grants_without_other_users(self):
        self.user.groups.add(Group.objects.get(name='Help Desk'))
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='projects', codename='add_project'))
        other = get_user_model().objects.create_user(username='private-other-user', email='private@example.test')
        other.groups.add(Group.objects.get(name='Project Manager'))
        self.client.force_login(self.user)
        response = self.client.get(reverse('account:index'), {'user': other.pk})
        self.assertContains(response, self.user.email)
        self.assertNotContains(response, other.email)
        self.assertNotContains(response, other.username)
        access = {row['label']: row['allowed'] for row in response.context['capabilities']}
        self.assertTrue(access['Create tickets'])
        self.assertTrue(access['Create projects'])
        self.assertFalse(access['Edit knowledge'])
        self.assertNotContains(response, 'href="' + reverse('account:roles'))
        self.assertNotContains(response, 'action="/password"')
        self.assertNotContains(response, 'upload.wikimedia.org')

    def test_revocation_union_and_partial_grants_reflect_next_request(self):
        self.user.groups.add(Group.objects.get(name='Help Desk'), Group.objects.get(name='Project Manager'))
        self.client.force_login(self.user)
        def capability(label):
            return next(r['allowed'] for r in self.client.get(reverse('account:index')).context['capabilities'] if r['label'] == label)
        self.assertTrue(capability('Create projects'))
        self.user.groups.remove(Group.objects.get(name='Project Manager'))
        self.assertFalse(capability('Create projects'))
        self.assertTrue(capability('Create tickets'))
        self.user.groups.clear()
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='issues', codename='add_issue'))
        self.assertFalse(capability('Create tickets'))
        self.grant(self.staff, 'view_group')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('account:roles')).status_code, 200)
        self.staff.user_permissions.clear()
        self.assertEqual(self.client.get(reverse('account:roles')).status_code, 403)

    def test_empty_account_guidance_and_superuser_access_are_truthful(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('account:index'))
        self.assertContains(response, 'No team groups assigned')
        self.assertFalse(any(r['allowed'] for r in response.context['capabilities']))
        self.client.force_login(self.admin)
        response = self.client.get(reverse('account:index'))
        self.assertContains(response, 'Superuser: full model access')
        self.assertTrue(all(r['allowed'] for r in response.context['capabilities']))

    def test_group_matrix_reports_actual_complete_route_grants(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('account:roles'))
        rows = {r['group'].name: r for r in response.context['role_rows']}
        self.assertEqual(set(rows), set(ROLE_PERMISSIONS))
        for name, row in rows.items():
            self.assertEqual(set(row['grants']), ROLE_PERMISSIONS[name])
            self.assertEqual(row['missing'], [])
            self.assertEqual(row['additional'], [])
            caps = {c['label']: c['allowed'] for c in row['capabilities']}
            self.assertEqual(caps['Create projects'], name == 'Project Manager')
            self.assertEqual(caps['Create tickets'], name == 'Help Desk')
            self.assertFalse(caps['Delete knowledge'])
