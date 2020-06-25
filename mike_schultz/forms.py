from django import forms
from mike_schultz.models import MikeSchultzSkateSession
from accounts.models import ChildSkater

class CreateMikeSchultzSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Mike Schultz skate sessions.'''

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['skater'].queryset = ChildSkater.objects.filter(user=self.user)

    class Meta:
        model = MikeSchultzSkateSession
        exclude = ['paid']
        widgets = {
            'user': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
