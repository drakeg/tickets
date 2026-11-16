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


class TeamRoleSetupTests(TestCase):
    def test_setup_creates_expected_groups_without_administration_or_delete_grants(self):
        from django.contrib.auth.models import Group
        from django.core.management import call_command
        call_command('setup_roles', verbosity=0)
        self.assertEqual(set(Group.objects.values_list('name', flat=True)), {
            'Infrastructure Team', 'Help Desk', 'Project Manager',
        })
        for group in Group.objects.all():
            self.assertFalse(group.permissions.filter(content_type__app_label='auth').exists())
            self.assertFalse(group.permissions.filter(codename__startswith='delete_').exists())
        self.assertTrue(Group.objects.get(name='Help Desk').permissions.filter(
            content_type__app_label='issues', codename='change_issue').exists())
        self.assertFalse(Group.objects.get(name='Help Desk').permissions.filter(
            content_type__app_label='inventory', codename='change_server').exists())
        self.assertTrue(Group.objects.get(name='Infrastructure Team').permissions.filter(
            content_type__app_label='inventory', codename='change_server').exists())
        self.assertTrue(Group.objects.get(name='Project Manager').permissions.filter(
            content_type__app_label='projects', codename='change_project').exists())
        self.assertFalse(Group.objects.get(name='Project Manager').permissions.filter(
            content_type__app_label='issues', codename='change_issue').exists())

    def test_setup_is_repeatable_and_preserves_custom_grants_and_memberships(self):
        from django.contrib.auth.models import Group, Permission
        from django.core.management import call_command
        call_command('setup_roles', verbosity=0)
        group = Group.objects.get(name='Help Desk')
        extra = Permission.objects.get(content_type__app_label='inventory', codename='add_server')
        group.permissions.add(extra)
        user = get_user_model().objects.create_user(username='existing-team-member')
        user.groups.add(group)
        before = set(group.permissions.values_list('pk', flat=True))
        call_command('setup_roles', verbosity=0)
        self.assertEqual(Group.objects.count(), 3)
        self.assertEqual(set(group.permissions.values_list('pk', flat=True)), before)
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.groups.filter(pk=group.pk).exists())

    def test_dry_run_writes_nothing(self):
        from django.contrib.auth.models import Group
        from django.core.management import call_command
        from io import StringIO
        output = StringIO()
        call_command('setup_roles', dry_run=True, stdout=output)
        self.assertFalse(Group.objects.exists())
        self.assertIn('would ensure', output.getvalue())

    def test_missing_permissions_fail_before_any_group_is_created(self):
        from django.contrib.auth.models import Group, Permission
        from django.core.management import call_command, CommandError
        Permission.objects.get(content_type__app_label='inventory', codename='change_server').delete()
        with self.assertRaises(CommandError):
            call_command('setup_roles')
        self.assertFalse(Group.objects.exists())

    def test_group_grants_enable_ticket_triage_without_staff_status(self):
        from django.contrib.auth.models import Group
        from django.core.management import call_command
        from issues.models import Issue, Priority
        from django.utils import timezone
        call_command('setup_roles', verbosity=0)
        user = get_user_model().objects.create_user(username='helpdesk-agent')
        user.groups.add(Group.objects.get(name='Help Desk'))
        ticket = Issue.objects.create(requestor_name='requestor', summary='Help',
            description='Request', priority=Priority.objects.create(name='Normal'),
            pub_date=timezone.now())
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('issues:issue_edit', args=[ticket.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)
