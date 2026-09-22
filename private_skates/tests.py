from django.test import TestCase
from django.urls import reverse

from programs.tests.base import ChildSkaterAppMixin
from .models import PrivateSkate, PrivateSkateDate, PrivateSkateSession


class PrivateSkatesTests(ChildSkaterAppMixin, TestCase):
    '''Private skates have no programs.Program row: name, caps and prices live on
    the PrivateSkate row, the date row is linked to it and the list URL takes the
    skate's slug.'''
    app_label = 'private_skates'
    url_ns = 'private_skates'
    list_url_name = 'skate-dates'
    remove_url_name = 'remove-session'
    date_model = PrivateSkateDate
    session_model = PrivateSkateSession
    program_kwargs = {'program_name': 'Test Private Skate'}
    date_attr = 'date'
    date_defaults = {'start_time': '20:00', 'end_time': '21:30'}
    # The list view joins the user to the group named after the slug.
    group_name = 'test-private-skate'

    def create_program(self):
        return PrivateSkate.objects.create(
            name=self.program_kwargs['program_name'], slug='test-private-skate',
            max_skaters=self.max_skaters, max_goalies=2,
            skater_price=self.skater_price, goalie_price=self.goalie_price)

    def make_date(self, **overrides):
        overrides.setdefault('private_skate', self.program)
        return super().make_date(**overrides)

    def list_url(self):
        return reverse('private_skates:skate-dates', kwargs={'slug': self.program.slug})

    def register(self, client, user, date_row, **post):
        # The template POSTs back to register/<pk>/ (the bare register/ route is
        # shadowed by the <slug>/ list route above it in urls.py and never used).
        data = self.register_post(user, date_row)
        data.update(post)
        return client.post(reverse('private_skates:register', kwargs={'pk': date_row.pk}), data)
