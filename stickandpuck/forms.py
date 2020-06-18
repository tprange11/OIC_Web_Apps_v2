from django import forms
from stickandpuck.models import StickAndPuckSkater, StickAndPuckSession
from django.contrib.auth import get_user_model
User = get_user_model()

class StickAndPuckSkaterForm(forms.ModelForm):
    '''Displays page with form where users can add minor skaters to their account'''
    
    class Meta:
        model = StickAndPuckSkater
        fields = ('first_name', 'last_name', 'date_of_birth')
        help_texts = {
            'date_of_birth': 'mm/dd/yyyy',
        }
        

class StickAndPuckSignupForm(forms.ModelForm):
    '''Displays page where users can sign up for stick and puck sessions'''

    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        
        self.fields['skater'].queryset = StickAndPuckSkater.objects.filter(guardian=self.user)
    

    class Meta:
        model = StickAndPuckSession
        fields = ('skater', 'session_date', 'session_time')
