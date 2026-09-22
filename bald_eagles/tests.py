from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import BaldEaglesSkateDate, BaldEaglesSession


class BaldEaglesTests(ProgramAppTestMixin, TestCase):
    app_label = 'bald_eagles'
    url_ns = 'bald_eagles'
    list_url_name = 'bald-eagles'
    date_model = BaldEaglesSkateDate
    session_model = BaldEaglesSession
    program_kwargs = {'pk': 9, 'program_name': 'Bald Eagles'}
    date_field = 'session_date'
    date_defaults = {'start_time': '8:00 PM', 'end_time': '9:30 PM'}
    group_name = 'Bald Eagles'
