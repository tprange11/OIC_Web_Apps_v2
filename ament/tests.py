from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import AmentSkateDate, AmentSkateSession


class AmentTests(ProgramAppTestMixin, TestCase):
    app_label = 'ament'
    url_ns = 'ament'
    list_url_name = 'skate-dates'
    date_model = AmentSkateDate
    session_model = AmentSkateSession
    program_kwargs = {'pk': 16, 'program_name': 'Ament Skate'}
    date_defaults = {'start_time': '20:00', 'end_time': '21:30'}
    group_name = 'Ament'
