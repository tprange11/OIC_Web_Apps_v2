from django.test import TestCase

from programs.tests.base import ProgramAppTestMixin
from .models import StickAndPuckDate, StickAndPuckSkater, StickAndPuckSession


class StickAndPuckTests(ProgramAppTestMixin, TestCase):
    '''Stick and puck sessions carry the calendar date/time themselves (no FK to
    StickAndPuckDate), the registrant is a StickAndPuckSkater owned by a guardian,
    and the remove view has a GET confirm page.'''
    app_label = 'stickandpuck'
    url_ns = 'stickandpuck'
    list_url_name = 'sessions'
    register_url_name = 'signup'
    remove_url_name = 'delete-session'
    date_model = StickAndPuckDate
    session_model = StickAndPuckSession
    program_kwargs = {'pk': 2, 'program_name': 'Stick and Puck'}
    date_attr = 'session_date'
    start_time_attr = 'session_start_time'
    owner_field = 'guardian'
    date_defaults = {'session_start_time': '10:00 AM', 'session_end_time': '11:00 AM',
                     'session_notes': 'All ages'}
    goalie_aware = False
    # Joined by the create view (Group.objects.get only catches IntegrityError).
    group_name = 'Stick and Puck'
    skip_tests = {
        # The remove view deliberately allows GET: it renders a confirm page.
        'test_remove_get_not_allowed',
    }

    def sp_skater(self, user):
        skater, _ = StickAndPuckSkater.objects.get_or_create(
            guardian=user, first_name=user.first_name, last_name=user.last_name,
            date_of_birth='2010-01-01')
        return skater

    def session_date_kwargs(self, date_row):
        return {'session_date': date_row.session_date,
                'session_time': date_row.session_start_time}

    def session_extra(self, user):
        return {'skater': self.sp_skater(user)}

    def cart_skater_name(self, user):
        return str(self.sp_skater(user))

    def register_post(self, user, date_row):
        # guardian is set from request.user
        return {'skater': self.sp_skater(user).pk,
                'session_date': date_row.session_date.isoformat(),
                'session_time': date_row.session_start_time}

    def test_remove_get_shows_confirm_page(self):
        a = self.make_user()
        session = self.make_session(a, self.make_date(), paid=True)
        self.login(a)
        response = self.client.get(self.remove_url(session))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.session_model.objects.filter(pk=session.pk).exists())
