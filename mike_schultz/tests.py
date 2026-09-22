from django.test import TestCase

from programs.tests.base import ChildSkaterAppMixin
from .models import MikeSchultzSkateDate, MikeSchultzSkateSession


class MikeSchultzTests(ChildSkaterAppMixin, TestCase):
    app_label = 'mike_schultz'
    url_ns = 'mike_schultz'
    list_url_name = 'mike-schultz'
    date_model = MikeSchultzSkateDate
    session_model = MikeSchultzSkateSession
    # Cart item name is hard-coded as 'Mike Schultz'.
    program_kwargs = {'pk': 6, 'program_name': 'Mike Schultz'}
    date_defaults = {'start_time': '8:00 PM', 'end_time': '9:30 PM'}
    group_name = 'Mike Schultz'
