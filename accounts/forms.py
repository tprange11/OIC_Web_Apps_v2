from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms
from accounts.models import Profile


class UserCreateForm(UserCreationForm):
    '''Form used to sign up for a user account.'''

    class Meta:
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'User Name'
        self.fields['username'].widget.attrs.pop('autofocus', None)
        self.fields['email'].label = 'Email Address'
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True


class ProfileForm(forms.ModelForm):
    '''Form used to update a users profile'''

    class Meta:
        model = Profile
        fields = ('user', 'open_hockey_email', 'stick_and_puck_email', 'figure_skating_email')
        widgets = {'user': forms.HiddenInput()}
        labels = {
            'open_hockey_email': 'Receive Open Hockey emails.',
            'stick_and_puck_email': 'Receive Stick and Puck emails.',
            'figure_skating_email': 'Receive Figure Skating emails.',
        }
