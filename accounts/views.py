from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_safe

from .access import access_summary, group_summary
from .roles import ROLE_PERMISSIONS

@login_required
def index(request):
    return render(request, 'accounts/profile.html', {
        'team_groups': request.user.groups.order_by('name'),
        'capabilities': access_summary(request.user),
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('dashboard:index')
    else:
        form = UserCreationForm()

    context = {'form': form}
    return render(request, 'registration/signup.html', context)

@login_required
@permission_required('auth.view_group', raise_exception=True)
@require_safe
def roles(request):
    if not request.user.is_staff:
        raise PermissionDenied
    groups = Group.objects.order_by('name').prefetch_related('permissions__content_type')
    rows = [group_summary(group) for group in groups]
    return render(request, 'accounts/roles.html', {
        'role_rows': rows,
        'missing_groups': sorted(set(ROLE_PERMISSIONS) - {row['group'].name for row in rows}),
    })
