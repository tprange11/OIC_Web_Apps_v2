'''Views for the Bald Eagles skate program: list upcoming skates, register for one,
remove a registration, and a staff list of registered skaters.'''
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

from .models import BaldEaglesSkateDate, BaldEaglesSession
from .forms import CreateBaldEaglesSessionForm
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date


class BaldEaglesSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Bald Eagles skate dates.'''

    template_name = 'bald_eagles_skate_dates.html'
    model = BaldEaglesSkateDate
    session_model = BaldEaglesSession
    credit_model = UserCredit
    group_model = Group
    profile_model = Profile
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Silently add the user to the Bald Eagles group (used for communication)
        self.join_bald_eagles_group()
        # All registrations for upcoming skates, so the template can list who is skating
        skate_sessions = self.session_model.objects.filter(session_date__skate_date__gte=date.today()).order_by('pk')
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
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('session_date','pk', 'paid')
        # If the user is already signed up for a skate date, attach their session details so the
        # template can disable the register button and show the Remove Me button
        for item in queryset:
            for session in skater_sessions:
                # User already has a session for this skate date (paid or unpaid): disable registration
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

    def join_bald_eagles_group(self, join_group='Bald Eagles'):
        '''Adds user to the Bald Eagles group "behind the scenes", for communication purposes,
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
            # If no profile exists, create one with Bald Eagles email notifications on
            profile = self.profile_model(user=self.request.user, bald_eagles_email=True, slug=self.request.user.id)
            profile.save()

        return

class CreateBaldEaglesSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for a Bald Eagles skate session.'''

    model = BaldEaglesSession
    form_class = CreateBaldEaglesSessionForm
    profile_model = Profile
    program_model = Program
    session_model = BaldEaglesSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'bald_eagles_sessions_form.html'
    success_url = reverse_lazy('bald_eagles:bald-eagles')

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['session_date'] = self.kwargs['pk']
            initial['skater'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        # Get skate date info to display on the template
        if self.request.method =='GET':
            context['skate_info'] = self.session_model.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        '''Enforces skater/goalie limits, then marks the session paid (staff, free, or
        paid from credit balance) or adds it to the cart for payment.'''

        # Get the user credit model instance
        user_credit = UserCredit.objects.get(user=self.request.user)
        credit_used = False # Used to set the message
        cost = 0
        
        self.object = form.save(commit=False)

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, session_date=self.object.session_date).count() == Program.objects.get(pk=9).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('bald_eagles:bald-eagles')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, session_date=self.object.session_date).count() == Program.objects.get(pk=9).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('bald_eagles:bald-eagles')
            # Spots are available: get the skater/goalie cost (Program id 9 is Bald Eagles)
            if self.request.user.is_staff: # Employees skate for free
                cost = 0
            elif self.object.goalie:
                cost = self.program_model.objects.get(id=9).goalie_price
            else:
                cost = self.program_model.objects.get(id=9).skater_price

            if cost == 0:
                self.object.paid = True
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
                self.add_to_cart(cost)
            self.object.save()
        except IntegrityError:
            pass
        # If all goes well set success message and return
        if cost == 0:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${cost} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, cost):
        '''Adds Bald Eagles Skate session to shopping cart.'''

        price = cost
        item_name = self.program_model.objects.get(id=9).program_name
        start_time = self.session_model.objects.filter(skate_date=self.object.session_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item=item_name, skater_name=self.request.user.get_full_name(), 
        event_date = self.object.session_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()
        return False


class DeleteBaldEaglesSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from a skate session (no credit refund; only the cart item is cleared).'''
    model = BaldEaglesSession
    skate_date_model = BaldEaglesSkateDate
    success_url = reverse_lazy('bald_eagles:bald-eagles')

    def delete(self, *args, **kwargs):
        '''Clears the matching cart item before the session is deleted.'''

        # Clear session from the cart
        skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('session_date', flat=True)
        cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
        cart_item = Cart.objects.filter(item=Program.objects.all().get(id=9).program_name, event_date=cart_date[0].skate_date).delete()

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, 'You have been removed from that skate session!')
        return super().delete(*args, **kwargs)

################ The following views are for staff only ##########################################################

class BaldEaglesSessionStaffListView(LoginRequiredMixin, ListView):
    '''Displays page with list of upcoming Bald Eagles skates with buttons for viewing registered skaters.'''

    model = BaldEaglesSkateDate
    sessions_model = BaldEaglesSession
    context_object_name = 'skate_dates'
    template_name = 'bald_eagles_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date').annotate(num_skaters=Count('session_skaters'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(session_date__skate_date__gte=date.today()).order_by('session_date', 'pk')
        context['session_skaters'] = session_skaters
        return context


