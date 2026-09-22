from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import OWHLSkateDate, OWHLSkateSession


class OWHLTests(ProgramAppTestMixin, TestCase):
    app_label = 'owhl'
    url_ns = 'owhl'
    list_url_name = 'owhl'
    date_model = OWHLSkateDate
    session_model = OWHLSkateSession
    # Caps are read from Program pk 13, prices/cart item by name 'OWHL Hockey'.
    program_kwargs = {'pk': 13, 'program_name': 'OWHL Hockey'}
    date_defaults = {'start_time': '8:00 PM', 'end_time': '9:30 PM'}
    group_name = 'OWHL Hockey'
