from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import EmployeeAdminCreationForm, EmployeeAdminChangeForm
from .models import Employee

class EmployeeAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = EmployeeAdminChangeForm
    add_form = EmployeeAdminCreationForm

    # The fields to be used in displaying the Employee model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'lname', 'fname', 'email', 'is_admin', 'is_active')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('lname', 'fname',)}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email', 'username', 'lname',)
    ordering = ('username', 'email', 'lname',)
    filter_horizontal = ()


admin.site.register(Employee, EmployeeAdmin)

# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)