from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ArticleForm
from .models import Article


def index(request):
    knowledgebase_list = Article.objects.order_by("-pub_date")[:15]
    context = {"knowledgebase_list": knowledgebase_list}
    return render(request, "knowledgebase/knowledgebase_list.html", context)


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
