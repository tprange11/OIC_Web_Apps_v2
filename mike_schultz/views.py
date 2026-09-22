'''Mike Schultz skate (Program id 6): users register a ChildSkater for scheduled skates.

Near-copy of open_roller and womens_hockey. The admin registrations are commented out
and the scraper targets the old MaxGalaxy site, so this app may no longer be in use.
'''
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
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart
from programs.removal import SessionRemovalMixin
from programs.auth import StaffRequiredMixin

from datetime import date


class MikeSchultzSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Mike Schultz skates.'''

    template_name = 'mike_schultz_skate_dates.html'
    model = models.MikeSchultzSkateDate
    session_model = models.MikeSchultzSkateSession
    group_model = Group
    profile_model = Profile
    credit_model = UserCredit
    context_object_name = 'skate_dates'

    def get(self, request, *args, **kwargs):
        '''Adds user to Mike Schultz group "behind the scenes", for communication purposes.'''
        
        try:
            group = self.group_model.objects.get(name='Mike Schultz')
            self.request.user.groups.add(group)
        except IntegrityError:
            pass
        
        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            # If no profile exists, create one and set mike_schultz_email to True
            profile = self.profile_model(user=self.request.user, mike_schultz_email=True, slug=self.request.user.id)
            profile.save()
        return super().get(request, *args, **kwargs)

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
        # skater_sessions is computed but unused (dead code, see backlog)
        skater_sessions = self.session_model.objects.filter(user=self.request.user).values_list('skate_date','pk', 'paid')
        return queryset


class CreateMikeSchultzSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = models.MikeSchultzSkateSession
    form_class = forms.CreateMikeSchultzSkateSessionForm
    group_model = Group
    profile_model = Profile
    program_model = Program
    session_model = models.MikeSchultzSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'mike_schultz_skate_sessions_form.html'
    success_url = '/web_apps/mike_schultz/'

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
        '''Enforce goalie/skater caps, then pay from user credit or add to the cart.'''

        user_credit = self.credit_model.objects.get(user=self.request.user)
        credit_used = False # Used to set the success message
        price = 0

        self.object = form.save(commit=False)

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=6).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('mike_schultz:mike-schultz')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=6).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('mike_schultz:mike-schultz')

            # If spots are not full do the following
            skater_cost = self.program_model.objects.get(id=6).skater_price
            goalie_cost = self.program_model.objects.get(id=6).goalie_price

            # Set the appropriate price
            if self.object.goalie:
                price = goalie_cost
            else:
                price = skater_cost

            # Reset the paid flag if the balance was already spent (checked before
            # this deduction, so a balance that hits zero here stays flagged paid)
            if user_credit.balance == 0:
                user_credit.paid = False
                
            # If the user has enough credits, deduct credits and set session as paid
            # (unlike the yeti/nacho/thane apps, user_credit.paid is not checked here)
            if user_credit.balance >= price:
                self.object.paid = True
                user_credit.balance -= price
                credit_used = True
            # Not enough credit: free sessions are marked paid, otherwise add to the cart
            else:
                if price == 0:
                    self.object.paid = True
                else:
                    self.add_to_cart(price)

            user_credit.save()
            self.object.save()
        # Duplicate sign-up is silently ignored; super().form_valid() will re-raise on save
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
        '''Adds Mike Schultz session to shopping cart.'''

        start_time = self.session_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item='Mike Schultz', skater_name=self.object.skater, 
            event_date=self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()
        return False


class DeleteMikeSchultzSkateSessionView(SessionRemovalMixin, DeleteView):
    '''Allows user to remove a skater from a skate session (refund / cart cleanup in the mixin).'''
    model = models.MikeSchultzSkateSession
    success_url = reverse_lazy('mike_schultz:mike-schultz')

    owner_field = 'user'
    program_filter = {'pk': 6}
    cart_item_name = 'Mike Schultz'   # hard-coded in CreateMikeSchultzSkateSessionView.add_to_cart
    removed_message = 'Skater has been removed from that skate session!'

# The following views are for staff only.

class MikeSchultzSkateDateStaffListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    '''Displays page with list of upcoming Mike Schultz skates with buttons for viewing registered skaters.'''

    model = models.MikeSchultzSkateDate
    sessions_model = models.MikeSchultzSkateSession
    context_object_name = 'skate_dates'
    template_name = 'mike_schultz_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('skate_date', 'pk')
        context['session_skaters'] = session_skaters
        return context
