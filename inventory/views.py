from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.contrib.auth.decorators import login_required, permission_required

from .models import Server
from .forms import (
    IDENTITY_CONFLICT_MESSAGE, InventoryForm, VendorForm, is_identity_conflict,
)

def _server_list(request, servers):
    page = Paginator(
        servers.select_related('os', 'vendor', 'cluster').order_by('cluster_id', 'server_name', 'pk'),
        15,
    ).get_page(request.GET.get('page'))
    return render(request, 'inventory/server_list.html', {
        'server_list': page.object_list,
        'page_obj': page,
        'query': request.GET.get('q', '').strip(),
    })


@login_required
@permission_required('inventory.view_server', raise_exception=True)
def index(request):
    return _server_list(request, Server.objects.all())


@login_required
@permission_required('inventory.view_server', raise_exception=True)
def servers(request, server_id):
	server = get_object_or_404(Server, pk=server_id)
	return render(request, 'inventory/server_single.html', {'server': server})

@login_required
@permission_required('inventory.view_operating_system', raise_exception=True)
def operating_systems(request, operating_system_id):
	response = "You're looking at operating system %s."
	return HttpResponse(response % operating_system_id)

@login_required
@permission_required(('inventory.view_server', 'inventory.add_server', 'inventory.view_operating_system', 'inventory.view_vendor', 'inventory.view_cluster'), raise_exception=True)
def servers_new(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            server = form.save(commit=False)
            server.pub_date = timezone.now()
            try:
                with transaction.atomic():
                    server.save()
            except IntegrityError as error:
                if not is_identity_conflict(error):
                    raise
                form.add_error('server_name', IDENTITY_CONFLICT_MESSAGE)
            else:
                return redirect('inventory:servers', server_id=server.pk)
    else:
        form = InventoryForm()
    missing_reference_data = [
        label for field, label in (
            ('os', 'operating systems'), ('vendor', 'vendors'), ('cluster', 'clusters')
        ) if not form.fields[field].queryset.exists()
    ]
    return render(request, 'inventory/server_new.html', {
        'form': form, 'missing_reference_data': missing_reference_data,
    })


@login_required
@permission_required('inventory.view_server', raise_exception=True)
def search(request):
    query = request.GET.get('q', '').strip()
    servers = Server.objects.none()
    if query:
        servers = Server.objects.filter(server_name__icontains=query)
    return _server_list(request, servers)

@login_required
@permission_required(('inventory.add_vendor', 'inventory.view_vendor'), raise_exception=True)
def vendor_new(request):
	if request.method == "POST":
		form = VendorForm(request.POST)
		if form.is_valid():
			vendor = form.save(commit=False)
			vendor.vendor_name = form.cleaned_data['vendor_name']
			vendor.save()
	else:
		form = VendorForm()
	return render(request, 'inventory/vendor_new.html', {'form': form})