from django import forms
from nacho_skate.models import NachoSkateSession


class CreateNachoSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Nacho skate sessions.'''

    class Meta:
        model = NachoSkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
