from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms
from accounts.models import Profile, ReleaseOfLiability, ChildSkater


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
        fields = ['user', 'stick_and_puck_email', 'figure_skating_email',
                 'thane_storck_email', 'adult_skills_email', 'mike_schultz_email', 'yeti_skate_email', 
                 'womens_hockey_email']
        widgets = {'user': forms.HiddenInput()}
        labels = {
            'stick_and_puck_email': 'Receive Stick and Puck emails.',
            'figure_skating_email': 'Receive Figure Skating emails.',
            'thane_storck_email': 'Receive Thane Storck Skate emails.',
            'adult_skills_email': 'Receive Adult Skills Skate emails.',
            'mike_schultz_email': 'Receive Mike Schultz Skate emails.',
            'yeti_skate_email': 'Receive Yeti Skate emails.',
            'womens_hockey_email': 'Receive Womens Hockey Emails.',
        }


class ReleaseOfLiablityForm(forms.ModelForm):
    '''Form used for Release of Liability Agreement'''

    class Meta:
        model = ReleaseOfLiability
        fields = ['release_of_liability']
        labels = {
            'release_of_liability': 'By checking this box I AGREE to the Release of Liability'
        }


class CreateChildSkaterForm(forms.ModelForm):
    '''Form used to add child skaters to ChildSkater model.'''

    class Meta:
        model = ChildSkater
        fields = ['first_name', 'last_name', 'date_of_birth']
        # widgets = {'user': forms.HiddenInput()}
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'date_of_birth': 'Date of Birth'
        }
        help_texts = {
            'date_of_birth': 'mm/dd/yyyy',
        }
