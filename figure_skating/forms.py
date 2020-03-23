from django import forms
from .models import FigureSkater, FigureSkatingSession, FigureSkatingDate
from datetime import date


class CreateFigureSkaterForm(forms.ModelForm):
    '''Displays page with form where users add skaters to the Figure Skater model.'''

    class Meta:
        model = FigureSkater
        fields = ('first_name', 'last_name', 'date_of_birth')
        help_texts = {
            'date_of_birth': 'mm/dd/yyyy',
        }


class CreateFigureSkatingSessionForm(forms.ModelForm):
    '''Displays page where users sign up skaters for Figure Skating sessions.'''

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        # self.session = kwargs.pop('session')
        super().__init__(*args, **kwargs)

        self.fields['skater'].queryset = FigureSkater.objects.filter(guardian=self.user)
        # self.fields['session'] = self.session
        self.fields['session'].queryset = FigureSkatingDate.objects.filter(skate_date__gte=date.today())


    class Meta:
        model = FigureSkatingSession
        fields = ('skater', 'session')

