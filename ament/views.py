'''Views for the Ament Skate program: list upcoming skates, register for one, remove a registration.'''
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
User = get_user_model()

from .models import AmentSkateDate, AmentSkateSession
from .forms import CreateAmentSkateSessionForm
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date


class AmentSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Ament skates.'''

    template_name = 'ament_dates.html'
    model = AmentSkateDate
    session_model = AmentSkateSession
    credit_model = UserCredit
    group_model = Group
    profile_model = Profile
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Silently add the user to the Ament group (used for communication)
        self.join_ament_group()
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
        queryset = queryset.filter(skate_date__gte=date.today()).values('pk', 'skate_date', 'start_time', 'end_time').order_by('skate_date', 'pk')
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('skate_date','pk', 'paid', 'goalie')
        # Annotate each skate date with head counts and, if the user is already signed up,
        # with their session details so the template can disable the register button
        # and show the Remove Me button.
        for item in queryset:
            item['registered_skaters'] = self.model.registered_skaters(skate_date=item['pk'])
            for session in skater_sessions:
                # User already has a session for this skate date (paid or unpaid): disable registration
                if item['pk'] == session[0] and session[2] == True:
                    item['disabled'] = True
                    item['session_pk'] = session[1]
                    item['paid'] = session[2]
                    item['goalie'] = session[3]
                    break
                elif item['pk'] == session[0] and session[2] == False:
                    item['disabled'] = True
                    item['session_pk'] = session[1]
                    item['paid'] = session[2]
                    item['goalie'] = session[3]
                    break
                else:
                    item['disabled'] = False
                    item['session_pk'] = None
                    item['paid'] = False
                    continue
        return queryset

    def join_ament_group(self, join_group='Ament'):
        '''Adds user to the Ament group "behind the scenes", for communication purposes,
        and creates a Profile for the user if one does not exist.'''
        
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass

        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            # If no profile exists, create one; Ament email notifications default to off
            profile = self.profile_model(user=self.request.user, ament_email=False, slug=self.request.user.id)
            profile.save()

        return

class CreateAmentSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for an Ament skate session.'''

    model = AmentSkateSession
    form_class = CreateAmentSkateSessionForm
    profile_model = Profile
    program_model = Program
    skate_date_model = AmentSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'ament_skate_sessions_form.html'
    success_url = reverse_lazy('ament:skate-dates')

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
            context['skate_info'] = self.skate_date_model.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        '''Enforces skater/goalie limits, then marks the session paid (staff, free, or
        paid from credit balance) or adds it to the cart for payment.'''

        # Get the user credit model instance
        user_credit = UserCredit.objects.get(user=self.request.user)
        credit_used = False # Used to set the message
        self.object = form.save(commit=False)

        # Get the program skater/goalie cost (Program id 16 is the Ament Skate)
        if self.object.goalie == True:
            cost = self.program_model.objects.get(id=16).goalie_price
        else:
            cost = self.program_model.objects.get(id=16).skater_price

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=16).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('ament:skate-dates')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=16).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('ament:skate-dates')
            # Spots are available: staff and $0-cost sessions (typically goalies) are free
            if self.request.user.is_staff or cost == 0:
                self.object.paid = True
                cost = 0 # Set cost = 0 for correct message
            # Pay from credit balance when the user has enough credit
            elif user_credit.balance >= cost and user_credit.paid:
                self.object.paid = True
                user_credit.balance -= cost
                # A $0 balance means there is no credit left to pay with
                if user_credit.balance == 0:
                    user_credit.paid = False
                user_credit.save()
                credit_used = True # Used to set the message
            # Otherwise the session goes in the cart to be paid for
            else:
                credit_used = self.add_to_cart(cost)
            self.object.save()
        except IntegrityError:
            pass
        # If all goes well set success message and return
        if cost == 0 or self.request.user.is_staff:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${cost} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, cost):
        '''Adds Ament Skate session to shopping cart. Always returns False (credit not used).'''
        price = cost
        item_name = self.program_model.objects.get(id=16).program_name
        start_time = self.skate_date_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item=item_name, skater_name=self.request.user.get_full_name(), 
        event_date = self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()
        return False


class DeleteAmentSkateSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user (or staff) to remove a skater from a skate session.'''
    model = AmentSkateSession
    skate_date_model = AmentSkateDate
    credit_model = UserCredit
    success_url = reverse_lazy('ament:skate-dates')

    def delete(self, *args, **kwargs):
        '''Refunds credit for a paid session, or clears the cart item for an unpaid one,
        before the session is deleted.'''

        user = User.objects.get(pk=kwargs['skater_pk'])
        if user.is_staff: # Staff doesn't pay to skate, so nothing to refund
            success_msg = 'Skater has been removed from that skate session!'
        elif kwargs['paid'] == 'True':
            # If the session is paid for, issue credit to the user (always the skater price)
            price = Program.objects.get(id=16).skater_price
            user_credit = self.credit_model.objects.get(slug=user)
            old_balance = user_credit.balance
            user_credit.balance += price
            user_credit.paid = True
            success_msg = f'{user.get_full_name()} has been removed from the session. The Users credit balance has been increased from ${old_balance} to ${user_credit.balance}.'
            user_credit.save()
        else:
            # Clear session from the cart, user hasn't paid yet.
            skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('skate_date', flat=True)
            cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
            cart_item = Cart.objects.filter(item=Program.objects.all().get(id=16).program_name, event_date=cart_date[0].skate_date)
            cart_item.delete()
            success_msg = 'You have been removed from that skate session!'

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, success_msg)
        return super().delete(*args, **kwargs)
