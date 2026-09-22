'''Thane Storck skate (Program id 4): adult skaters register themselves for scheduled skates.

Goalies and staff skate for free. Near-copy of owhl/yeti_skate/nacho_skate.
'''
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

from . import models, forms
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart
from programs.removal import SessionRemovalMixin
from programs.auth import StaffRequiredMixin

from datetime import date


class SkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Thane Storck skates.'''

    template_name = 'thane_storck_skate_dates.html'
    model = models.SkateDate
    session_model = models.SkateSession
    credit_model = UserCredit
    profile_model = Profile
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all skaters signed up for each session to display the list of skaters for each session
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
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('skate_date','pk', 'paid')
        # Annotate each date with skater/goalie counts and, if the user is already
        # signed up, the session details so the template can disable the button
        for item in queryset:
            item['registered_skaters'] = self.model.registered_skaters(skate_date=item['pk'])
            for session in skater_sessions:
                # Both branches do the same thing; paid/unpaid are handled identically here
                if item['pk'] == session[0] and session[2] == True:
                    item['disabled'] = True
                    item['session_pk'] = session[1]
                    item['paid'] = session[2]
                    break
                elif item['pk'] == session[0] and session[2] == False:
                    item['disabled'] = True
                    item['session_pk'] = session[1]
                    item['paid'] = session[2]
                    break
                else:
                    item['disabled'] = False
                    item['session_pk'] = None
                    item['paid'] = False
                    continue
        return queryset


class CreateSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = models.SkateSession
    form_class = forms.CreateSkateSessionForm
    group_model = Group
    profile_model = Profile
    program_model = Program
    session_model = models.SkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'thane_storck_skate_sessions_form.html'
    success_url = '/web_apps/thane_storck/'

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['skate_date'] = self.kwargs['pk']
            initial['skater'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        # Get skate date info to display on the template
        if self.request.method =='GET':
            context['skate_info'] = self.session_model.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        '''Enforce goalie/skater caps, then pay from user credit or add to the cart.'''

        user_credit = UserCredit.objects.get(user=self.request.user)
        credit_used = False # Used to set the message
        cost = 0

        self.object = form.save(commit=False)
        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=4).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('thane_storck:thane-skate')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=4).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('thane_storck:thane-skate')
            cost = self.program_model.objects.get(id=4).skater_price
            # Goalies and staff members skate for free
            if self.object.goalie or self.request.user.is_staff:
                self.object.paid = True
            elif user_credit.balance >= cost and user_credit.paid:
                self.object.paid = True
                user_credit.balance -= cost
                # A zero balance is flagged as unpaid so it can't be spent again
                if user_credit.balance == 0:
                    user_credit.paid = False
                user_credit.save()
                credit_used = True # Used to set the message
            else:
                self.add_to_cart()
            self.join_thane_storck_group()
            self.add_thane_storck_email_to_profile()
            self.object.save()
        # Duplicate sign-up is silently ignored; super().form_valid() will re-raise on save
        except IntegrityError:
            pass
        # If all goes well set success message and return.
        # User id 52 gets the "free" message here but is NOT exempted from payment above (see backlog).
        if self.object.goalie or self.request.user.is_staff or self.request.user.id == 52:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${cost} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self):
        '''Adds Thane Storck session to shopping cart.'''
        price = self.program_model.objects.get(id=4).skater_price
        start_time = self.session_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item='Thane Storck', skater_name=self.request.user.get_full_name(), 
            event_date=self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()

    def join_thane_storck_group(self, join_group='Thane Storck'):
        '''Adds user to Thane Storck group "behind the scenes", for communication purposes.'''
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass
        return

    def add_thane_storck_email_to_profile(self):
        '''If no user profile exists, create one and set thane_storck_email to True.'''
        
        # If a profile already exists, do nothing
        try:
            self.profile_model.objects.get(user=self.request.user)
            return
        # If no profile exists, add one and set thane_storck_email to True
        except ObjectDoesNotExist:
            profile = self.profile_model(user=self.request.user, slug=self.request.user.id, thane_storck_email=True)
            profile.save()
            return


class DeleteSkateSessionView(SessionRemovalMixin, DeleteView):
    '''Allows user to remove themself from a skate session (refund / cart cleanup in the mixin).'''
    model = models.SkateSession
    success_url = reverse_lazy('thane_storck:thane-skate')

    program_filter = {'pk': 4}
    cart_item_name = 'Thane Storck'   # hard-coded in CreateSkateSessionView.add_to_cart
    manager_user_ids = (11,)          # the template shows user 11 the remove buttons

    def get_refund_amount(self, session):
        # Goalies are never charged in this program (see CreateSkateSessionView), so nothing to refund
        if session.goalie:
            return 0
        return super().get_refund_amount(session)

# The following views are for staff only.

class PrintSkateDateListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    '''Displays page with list of upcoming Thane Storck skates with buttons for printing each skate.'''

    model = models.SkateDate
    sessions_model = models.SkateSession
    context_object_name = 'skate_dates'
    template_name = 'thane_storck_print_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('skate_date', 'pk')
        context['session_skaters'] = session_skaters
        return context


class PrintSkateDateView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    '''Displays Liability Waiver page with skater names for printing.'''
    model = models.SkateSession
    skate_date_model = models.SkateDate
    context_object_name = 'session_skaters'
    template_name = 'thane_storck_print_view.html'

    def get_queryset(self):
        queryset = super().get_queryset().filter(skate_date=self.kwargs['pk'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Unpack the single (date, start_time) row for the waiver header
        skate_date_info = self.skate_date_model.objects.filter(pk=self.kwargs['pk']).values_list('skate_date', 'start_time')
        for info in skate_date_info:
            context['skate_date'] = info[0]
            context['skate_time'] = info[1]
        context['skate_info'] = skate_date_info
        return context

