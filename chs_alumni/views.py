'''Views for the CHS Alumni skate program: list upcoming skates, register for one,
remove an unpaid registration, and a staff list of skate dates.'''
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from programs.removal import SessionRemovalMixin
from programs.auth import StaffRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

from .models import CHSAlumniDate, CHSAlumniSession
from .forms import CreateCHSAlumniSkateSessionForm
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date, datetime


class CHSAlumniSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming CHS Alumni skates.'''

    template_name = 'chs_alumni_dates.html'
    model = CHSAlumniDate
    credit_model = UserCredit
    group_model = Group
    profile_model = Profile
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Silently add the user to the CHS Alumni group (used for communication)
        self.join_chs_alumni_group()
        
        # Create a user credit object if one does not exist
        try:
            credit = self.credit_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            credit = self.credit_model.objects.create(user=self.request.user, slug=self.request.user.username)
        context['credit'] = credit
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today())
        return queryset

    def join_chs_alumni_group(self, join_group='CHS Alumni'):
        '''Adds user to the CHS Alumni group "behind the scenes", for communication purposes,
        and creates a Profile for the user if one does not exist.'''
        
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass

        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except IntegrityError:
            pass
        except ObjectDoesNotExist:
            # If no profile exists, create one with CHS Alumni email notifications on
            profile = self.profile_model(user=self.request.user, chs_alumni_email=True, slug=self.request.user.id)
            profile.save()
        return


class CreateCHSAlumniSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for a CHS Alumni skate session.'''

    model = CHSAlumniSession
    form_class = CreateCHSAlumniSkateSessionForm
    profile_model = Profile
    program_model = Program
    skate_date_model = CHSAlumniDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'chs_alumni_sessions_form.html'
    success_url = reverse_lazy('chs_alumni:chs-alumni')

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['date'] = self.kwargs['pk']
            initial['skater'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        # Get skate date info to display on the template
        if self.request.method =='GET':
            context['skate_info'] = self.skate_date_model.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        '''Enforces skater/goalie limits, then marks the session paid (free goalie or paid
        from credit balance) or adds it to the cart for payment.'''

        # Get the user credit model instance
        user_credit = UserCredit.objects.get(user=self.request.user)
        credit_used = False # Used to set the message
        price = 0
        self.object = form.save(commit=False)

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, date=self.object.date).count() == Program.objects.get(pk=11).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('chs_alumni:chs-alumni')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, date=self.object.date).count() == Program.objects.get(pk=11).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('chs_alumni:chs-alumni')

            # Get the price of the skate (Program id 11 is CHS Alumni); goalies at $0 are marked paid
            if self.object.goalie:
                price = self.program_model.objects.get(id=11).goalie_price
                if price == 0:
                    self.object.paid = True
            else:
                price = self.program_model.objects.get(id=11).skater_price

            # Pay from credit balance when the user has enough credit, otherwise add to cart
            if user_credit.balance >= price and user_credit.paid:
                self.object.paid = True
                user_credit.balance -= price
                # A $0 balance means there is no credit left to pay with
                if user_credit.balance == 0:
                    user_credit.paid = False
                user_credit.save()
                credit_used = True # Used to set the message
            else:
                self.add_to_cart(price)
            self.object.save()
        except IntegrityError:
            pass
        
        # If all goes well set success message and return
        if credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${price} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, price):
        '''Adds CHS Alumni Skate session to shopping cart.'''
        
        item_name = self.program_model.objects.get(id=11).program_name
        start_time = self.skate_date_model.objects.filter(skate_date=self.object.date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item=item_name, skater_name=self.request.user.get_full_name(), 
            event_date = self.object.date.skate_date, event_start_time=start_time[0].strftime('%I:%M %p'), amount=price)
        cart.save()
        return False


class DeleteCHSAlumniSessionView(SessionRemovalMixin, DeleteView):
    '''Allows the skater or staff to remove a skater from a skate session. Refunds credit for
    a paid session or clears the cart item for an unpaid one.'''
    model = CHSAlumniSession
    success_url = reverse_lazy('chs_alumni:chs-alumni')
    date_field = 'date'
    program_filter = {'pk': 11}


class CHSAlumniSkateDateStaffListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    '''Displays page with list of upcoming CHS Alumni skate dates with buttons for viewing registered skaters.'''

    model = CHSAlumniDate
    context_object_name = 'skate_dates'
    template_name = 'chs_alumni_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date')
        return queryset
