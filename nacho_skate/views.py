from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from .models import NachoSkateDate, NachoSkateSession
from .forms import CreateNachoSkateSessionForm
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date

User = get_user_model()

# Create your views here.

class NachoSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Nacho skates.'''

    template_name = 'nacho_skate_dates.html'
    model = NachoSkateDate
    session_model = NachoSkateSession
    credit_model = UserCredit
    group_model = Group
    profile_model = Profile
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Join the Nacho Group
        self.join_nacho_skate_group()
        # Get all skaters signed up for each session to display the list of skaters for each session
        skate_sessions = self.session_model.objects.filter(skate_date__skate_date__gte=date.today())
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
        queryset = queryset.filter(skate_date__gte=date.today()).values('pk', 'skate_date', 'start_time', 'end_time')
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('skate_date','pk', 'paid', 'goalie')
        # If user is already signed up for the skate, add key value pair to disable button
        for item in queryset:
            item['registered_skaters'] = self.model.registered_skaters(skate_date=item['pk'])
            for session in skater_sessions:
                # If the session date and skate date match and paid is True, add disabled = True to queryset
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

    def join_nacho_skate_group(self, join_group='Nacho Skate'):
        '''Adds user to Nacho group "behind the scenes", for communication purposes.'''
        
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass

        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            # If no profile exists, create one and set nacho_skate_email to False
            profile = self.profile_model(user=self.request.user, nacho_skate_email=False, slug=self.request.user.id)
            profile.save()

        return

class CreateNachoSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = NachoSkateSession
    form_class = CreateNachoSkateSessionForm
    profile_model = Profile
    program_model = Program
    skate_date_model = NachoSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'nacho_skate_sessions_form.html'
    success_url = reverse_lazy('nacho_skate:index')

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
            try:
                context['skate_info'] = self.skate_date_model.objects.get(pk=self.kwargs['pk'])
            except ObjectDoesNotExist:
                context['error'] = {'error': True}
        return context

    def form_valid(self, form):

        # Get the user credit model instance
        user_credit = UserCredit.objects.get(user=self.request.user)
        credit_used = False # Used to set the message
        self.object = form.save(commit=False)

        # Get the program skater/goalie cost
        if self.object.goalie == True:
            cost = self.program_model.objects.get(id=15).goalie_price
        else:
            cost = self.program_model.objects.get(id=15).skater_price
        # print(f'Cost: {cost}')

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=15).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('nacho_skate:index')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=15).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('nacho_skate:index')
            # If spots are not full do the following
            
            if cost == 0: # Employees skate for free
                self.object.paid = True
            elif user_credit.balance >= cost and user_credit.paid:
                self.object.paid = True
                user_credit.balance -= cost
                # Check to see if there's a $0 balance, if so, set paid to false
                if user_credit.balance == 0:
                    user_credit.paid = False
                user_credit.save()
                credit_used = True # Used to set the message
            else:
                credit_used = self.add_to_cart(cost)
            self.object.save()
        except IntegrityError:
            pass
        # If all goes well set success message and return
        if cost == 0:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! {cost} credits has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.ERROR, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, cost):
        '''Adds Nacho Skate session to shopping cart.'''
        price = cost
        item_name = self.program_model.objects.get(id=15).program_name
        start_time = self.skate_date_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item=item_name, skater_name=self.request.user.get_full_name(), 
        event_date = self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()
        return False


class DeleteNachoSkateSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from a skate session'''
    model = NachoSkateSession
    skate_date_model = NachoSkateDate
    credit_model = UserCredit
    success_url = reverse_lazy('nacho_skate:index')

    def delete(self, *args, **kwargs):
        '''Things that need doing once a session is removed.'''

        user = User.objects.get(pk=kwargs['skater_pk'])

        if kwargs['paid'] == 'True':
            # If the session is paid for, issue credit to the user
            price = Program.objects.get(id=15).skater_price
            user_credit = self.credit_model.objects.get(slug=user)
            old_balance = user_credit.balance
            user_credit.balance += price
            user_credit.paid = True
            success_msg = f'{user.get_full_name()} has been removed from the session. The Users credit balance has been increased from ${old_balance} to ${user_credit.balance}.'
            user_credit.save()
        else:
            # Clear session from the cart, user hasn't paid yet
            skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('skate_date', flat=True)
            cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
            cart_item = Cart.objects.filter(item=Program.objects.all().get(id=15).program_name, event_date=cart_date[0].skate_date)
            cart_item.delete()
            success_msg = 'You have been removed from that skate session!'

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, success_msg)
        return super().delete(*args, **kwargs)
