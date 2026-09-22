from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import NachoSkateDate, NachoSkateSession


class NachoSkateTests(ProgramAppTestMixin, TestCase):
    app_label = 'nacho_skate'
    url_ns = 'nacho_skate'
    list_url_name = 'index'
    date_model = NachoSkateDate
    emails_on_removal = True
    session_model = NachoSkateSession
    program_kwargs = {'pk': 15, 'program_name': 'Nacho Skate'}
    date_defaults = {'start_time': '20:00', 'end_time': '21:30'}
    group_name = 'Nacho Skate'
