from django.test import TestCase

from programs.models import Program
from programs.tests.base import ChildSkaterAppMixin
from .models import OpenRollerSkateDate, OpenRollerSkateSession


class OpenRollerTests(ChildSkaterAppMixin, TestCase):
    app_label = 'open_roller'
    url_ns = 'open_roller'
    list_url_name = 'open-roller'
    date_model = OpenRollerSkateDate
    session_model = OpenRollerSkateSession
    # Prices and cart item are looked up by name 'Open Roller Hockey'.
    program_kwargs = {'pk': 12, 'program_name': 'Open Roller Hockey'}
    date_defaults = {'start_time': '8:00 PM', 'end_time': '9:30 PM'}
    group_name = 'Open Roller Hockey'

    def create_program(self):
        # Known bug: CreateOpenRollerSkateSessionView reads max_skaters/max_goalies
        # from Program pk 6 (Mike Schultz). Both rows are created so the view works;
        # the caps on pk 6 are what the "full" test exercises.
        Program.objects.create(pk=6, program_name='Mike Schultz',
                               max_skaters=self.max_skaters, max_goalies=2,
                               skater_price=99, goalie_price=99)
        return super().create_program()
