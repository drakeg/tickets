from django.apps import AppConfig

class ProjectsConfig(AppConfig):
    name = 'projects'
    def read(self):
        Project = self.get_model("Project")
