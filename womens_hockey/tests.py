from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import WomensHockeySkateDate


class WomensHockeySkateDateOrderingTests(TestCase):
    '''Regression: upcoming skate dates must be listed chronologically,
    regardless of the order they were entered (Django >= 3.1 ignores
    Meta.ordering on values().annotate() GROUP BY queries).'''

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='skater', password='pw')
        # The list view adds every visitor to the Womens Hockey group (id=8).
        Group.objects.create(id=8, name='Womens Hockey')

        today = date.today()
        # Deliberately insert out of chronological order so pk order != date order
        for offset in (13, 27, 6, 20):
            WomensHockeySkateDate.objects.create(
                skate_date=today + timedelta(days=offset),
                start_time='8:00 PM', end_time='9:30 PM')
        # A past date must not appear at all
        WomensHockeySkateDate.objects.create(
            skate_date=today - timedelta(days=1),
            start_time='8:00 PM', end_time='9:30 PM')

    def test_skate_dates_listed_chronologically(self):
        self.client.login(username='skater', password='pw')
        response = self.client.get(reverse('womens_hockey:womens-hockey'))
        self.assertEqual(response.status_code, 200)

        skate_dates = response.context['skate_dates']
        # SQLite may return GROUP BY rows in index order by luck; MySQL (production)
        # does not. Require an explicit ORDER BY on the query itself.
        self.assertTrue(skate_dates.ordered,
                        'skate date queryset has no explicit ordering')

        listed = [row['skate_date'] for row in skate_dates]
        self.assertEqual(len(listed), 4)
        self.assertEqual(listed, sorted(listed))
        self.assertTrue(all(d >= date.today() for d in listed))
