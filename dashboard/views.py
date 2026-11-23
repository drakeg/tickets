import datetime
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import render
from inventory.models import Server
from issues.models import Issue
from projects.models import Project

def index(request):
    max_systems = 2000
    num_systems = Server.objects.count() if request.user.has_perm('inventory.view_server') else 0
    percent_systems = str(num_systems/max_systems * 100) + "%"
    max_my_issues = 100
    num_my_issues = Issue.objects.filter(issue_open=True, assigned=request.user.id).count() if request.user.has_perm('issues.view_issue') else 0
    percent_my_issues = str(num_my_issues/max_my_issues * 100) + "%"
    max_open_issues = 100
    num_open_issues = Issue.objects.filter(issue_open=True).count() if request.user.has_perm('issues.view_issue') else 0
    percent_open_issues = str(num_open_issues/max_open_issues * 100) + "%"
    # Derive actionable aging metrics only for users with ticket-read grants.
    # The thresholds match the ticket queue's age filter and are not SLA breaches.
    aging = {'older_3': 0, 'older_7': 0}
    if request.user.has_perm('issues.view_issue'):
        now = timezone.now()
        aging = Issue.objects.filter(issue_open=True).aggregate(
            older_3=Count('pk', filter=Q(pub_date__lte=now - timedelta(days=3))),
            older_7=Count('pk', filter=Q(pub_date__lte=now - timedelta(days=7))),
        )
    num_unassigned_open = (
        Issue.objects.filter(issue_open=True, assigned__isnull=True).count()
        if request.user.has_perm('issues.view_issue') else 0
    )
    max_open_projects = 100
    num_open_projects = Project.objects.filter(end_date__gte=datetime.date.today()).count() if request.user.has_perm('projects.view_project') else 0
    percent_open_projects = str(num_open_projects/max_open_projects * 100) + "%"
    return render(
        request,
        'dashboard/home.html',
        context={'num_systems':num_systems, 'percent_systems':percent_systems, 'max_systems':max_systems,
                 'num_my_issues':num_my_issues, 'percent_my_issues':percent_my_issues, 'max_my_issues':max_my_issues,
                 'num_open_issues':num_open_issues, 'percent_open_issues':percent_open_issues, 'max_open_issues':max_open_issues,
                 'num_aging_3_days':aging['older_3'], 'num_aging_7_days':aging['older_7'],
                 'num_unassigned_open':num_unassigned_open,
                 'num_open_projects': num_open_projects, 'percent_open_projects': percent_open_projects,'max_open_projects': max_open_projects,
                 }
    )