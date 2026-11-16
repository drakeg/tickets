from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse

from inventory.models import Server
from issues.models import Issue
from projects.models import Project
from knowledgebase.models import Article


@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    sources = (
        ('issues.view_issue', Issue, ('summary', 'description'), 'summary', 'issues:issue', 'Ticket'),
        ('projects.view_project', Project, ('summary', 'description'), 'summary', 'projects:project', 'Project'),
        ('inventory.view_server', Server, ('server_name',), 'server_name', 'inventory:servers', 'System'),
        ('knowledgebase.view_article', Article, ('description', 'keywords', 'problem', 'solution'),
         'description', 'knowledgebase:detail', 'Article'),
    )
    allowed = [source for source in sources if request.user.has_perm(source[0])]
    if not allowed:
        raise PermissionDenied
    results = []
    if query:
        for permission, model, fields, title, route, label in allowed:
            condition = Q()
            for field in fields:
                condition |= Q(**{field + '__icontains': query})
            # Bound each permitted section; never query or expose denied models.
            for item in model.objects.filter(condition).order_by('-pk')[:10]:
                results.append({'title': getattr(item, title), 'url': reverse(route, args=[item.pk]),
                                'kind': label})
    return render(request, 'dashboard/search.html', {'query': query, 'results': results})
