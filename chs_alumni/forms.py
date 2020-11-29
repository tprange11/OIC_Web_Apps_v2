from django import forms
from chs_alumni.models import CHSAlumniSession


class CreateCHSAlumniSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for CHS Alumni skate sessions.'''

    class Meta:
        model = CHSAlumniSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
