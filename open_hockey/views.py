'''Open hockey: Tuesday/Friday morning drop-in sessions plus prepaid memberships.

Unlike the newer program apps, session dates are not stored in a model; the
views generate the current week's Tuesday and Friday on the fly.
'''
from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, ListView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import date, timedelta, datetime
from . import models
from accounts.models import Profile
from . import forms
from cart.models import Cart
from programs.models import Program
from programs.removal import SessionRemovalMixin


class OpenHockeySessionsPage(LoginRequiredMixin, TemplateView):
    '''Page that displays available open hockey dates'''

    template_name = 'open_hockey.html'
    model = models.OpenHockeySessions
    member_model = models.OpenHockeyMember

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Members (prepaid) get their membership details shown on the page.
        try:
            is_member = self.member_model.objects.get(member=self.request.user, active=True)
            context['is_member'] = True
            context['member_info'] = is_member
        except ObjectDoesNotExist:
            pass

        the_date = date.today()
        # Each list is [date, goalie spots left, skater spots left] for this week's session.
        tuesday = []
        friday = []

        # Walk from today to Friday, so on Saturday/Sunday no sessions are listed.
        # Caps are hard-coded (2 goalies, 22 skaters) rather than read from Program.
        while the_date.weekday() < 5:
            if the_date.weekday() == 1:
                tuesday.append(the_date)
                tuesday.append(2 - self.model.objects.goalie_count(the_date))
                tuesday.append(22 - self.model.objects.skater_count(the_date))
            if the_date.weekday() == 4:
                friday.append(the_date)
                friday.append(2 - self.model.objects.goalie_count(the_date))
                friday.append(22 - self.model.objects.skater_count(the_date))
            the_date += timedelta(days=1)

        # Only include sessions that are still ahead of us this week.
        if len(tuesday) == 0 and len(friday) == 0:
            context['data'] = []
        elif len(tuesday) == 0:
            context['data'] = [friday]
        else:
            context['data'] = [tuesday, friday]
        return context


class CreateOpenHockeySessions(LoginRequiredMixin, CreateView):
    '''Allows users to sign up for open hockey sessions'''

    model = models.OpenHockeySessions
    group_model = Group
    profile_model = Profile
    program_model = Program
    cart_model = Cart
    fields = ('date', 'goalie') # skater is set from request.user; paid is set by the payment flow
    template_name = 'openhockeysessions_form.html'
    success_url = '/web_apps/open_hockey/success'
    
    def get_initial(self, *args, **kwargs):
        '''Capture the open hockey session date from the url for the purpose of populating date field on the form'''

        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['date'] = self.kwargs['date']
            return initial
        else:
            return {}

    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)
            # Goalie spots full (cap of 2): render the error page instead of saving
            if self.model.objects.goalie_count(self.object.date) == 2 and self.object.goalie == True:
                context = { 'user': self.request.user, 
                    'message': "Sorry, goalie spots are full for that session!" }
                return render(None, 'open_hockey_error.html', context)
            # Skater spots full (cap of 22): render the error page instead of saving
            if self.model.objects.skater_count(self.object.date) == 22 and self.object.goalie == False:
                context = { 'user': self.request.user,
                    'message': "Sorry, skater spots are full for that session!"}
                return render(None, 'open_hockey_error.html', context)
            else:
                self.object.skater = self.request.user
                self.join_open_hockey_group()
                self.add_open_hockey_email_to_profile()
                self.object.save()
        # Duplicate (skater, date) pair: the user is already signed up
        except IntegrityError:
            context = { 'user': self.request.user, 
                'message': "You are already signed up for this session!" }
            return render(self.request, 'open_hockey_error.html', context)

        # Goalies skate for free, so only skaters get a cart item
        if self.object.goalie == False:
            self.add_to_cart()
        messages.add_message(self.request, messages.WARNING, 'Please make sure to view your cart and pay for your session(s)!')
        return super().form_valid(form)

    def join_open_hockey_group(self, join_group='Open Hockey'):
        '''Adds user to open hockey group "behind the scenes", for communication purposes.'''
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass
        return

    def add_open_hockey_email_to_profile(self):
        '''If no user profile exists, create one and set open_hockey_email to True.'''
        
        # If a profile already exists, do nothing
        try:
            self.profile_model.objects.get(user=self.request.user)
            return
        # If no profile exists, add one and set open_hockey_email to True
        except ObjectDoesNotExist:
            profile = self.profile_model(user=self.request.user, slug=self.request.user.id, open_hockey_email=True)
            profile.save()
            return

    def add_to_cart(self):
        '''Adds open hockey session to shopping cart.'''
        # Program id 1 is Open Hockey
        program = self.program_model.objects.get(id=1)
        price = program.skater_price
        cart = self.cart_model(customer=self.request.user, item='Open Hockey', skater_name=self.request.user.get_full_name(), event_date=self.object.date, event_start_time='6:15 AM', amount=price)
        cart.save()


class OpenHockeySessionsSuccess(LoginRequiredMixin, TemplateView):
    '''Redirect to template_name after successfully signing up for open hockey sessions'''

    template_name = 'open_hockey_success.html'


class SkaterOpenHockeySessions(LoginRequiredMixin, TemplateView):
    '''Displays open hockey sessions for which a user has signed up'''

    model = models.OpenHockeySessions
    template_name = 'skater_sessions.html'

    def get_context_data(self, **kwargs):
        '''Get users open hockey sessions to return as context'''
        context = super().get_context_data(**kwargs)
        sessions = self.model.objects.get_skater_sessions(self.request.user, date.today())
        context['sessions'] = sessions
        return context

class DeleteOpenHockeySessions(SessionRemovalMixin, DeleteView):
    '''Allows user to remove themself from an open hockey session'''

    model = models.OpenHockeySessions
    success_url = reverse_lazy('open_hockey:skater-sessions')
    template_name = "openhockeysessions_confirm_delete.html"
    http_method_names = ['get', 'post']
    owner_field = 'skater'
    date_field = None
    date_attr = 'date'
    start_time_attr = None
    program_filter = {'id': 1}
    cart_item_name = 'Open Hockey'
    removed_message = 'You have been removed from the Open Hockey Session!'


class OpenHockeyMemberView(LoginRequiredMixin, TemplateView):
    '''Displays page to user with their open hockey member details'''

    model = models.OpenHockeyMember
    type_model = models.OpenHockeyMemberType
    template_name = 'openhockeymember_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.model.objects.all().filter(member=self.request.user)
        context['member'] = queryset
        past_due = queryset.filter(end_date__lte=date.today())
        if past_due:
            context['past_due'] = True
        member_types = self.type_model.objects.all()
        context['member_types'] = member_types
        return context


class CreateOpenHockeyMemberView(LoginRequiredMixin, CreateView):
    '''Displays page where user can sign up as an open hockey member'''

    model = models.OpenHockeyMember
    type_model = models.OpenHockeyMemberType
    template_name = 'openhockeymember_form.html'
    redirect_field_name = 'openhockeymember_detail.html'
    form_class = forms.OpenHockeyMemberForm
    cart_model = Cart

    def get_initial(self):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['member'] = self.request.user
            initial['active'] = False
            initial['end_date'] = date.today()
            return initial
        else:
            return {}

    def form_valid(self, form):
        '''Sets end_date from the chosen membership type's duration and adds the fee to the cart.'''

        member_type = form.cleaned_data['member_type'].id
        duration = self.type_model.objects.get(id=member_type).duration
        expires = date.today() + timedelta(days=duration)
        form.instance.end_date = expires
        amount = self.type_model.objects.get(id=member_type).cost
        self.add_to_cart(amount)
        messages.add_message(self.request, messages.WARNING, 'To activate your membership, you must view your cart and pay for your membership!')
        return super().form_valid(form)

    def add_to_cart(self, amount):
        '''Adds open hockey membership fee to shopping cart.'''
        cart = self.cart_model(customer=self.request.user, item='OH Membership', skater_name=self.request.user.get_full_name(), event_date=date.today(), event_start_time='6:15 AM', amount=amount)
        cart.save()


class UpdateOpenHockeyMemberView(LoginRequiredMixin, UpdateView):
    '''Displays page where user can activate an expired open hockey membership.'''

    model = models.OpenHockeyMember
    type_model = models.OpenHockeyMemberType
    template_name = 'openhockeymember_form.html'
    form_class = forms.OpenHockeyMemberForm
    success_url = reverse_lazy('open_hockey:member-detail')
    cart_model = Cart

    def form_valid(self, form):
        '''Same as CreateOpenHockeyMemberView: recompute end_date and add the fee to the cart.'''

        member_type = form.cleaned_data['member_type'].id
        duration = self.type_model.objects.get(id=member_type).duration
        expires = date.today() + timedelta(days=duration)
        form.instance.end_date = expires
        amount = self.type_model.objects.get(id=member_type).cost
        self.add_to_cart(amount)
        messages.add_message(self.request, messages.WARNING, 'To activate your membership, you must view your cart and pay for your membership!')
        return super().form_valid(form)

    def add_to_cart(self, amount):
        '''Adds open hockey membership fee to shopping cart.'''
        cart = self.cart_model(customer=self.request.user, item='OH Membership', skater_name=self.request.user.get_full_name(), event_date=date.today(), amount=amount)
        cart.save()


# The following views are for staff.
class OpenHockeySessionsPrint(LoginRequiredMixin, TemplateView):
    '''Displays a page with open hockey sessions available to print'''

    template_name = 'open_hockey_print.html'
    model = models.OpenHockeySessions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        the_date = date.today()
        open_hockey_dates = []
        skater_lists = []

        # Same Tuesday/Friday walk as OpenHockeySessionsPage
        while the_date.weekday() < 5:
            if the_date.weekday() == 1:
                open_hockey_dates.append(the_date)
                skater_lists.append(self.model.objects.get_session_participants(the_date))
            if the_date.weekday() == 4:
                open_hockey_dates.append(the_date)
                skater_lists.append(self.model.objects.get_session_participants(the_date))
            the_date += timedelta(days=1)

        context['dates'] = open_hockey_dates
        context['skater_lists'] = skater_lists
        return context


class OpenHockeySessionsView(LoginRequiredMixin, TemplateView):
    '''Displays a page with the "Release of Liability" form and pre-printed names of users signed up for that session'''

    model = models.OpenHockeySessions
    template_name = 'open_hockey_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date'] = self.kwargs['date']
        context['participants'] = self.model.objects.get_session_participants(self.kwargs['date'])
        return context


class OpenHockeyMemberListView(LoginRequiredMixin, ListView):
    '''Displays page to staff with list of open hockey members where they can add or update a member'''

    model = models.OpenHockeyMember
    template_name = 'openhockeymember_list.html'
