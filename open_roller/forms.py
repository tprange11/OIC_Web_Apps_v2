from django import forms
from open_roller.models import OpenRollerSkateSession
from accounts.models import ChildSkater

class CreateOpenRollerSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Open Roller Hockey skate sessions.'''

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['skater'].queryset = ChildSkater.objects.filter(user=self.user)

    class Meta:
        model = OpenRollerSkateSession
        exclude = ['paid']
        widgets = {
            'user': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
