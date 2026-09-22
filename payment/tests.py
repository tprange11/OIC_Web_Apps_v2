'''process_payment with the Square client faked out: the card is "charged" by the
fake, and the tests check the bookkeeping that follows (Payment row, sessions paid,
pending credits moved to balance, cart emptied) and that it is all-or-nothing.'''
import os
from datetime import date, timedelta
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserCredit
from ament.models import AmentSkateDate, AmentSkateSession
from cart.models import Cart
from programs.models import Program
from .models import Payment, PaymentError

User = get_user_model()
LOCATION_ID = 'LOC_TEST'


class FakePayments:
    def __init__(self, errors=None):
        self.errors = errors
        self.calls = []

    def create(self, **body):
        self.calls.append(body)
        if self.errors:
            return SimpleNamespace(errors=self.errors, payment=None)
        payment = SimpleNamespace(
            id='PAY123',
            amount_money=SimpleNamespace(amount=body['amount_money']['amount'],
                                         currency=body['amount_money']['currency']),
            note=body['note'],
            # no receipt_number attribute: the view must tolerate its absence
        )
        return SimpleNamespace(errors=None, payment=payment)


class FakeLocations:
    def list(self):
        return SimpleNamespace(errors=None, locations=[
            SimpleNamespace(id='OTHER', currency='CAD', country='CA'),
            SimpleNamespace(id=LOCATION_ID, currency='USD', country='US'),
        ])


def fake_client(payment_errors=None):
    return SimpleNamespace(locations=FakeLocations(), payments=FakePayments(payment_errors))


@mock.patch.dict(os.environ, {'SQUARE_LOCATION_ID': LOCATION_ID, 'SQUARE_API_ACCESS_TOKEN': 'tok'})
class ProcessPaymentTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='payer', password='pw',
                                             first_name='Pat', last_name='Payer', email='p@example.com')
        self.other = User.objects.create_user(username='other', password='pw',
                                              first_name='Oli', last_name='Other')
        self.program = Program.objects.create(pk=16, program_name='Ament Skate', skater_price=10, goalie_price=0)
        skate_date = AmentSkateDate.objects.create(
            skate_date=date.today() + timedelta(days=7), start_time='20:00', end_time='21:30')
        # An unpaid session with its cart row, plus a pending credit purchase.
        self.session = AmentSkateSession.objects.create(skater=self.user, skate_date=skate_date, paid=False)
        Cart.objects.create(customer=self.user, item='Ament Skate', skater_name='Pat Payer',
                            event_date=skate_date.skate_date, event_start_time='20:00:00', amount=10)
        Cart.objects.create(customer=self.user, item='User Credits', skater_name='Pat Payer',
                            event_date=date.today(), event_start_time='N/A', amount=25)
        self.credit = UserCredit.objects.create(user=self.user, slug='payer', balance=5, pending=25, paid=True)
        # Another user's unpaid session and cart must be untouched.
        self.other_session = AmentSkateSession.objects.create(skater=self.other, skate_date=skate_date, paid=False)
        Cart.objects.create(customer=self.other, item='Ament Skate', skater_name='Oli Other',
                            event_date=skate_date.skate_date, event_start_time='20:00:00', amount=10)
        self.client.force_login(self.user)
        self.url = reverse('payment:process_payment')

    def post(self):
        return self.client.post(self.url, {'payment-token': 'cnon:card-nonce-ok'})

    def test_success_records_payment_and_settles_everything(self):
        client = fake_client()
        with mock.patch('payment.views.get_square_client', return_value=client):
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['message'])

        # Square was asked for the cart total, in the location's currency.
        body = client.payments.calls[0]
        self.assertEqual(body['amount_money'], {'amount': 3500, 'currency': 'USD'})
        self.assertEqual(body['location_id'], LOCATION_ID)
        self.assertEqual(body['source_id'], 'cnon:card-nonce-ok')
        self.assertIn('(Ament Skate $10)', body['note'])
        self.assertIn('(User Credits $25)', body['note'])

        payment = Payment.objects.get(payer=self.user)
        self.assertEqual(payment.square_id, 'PAY123')
        self.assertIsNone(payment.square_receipt)
        self.assertEqual(payment.amount, 35.0)
        self.assertEqual(payment.note, body['note'])

        self.session.refresh_from_db()
        self.assertTrue(self.session.paid)
        self.credit.refresh_from_db()
        self.assertEqual((self.credit.balance, self.credit.pending, self.credit.paid), (30, 0, True))
        self.assertEqual(Cart.objects.filter(customer=self.user).count(), 0)

        # The other user's things are untouched.
        self.other_session.refresh_from_db()
        self.assertFalse(self.other_session.paid)
        self.assertEqual(Cart.objects.filter(customer=self.other).count(), 1)
        self.assertEqual(PaymentError.objects.count(), 0)

    def test_bookkeeping_failure_rolls_everything_back(self):
        client = fake_client()
        # Blow up inside the atomic block, after the Payment row has been inserted.
        broken = mock.MagicMock()
        broken.objects.filter.side_effect = IntegrityError('boom')
        with mock.patch('payment.views.get_square_client', return_value=client), \
             mock.patch('payment.views.AmentSkateSession', broken), \
             self.assertLogs('payment.views', level='ERROR'):
            with self.assertRaises(IntegrityError):
                self.post()

        self.assertEqual(Payment.objects.count(), 0)
        self.session.refresh_from_db()
        self.assertFalse(self.session.paid)
        self.credit.refresh_from_db()
        self.assertEqual((self.credit.balance, self.credit.pending), (5, 25))
        self.assertEqual(Cart.objects.filter(customer=self.user).count(), 2)

    def test_square_decline_records_error_and_changes_nothing(self):
        client = fake_client(payment_errors=[SimpleNamespace(detail='Card declined')])
        with mock.patch('payment.views.get_square_client', return_value=client):
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['error'])
        self.assertEqual(response.context['error_message'], 'Card declined')
        self.assertEqual(PaymentError.objects.filter(payer=self.user).count(), 1)
        self.assertEqual(Payment.objects.count(), 0)
        self.session.refresh_from_db()
        self.assertFalse(self.session.paid)
        self.assertEqual(Cart.objects.filter(customer=self.user).count(), 2)

    def test_missing_token_is_an_error_page(self):
        with mock.patch('payment.views.get_square_client') as get_client:
            response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['error'])
        get_client.assert_not_called()
        self.assertEqual(Payment.objects.count(), 0)

    def test_get_redirects_to_cart(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('cart:shopping-cart'))

    def test_requires_login(self):
        self.client.logout()
        response = self.post()
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])
