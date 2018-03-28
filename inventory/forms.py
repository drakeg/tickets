from django import forms
from .models import Server

class InventoryForm(forms.ModelForm):
	class Meta:
		model = Server
		fields = ('server_name', 'os', 'vendor', 'cluster', )