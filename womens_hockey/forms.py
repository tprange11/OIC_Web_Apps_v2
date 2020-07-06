from django import forms
from womens_hockey.models import WomensHockeySkateSession
from accounts.models import ChildSkater

class CreateWomensHockeySkateSessionForm(forms.ModelForm):
    '''Form used to sign up for Womens Hockey skate sessions.'''

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['skater'].queryset = ChildSkater.objects.filter(user=self.user)

    class Meta:
        model = WomensHockeySkateSession
        exclude = ['paid']
        widgets = {
            'user': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
