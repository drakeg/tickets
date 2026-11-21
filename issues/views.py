import csv

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import Http404, StreamingHttpResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods

from .models import Issue, Priority
from .forms import IssueForm, IssueTriageForm
from .services import update_ticket

def _safe_spreadsheet_cell(value):
    """Avoid formula execution in CSV readers such as Excel or Sheets."""
    text = str(value) if value is not None else ''
    if text.lstrip(' \t\r\n').startswith(('=', '+', '-', '@')):
        return "'" + text
    return text


class _CSVWriter:
    def write(self, value):
        return value


def _ticket_csv(queryset, ordering):
    writer = csv.writer(_CSVWriter())

    def rows():
        yield writer.writerow((
            'Ticket ID', 'Summary', 'Requestor', 'Description',
            'Priority', 'Assignee', 'Status', 'Created (ISO 8601)',
        ))
        for ticket in queryset.select_related('priority', 'assigned').order_by(
            *ordering
        ).iterator(chunk_size=500):
            yield writer.writerow((
                ticket.pk, _safe_spreadsheet_cell(ticket.summary),
                _safe_spreadsheet_cell(ticket.requestor_name),
                _safe_spreadsheet_cell(ticket.description),
                _safe_spreadsheet_cell(ticket.priority.name),
                _safe_spreadsheet_cell(
                    ticket.assigned.get_username() if ticket.assigned_id else 'Unassigned'
                ),
                'Open' if ticket.issue_open else 'Closed',
                ticket.pub_date.isoformat(),
            ))

    response = StreamingHttpResponse(rows(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="servdesk-tickets.csv"'
    response['Cache-Control'] = 'private, no-store'
    return response


def _issue_list(request, queryset, title):
    # Offer only users who have assignments within the current queue scope.
    assignees = get_user_model().objects.filter(
        pk__in=queryset.exclude(assigned__isnull=True).values('assigned_id')
    ).order_by('username', 'pk')
    status = request.GET.get('status', 'all')
    if status not in ('all', 'open', 'closed'):
        status = 'all'
    if status != 'all':
        queryset = queryset.filter(issue_open=(status == 'open'))
    priority = request.GET.get('priority', '')
    priorities = Priority.objects.order_by('name', 'pk')
    if priority and priority.isdecimal() and priorities.filter(pk=priority).exists():
        queryset = queryset.filter(priority_id=priority)
    else:
        priority = ''
    assignee = request.GET.get('assignee', '')
    if assignee == 'unassigned':
        queryset = queryset.filter(assigned__isnull=True)
    elif (
        assignee.isdecimal() and len(assignee) <= 18
        and assignees.filter(pk=assignee).exists()
    ):
        queryset = queryset.filter(assigned_id=assignee)
    else:
        assignee = ''
    sort = request.GET.get('sort', 'newest')
    if sort not in ('newest', 'oldest'):
        sort = 'newest'
    ordering = ('pub_date', 'pk') if sort == 'oldest' else ('-pub_date', '-pk')
    if request.method == 'GET' and request.GET.get('export') == 'csv':
        return _ticket_csv(queryset, ordering)
    page = Paginator(
        queryset.select_related('assigned', 'priority').order_by(*ordering), 15
    ).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    params.pop('export', None)
    return render(request, 'issue/issue_list.html', {
        'issue_list': page.object_list,
        'page_obj': page,
        'queue_title': title,
        'status': status,
        'sort': sort,
        'priority': priority,
        'priorities': priorities,
        'assignee': assignee,
        'assignees': assignees,
        'pagination_query': params.urlencode(),
    })


@login_required
@permission_required('issues.view_issue', raise_exception=True)
def index(request):
    return _issue_list(request, Issue.objects.all(), 'All tickets')


@login_required
@permission_required('issues.view_issue', raise_exception=True)
def issues(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    history = None
    if request.user.has_perm('issues.change_issue'):
        history = Paginator(issue.changes.all(), 10).get_page(request.GET.get('history_page'))
    return render(request, 'issue/issue_single.html', {'issue': issue, 'history': history})


@login_required
@permission_required('issues.view_issue', raise_exception=True)
def my_issues(request):
    return _issue_list(request, Issue.objects.filter(assigned=request.user), 'Assigned to me')


@login_required
@permission_required('issues.view_issue', raise_exception=True)
def unassigned_issues(request):
    return _issue_list(request, Issue.objects.filter(assigned__isnull=True), 'Unassigned tickets')


@login_required
@permission_required(('issues.view_issue', 'issues.add_issue', 'issues.view_priority'), raise_exception=True)
@require_http_methods(['GET', 'POST'])
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


@login_required
@permission_required('issues.view_issue', raise_exception=True)
def search(request):
    query = request.GET.get('q', '').strip()
    issue_list = Issue.objects.none()
    if query:
        issue_list = Issue.objects.filter(
            Q(summary__icontains=query)
            | Q(description__icontains=query)
            | Q(requestor_name__icontains=query)
            | Q(assigned__username__icontains=query)
            | Q(priority__name__icontains=query)
        )
    return _issue_list(request, issue_list, 'Search results')


@login_required
@permission_required(('issues.view_issue', 'issues.change_issue', 'issues.view_priority'), raise_exception=True)
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
