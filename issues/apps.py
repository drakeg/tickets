from django.apps import AppConfig

class IssuesConfig(AppConfig):
    name = 'issues'
    def ready(self):
        Issue = self.get_model("Issue")
