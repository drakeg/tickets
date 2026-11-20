"""Role-aware, synthetic SMB support workflow. Never touches operator data."""
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from inventory.models import Cluster, Operating_System, Server, Vendor
from issues.models import Issue, IssueChange, Priority
from knowledgebase.models import Article
from projects.models import Project


class SmallHelpDeskDemoSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", stdout=StringIO())
        user_model = get_user_model()
        cls.helpdesk = user_model.objects.create_user(username="demo-helpdesk")
        cls.infrastructure = user_model.objects.create_user(username="demo-infrastructure")
        cls.manager = user_model.objects.create_user(username="demo-project-manager")
        for user, role in (
            (cls.helpdesk, "Help Desk"),
            (cls.infrastructure, "Infrastructure Team"),
            (cls.manager, "Project Manager"),
        ):
            user.groups.add(Group.objects.get(name=role))
        cls.priority = Priority.objects.create(name="Normal")
        cls.vendor = Vendor.objects.create(vendor_name="Fixture vendor")
        cls.cluster = Cluster.objects.create(cluster_name="Fixture cluster")
        cls.os = Operating_System.objects.create(os_name="Fixture OS")

    def test_ticket_triage_to_knowledge_reuse_and_role_boundaries(self):
        self.client.force_login(self.helpdesk)
        issue_create = reverse("issues:issue_new")
        response = self.client.post(issue_create, {
            "summary": "Demo VPN outage",
            "description": "Users cannot reach the office VPN",
            "priority": self.priority.pk,
            "assigned": self.helpdesk.pk,
        })
        self.assertEqual(response.status_code, 302)
        ticket = Issue.objects.get(summary="Demo VPN outage")
        self.assertEqual(response["Location"], reverse("issues:issue", args=[ticket.pk]))
        self.assertTrue(ticket.issue_open)
        self.assertEqual(self.client.get(reverse("issues:issue", args=[ticket.pk])).status_code, 200)

        response = self.client.post(reverse("issues:issue_edit", args=[ticket.pk]), {
            "issue_open": "closed",
            "priority": self.priority.pk,
            "assigned": self.helpdesk.pk,
        })
        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertFalse(ticket.issue_open)
        change = IssueChange.objects.get(issue=ticket)
        self.assertEqual(change.actor, self.helpdesk)
        self.assertEqual(change.after["status"], "Closed")

        response = self.client.post(reverse("knowledgebase:from_ticket", args=[ticket.pk]), {
            "description": "Office VPN recovery",
            "problem": "Users cannot reach the office VPN",
            "keywords": "VPN recovery",
            "solution": "Verify connectivity and reconnect the VPN client",
        })
        self.assertEqual(response.status_code, 302)
        article = Article.objects.get(source_issue=ticket)
        self.assertEqual(response["Location"], reverse("knowledgebase:detail", args=[article.pk]))
        self.assertEqual(self.client.get(reverse("knowledgebase:detail", args=[article.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("knowledgebase:search"), {"q": "VPN recovery"}).status_code, 200)
        self.assertEqual(Article.objects.filter(source_issue=ticket).count(), 1)

        # Help Desk can read inventory/projects, not create assets or projects.
        self.assertEqual(self.client.get(reverse("inventory:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("projects:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("inventory:servers_new")).status_code, 403)
        self.assertEqual(self.client.get(reverse("projects:project_new")).status_code, 403)

    def test_infrastructure_and_project_manager_create_their_own_records(self):
        self.client.force_login(self.infrastructure)
        payload = {
            "server_name": "demo-vpn-gateway",
            "os": self.os.pk, "vendor": self.vendor.pk, "cluster": self.cluster.pk,
        }
        response = self.client.post(reverse("inventory:servers_new"), payload)
        self.assertEqual(response.status_code, 302)
        asset = Server.objects.get(server_name="demo-vpn-gateway")
        self.assertEqual(response["Location"], reverse("inventory:servers", args=[asset.pk]))
        self.assertEqual(self.client.get(response["Location"]).status_code, 200)
        self.assertEqual(self.client.get(reverse("inventory:search"), {"q": "demo-vpn"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("projects:project_new")).status_code, 403)

        self.client.force_login(self.manager)
        response = self.client.post(reverse("projects:project_new"), {
            "summary": "VPN rollout",
            "description": "Improve VPN resiliency",
            "start_date": "2026-11-20",
            "end_date": "2026-11-25",
            "assigned": self.manager.pk,
        })
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(summary="VPN rollout")
        self.assertEqual(response["Location"], reverse("projects:project", args=[project.pk]))
        self.assertEqual(self.client.get(response["Location"]).status_code, 200)
        self.assertEqual(self.client.get(reverse("projects:search"), {"q": "VPN"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("inventory:servers_new")).status_code, 403)

    def test_anonymous_users_cannot_read_private_business_records(self):
        for name in ("issues:index", "inventory:index", "projects:index",
                     "knowledgebase:index"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
        self.assertFalse(Issue.objects.exists())
        self.assertFalse(Server.objects.exists())
        self.assertFalse(Project.objects.exists())
        self.assertFalse(Article.objects.exists())
