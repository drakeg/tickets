from django import forms

from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ("description", "problem", "solution", "keywords")
        labels = {"description": "Title", "problem": "Issue / symptoms", "solution": "Solution"}
        widgets = {
            "problem": forms.Textarea(attrs={"rows": 5}),
            "solution": forms.Textarea(attrs={"rows": 6}),
        }


class TicketArticleForm(ArticleForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['solution'].required = True
        self.fields['solution'].help_text = 'Explain the tested steps that resolve this issue.'
