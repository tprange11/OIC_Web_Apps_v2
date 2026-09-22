from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import AdultSkillsSkateDate, AdultSkillsSkateSession


class AdultSkillsTests(ProgramAppTestMixin, TestCase):
    app_label = 'adult_skills'
    url_ns = 'adult_skills'
    list_url_name = 'adult-skills'
    date_model = AdultSkillsSkateDate
    session_model = AdultSkillsSkateSession
    # The cart item name is hard-coded as 'Adult Skills' in the create/delete views.
    program_kwargs = {'pk': 5, 'program_name': 'Adult Skills'}
    date_defaults = {'start_time': '8:00 PM', 'end_time': '9:30 PM'}
    group_name = 'Adult Skills'
