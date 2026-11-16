from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone

from .forms import ArticleForm, TicketArticleForm
from issues.models import Issue
from .models import Article


def _article_list(request, articles, query=""):
    page = Paginator(articles.order_by('-pub_date', '-pk'), 15).get_page(
        request.GET.get('page')
    )
    return render(request, "knowledgebase/knowledgebase_list.html", {
        "knowledgebase_list": page.object_list,
        "page_obj": page,
        "query": query,
    })


def index(request):
    return _article_list(request, Article.objects.all())


def article_detail(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    return render(
        request,
        "knowledgebase/knowledgebase_detail.html",
        {"article": article},
    )


@login_required
def article_new(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user.username
            article.pub_date = timezone.now()
            article.save()
            return redirect("knowledgebase:detail", article_id=article.pk)
    else:
        form = ArticleForm()

    return render(
        request,
        "knowledgebase/knowledgebase_new.html",
        {"form": form},
    )

def search(request):
    query = request.GET.get("q", "").strip()
    knowledgebase_list = Article.objects.none()
    if query:
        knowledgebase_list = Article.objects.filter(
            Q(description__icontains=query)
            | Q(problem__icontains=query)
            | Q(solution__icontains=query)
            | Q(keywords__icontains=query)
            | Q(author__icontains=query)
        ).order_by("-pub_date")

    return _article_list(request, knowledgebase_list, query)


def _can_manage_article(user, article):
    return user.is_authenticated and (
        user.is_staff or article.author == user.username
    )


@login_required
def article_edit(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if not _can_manage_article(request.user, article):
        raise PermissionDenied

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect("knowledgebase:detail", article_id=article.pk)
    else:
        form = ArticleForm(instance=article)

    return render(
        request,
        "knowledgebase/knowledgebase_edit.html",
        {"form": form, "article": article},
    )


@login_required
@require_POST
def article_delete(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if not _can_manage_article(request.user, article):
        raise PermissionDenied

    article.delete()
    return redirect("knowledgebase:index")


@login_required
@permission_required(('issues.view_issue', 'knowledgebase.add_article'), raise_exception=True)
@require_http_methods(['GET', 'POST'])
def article_from_ticket(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    existing = Article.objects.filter(source_issue=issue).first()
    if existing:
        return redirect('knowledgebase:detail', article_id=existing.pk)
    initial = {
        'description': issue.summary,
        'problem': issue.description,
        'keywords': issue.summary,
    }
    form = TicketArticleForm(request.POST if request.method == 'POST' else None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        # The unique source link makes repeated/concurrent submissions non-duplicating.
        article, created = Article.objects.get_or_create(source_issue=issue, defaults={
            **form.cleaned_data, 'author': request.user.username, 'pub_date': timezone.now(),
        })
        return redirect('knowledgebase:detail', article_id=article.pk)
    return render(request, 'knowledgebase/knowledgebase_from_ticket.html', {
        'form': form, 'issue': issue,
    })
