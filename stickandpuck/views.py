from django.shortcuts import render, render_to_response
from django.views.generic import CreateView, TemplateView, ListView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from . import models
from . import forms
from cart.models import Cart
from accounts.models import Profile
from programs.models import Program
from datetime import date, timedelta

# Create your views here.

class StickAndPuckIndex(LoginRequiredMixin, TemplateView):
    '''Displays page with stick and puck index view'''
    template_name = 'stick_and_puck.html'


class CreateStickAndPuckSkaterView(LoginRequiredMixin, CreateView):
    '''Displays page where users can add skaters to their account'''
    model = models.StickAndPuckSkater
    template_name = 'stickandpuckskaters_form.html'
    success_url = reverse_lazy('stickandpuck:skater-list')
    form_class = forms.StickAndPuckSkaterForm

    def form_valid(self, form):
        # Set the user as guardian for the Stick and Puck Skater Model
        form.instance.guardian = self.request.user
        try:
            return super(CreateStickAndPuckSkaterView, self).form_valid(form)
        except IntegrityError:
            messages.add_message(self.request, messages.ERROR, 'This skater is already in your skater list!')
            return render(self.request, template_name=self.template_name, context=self.get_context_data())


class StickAndPuckSkaterListView(LoginRequiredMixin, ListView):
    '''Displays page with list of stick and puck skaters'''
    model = models.StickAndPuckSkater
    template_name = 'stickandpuckskaters_list.html'

    def get_queryset(self):
        '''Get list of users stick and puck skaters'''
        queryset = super().get_queryset()
        return queryset.filter(guardian=self.request.user.id)


class DeleteStickAndPuckSkater(LoginRequiredMixin, DeleteView):
    '''Display page where user can confirm deletion of a stick and puck skater'''
    model = models.StickAndPuckSkater
    success_url = reverse_lazy('stickandpuck:skater-list')
    template_name = 'stickandpuckskaters_confirm_delete.html'

    def delete(self, *args, **kwargs):
        # Sets message to be displayed on page after skater has been removed.
        messages.success(self.request, "Skater has been removed!")
        return super().delete(*args, **kwargs)


class StickAndPuckSessionListView(LoginRequiredMixin, ListView):
    '''Displays page with list of users upcoming stick and puck sessions'''
    template_name = 'stickandpucksessions_list.html'
    model = models.StickAndPuckDate

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter queryset by sessions greater than yesteday and order by session_date and primary key('pk')
        return queryset.filter(session_date__gte=date.today()).order_by('session_date', 'pk')


class StickAndPuckSessionCount(LoginRequiredMixin, TemplateView):
    '''Displays page where user can check for how many open skater spots exist for a particular session of stick and puck'''
    template_name = 'stickandpucksessions_count.html'
    model = models.StickAndPuckSession

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skater_spots'] = 26 - self.model.objects.filter(session_date=kwargs['session_date'], session_time=kwargs['session_time']).count()
        return context


class CreateStickAndPuckSession(LoginRequiredMixin, CreateView):
    '''Display page where user can sign skaters up for stick and puck sessions'''
    model = models.StickAndPuckSession
    group_model = Group
    profile_model = Profile
    cart_model = Cart
    template_name = 'stickandpucksessions_form.html'
    success_url = reverse_lazy('stickandpuck:sessions')
    form_class = forms.StickAndPuckSignupForm
    skater_model = models.StickAndPuckSkater
    program_model = Program

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        # Get stick and puck session date and time from URL and return to populate the form's text inputs
        if self.request.method == 'GET':
            initial['session_date'] = self.kwargs['session_date']
            initial['session_time'] = self.kwargs['session_time']
            return initial
        else:
            return {}

    def form_valid(self, form):
        # Set user as guardian for stick and puck sessions model
        form.instance.guardian = self.request.user

        try:
            self.object = form.save(commit=False)
            # If this session of stick and puck is full, set message and redirect to error page
            if self.model.objects.filter(session_date=self.object.session_date, session_time=self.object.session_time).count() >= 26:
                context = {'user': self.request.user,
                        'message': "Sorry, this session of stick and puck is full!"}
                return render_to_response('stickandpuck_error.html', context)
            # Else save the object to the model
            else:
                self.join_stick_and_puck_group()
                self.add_stick_and_puck_email_to_profile()
                self.object.save()
        # If the skater is already signed up for that session, set message and redirect to error page
        except IntegrityError:
            context = {'user': self.request.user,
            'message': "Skater is already signed up for this session!"}
            return render(self.request, 'stickandpuck_error.html', context)

        # If all goes well, add stick and puck session to Shopping Cart
        self.add_to_cart(form.instance.skater)
        messages.add_message(self.request, messages.INFO, 'Please make sure to view your cart and pay for your session(s)!')
        return super().form_valid(form)

    def join_stick_and_puck_group(self, join_group='Stick and Puck'):
        '''Adds user to Stick and Puck Group "behind the scenes", for communication purposes.'''
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass
        return

    def add_stick_and_puck_email_to_profile(self):
        '''If no user profile exists, create one and set stick_and_puck_email to True'''

        # If a profile already exists, do nothing
        try:
            self.profile_model.objects.get(user=self.request.user)
            return
        # If no profile exists, add one and set stick_and_puck_email to True
        except ObjectDoesNotExist:
            profile = self.profile_model(user=self.request.user, slug=self.request.user.id, stick_and_puck_email=True)
            profile.save()
            return

    def add_to_cart(self, skater):
        '''Adds stick and puck session to shopping cart.'''
        # Get price of stick and puck program
        program = self.program_model.objects.get(id=2)
        price = program.skater_price
        cart = self.cart_model(customer=self.request.user, item='Stick and Puck', skater_name=skater, event_date=self.object.session_date, event_start_time=self.object.session_time, amount=price)
        cart.save()


class StickAndPuckMySessionsListView(LoginRequiredMixin, ListView):
    '''Displays page with list of the users stick and puck sessions.'''
    model = models.StickAndPuckSession
    template_name = 'stickandpuckmysessions_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter stick and puck sessions to show sessions greater than or equal to today and ordered by session_date then session_time
        return queryset.filter(guardian=self.request.user.id, session_date__gte=date.today()).order_by('session_date', 'session_time')


class StickAndPuckSessionDeleteView(LoginRequiredMixin, DeleteView):
    '''Displays page where user can confirm deletion of skater from a particular stick and puck session.'''
    model = models.StickAndPuckSession
    skater_model = models.StickAndPuckSkater
    success_url = reverse_lazy('stickandpuck:mysessions')
    template_name = 'stickandpucksessions_confirm_delete.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def delete(self, *args, **kwargs):
        # If a stick and puck session is removed before paying, remove it from the cart too
        session_date = self.model.objects.filter(id=kwargs['pk']).values_list('session_date', flat=True)
        start_time = self.model.objects.filter(id=kwargs['pk']).values_list('session_time', flat=True)
        skater_id = self.model.objects.filter(id=kwargs['pk']).values_list('skater', flat=True)
        skater = self.skater_model.objects.get(id=skater_id[0])
        cart_item = Cart.objects.filter(event_date=session_date[0], event_start_time=start_time[0], skater_name=skater).delete()
        # Set message to display on page after skater has been removed from stick and puck session
        messages.success(self.request, 'Skater has been removed from the Stick and Puck Session!')
        return super().delete(*args, **kwargs)


# The following views are for staff only

class StickAndPuckPrintListView(LoginRequiredMixin, ListView):
    '''Displays page with list of upcoming stick and puck dates for printing purposes.'''
    model = models.StickAndPuckDate
    sessions_model = models.StickAndPuckSession
    template_name = 'stickandpuckprint_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter queryset by dates greater than or equal to today, order by primary key('pk')
        return queryset.filter(session_date__gte=date.today()).order_by('pk')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session_skaters'] = self.sessions_model.objects.filter(session_date__gte=date.today())
        return context


class StickAndPuckPrintView(LoginRequiredMixin, ListView):
    '''Displays page to print Release of Liability with skaters names preprinted.'''
    model = models.StickAndPuckSession
    template_name = 'stickandpuckprint_view.html'

    def get_queryset(self):
        # Filter queryset by date and time of particular stick and puck session
        queryset = super().get_queryset().filter(session_date=self.kwargs['date'], session_time=self.kwargs['time'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get stick and puck session date and time from URL
        context['date'] = self.kwargs['date']
        context['time'] = self.kwargs['time']
        return context
