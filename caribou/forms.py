from django import forms
from caribou.models import CaribouSkateSession


class CreateCaribouSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Caribou skate sessions.'''

    class Meta:
        model = CaribouSkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
