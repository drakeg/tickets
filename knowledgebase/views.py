from django.shortcuts import render
from .models import Article 

def index(request):
    knowledgebase_list = Article.objects.order_by('pub_date')[:15]
    context = {'knowledgebase_list': knowledgebase_list}
    return render(request, 'knowledgebase/knowledgebase_list.html', context)
