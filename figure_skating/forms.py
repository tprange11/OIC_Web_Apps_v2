from django import forms
from .models import FigureSkater, FigureSkatingSession, FigureSkatingDate
from datetime import date


class CreateFigureSkaterForm(forms.ModelForm):
    '''Form where users add skaters to the FigureSkater model.'''

    class Meta:
        model = FigureSkater
        fields = ('first_name', 'last_name', 'date_of_birth')
        help_texts = {
            'date_of_birth': 'mm/dd/yyyy',
        }


class CreateFigureSkatingSessionForm(forms.ModelForm):
    '''Form where users sign up one of their skaters for a Figure Skating session.'''

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Only offer the user's own skaters and upcoming sessions
        self.fields['skater'].queryset = FigureSkater.objects.filter(guardian=self.user)
        self.fields['session'].queryset = FigureSkatingDate.objects.filter(skate_date__gte=date.today())


    class Meta:
        model = FigureSkatingSession
        fields = ('skater', 'session')

