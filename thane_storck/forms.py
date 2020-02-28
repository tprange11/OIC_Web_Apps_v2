from django import forms
from thane_storck.models import SkateSession


class CreateSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Thane Storck skate sessions.'''

    class Meta:
        model = SkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
