from django.test import SimpleTestCase
from .models import Project

class ProjectModelTest(SimpleTestCase):
	def test_new_project_status_code(self):
		response = self.client.get('/projects/projects/new/')
		self.assertEqual(response.status_code, 200)
	def test_unassigned_project_status_code(self):
		response = self.client.get('/projects/projects/unassigned/')
		self.assertEqual(response.status_code, 200)
	def test_assigned_project_status_code(self)
		response = self.client.get('/projects/projects/my/')
                self.assertEqual(response.status_code, 200)
