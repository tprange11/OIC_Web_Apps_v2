from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import KranichSkateDate, KranichSkateSession


class KranichTests(ProgramAppTestMixin, TestCase):
    app_label = 'kranich'
    url_ns = 'kranich'
    list_url_name = 'kranich'
    date_model = KranichSkateDate
    session_model = KranichSkateSession
    program_kwargs = {'pk': 14, 'program_name': 'Kranich Skate'}
    date_defaults = {'start_time': '20:00', 'end_time': '21:30'}
    group_name = 'Kranich'
