from re import template
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.base import TemplateView
from . import forms
from accounts.models import Profile, ReleaseOfLiability, ChildSkater, UserCredit
from cart.models import Cart
from programs.models import UserCreditIncentive
from payment.models import Payment

from datetime import date, timedelta
from django.utils import timezone


class SignUp(CreateView):
    form_class = forms.UserCreateForm
    success_url = reverse_lazy('login')
    template_name = 'accounts/signup.html'


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    '''Displays page where user can update their profile.'''
    model = Profile
    form_class = forms.ProfileForm
    template_name = 'accounts/profile_form.html'

    def get(self, request, *args, **kwargs):
        try:
            UserCredit.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            user_credit = UserCredit(user=self.request.user, slug=self.request.user.username)
            user_credit.save()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Try to create a profile object
        try:
            profile = self.model(user=self.request.user, slug=self.request.user.id)
            profile.save()
            queryset = self.model.objects.filter(user=self.request.user)
            return queryset
        # If a profile already exists, return the user profile object
        except IntegrityError:
            queryset = super().get_queryset()
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_skaters'] = ChildSkater.objects.all().filter(user=self.request.user)
        context['credit'] = UserCredit.objects.get(user=self.request.user)
        return context

    def form_valid(self, form):
        # Return a message if the profile has been updated successfully
        messages.add_message(self.request, messages.SUCCESS, 'Your profile has been successfully updated!')
        return super().form_valid(form)


class ReleaseOfLiablityView(LoginRequiredMixin, CreateView):
    '''Displays page where user must sign Release of Liablity form.'''
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
            messages.add_message(self.request, messages.ERROR, 'This skater is already in your skater list!')
            return render(self.request, template_name=self.template_name, context=self.get_context_data())
        # If all goes well add success message
        messages.add_message(self.request, messages.SUCCESS, 'Skater successfully added to your list!')
        
        return super().form_valid(form)


class DeleteChildSkaterView(LoginRequiredMixin, DeleteView):
    '''Displays page where user can remove child or dependent skaters.'''
    model = ChildSkater
    success_url = ''
    
    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS, 'Skater has been removed from your list!')
        self.success_url = reverse('accounts:profile', kwargs={'slug': self.request.user.id})
        return super().delete(*args, **kwargs)


class UpdateUserCreditView(LoginRequiredMixin, UpdateView):
    '''Displays page where user can purchase credits to use toward skate sessions.'''

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

    def get_initial(self):
        initial = super().get_initial()
        initial['pending'] = ''
        return initial

    def form_valid(self, form):
        user_credit = self.model.objects.get(user=self.request.user)
        form.instance.user = self.request.user
        self.object = form.save(commit=False)
        # pending credits are added to balance upon payment in payment/views.py
        self.add_to_cart(self.object.pending)
        self.apply_incentive(self.object.pending)
        messages.add_message(self.request, messages.SUCCESS, 'Credits added to your Shopping Cart.  \
            Please make sure you view your cart and pay for your credits!  Unpaid credits will be \
            removed within 24 hours!')
        self.success_url = reverse('accounts:profile', kwargs={'slug': self.request.user.id})
        return super().form_valid(form)

    def add_to_cart(self, credits):
        '''Adds credits to shopping cart.'''

        price = credits
        item_name = 'User Credits'
        event_date = date.today()
        start_time = 'N/A'
        skater_name = self.request.user.get_full_name()
        customer = self.request.user

        cart = self.cart_model(customer=customer, item=item_name, skater_name=skater_name, event_date=event_date, event_start_time=start_time, amount=price)
        cart.save()
        return

    def apply_incentive(self, credits):
        '''Applies credit incentive percentage to amount of credits purchased.'''

        # Get user credit incentives model 
        incentives = self.incentives_model.objects.all()

        if self.object.pending < incentives.last().price_point:
            return
        
        for incentive in incentives:
            if self.object.pending >= incentive.price_point:
                free_points = self.object.pending * ((incentive.incentive / 100) + 1)
                self.object.pending = round(free_points)
                return


class ReportView(TemplateView, LoginRequiredMixin):
    
    template_name = 'accounts/reports.html'


class OutstandingUserCreditsView(TemplateView, LoginRequiredMixin):

    template_name = 'accounts/user_credits_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        outstanding_credits = 0
        credits = UserCredit.objects.all().filter(balance__gte=1)
        for object in credits:
            outstanding_credits += object.balance
        context['outstanding_credits'] = outstanding_credits

        today = timezone.now()
        today = today.replace(hour=0, minute=0, second=0)
        start_date = today + timedelta(days=-365)

        payment_records = Payment.objects.all().filter(note__icontains='User Credits', date__gte=start_date)
        context['payment_records'] = payment_records

        user_credit_records = []
        user_credit_revenue = 0
        for record in payment_records:
            credits = record.note.split(') (')
            for credit in credits:
                if 'Credits' in credit:
                    user_credit_records.append(credit)

        for item in user_credit_records:
            item = item.split(' ')
            user_credit_revenue += int(item[2].strip('$').strip(')'))
        
        context['user_credit_revenue'] = user_credit_revenue

        return context
