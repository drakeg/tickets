from django import forms

from .models import Server, Vendor


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ('server_name', 'os', 'vendor', 'cluster')

    def clean_server_name(self):
        name = self.cleaned_data['server_name'].strip()
        if not name:
            raise forms.ValidationError('Enter a system name.')
        return name

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get('server_name')
        cluster = cleaned.get('cluster')
        if name and cluster:
            existing = Server.objects.filter(
                cluster=cluster, server_name__iexact=name,
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                self.add_error(
                    'server_name',
                    'A system with this name already exists in the selected cluster.',
                )
        return cleaned


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ('vendor_name',)
