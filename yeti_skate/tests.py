from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import YetiSkateDate, YetiSkateSession


class YetiSkateTests(ProgramAppTestMixin, TestCase):
    app_label = 'yeti_skate'
    url_ns = 'yeti_skate'
    list_url_name = 'yeti-skate'
    date_model = YetiSkateDate
    session_model = YetiSkateSession
    program_kwargs = {'pk': 7, 'program_name': 'Yeti Skate'}
    date_defaults = {'start_time': '6:00 AM', 'end_time': '7:30 AM'}
    # Goalies never pay in this program, so removing a paid goalie refunds nothing.
    goalie_refund_amount = 0
