from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import SkateDate, SkateSession


class ThaneStorckTests(ProgramAppTestMixin, TestCase):
    app_label = 'thane_storck'
    url_ns = 'thane_storck'
    list_url_name = 'thane-skate'
    date_model = SkateDate
    session_model = SkateSession
    # The cart item name is hard-coded as 'Thane Storck' in the create/delete views.
    program_kwargs = {'pk': 4, 'program_name': 'Thane Storck'}
    date_defaults = {'start_time': '8:00 PM', 'end_time': '9:30 PM'}
    # Joined by the create view (Group.objects.get only catches IntegrityError).
    group_name = 'Thane Storck'
    # Goalies never pay in this program, so removing a paid goalie refunds nothing.
    goalie_refund_amount = 0
