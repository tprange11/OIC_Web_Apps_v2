from django import forms
from lady_hawks.models import LadyHawksSkateSession
from accounts.models import ChildSkater

class CreateLadyHawksSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Lady Hawks skate sessions.'''

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['skater'].queryset = ChildSkater.objects.filter(user=self.user)

    class Meta:
        model = LadyHawksSkateSession
        exclude = ['paid']
        widgets = {
            'user': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
