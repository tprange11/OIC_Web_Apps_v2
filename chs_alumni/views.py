from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

from .models import CHSAlumniDate, CHSAlumniSession
from .forms import CreateCHSAlumniSkateSessionForm
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date, datetime

# Create your views here.

class CHSAlumniSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming CHS Alumni skates.'''

    template_name = 'chs_alumni_dates.html'
    model = CHSAlumniDate
    # skate_date_model = CHSAlumniSession
    credit_model = UserCredit
    group_model = Group
    profile_model = Profile
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Join the CHS Alumni Skate Group
        self.join_chs_alumni_group()
        
        # Create a user credit object if one does not exist
        try:
            credit = self.credit_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            credit = self.credit_model.objects.create(user=self.request.user, slug=self.request.user.username)
        context['credit'] = credit
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today())
        return queryset

    def join_chs_alumni_group(self, join_group='CHS Alumni'):
        '''Adds user to CHS Alumni group "behind the scenes".'''
        
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass

        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except IntegrityError:
            pass
        except ObjectDoesNotExist:
            # If no profile exists, create one and set chs_alumni_email to True
            profile = self.profile_model(user=self.request.user, chs_alumni_email=True, slug=self.request.user.id)
            profile.save()
        return


class CreateCHSAlumniSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = CHSAlumniSession
    form_class = CreateCHSAlumniSkateSessionForm
    profile_model = Profile
    program_model = Program
    skate_date_model = CHSAlumniDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'chs_alumni_sessions_form.html'
    success_url = reverse_lazy('chs_alumni:chs-alumni')

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['date'] = self.kwargs['pk']
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
        price = 0
        self.object = form.save(commit=False)

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, date=self.object.date).count() == Program.objects.get(pk=11).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('chs_alumni:chs-alumni')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, date=self.object.date).count() == Program.objects.get(pk=11).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('chs_alumni:chs-alumni')

            # Get the price of the skate
            if self.object.goalie:
                price = self.program_model.objects.get(id=11).goalie_price
                if price == 0:
                    self.object.paid = True
            else:
                price = self.program_model.objects.get(id=11).skater_price

            # If spots are not full do the following
            if user_credit.balance >= price and user_credit.paid:
                self.object.paid = True
                user_credit.balance -= price
                # Check to see if there's a $0 balance, if so, set paid to false
                if user_credit.balance == 0:
                    user_credit.paid = False
                user_credit.save()
                credit_used = True # Used to set the message
            else:
                self.add_to_cart(price)
                self.object.save()
        except IntegrityError:
            pass
        
        # If all goes well set success message and return
        if credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${price} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, price):
        '''Adds CHS Alumni Skate session to shopping cart.'''
        
        item_name = self.program_model.objects.get(id=11).program_name
        start_time = self.skate_date_model.objects.filter(skate_date=self.object.date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item=item_name, skater_name=self.request.user.get_full_name(), 
            event_date = self.object.date.skate_date, event_start_time=start_time[0].strftime('%I:%M %p'), amount=price)
        cart.save()
        return False


class DeleteCHSAlumniSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from a skate session if it is unpaid.'''
    model = CHSAlumniSession
    skate_date_model = CHSAlumniDate
    success_url = reverse_lazy('chs_alumni:chs-alumni')

    def delete(self, *args, **kwargs):
        '''Things that need doing once a session is removed.'''

        # Clear session from the cart
        skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('date', flat=True)
        cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
        # print(cart_date[0])
        Cart.objects.filter(
            item=Program.objects.all().get(id=11).program_name, 
            event_date=cart_date[0].skate_date, 
            customer=self.request.user).delete()

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, 'You have been removed from that skate session!')
        return super().delete(*args, **kwargs)


################ The following views are for staff only ##########################################################

class CHSAlumniSkateDateStaffListView(LoginRequiredMixin, ListView):
    '''Displays page with list of upcoming CHS ALumni Skate dates with buttons for viewing registered skaters.'''

    model = CHSAlumniDate
    context_object_name = 'skate_dates'
    template_name = 'chs_alumni_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date')
        return queryset
