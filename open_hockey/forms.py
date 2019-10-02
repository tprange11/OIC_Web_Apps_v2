from django import forms
from open_hockey.models import OpenHockeySessions, OpenHockeyMember
from django.contrib.auth.models import User

class OpenHockeySignupForm(forms.ModelForm):
    '''Form used to sign up for open hockey sessions.'''

    class Meta:
        model = OpenHockeySessions
        fields = ('skater', 'date', 'goalie')

    date = forms.CharField(disabled=True)


class OpenHockeyMemberForm(forms.ModelForm):
    '''Form used by staff to add open hockey members.'''

    class Meta():
        model = OpenHockeyMember
        fields = ('member', 'end_date', 'active')

    # member = forms.ChoiceField(disabled=True)