from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import FigureSkatingDate, FigureSkater, FigureSkatingSession

UP_CHARGE = 3


class FigureSkatingTests(ProgramAppTestMixin, TestCase):
    '''Figure skating differs from the hockey apps: the registrant is a FigureSkater
    owned by a guardian, the session FK is `session`, capacity is per date row
    (available_spots) and the price/refund includes the date's up_down_charge.'''
    app_label = 'figure_skating'
    url_ns = 'figure_skating'
    list_url_name = 'figure-skating'
    register_url_name = 'session-register'
    date_model = FigureSkatingDate
    session_model = FigureSkatingSession
    program_kwargs = {'pk': 3, 'program_name': 'Figure Skating'}
    date_field = 'session'
    owner_field = 'guardian'
    date_defaults = {'start_time': '8:00 AM', 'end_time': '9:00 AM',
                     'available_spots': 2, 'up_down_charge': UP_CHARGE}
    goalie_aware = False
    # Joined by the create view (Group.objects.get only catches IntegrityError).
    group_name = 'Figure Skating'

    def figure_skater(self, user):
        skater, _ = FigureSkater.objects.get_or_create(
            guardian=user, first_name=user.first_name, last_name=user.last_name)
        return skater

    def session_extra(self, user):
        return {'skater': self.figure_skater(user)}

    def cart_skater_name(self, user):
        return str(self.figure_skater(user))

    def register_post(self, user, date_row):
        # guardian is set from request.user; the form only has skater + session
        return {'skater': self.figure_skater(user).pk, 'session': date_row.pk}

    def price_of(self, goalie=False):
        return self.program.skater_price + UP_CHARGE
