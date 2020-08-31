from django import forms
from .models import BaldEaglesSession


class CreateBaldEaglesSessionForm(forms.ModelForm):
    '''Form used to sign up for Bald Eagles skate sessions.'''

    class Meta:
        model = BaldEaglesSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'session_date': forms.HiddenInput(),
        }
        labels = { 'goalie': 'Goalie?' }
