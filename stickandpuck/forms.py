from django import forms
from stickandpuck.models import StickAndPuckSkater, StickAndPuckSession
from django.contrib.auth import get_user_model
User = get_user_model()

class StickAndPuckSkaterForm(forms.ModelForm):
    '''Form for adding a (minor) skater to the user's account.'''
    
    class Meta:
        model = StickAndPuckSkater
        fields = ('first_name', 'last_name', 'date_of_birth')
        help_texts = {
            'date_of_birth': 'mm/dd/yyyy',
        }
        

class StickAndPuckSignupForm(forms.ModelForm):
    '''Form for signing a skater up for a stick and puck session.'''

    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        # Only offer the skaters that belong to this user
        self.fields['skater'].queryset = StickAndPuckSkater.objects.filter(guardian=self.user)
    

    class Meta:
        model = StickAndPuckSession
        fields = ('skater', 'session_date', 'session_time')
