from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import Project 
from .forms import ProjectForm

def _project_list(request, projects, title):
    page = Paginator(
        projects.select_related('assigned').order_by('-pub_date', '-pk'), 15
    ).get_page(request.GET.get('page'))
    query = request.GET.get('q', '').strip()
    return render(request, 'projects/project_list.html', {
        'project_list': page.object_list,
        'page_obj': page,
        'queue_title': title,
        'query': query,
    })


def index(request):
    return _project_list(request, Project.objects.all(), 'All projects')


def project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, 'projects/project_single.html', {'project': project})


@login_required
def my_projects(request):
    return _project_list(request, Project.objects.filter(assigned=request.user), 'My projects')


def unassigned_projects(request):
    return _project_list(request, Project.objects.filter(assigned__isnull=True), 'Unassigned projects')


@login_required
def project_new(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.requestor_name = request.user.username
            project.pub_date = timezone.now()
            project.save()
            return redirect("projects:project", project_id=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'projects/project_new.html', {'form': form})


def search(request):
    query = request.GET.get('q', '').strip()
    project_list = Project.objects.none()
    if query:
        project_list = Project.objects.filter(
            Q(summary__icontains=query) | Q(description__icontains=query)
        )
    return _project_list(request, project_list, 'Project search results')
