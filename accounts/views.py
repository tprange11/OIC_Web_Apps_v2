"""Accounts: sign-up, profile/email preferences, release of liability, child skaters,
user credit purchases and the staff revenue/credit reports."""
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.base import TemplateView
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from . import forms
from accounts.models import Profile, ReleaseOfLiability, ChildSkater, UserCredit
from cart.models import Cart
from programs.models import UserCreditIncentive
from payment.models import Payment
from programs.removal import OwnedDeleteMixin
from programs.auth import StaffRequiredMixin

from datetime import date, datetime, timedelta
import csv
import os
import calendar

class SignUp(CreateView):
    '''Public sign-up page; new users are sent to the login page.'''
    form_class = forms.UserCreateForm
    success_url = reverse_lazy('accounts:login')
    template_name = 'accounts/signup.html'


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    '''Displays page where user can update their profile.'''
    model = Profile
    form_class = forms.ProfileForm
    template_name = 'accounts/profile_form.html'

    def get(self, request, *args, **kwargs):
        # Make sure the user has a UserCredit row; the template and
        # get_context_data() assume one exists.
        try:
            UserCredit.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            user_credit = UserCredit(user=self.request.user, slug=self.request.user.username)
            user_credit.save()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Profiles are created on first visit: try to insert one and fall back to the
        # existing row when the unique (user, slug) constraint rejects the insert.
        try:
            profile = self.model(user=self.request.user, slug=self.request.user.id)
            profile.save()
            queryset = self.model.objects.filter(user=self.request.user)
            return queryset
        except IntegrityError:
            queryset = super().get_queryset()
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_skaters'] = ChildSkater.objects.all().filter(user=self.request.user)
        context['credit'] = UserCredit.objects.get(user=self.request.user)
        return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, 'Your profile has been successfully updated!')
        return super().form_valid(form)


class ReleaseOfLiablityView(LoginRequiredMixin, CreateView):
    '''Displays page where user must sign the Release of Liability form. Users who
    have already signed are sent straight to the web apps page.'''
    model = ReleaseOfLiability
    form_class = forms.ReleaseOfLiablityForm
    success_url = reverse_lazy('web_apps')
    template_name = 'accounts/release_of_liability.html'

    def get(self, request, *args, **kwargs):
        try:
            self.model.objects.get(user=self.request.user)
            return redirect('web_apps')
        except ObjectDoesNotExist:
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CreateChildSkaterView(LoginRequiredMixin, CreateView):
    '''Displays page where user can add child or dependent skaters.'''
    model = ChildSkater
    form_class = forms.CreateChildSkaterForm
    template_name = 'accounts/create_my_skater_form.html'


    def form_valid(self, form):
        self.object = form.save(commit=False)
        form.instance.user = self.request.user
        self.success_url = reverse('accounts:profile', kwargs={'slug': self.request.user.id})
        try:
            self.object.save()
        except IntegrityError:
            # unique_together on (user, first_name, last_name)
            messages.add_message(self.request, messages.ERROR, 'This skater is already in your skater list!')
            return render(self.request, template_name=self.template_name, context=self.get_context_data())
        messages.add_message(self.request, messages.SUCCESS, 'Skater successfully added to your list!')

        return super().form_valid(form)


class DeleteChildSkaterView(OwnedDeleteMixin, DeleteView):
    '''Removes a child skater (POSTed from the profile page); only the owner or staff may delete it.'''
    model = ChildSkater
    owner_field = 'user'
    success_message = 'Skater has been removed from your list!'

    def get_success_url(self):
        return reverse('accounts:profile', kwargs={'slug': self.request.user.id})


class UpdateUserCreditView(LoginRequiredMixin, UpdateView):
    '''Displays page where user can purchase credits to use toward skate sessions.

    Purchase rule: the dollar amount entered goes into the cart as a "User Credits"
    item, and the credits to be granted (amount plus any incentive bonus) are stored in
    UserCredit.pending. Nothing is spendable until payment/views.py moves pending into
    balance; unpaid pending credits are zeroed by the nightly cleanup.

    The row edited is always the logged-in user's own UserCredit (created on demand);
    the <slug> in the URL is ignored. Submitting again before paying replaces the
    existing "User Credits" cart row rather than adding a second one.
    '''

    model = UserCredit
    incentives_model = UserCreditIncentive
    cart_model = Cart
    incentive_model = UserCreditIncentive
    form_class = forms.CreateUserCreditForm
    template_name = 'accounts/update_user_credit_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incentives'] = self.incentive_model.objects.all().order_by('price_point')
        return context

    def get_object(self, queryset=None):
        # Ignore the URL slug: users may only ever edit their own credit row.
        return self.model.objects.get_or_create(
            user=self.request.user,
            defaults={'slug': self.request.user.username},
        )[0]

    def get_initial(self):
        initial = super().get_initial()
        initial['pending'] = ''
        return initial

    def form_valid(self, form):
        self.object = form.save(commit=False)
        # Order matters: the cart gets the dollar amount before the incentive
        # inflates `pending` into the credit total.
        self.add_to_cart(self.object.pending)
        self.apply_incentive(self.object.pending)
        messages.add_message(self.request, messages.SUCCESS, 'Credits added to your Shopping Cart.  \
            Please make sure you view your cart and pay for your credits!  Unpaid credits will be \
            removed within 24 hours!')
        self.success_url = reverse('accounts:profile', kwargs={'slug': self.request.user.id})
        return super().form_valid(form)

    def add_to_cart(self, credits):
        '''Adds a "User Credits" cart item for the dollar amount purchased.'''

        price = credits
        item_name = 'User Credits'
        event_date = date.today()
        start_time = 'N/A'
        skater_name = self.request.user.get_full_name()
        customer = self.request.user

        # Replace any existing unpaid credit purchase instead of adding a second row,
        # so re-submitting before paying does not charge for both.
        existing = self.cart_model.objects.filter(customer=customer, item=item_name).first()
        if existing:
            existing.skater_name = skater_name
            existing.event_date = event_date
            existing.event_start_time = start_time
            existing.amount = price
            existing.save()
            return

        cart = self.cart_model(customer=customer, item=item_name, skater_name=skater_name, event_date=event_date, event_start_time=start_time, amount=price)
        cart.save()
        return

    def apply_incentive(self, credits):
        '''Bumps `pending` by the bonus percentage of the highest price point reached.

        UserCreditIncentive is ordered by price_point descending, so the first match is
        the best tier and `incentives.last()` is the lowest tier. Only one tier applies.
        The `credits` argument is unused; the method reads self.object.pending directly.
        '''

        incentives = self.incentives_model.objects.all()

        if self.object.pending < incentives.last().price_point:
            return

        for incentive in incentives:
            if self.object.pending >= incentive.price_point:
                free_points = self.object.pending * ((incentive.incentive / 100) + 1)
                self.object.pending = round(free_points)
                return


# Report views: staff only.

class ReportView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    '''Landing page linking to the individual reports.'''

    template_name = 'accounts/reports.html'


class OutstandingUserCreditsView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    '''Outstanding credit balances and last-12-month credit revenue. Also writes both
    data sets to CSV files under STATIC_ROOT/reports/ for download.'''

    template_name = 'accounts/user_credits_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if os.name == 'nt':
            path_to_file = '\\reports\\UserCreditsPurchased.csv'
            path_to_credits_file = '\\reports\\OutstandingCreditsData.csv'
        else:
            path_to_file = '/reports/UserCreditsPurchased.csv'
            path_to_credits_file = '/reports/OutstandingCreditsData.csv'

        cf = open(settings.STATIC_ROOT + path_to_credits_file, 'w', newline='')
        writer = csv.writer(cf)
        writer.writerow(['User', 'Credit Balance'])

        outstanding_credits = 0
        credits = UserCredit.objects.all().filter(balance__gte=1)
        for object in credits:
            writer.writerow([object.user.get_full_name(), object.balance])
            outstanding_credits += object.balance
        context['outstanding_credits'] = outstanding_credits
        cf.close()

        today = timezone.now()
        today = today.replace(hour=0, minute=0, second=0)
        offset = -365
        if calendar.isleap(today.year):
            offset = -366
        start_date = today + timedelta(days=offset)

        payment_records = Payment.objects.all().filter(note__icontains='User Credits', date__gte=start_date)
        f = open(settings.STATIC_ROOT + path_to_file, 'w', newline='')
        writer = csv.writer(f)
        writer.writerow(['User', 'Amount', 'Payment Breakdown', 'Date'])

        user_credit_records = []
        user_credit_revenue = 0
        # Pull the "(User Credits $N)" chunk out of each payment note and total N.
        for record in payment_records:
            writer.writerow([record.payer.get_full_name(),record.amount,record.note,record.date.strftime('%Y-%m-%d')])
            credits = record.note.split(') (')
            for credit in credits:
                if 'Credits' in credit:
                    user_credit_records.append(credit)
        f.close()

        for item in user_credit_records:
            item = item.split(' ')
            user_credit_revenue += int(item[2].strip('$').strip(')'))

        context['user_credit_revenue'] = user_credit_revenue

        return context


@staff_member_required
def download_credit_revenue(request):
    '''Streams the User Credit purchase history for the past 12 months as a CSV download.'''
    today = timezone.now().replace(hour=0, minute=0, second=0)
    offset = -366 if calendar.isleap(today.year) else -365
    start_date = today + timedelta(days=offset)

    payment_records = Payment.objects.filter(
        note__icontains='User Credits',
        date__gte=start_date
    ).order_by('-date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="UserCreditsPurchased.csv"'
    writer = csv.writer(response)
    writer.writerow(['User', 'Amount', 'Payment Breakdown', 'Date'])
    for record in payment_records:
        writer.writerow([
            record.payer.get_full_name(),
            record.amount,
            record.note,
            record.date.strftime('%Y-%m-%d'),
        ])
    return response


@staff_member_required
def download_outstanding_credits(request):
    '''Streams the current outstanding user credit balances as a CSV download.'''
    credits = UserCredit.objects.filter(balance__gte=1).select_related('user')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="OutstandingCreditsData.csv"'
    writer = csv.writer(response)
    writer.writerow(['User', 'Credit Balance'])
    for obj in credits:
        writer.writerow([obj.user.get_full_name(), obj.balance])
    return response


class FigureSkatingRevenueReport(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    '''Writes the last 12 months of payments by members of the "Figure Skating" group
    to STATIC_ROOT/reports/FSRevenueReport.csv; the page itself only links to it.'''
    template_name = 'accounts/fs_revenue_report.html'

    def in_group_figure(self, user):
        return user.groups.filter(name='Figure Skating')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if os.name == 'nt':
            path_to_file = '\\reports\\FSRevenueReport.csv'
        else:
            path_to_file = '/reports/FSRevenueReport.csv'

        today = timezone.now()
        today = today.replace(hour=0, minute=0, second=0)
        offset = -365
        if calendar.isleap(today.year):
            offset = -366
        start_date = today + timedelta(days=offset)

        payment_records = Payment.objects.all().filter(date__gte=start_date)
        f = open(settings.STATIC_ROOT + path_to_file, 'w', newline='')
        writer = csv.writer(f)
        writer.writerow(['User', 'Amount', 'Payment Breakdown', 'Date'])

        for record in payment_records:
            if self.in_group_figure(record.payer):
                writer.writerow([record.payer.get_full_name(),record.amount,record.note,record.date.strftime('%Y-%m-%d')])
        f.close()

        return context


@staff_member_required
def download_fs_revenue(request):
    '''Streams the Figure Skating revenue for the past 12 months as a CSV download.'''
    today = timezone.now().replace(hour=0, minute=0, second=0)
    offset = -366 if calendar.isleap(today.year) else -365
    start_date = today + timedelta(days=offset)

    payment_records = Payment.objects.filter(date__gte=start_date).order_by('-date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="FSRevenueReport.csv"'
    writer = csv.writer(response)
    writer.writerow(['User', 'Amount', 'Payment Breakdown', 'Date'])
    for record in payment_records:
        if record.payer.groups.filter(name='Figure Skating').exists():
            writer.writerow([
                record.payer.get_full_name(),
                record.amount,
                record.note,
                record.date.strftime('%Y-%m-%d'),
            ])
    return response


@staff_member_required
def revenue_report(request, **kwargs):
    '''GET renders the date-range form; POST totals payments per program between the
    two dates by parsing the "(Program $amount) ..." payment notes.'''

    context = None

    if request.method == 'GET':
        return render(request, 'accounts/revenue_report_form.html')
    else:
        start_date = timezone.make_aware(datetime.strptime(request.POST['start_date'], '%Y-%m-%d'))
        end_date = timezone.make_aware(datetime.strptime(request.POST['end_date'], '%Y-%m-%d'))

        payment_records = Payment.objects.all().filter(date__gte=start_date, date__lte=end_date)
        payments = []
        totals = {}
        total_revenue = 0
        for record in payment_records:
            payments.append(record.note.replace(' $', ', ').replace(') (', ')#(').split('#'))
        for payment in payments:
            for each_item in payment:
                s = each_item.strip('(').strip(')').strip(') ').split(', ')
                current_total = totals.get(s[0], 0)
                if current_total == 0:
                    totals.update({s[0]: int(s[1])})
                else:
                    totals.update({s[0]: int(s[1]) + current_total})
                total_revenue += int(s[1])

        context = {'payment_totals': totals, 'total_revenue': total_revenue, 'start_date': start_date, 'end_date': end_date}

    return render(request, 'accounts/revenue_report.html', context)
