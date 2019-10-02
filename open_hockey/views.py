from django.shortcuts import render, render_to_response, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import date, timedelta, datetime
from . import models
from . import forms

# Create your views here.

class OpenHockeySessionsPage(LoginRequiredMixin, TemplateView):
    '''Page that displays available open hockey dates'''

    template_name = 'open_hockey.html'
    model = models.OpenHockeySessions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        the_date = date.today()
        # Lists that hold the open hockey session date and the number of skater and goalie spots available
        tuesday = []
        friday = []

        # Append open hockey date and number of skater and goalie spots available for those dates
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

        # If tuesday and friday are empty, return and empty list as context
        # else if tuesday is empty, just return friday as context
        # else return both tuesday and friday as context
        if len(tuesday) == 0 and len(friday) == 0:
            context['data'] = []
        elif len(tuesday) == 0:
            context['data'] = [friday]
        else:
            context['data'] = [tuesday, friday]
        # print(context['data'])
        return context


class CreateOpenHockeySessions(LoginRequiredMixin, CreateView):
    '''Allows users to sign up for open hockey sessions'''

    model = models.OpenHockeySessions
    group_model = Group
    fields = ('date', 'goalie') # Do not need skater or paid fields
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
            # If the user has signed up as goalie and the goalie spots are full, redirect to error page
            if self.model.objects.goalie_count(self.object.date) == 2 and self.object.goalie == True:
                context = { 'user': self.request.user, 
                    'message': "Sorry, goalie spots are full for that session!" }
                return render_to_response('open_hockey_error.html', context)
            # If the user has signed up as a skater and the skater spots are full, redirect to error page
            if self.model.objects.skater_count(self.object.date) == 22 and self.object.goalie == False:
                context = { 'user': self.request.user,
                    'message': "Sorry, skater spots are full for that session!"}
                return render_to_response('open_hockey_error.html', context)
            # If spots are available, try and save the object to the model
            else:
                self.object.skater = self.request.user
                self.join_open_hockey_group()
                self.object.save()
                return super().form_valid(form)
        # If this is a duplicate entry, redirect to error page
        except IntegrityError:
            context = { 'user': self.request.user, 
                'message': "You are already signed up for this session!" }
            return render(self.request, 'open_hockey_error.html', context)

    def join_open_hockey_group(self, join_group='Open Hockey'):
        '''Adds user to open hockey group "behind the scenes", for communication purposes.'''
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass
        return


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

class DeleteOpenHockeySessions(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from an open hockey session'''
    model = models.OpenHockeySessions
    success_url = reverse_lazy('open_hockey:skater-sessions')
    template_name = "openhockeysessions_confirm_delete.html"

    def get_queryset(self):
        '''Get the open hockey sessions that user is signed up for'''
        queryset = super().get_queryset()
        return queryset.filter(skater_id=self.request.user.id)

    def delete(self, *args, **kwargs):
        messages.success(self.request, 'You have been removed from the Open Hockey Session!')
        return super().delete(*args, **kwargs)


# The following views are for staff when they are logged in.

class OpenHockeySessionsPrint(LoginRequiredMixin, TemplateView):
    '''Displays a page with open hockey sessions available to print'''
    template_name = 'open_hockey_print.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        the_date = date.today()
        open_hockey_dates = []

        while the_date.weekday() < 5:
            if the_date.weekday() == 1:
                open_hockey_dates.append(the_date)
            if the_date.weekday() == 4:
                open_hockey_dates.append(the_date)
            the_date += timedelta(days=1)

        context['dates'] = open_hockey_dates
        return context


class OpenHockeySessionsView(LoginRequiredMixin, TemplateView):
    '''Displays a page with the "Release of Liability" form and pre-printed names of users signed up for that session'''
    model = models.OpenHockeySessions
    template_name = 'open_hockey_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date'] = self.kwargs['date']
        context['participants'] = self.model.objects.get_session_participants(self.kwargs['date'])
        # print(context)
        return context


class OpenHockeyMemberView(LoginRequiredMixin, TemplateView):
    '''Displays page to user with their open hockey member details'''
    model = models.OpenHockeyMember
    template_name = 'openhockeymember_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.model.objects.all().filter(member=self.request.user)
        # print(context['member'])
        return context


class OpenHockeyMemberListView(LoginRequiredMixin, ListView):
    '''Displays page to staff with list of open hockey members where they can add or update a member'''
    model = models.OpenHockeyMember
    template_name = 'openhockeymember_list.html'
    

    # def get_queryset(self):
    #     return self.model.objects.all().prefetch_related('member').get()


class CreateOpenHockeyMemberView(LoginRequiredMixin, CreateView):
    '''Displays page where staff can add a user as an open hockey member'''
    model = models.OpenHockeyMember
    template_name = 'openhockeymember_form.html'
    redirect_field_name = 'openhockeymember_list.html'
    form_class = forms.OpenHockeyMemberForm


class UpdateOpenHockeyMemberView(LoginRequiredMixin, UpdateView):
    '''Displays page where staff can update an open hockey member's End Date or Active status'''
    model = models.OpenHockeyMember
    template_name = 'openhockeymember_form.html'
    form_class = forms.OpenHockeyMemberForm
    success_url = reverse_lazy('open_hockey:member-list')