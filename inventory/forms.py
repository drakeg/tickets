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
                original = Server.objects.filter(pk=self.instance.pk).values(
                    'server_name', 'cluster_id',
                ).first()
                # Legacy duplicates can still be edited when their identity
                # stays the same. Only newly introduced conflicts are blocked.
                if original and original['cluster_id'] == cluster.pk and (
                    (original['server_name'] or '').strip().casefold()
                    == name.casefold()
                ):
                    return cleaned
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                self.add_error(
                    'server_name',
                    'A system with this name already exists in the selected cluster.',
                )
        return cleaned


class ServerAdminForm(InventoryForm):
    """The admin retains all model fields, including publication date."""

    class Meta(InventoryForm.Meta):
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not (self.instance.server_name or '').strip():
            # Permit unrelated edits to legacy blank-name assets, but
            # never permit blank names for newly created assets.
            self.fields['server_name'].required = False

    def clean_server_name(self):
        name = (self.cleaned_data.get('server_name') or '').strip()
        if not name and self.instance.pk and not (
            self.instance.server_name or ''
        ).strip():
            return self.instance.server_name
        return super().clean_server_name()


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ('vendor_name',)
