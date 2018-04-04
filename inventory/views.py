from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q

from .models import Server
from .forms import InventoryForm

def index(request):
	server_list = Server.objects.order_by('cluster')[:15]
	context = {'server_list': server_list}
	return render(request, 'inventory/server_list.html', context)

def servers(request, server_id):
	server = get_object_or_404(Server, pk=server_id)
	return render(request, 'inventory/server_single.html', {'server': server})

def operating_systems(operating_system_id):
	response = "You're looking at operating system %s."
	return HttpResponse(response % operating_system_id)

def servers_new(request):
	if request.method == "POST":
		form = InventoryForm(request.POST)
		if form.is_valid():
			server = form.save(commit=False)
			server.server_name = form.cleaned_data['server_name']
			server.os = form.cleaned_data['os']
			server.vendor = form.cleaned_data['vendor']
			server.pub_date = timezone.now()
			server.save()
	else:
		form = InventoryForm()
	return render(request, 'inventory/server_new.html', {'form': form})

def search(request):
    template = 'inventory/server_list.html'
    query = request.GET.get('q')
    if query:
        server_list = Server.objects.filter(Q(server_name__icontains=query))
    context = {'server_list': server_list}
    return render(request, template, context)