from django.apps import AppConfig
from watson import search as watson

class IssuesConfig(AppConfig):
    name = 'issues'
    def ready(self):
        Issue = self.get_model("Issue")
        watson.register(Issue)
