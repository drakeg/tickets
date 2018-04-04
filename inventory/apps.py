from django.apps import AppConfig
from watson import search as watson

class InventoryConfig(AppConfig):
    name = 'inventory'
    def ready(self):
        Server = self.get_model("Server")
        watson.register(Server)
