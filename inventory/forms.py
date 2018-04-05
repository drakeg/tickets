from django import forms
from .models import Server, Vendor

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ('server_name', 'os', 'vendor', 'cluster', )

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ('vendor_name',)