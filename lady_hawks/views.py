'''Views for the Lady Hawks skate program: list upcoming skates, register a child skater,
remove a registration, and a staff list of registered skaters.'''
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

from . import models, forms
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date


class LadyHawksSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Lady Hawks skates.'''

    template_name = 'lady_hawks_skate_dates.html'
    model = models.LadyHawksSkateDate
    session_model = models.LadyHawksSkateSession
    group_model = Group
    profile_model = Profile
    credit_model = UserCredit
    context_object_name = 'skate_dates'

    def get(self, request, *args, **kwargs):
        '''Adds user to the Lady Hawks group "behind the scenes", for communication purposes,
        and creates a Profile for the user if one does not exist.'''
        
        try:
            group = self.group_model.objects.get(name='Lady Hawks')
            self.request.user.groups.add(group)
        except IntegrityError:
            pass
        
        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            # If no profile exists, create one with Lady Hawks email notifications on
            profile = self.profile_model(user=self.request.user, lady_hawks_email=True, slug=self.request.user.id)
            profile.save()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # All registrations for upcoming skates, so the template can list who is skating
        skate_sessions = self.session_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('pk')
        context['skate_sessions'] = skate_sessions
        # Create a user credit object if one does not exist
        try:
            credit = self.credit_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            credit = self.credit_model.objects.create(user=self.request.user, slug=self.request.user.username)
        context['credit'] = credit
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).values('pk', 'skate_date', 'start_time', 'end_time').annotate(num_skaters=Count('session_skaters')).order_by('skate_date', 'pk')
        return queryset


class CreateLadyHawksSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register one of their child skaters for a Lady Hawks skate session.'''

    model = models.LadyHawksSkateSession
    form_class = forms.CreateLadyHawksSkateSessionForm
    group_model = Group
    profile_model = Profile
    program_model = Program
    session_model = models.LadyHawksSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'lady_hawks_skate_sessions_form.html'
    success_url = '/web_apps/lady_hawks/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['skate_date'] = self.kwargs['pk']
            initial['user'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        # Get skate date info to display on the template
        if self.request.method =='GET':
            context['skate_info'] = self.session_model.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        '''Enforces skater/goalie limits, then marks the session paid (from credit balance or
        free) or adds it to the cart for payment.'''

        user_credit = self.credit_model.objects.get(user=self.request.user) # User credit model
        credit_used = False # Used to set the success message
        price = 0

        self.object = form.save(commit=False)

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=6).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('lady_hawks:lady-hawks')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=6).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('lady_hawks:lady-hawks')

            # Spots are available: get the skater/goalie cost (Program id 10 is Lady Hawks)
            skater_cost = self.program_model.objects.get(id=10).skater_price
            goalie_cost = self.program_model.objects.get(id=10).goalie_price

            # Set the appropriate price
            if self.object.goalie:
                price = goalie_cost
            else:
                price = skater_cost

            if user_credit.balance == 0:
                # A $0 balance means there is no credit left to pay with
                user_credit.paid = False
                
            # If the user has enough credits, deduct credits and set session as paid
            if user_credit.balance >= price:
                self.object.paid = True
                user_credit.balance -= price
                credit_used = True
            # Not enough credit: free sessions are marked paid, everything else goes in the cart
            else:
                if price == 0:
                    self.object.paid = True
                else:
                    self.add_to_cart(price)

            # Save the user credit model
            user_credit.save()
            self.object.save()
        except IntegrityError:
            pass
        # If all goes well set success message and return
        if price == 0:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate!  ${price} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, price):
        '''Adds Lady Hawks session to shopping cart.'''

        start_time = self.session_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item='Lady Hawks', skater_name=self.object.skater, 
            event_date=self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()
        return False


class DeleteLadyHawksSkateSessionView(SessionRemovalMixin, DeleteView):
    '''Allows the guardian or staff to remove a child skater from a skate session. Refunds
    credit for a paid session or clears the cart item for an unpaid one.'''
    model = models.LadyHawksSkateSession
    success_url = reverse_lazy('lady_hawks:lady-hawks')
    owner_field = 'user'
    program_filter = {'pk': 10}
    cart_item_name = 'Lady Hawks'
    removed_message = 'Skater has been removed from that skate session!'

class LadyHawksSkateDateStaffListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    '''Displays page with list of upcoming Lady Hawks skates with buttons for viewing registered skaters.'''

    model = models.LadyHawksSkateDate
    sessions_model = models.LadyHawksSkateSession
    context_object_name = 'skate_dates'
    template_name = 'lady_hawks_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date').annotate(num_skaters=Count('session_skaters'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('skate_date', 'pk')
        context['session_skaters'] = session_skaters
        return context
