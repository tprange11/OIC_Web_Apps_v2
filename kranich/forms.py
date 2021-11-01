from django import forms
from kranich.models import KranichSkateSession


class CreateKranichSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Kranich skate sessions.'''

    class Meta:
        model = KranichSkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
