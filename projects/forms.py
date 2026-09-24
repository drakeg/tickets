from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
	class Meta:
		model = Project
		fields = ('summary', 'description', 'start_date', 'end_date', 'assigned',)
