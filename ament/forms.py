from django import forms
from ament.models import AmentSkateSession


class CreateAmentSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Ament skate sessions.'''

    class Meta:
        model = AmentSkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
