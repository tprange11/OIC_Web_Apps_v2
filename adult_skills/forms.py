from django import forms
from adult_skills.models import AdultSkillsSkateSession


class CreateAdultSkillsSkateSessionForm(forms.ModelForm):
    '''Form used to sign up for adult skills skate sessions.'''

    class Meta:
        model = AdultSkillsSkateSession
        exclude = ['paid']
        widgets = {
            'skater': forms.HiddenInput(),
            'skate_date': forms.HiddenInput(),
        }
        labels = {'goalie': 'Goalie?', }
