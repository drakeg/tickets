from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.http import HttpResponse
from django.template import loader
from django.utils import timezone

from .models import Issue
from .forms import IssueForm

def index(request):
        issue_list = Issue.objects.order_by('pub_date')[:15]
        context = {'issue_list': issue_list}
        return render(request, 'issue/issue_list.html', context)

def issues(request, issue_id):
        issue = get_object_or_404(Issue, pk=issue_id)
        return render(request, 'issue/issue_single.html', {'issue': issue})

def my_issues(request, issue_id):
        response = "You're looking at issue %s."
        return HttpResponse(response % issue_id)

def issue_new(request):
	if request.method == "POST":
		form = IssueForm(request.POST)
		if form.is_valid():
			issue = form.save(commit=False)
			issue.requestor_name = request.user
			issue.description = form.cleaned_data['description']
			issue.pub_date = timezone.now()
			issue.save()
	else:
		form = IssueForm()
	return render(request, 'issue/issue_new.html', {'form': form})
