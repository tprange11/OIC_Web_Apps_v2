from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import CHSAlumniDate, CHSAlumniSession


class CHSAlumniTests(ProgramAppTestMixin, TestCase):
    app_label = 'chs_alumni'
    url_ns = 'chs_alumni'
    list_url_name = 'chs-alumni'
    date_model = CHSAlumniDate
    session_model = CHSAlumniSession
    program_kwargs = {'pk': 11, 'program_name': 'CHS Alumni'}
    date_field = 'date'
    date_defaults = {'start_time': '20:00', 'end_time': '21:30'}
    group_name = 'CHS Alumni'
