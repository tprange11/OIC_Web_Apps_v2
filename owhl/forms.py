from django import forms
from owhl.models import OWHLSkateSession

class CreateOWHLSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for OWHL Hockey skate sessions.'''

    class Meta:
        model = OWHLSkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
            'goalie': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
