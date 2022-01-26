from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from .models import CaribouSkateDate, CaribouSkateSession
from .forms import CreateCaribouSkateSessionForm
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date

# Create your views here.

class CaribouSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Caribou skates.'''

    template_name = 'caribou_dates.html'
    model = CaribouSkateDate
    session_model = CaribouSkateSession
    credit_model = UserCredit
    group_model = Group
    profile_model = Profile
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Join the Caribou Group
        self.join_caribou_group()
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
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('skate_date','pk', 'paid')
        # If user is already signed up for the skate, add key value pair to disable button
        for item in queryset:
            item['registered_skaters'] = self.model.registered_skaters(skate_date=item['pk'])
            for session in skater_sessions:
                # If the session date and skate date match and paid is True, add disabled = True to queryset
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

    def join_caribou_group(self, join_group='Caribou'):
        '''Adds user to Caribou group "behind the scenes", for communication purposes.'''
        
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass

        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            # If no profile exists, create one and set caribou_email to True
            profile = self.profile_model(user=self.request.user, caribou_email=False, slug=self.request.user.id)
            profile.save()

        return

class CreateCaribouSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = CaribouSkateSession
    form_class = CreateCaribouSkateSessionForm
    profile_model = Profile
    program_model = Program
    skate_date_model = CaribouSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'caribou_skate_sessions_form.html'
    success_url = reverse_lazy('caribou:caribou')

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
                return redirect('caribou:caribou')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=15).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('caribou:caribou')
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
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! {cost} credits have been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.ERROR, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, cost):
        '''Adds Caribou Skate session to shopping cart.'''
        # Get price of Caribou Skate program
        # if self.object.goalie:
        #     price = self.program_model.objects.get(id=15).goalie_price
        #     if price == 0:
        #         return True
        # else:
        price = cost
        item_name = self.program_model.objects.get(id=15).program_name
        start_time = self.skate_date_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item=item_name, skater_name=self.request.user.get_full_name(), 
        event_date = self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()
        return False


class DeleteCaribouSkateSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from a skate session'''
    model = CaribouSkateSession
    skate_date_model = CaribouSkateDate
    success_url = reverse_lazy('caribou:caribou')

    def delete(self, *args, **kwargs):
        '''Things that need doing once a session is removed.'''

        # Clear session from the cart
        skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('skate_date', flat=True)
        cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
        # print(cart_date[0])
        cart_item = Cart.objects.filter(item=Program.objects.all().get(id=15).program_name, event_date=cart_date[0].skate_date)
        cart_item.delete()

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, 'You have been removed from that skate session!')
        return super().delete(*args, **kwargs)