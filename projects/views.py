from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.http import HttpResponse
from django.template import loader

from .models import Project 

def index(request):
        project_list = Project.objects.order_by('pub_date')[:15]
        context = {'project_list': projects_list}
        return render(request, 'projects/project_list.html', context)

def project(request, project_id):
        project = get_object_or_404, pk=project_id
        return render(request, 'projects/project_single.html', {'project': project})

def my_issues(request, issue_id):
        response = "You're looking at issue %s."
        return HttpResponse(response % issue_id)

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
        return render(request, 'project/project_new.html', {'form': form})
