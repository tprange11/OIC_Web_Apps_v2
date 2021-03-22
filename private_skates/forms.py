from django import forms
from private_skates.models import PrivateSkateSession
from accounts.models import ChildSkater


class PrivateSkateSessionForm(forms.ModelForm):
    '''Form used to register for Private Skate sessions.'''

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['skater'].queryset = ChildSkater.objects.filter(user=self.user)
    
    class Meta:
        model = PrivateSkateSession
        exclude = ['paid']
        widgets = {
            'user': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?'}
