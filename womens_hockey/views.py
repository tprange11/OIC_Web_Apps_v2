from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

from . import models, forms
from accounts.models import Profile, ChildSkater, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date


class WomensHockeySkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Womens Hockey skates.'''

    template_name = 'womens_hockey_skate_dates.html'
    model = models.WomensHockeySkateDate
    session_model = models.WomensHockeySkateSession
    group_model = Group
    profile_model = Profile
    credit_model = UserCredit
    context_object_name = 'skate_dates'

    def get(self, request, *args, **kwargs):
        '''Adds user to Womens Hockey group "behind the scenes", for communication purposes.'''

        try:
            group = self.group_model.objects.get(id=8)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass

        try:
            # If a profile already exists, set womens_hockey_email to True
            profile = self.profile_model.objects.get(
                user=self.request.user)
            profile.womens_hockey_email = True
            profile.save()
        except ObjectDoesNotExist:
            pass

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all skaters signed up for each session to display the list of skaters for each session
        skate_sessions = self.session_model.objects.filter(
            skate_date__skate_date__gte=date.today())
        context['skate_sessions'] = skate_sessions

        try:
            credit = self.credit_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            credit = self.credit_model.objects.create(user=self.request.user, slug=self.request.user.username)
        context['credit'] = credit

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).values(
            'pk', 'skate_date', 'start_time', 'end_time').annotate(num_skaters=Count('session_skaters'))
        skater_sessions = self.session_model.objects.filter(
            user=self.request.user).values_list('skate_date', 'pk', 'paid')
        return queryset


class CreateWomensHockeySkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = models.WomensHockeySkateSession
    form_class = forms.CreateWomensHockeySkateSessionForm
    group_model = Group
    profile_model = Profile
    program_model = Program
    session_model = models.WomensHockeySkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'womens_hockey_skate_sessions_form.html'
    success_url = '/web_apps/womens_hockey/'

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
        context = super().get_context_data(**kwargs)
        # Get skate date info to display on the template
        if self.request.method == 'GET':
            context['skate_info'] = self.session_model.objects.get(
                pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):

        user_credit = self.credit_model.objects.get(user=self.request.user) # User credit model
        credit_used = False # Used to set the success message

        self.object = form.save(commit=False)

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=8).max_goalies:
                messages.add_message(
                    self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('womens_hockey:womens-hockey')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=8).max_skaters:
                messages.add_message(
                    self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('womens_hockey:womens-hockey')

            # If spots are not full do the following
            skater_cost = self.program_model.objects.get(id=8).skater_price
            goalie_cost = self.program_model.objects.get(id=8).goalie_price

            # Set the appropriate price
            if self.object.goalie:
                price = goalie_cost
            else:
                price = skater_cost

            # If user credit has been depleted, make sure user credit paid is set to False
            if user_credit.balance == 0:
                user_credit.paid = False
            
            if user_credit.balance >= price:
                self.object.paid = True
                user_credit.balance -= price
                credit_used = True
            # If the user doesn't have enough credits
            else:
                if price == 0:
                    self.object.paid = True
                else:
                    self.add_to_cart(price)
            
            # Save the user credit model
            user_credit.save()
            self.add_womens_hockey_email_to_profile()
            self.object.save()
        except IntegrityError:
            pass
        # If all goes well set success message and return
        if price == 0:
            messages.add_message(self.request, messages.INFO,
                                 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${price} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO,
                                 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, price):
        '''Adds Womens Hockey session to shopping cart.'''

        start_time = self.session_model.objects.filter(
            skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item='Womens Hockey', skater_name=self.object.skater,
                               event_date=self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()
        return False

    def add_womens_hockey_email_to_profile(self):
        '''If no user profile exists, create one and set womens_hockey_email to True.'''

        # If a profile already exists, do nothing
        try:
            self.profile_model.objects.get(user=self.request.user)
            return
        # If no profile exists, add one and set open_hockey_email to True
        except ObjectDoesNotExist:
            profile = self.profile_model(
                user=self.request.user, slug=self.request.user.id, womens_hockey_email=True)
            profile.save()
            return


class DeleteWomensHockeySkateSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from a skate session'''
    model = models.WomensHockeySkateSession
    skate_date_model = models.WomensHockeySkateDate
    success_url = reverse_lazy('womens_hockey:womens-hockey')

    def delete(self, *args, **kwargs):
        '''Things that need doing once a session is removed.'''

        # Clear session from the cart
        skate_date = self.model.objects.filter(
            id=kwargs['pk']).values_list('skate_date', flat=True)
        skater_id = self.model.objects.filter(
            id=kwargs['pk']).values_list('skater', flat=True)
        skater = ChildSkater.objects.get(id=skater_id[0])
        cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
        cart_item = Cart.objects.filter(item=Program.objects.all().get(
            id=8), skater_name=skater, event_date=cart_date[0].skate_date).delete()

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS,
                             'Skater has been removed from that skate session!')
        return super().delete(*args, **kwargs)

################ The following views are for staff only ##########################################################


class WomensHockeySkateDateStaffListView(LoginRequiredMixin, ListView):
    '''Displays page with list of upcoming Womens Hockey skates with buttons for viewing registered skaters.'''

    model = models.WomensHockeySkateDate
    sessions_model = models.WomensHockeySkateSession
    context_object_name = 'skate_dates'
    template_name = 'womens_hockey_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            skate_date__gte=date.today()).order_by('skate_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(
            skate_date__skate_date__gte=date.today()).order_by('skate_date')
        context['session_skaters'] = session_skaters
        return context
