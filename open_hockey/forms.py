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
    '''Form used to sign up for open hockey membership.'''

    class Meta():
        model = OpenHockeyMember
        fields = ('member', 'member_type', 'end_date', 'active')
        widgets = {'member': forms.HiddenInput(), 'end_date': forms.HiddenInput(), 'active': forms.HiddenInput()}
        labels = {
            'member_type': 'Choose Membership Type',
        }
