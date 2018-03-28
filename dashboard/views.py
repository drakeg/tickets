import datetime
from django.shortcuts import render, redirect
from inventory.models import Server
from issues.models import Issue
from projects.models import Project

def index(request):
    max_systems = 2000
    num_systems = Server.objects.all().count()
    percent_systems = str(num_systems/max_systems * 100) + "%"
    max_my_issues = 100
    num_my_issues = (Issue.objects.filter(issue_open__exact='True') & Issue.objects.filter(assigned__exact=request.user.id)).count()
    percent_my_issues = str(num_my_issues/max_my_issues * 100) + "%"
    max_open_issues = 100
    num_open_issues = Issue.objects.filter(issue_open__exact='True').count()
    percent_open_issues = str(num_open_issues/max_open_issues * 100) + "%"
    max_open_projects = 100
    num_open_projects = Project.objects.filter(end_date__gte=datetime.date.today()).count()
    percent_open_projects = str(num_open_projects/max_open_projects * 100) + "%"
    return render(
        request,
        'dashboard/home.html',
        context={'num_systems':num_systems, 'percent_systems':percent_systems, 'max_systems':max_systems,
                 'num_my_issues':num_my_issues, 'percent_my_issues':percent_my_issues, 'max_my_issues':max_my_issues,
                 'num_open_issues':num_open_issues, 'percent_open_issues':percent_open_issues, 'max_open_issues':max_open_issues,
                 'num_open_projects': num_open_projects, 'percent_open_projects': percent_open_projects,'max_open_projects': max_open_projects,
                 }
    )
