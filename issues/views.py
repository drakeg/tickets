from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import Http404
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods

from .models import Issue
from .forms import IssueForm, IssueTriageForm
from .services import update_ticket

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
    history = None
    if request.user.has_perm('issues.change_issue'):
        history = Paginator(issue.changes.all(), 10).get_page(request.GET.get('history_page'))
    return render(request, 'issue/issue_single.html', {'issue': issue, 'history': history})


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


@login_required
@permission_required('issues.change_issue', raise_exception=True)
@require_http_methods(['GET', 'POST'])
def issue_edit(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        try:
            form = update_ticket(issue.pk, request.POST, request.user)
        except Issue.DoesNotExist:
            raise Http404('Ticket not found')
        if not form.errors:
            return redirect('issues:issue', issue_id=issue.pk)
    else:
        form = IssueTriageForm(instance=issue)
    return render(request, 'issue/issue_edit.html', {'issue': issue, 'form': form})
