from django.test import TestCase

from programs.models import Program
from programs.tests.base import ChildSkaterAppMixin
from .models import LadyHawksSkateDate, LadyHawksSkateSession


class LadyHawksTests(ChildSkaterAppMixin, TestCase):
    app_label = 'lady_hawks'
    url_ns = 'lady_hawks'
    list_url_name = 'lady-hawks'
    date_model = LadyHawksSkateDate
    session_model = LadyHawksSkateSession
    # Cart item name is hard-coded as 'Lady Hawks'; prices come from Program pk 10.
    program_kwargs = {'pk': 10, 'program_name': 'Lady Hawks'}
    date_defaults = {'start_time': '8:00 PM', 'end_time': '9:30 PM'}
    group_name = 'Lady Hawks'

    def create_program(self):
        # Known bug: CreateLadyHawksSkateSessionView reads max_skaters/max_goalies
        # from Program pk 6 (Mike Schultz), not pk 10. Both rows are created so the
        # view works; the caps on pk 6 are what the "full" test exercises.
        Program.objects.create(pk=6, program_name='Mike Schultz',
                               max_skaters=self.max_skaters, max_goalies=2,
                               skater_price=99, goalie_price=99)
        return super().create_program()
