from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone

from .models import Project 
from .forms import ProjectForm

def index(request):
        project_list = Project.objects.order_by('pub_date')[:15]
        context = {'project_list': project_list}
        return render(request, 'projects/project_list.html', context)

def project(request, project_id):
        project = get_object_or_404, pk=project_id
        return render(request, 'projects/project_single.html', {'project': project})


def my_projects(request):
        username = request.user
        project_list = Project.objects.filter(assigned=username)
        context = {'project_list': project_list}
        return render(request, 'projects/project_list.html', context)

def unassigned_projects(request):
        project_list = Project.objects.filter(assigned__isnull=True)
        context = {'project_list': project_list}
        return render(request, 'projects/project_list.html', context)

def project_new(request):
        if request.method == "POST":
                form = ProjectForm(request.POST)
                if form.is_valid():
                        project = form.save(commit=False)
                        project.requestor_name = request.user
                        project.description = form.cleaned_data['description']
                        project.pub_date = timezone.now()
                        project.save()
        else:
                form = ProjectForm()
        return render(request, 'projects/project_new.html', {'form': form})
