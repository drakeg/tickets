from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import Issue
from .forms import IssueForm

def _issue_list(request, queryset, title):
    status = request.GET.get('status', 'all')
    if status not in ('all', 'open', 'closed'):
        status = 'all'
    if status != 'all':
        queryset = queryset.filter(issue_open=(status == 'open'))
    page = Paginator(
        queryset.select_related('assigned').order_by('-pub_date', '-pk'), 15
    ).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'issue/issue_list.html', {
        'issue_list': page.object_list,
        'page_obj': page,
        'queue_title': title,
        'status': status,
        'pagination_query': params.urlencode(),
    })


def index(request):
    return _issue_list(request, Issue.objects.all(), 'All tickets')


def issues(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    return render(request, 'issue/issue_single.html', {'issue': issue})


@login_required
def my_issues(request):
    return _issue_list(request, Issue.objects.filter(assigned=request.user), 'Assigned to me')


def unassigned_issues(request):
    return _issue_list(request, Issue.objects.filter(assigned__isnull=True), 'Unassigned tickets')


@login_required
def issue_new(request):
    if request.method == "POST":
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.requestor_name = request.user.username
            issue.pub_date = timezone.now()
            issue.save()
            return redirect('issues:issue', issue_id=issue.pk)
    else:
        form = IssueForm()
    return render(request, 'issue/issue_new.html', {'form': form})


def search(request):
    query = request.GET.get('q', '').strip()
    issue_list = Issue.objects.none()
    if query:
        issue_list = Issue.objects.filter(
            Q(summary__icontains=query) | Q(description__icontains=query)
        )
    return _issue_list(request, issue_list, 'Search results')
