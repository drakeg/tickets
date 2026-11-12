from django import forms
from .models import Issue

class IssueForm(forms.ModelForm):
	class Meta:
		model = Issue
		fields = ('summary', 'description', 'priority', 'assigned', )


class IssueTriageForm(forms.ModelForm):
    issue_open = forms.TypedChoiceField(
        label="Status",
        choices=(("open", "Open"), ("closed", "Closed")),
        coerce=lambda value: value == "open",
    )

    class Meta:
        model = Issue
        fields = ('issue_open', 'priority', 'assigned')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['issue_open'] = 'open' if self.instance.issue_open else 'closed'
