from django import forms
from yeti_skate.models import YetiSkateSession


class CreateYetiSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Yeti skate sessions.'''

    class Meta:
        model = YetiSkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
