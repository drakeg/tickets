from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article


class KnowledgeBaseTests(TestCase):
    def test_index_lists_articles(self):
        article = Article.objects.create(
            author="Support",
            description="Reset a locked account",
            keywords="account,password",
            pub_date=timezone.now(),
        )

        response = self.client.get(reverse("knowledgebase:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["knowledgebase_list"]), [article])
