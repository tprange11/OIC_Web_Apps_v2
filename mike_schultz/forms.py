from django import forms
from mike_schultz.models import MikeSchultzSkateSession


class CreateMikeSchultzSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Thane Storck skate sessions.'''

    class Meta:
        model = MikeSchultzSkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
