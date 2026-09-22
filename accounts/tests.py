from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cart.models import Cart
from programs.models import UserCreditIncentive
from .models import ChildSkater, UserCredit

User = get_user_model()


def make_user(name, staff=False):
    return User.objects.create_user(username=name, password='pw', first_name=name.title(),
                                    last_name='Tester', email=f'{name}@example.com', is_staff=staff)


class UpdateUserCreditViewTests(TestCase):
    '''Users may only ever edit their own credit row; the <slug> in the URL is ignored.'''

    def setUp(self):
        self.a = make_user('alice')
        self.b = make_user('bob')
        self.a_credit = UserCredit.objects.create(user=self.a, slug='alice', balance=40, pending=0, paid=True)
        # apply_incentive() calls incentives.last() unconditionally, so a tier must exist.
        UserCreditIncentive.objects.create(price_point=100, incentive=10)

    def test_posting_to_another_users_slug_only_changes_own_row(self):
        self.client.force_login(self.b)
        response = self.client.post(
            reverse('accounts:purchase-credit', kwargs={'slug': self.a_credit.slug}), {'pending': 20})
        self.assertEqual(response.status_code, 302)

        self.a_credit.refresh_from_db()
        self.assertEqual((self.a_credit.balance, self.a_credit.pending), (40, 0))

        b_credit = UserCredit.objects.get(user=self.b)
        self.assertEqual(b_credit.pending, 20)
        self.assertEqual(b_credit.balance, 0)
        cart = Cart.objects.filter(item='User Credits')
        self.assertEqual(cart.count(), 1)
        self.assertEqual(cart.get().customer, self.b)
        self.assertEqual(cart.get().amount, 20)

    def test_incentive_applies_to_pending_not_cart(self):
        self.client.force_login(self.b)
        self.client.post(reverse('accounts:purchase-credit', kwargs={'slug': 'bob'}), {'pending': 100})
        self.assertEqual(UserCredit.objects.get(user=self.b).pending, 110)
        self.assertEqual(Cart.objects.get(customer=self.b).amount, 100)

    def test_resubmitting_replaces_cart_row(self):
        self.client.force_login(self.b)
        url = reverse('accounts:purchase-credit', kwargs={'slug': 'bob'})
        self.client.post(url, {'pending': 20})
        self.client.post(url, {'pending': 30})
        cart = Cart.objects.filter(customer=self.b, item='User Credits')
        self.assertEqual(cart.count(), 1)
        self.assertEqual(cart.get().amount, 30)

    def test_requires_login(self):
        response = self.client.post(reverse('accounts:purchase-credit', kwargs={'slug': 'alice'}), {'pending': 20})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response['Location'])


class ReportAccessTests(TestCase):
    '''Reports are staff only: anonymous -> login redirect, non-staff -> 403.'''

    def setUp(self):
        self.user = make_user('carol')
        self.staff = make_user('dave', staff=True)

    def assert_staff_only(self, url, staff_status=200):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, url)
        self.assertIn(reverse('accounts:login'), response['Location'])

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 403, url)

        if staff_status is not None:
            self.client.force_login(self.staff)
            self.assertEqual(self.client.get(url).status_code, staff_status, url)

    def test_reports_index(self):
        self.assert_staff_only(reverse('reports'), staff_status=200)

    def test_outstanding_credits_report(self):
        # The staff GET writes CSV files under STATIC_ROOT, so only access is asserted.
        self.assert_staff_only(reverse('outstanding-credits-report'), staff_status=None)

    def test_fs_revenue_report(self):
        self.assert_staff_only(reverse('fs-revenue-report'), staff_status=None)

    def test_csv_downloads_are_staff_only(self):
        for name in ('accounts:download-credit-revenue', 'accounts:download-outstanding-credits',
                     'accounts:download-fs-revenue'):
            url = reverse(name)
            self.client.logout()
            self.assertEqual(self.client.get(url).status_code, 302, url)
            # staff_member_required redirects non-staff to the login page rather than 403
            self.client.force_login(self.user)
            self.assertEqual(self.client.get(url).status_code, 302, url)
            self.client.force_login(self.staff)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertEqual(response['Content-Type'], 'text/csv')


class DeleteChildSkaterViewTests(TestCase):

    def setUp(self):
        self.a = make_user('erin')
        self.b = make_user('frank')
        self.skater = ChildSkater.objects.create(user=self.a, first_name='Kid', last_name='Erin')

    def test_other_users_skater_is_404(self):
        self.client.force_login(self.b)
        response = self.client.post(reverse('accounts:my-skaters-remove', kwargs={'pk': self.skater.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ChildSkater.objects.filter(pk=self.skater.pk).exists())

    def test_own_skater_is_deleted(self):
        self.client.force_login(self.a)
        response = self.client.post(reverse('accounts:my-skaters-remove', kwargs={'pk': self.skater.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ChildSkater.objects.filter(pk=self.skater.pk).exists())

    def test_get_not_allowed(self):
        self.client.force_login(self.a)
        response = self.client.get(reverse('accounts:my-skaters-remove', kwargs={'pk': self.skater.pk}))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(ChildSkater.objects.filter(pk=self.skater.pk).exists())
