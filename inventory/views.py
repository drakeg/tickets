from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.http import HttpResponse
from django.template import loader

from .models import Server

def index(request):
	server_list = Server.objects.order_by('cluster')[:15]
	context = {'server_list': server_list}
	return render(request, 'inventory/server_list.html', context)

def servers(request, server_id):
	server = get_object_or_404(Server, pk=server_id)
	return render(request, 'inventory/server_single.html', {'server': server})

def operating_systems(request, operating_system_id):
	response = "You're looking at operating system %s."
	return HttpResponse(response % operating_system_id)

def search(request):
    template = 'inventory/server_list.html'
    query = request.GET.get('q')
    if query:
        server_list = Issue.objects.filter(Q(server_name__icontains=query))
    context = {'server_list': server_list}
    return render(request, template, context)