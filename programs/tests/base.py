"""Shared, parametrised regression tests for the program apps.

Every program app (ament, kranich, womens_hockey, ...) has the same three moving
parts: a list page, a "register for a skate date" CreateView that either pays from
the user's credit balance or drops a Cart row, and a DeleteView built on
programs.removal.SessionRemovalMixin that refunds / clears the cart. This module
tests those behaviours once, through the test client, and each app's tests module
subclasses ProgramAppTestMixin with a handful of class attributes describing the
app (see ament/tests.py for the simplest example).

ProgramAppTestMixin is deliberately NOT a TestCase subclass, so the test runner
does not collect it on its own; the per-app class is `class XTests(ProgramAppTestMixin,
TestCase)`.

Per-app quirks are handled by overriding the small hooks below (create_program,
session_extra, cart_skater_name, register_post, ...). A test that an app genuinely
cannot pass (missing feature or a known pre-existing bug) is listed in `skip_tests`
with a comment in that app's tests module.
"""
from datetime import date, time, timedelta
from unittest import SkipTest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from accounts.models import ChildSkater, UserCredit
from cart.models import Cart
from programs.models import Program

User = get_user_model()

# User ids that the legacy views special-case (free skaters, organizers who may
# remove anyone, "free" success messages). make_user() never hands one of these out
# so the generic assertions are not skewed by which id the sequence happened to reach.
RESERVED_USER_IDS = {11, 21, 52, 359, 870}


class ProgramAppTestMixin:
    # ---- per-app configuration -------------------------------------------------
    app_label = None            # e.g. 'ament'
    url_ns = None               # URL namespace, usually == app_label
    list_url_name = None        # name of the skate-date list view
    register_url_name = 'register'      # the CreateView (the no-pk POST route)
    remove_url_name = 'session-remove'  # the DeleteView
    date_model = None           # the *Date model
    session_model = None        # the *Session model
    program_kwargs = None       # kwargs for the Program row the views look up (pk!)
    date_field = 'skate_date'   # FK on the session pointing at the date row
    date_attr = 'skate_date'    # calendar-date field on the date row
    start_time_attr = 'start_time'
    owner_field = 'skater'      # FK on the session pointing at the paying user
    date_defaults = None        # extra kwargs (times etc.) to build a date row
    goalie_aware = True         # session has a goalie flag and a goalie price
    goalie_refund_amount = None # None -> program goalie_price; 0 for apps where goalies are free
    group_name = None           # Group the list/create view auto-joins (must exist)
    group_id = None             # some views look the group up by id
    max_skaters = 2             # capacity used by the "full" test
    skater_price = 10
    goalie_price = 5
    days_ahead = 7
    skip_tests = frozenset()    # test method names this app skips (say why in a comment)

    # ---- setUp -----------------------------------------------------------------

    def setUp(self):
        super().setUp()
        test_name = self._testMethodName
        if test_name in self.skip_tests:
            raise SkipTest(f'{self.app_label}: {test_name} skipped (see skip_tests)')
        self._user_counter = 0
        if self.group_name:
            kwargs = {'name': self.group_name}
            if self.group_id:
                kwargs['id'] = self.group_id
            Group.objects.get_or_create(**kwargs)
        self.program = self.create_program()

    def create_program(self):
        '''Create the Program row the app looks up. Returns the object holding prices.'''
        kwargs = dict(self.program_kwargs)
        kwargs.setdefault('max_skaters', self.max_skaters)
        kwargs.setdefault('max_goalies', 2)
        kwargs.setdefault('skater_price', self.skater_price)
        kwargs.setdefault('goalie_price', self.goalie_price)
        return Program.objects.create(**kwargs)

    # ---- factories -------------------------------------------------------------

    def make_user(self, staff=False):
        for _ in range(5):
            self._user_counter += 1
            n = self._user_counter
            # No password hashing (tests use force_login): keeps the suite fast.
            user = User(username=f'{self.app_label}_user{n}',
                        first_name=f'First{n}', last_name=f'Last{n}',
                        email=f'user{n}@example.com', is_staff=staff)
            user.set_unusable_password()
            user.save()
            if user.pk not in RESERVED_USER_IDS:
                return user
            # Leave the reserved-id user in place (harmless) and make another.
        raise AssertionError('could not allocate a non-reserved user id')

    def login(self, user):
        self.client.force_login(user)

    def make_credit(self, user, balance, paid=True):
        credit, _ = UserCredit.objects.update_or_create(
            user=user, defaults={'balance': balance, 'paid': paid, 'slug': user.username})
        return credit

    def balance_of(self, user):
        return UserCredit.objects.get(user=user).balance

    def make_date(self, **overrides):
        kwargs = {self.date_attr: date.today() + timedelta(days=self.days_ahead)}
        kwargs.update(self.date_defaults or {})
        kwargs.update(overrides)
        return self.date_model.objects.create(**kwargs)

    def date_of(self, date_row):
        return getattr(date_row, self.date_attr)

    def start_time_of(self, date_row):
        return getattr(date_row, self.start_time_attr)

    def session_date_kwargs(self, date_row):
        '''How a session row refers to its date (FK by default).'''
        return {self.date_field: date_row}

    def session_extra(self, user):
        '''Extra kwargs needed to build a session for `user` (e.g. a ChildSkater).'''
        return {}

    def make_session(self, user, date_row, paid, goalie=False):
        kwargs = {self.owner_field: user, 'paid': paid}
        kwargs.update(self.session_date_kwargs(date_row))
        if self.goalie_aware:
            kwargs['goalie'] = goalie
        kwargs.update(self.session_extra(user))
        return self.session_model.objects.create(**kwargs)

    def cart_item(self):
        return self.program_kwargs['program_name']

    def cart_skater_name(self, user):
        '''What the app's add_to_cart stores in Cart.skater_name for this user.'''
        return user.get_full_name()

    def make_cart_row(self, user, date_row, amount=None):
        return Cart.objects.create(
            customer=user, item=self.cart_item(), skater_name=self.cart_skater_name(user),
            event_date=self.date_of(date_row), event_start_time=str(self.start_time_of(date_row)),
            amount=self.skater_price if amount is None else amount)

    def price_of(self, goalie=False):
        '''What registering costs (and what removal refunds).'''
        if goalie:
            return self.program.goalie_price
        return self.program.skater_price

    def expected_goalie_refund(self):
        if self.goalie_refund_amount is not None:
            return self.goalie_refund_amount
        return self.price_of(goalie=True)

    # ---- URLs / requests -------------------------------------------------------

    def list_url(self):
        return reverse(f'{self.url_ns}:{self.list_url_name}')

    def register_url(self):
        return reverse(f'{self.url_ns}:{self.register_url_name}')

    def remove_url(self, session):
        return reverse(f'{self.url_ns}:{self.remove_url_name}', kwargs={'pk': session.pk})

    def register_post(self, user, date_row):
        '''The POST body the registration template submits.'''
        return {self.owner_field: user.pk, self.date_field: date_row.pk}

    def register(self, client, user, date_row, **post):
        data = self.register_post(user, date_row)
        data.update(post)
        return client.post(self.register_url(), data)

    def remove(self, client, session):
        return client.post(self.remove_url(session))

    def sessions_for(self, user):
        return self.session_model.objects.filter(**{self.owner_field: user})

    # ---- tests -----------------------------------------------------------------

    def test_list_requires_login(self):
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])

    def test_list_renders_for_logged_in_user(self):
        user = self.make_user()
        self.make_date()
        self.login(user)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, 200)

    def test_register_with_sufficient_credit_marks_paid_and_deducts(self):
        user = self.make_user()
        price = self.price_of()
        self.make_credit(user, balance=price + 5)
        date_row = self.make_date()
        self.login(user)
        response = self.register(self.client, user, date_row)
        self.assertEqual(response.status_code, 302, getattr(response, 'content', b'')[:500])
        sessions = self.sessions_for(user)
        self.assertEqual(sessions.count(), 1)
        self.assertTrue(sessions.get().paid)
        self.assertEqual(self.balance_of(user), 5)
        self.assertEqual(Cart.objects.filter(customer=user).count(), 0)

    def test_register_without_credit_goes_to_cart(self):
        user = self.make_user()
        self.make_credit(user, balance=0, paid=False)
        date_row = self.make_date()
        self.login(user)
        response = self.register(self.client, user, date_row)
        self.assertEqual(response.status_code, 302, getattr(response, 'content', b'')[:500])
        session = self.sessions_for(user).get()
        self.assertFalse(session.paid)
        cart = Cart.objects.filter(customer=user)
        self.assertEqual(cart.count(), 1)
        row = cart.get()
        self.assertEqual(row.item, self.cart_item())
        self.assertEqual(row.event_date, self.date_of(date_row))
        self.assertEqual(row.amount, self.price_of())
        self.assertEqual(self.balance_of(user), 0)

    def test_register_when_skaters_full_is_refused(self):
        date_row = self.make_date()
        for _ in range(self.max_skaters):
            other = self.make_user()
            self.make_session(other, date_row, paid=True)
        before = self.session_model.objects.count()
        user = self.make_user()
        self.make_credit(user, balance=self.price_of() + 5)
        self.login(user)
        self.register(self.client, user, date_row)
        self.assertEqual(self.session_model.objects.count(), before)
        self.assertEqual(self.sessions_for(user).count(), 0)
        self.assertEqual(self.balance_of(user), self.price_of() + 5)
        self.assertEqual(Cart.objects.filter(customer=user).count(), 0)

    def test_remove_unpaid_clears_only_own_cart_row(self):
        a, b = self.make_user(), self.make_user()
        date_row = self.make_date()
        sa = self.make_session(a, date_row, paid=False)
        sb = self.make_session(b, date_row, paid=False)
        self.make_cart_row(a, date_row)
        self.make_cart_row(b, date_row)
        self.make_credit(a, 0, paid=False)
        self.login(a)
        response = self.remove(self.client, sa)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.session_model.objects.filter(pk=sa.pk).exists())
        self.assertTrue(self.session_model.objects.filter(pk=sb.pk).exists())
        self.assertEqual(Cart.objects.filter(customer=a).count(), 0)
        self.assertEqual(Cart.objects.filter(customer=b).count(), 1)
        self.assertEqual(self.balance_of(a), 0)

    def test_remove_paid_refunds_credit(self):
        a = self.make_user()
        date_row = self.make_date()
        session = self.make_session(a, date_row, paid=True)
        self.make_credit(a, 0, paid=False)
        self.login(a)
        response = self.remove(self.client, session)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.session_model.objects.filter(pk=session.pk).exists())
        credit = UserCredit.objects.get(user=a)
        self.assertEqual(credit.balance, self.price_of())
        self.assertTrue(credit.paid)

    def test_remove_paid_goalie_refunds_goalie_price(self):
        if not self.goalie_aware:
            raise SkipTest(f'{self.app_label}: sessions have no goalie flag')
        a = self.make_user()
        date_row = self.make_date()
        session = self.make_session(a, date_row, paid=True, goalie=True)
        self.make_credit(a, 0, paid=False)
        self.login(a)
        self.remove(self.client, session)
        self.assertFalse(self.session_model.objects.filter(pk=session.pk).exists())
        self.assertEqual(self.balance_of(a), self.expected_goalie_refund())

    def test_remove_other_users_session_is_404(self):
        a, b = self.make_user(), self.make_user()
        date_row = self.make_date()
        session = self.make_session(a, date_row, paid=True)
        self.make_credit(a, 0, paid=False)
        self.make_credit(b, 0, paid=False)
        self.login(b)
        response = self.remove(self.client, session)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.session_model.objects.filter(pk=session.pk).exists())
        self.assertEqual(self.balance_of(a), 0)
        self.assertEqual(self.balance_of(b), 0)

    def test_staff_can_remove_any_session(self):
        a = self.make_user()
        staff = self.make_user(staff=True)
        date_row = self.make_date()
        session = self.make_session(a, date_row, paid=True)
        self.make_credit(a, 0, paid=False)
        self.make_credit(staff, 0, paid=False)
        self.login(staff)
        response = self.remove(self.client, session)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.session_model.objects.filter(pk=session.pk).exists())
        # The refund goes to the owner, never to the staff member who removed it.
        self.assertEqual(self.balance_of(a), self.price_of())
        self.assertEqual(self.balance_of(staff), 0)

    def test_remove_get_not_allowed(self):
        a = self.make_user()
        date_row = self.make_date()
        session = self.make_session(a, date_row, paid=True)
        self.login(a)
        response = self.client.get(self.remove_url(session))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.session_model.objects.filter(pk=session.pk).exists())


class ChildSkaterAppMixin(ProgramAppTestMixin):
    '''For the apps where the registrant is a ChildSkater belonging to the user
    (womens_hockey, lady_hawks, mike_schultz, open_roller, private_skates).'''

    owner_field = 'user'

    def child_skater(self, user):
        skater, _ = ChildSkater.objects.get_or_create(
            user=user, first_name=user.first_name, last_name=user.last_name)
        return skater

    def session_extra(self, user):
        return {'skater': self.child_skater(user)}

    def cart_skater_name(self, user):
        return str(self.child_skater(user))

    def register_post(self, user, date_row):
        post = super().register_post(user, date_row)
        post['skater'] = self.child_skater(user).pk
        return post
