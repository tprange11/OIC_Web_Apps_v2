'''Views for the Adult Skills program: list upcoming skates, register for one,
remove a registration, and a staff list of registered skaters.'''
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from programs.removal import SessionRemovalMixin
from programs.auth import StaffRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

from . import models, forms
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date


class AdultSkillsSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Adult Skills skates.'''

    template_name = 'adult_skills_skate_dates.html'
    model = models.AdultSkillsSkateDate
    session_model = models.AdultSkillsSkateSession
    program_model = Program
    profile_model = Profile
    credit_model = UserCredit
    group_model = Group
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Silently add the user to the Adult Skills group (used for communication)
        self.join_adult_skills_group()
        
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
        queryset = queryset.filter(skate_date__gte=date.today()).values('pk', 'skate_date', 'start_time', 'end_time')
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('skate_date', 'pk', 'paid')
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

    def join_adult_skills_group(self, join_group='Adult Skills'):
        '''Adds user to the Adult Skills group "behind the scenes", for communication purposes,
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
            # If no profile exists, create one with Adult Skills email notifications on
            profile = self.profile_model(user=self.request.user, adult_skills_email=True, slug=self.request.user.id)
            profile.save()

        return


class CreateAdultSkillsSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for an Adult Skills skate session.'''

    model = models.AdultSkillsSkateSession
    form_class = forms.CreateAdultSkillsSkateSessionForm
    profile_model = Profile
    program_model = Program
    session_model = models.AdultSkillsSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'adult_skills_skate_sessions_form.html'
    success_url = '/web_apps/adult_skills/'

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['skate_date'] = self.kwargs['pk']
            initial['skater'] = self.request.user
        return initial

    def form_valid(self, form):
        '''Enforces skater/goalie limits, then marks the session paid (from credit balance or
        free) or adds it to the cart for payment.'''

        user_credit = self.credit_model.objects.get(user=self.request.user) # User credit model
        credit_used = False # Used to set the success message
        price = 0

        self.object = form.save(commit=False)
        
        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=5).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('adult_skills:adult-skills')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=5).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('adult_skills:adult-skills')

            # Spots are available: get the skater/goalie cost (Program id 5 is Adult Skills)
            skater_cost = self.program_model.objects.get(id=5).skater_price
            goalie_cost = self.program_model.objects.get(id=5).goalie_price

            # Set the appropriate price
            if self.object.goalie:
                price = goalie_cost
            else:
                price = skater_cost

            # If the user has enough credits, deduct credits and set session as paid
            if user_credit.balance >= price:
                self.object.paid = True
                user_credit.balance -= price
                # A $0 balance means there is no credit left to pay with
                if user_credit.balance == 0:
                    user_credit.paid = False
                credit_used = True
            # Not enough credit: free sessions are marked paid, everything else goes in the cart
            else:
                if price == 0:
                    self.object.paid = True
                else:
                    self.add_to_cart(price)
            
            # Save the user credit model
            user_credit.save()
            self.object.save()
        except IntegrityError:
            pass

        # If all goes well set success message and return
        if price == 0:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${price} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your session(s)!')
        return super().form_valid(form)

    def add_to_cart(self, price):
        '''Adds Adult Skills session to shopping cart.'''

        start_time = self.session_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item='Adult Skills', skater_name=self.request.user.get_full_name(), 
            event_date=self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()


class DeleteAdultSkillsSkateSessionView(SessionRemovalMixin, DeleteView):
    '''Allows the skater or staff to remove a skater from a skate session. Refunds credit for
    a paid session (emailing the admins and the skater) or clears the cart item for an unpaid one.'''

    model = models.AdultSkillsSkateSession
    success_url = reverse_lazy('adult_skills:adult-skills')
    program_filter = {'pk': 5}
    cart_item_name = 'Adult Skills'
    notify_on_removal = True
    notify_subject = 'Credit Issued for Adult Skills Session'


class AdultSkillsSkateDateStaffListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    '''Displays page for staff that lists upcoming adult skills skate sessions.'''

    model = models.AdultSkillsSkateDate
    sessions_model = models.AdultSkillsSkateSession
    context_object_name = 'skate_dates'
    template_name = 'adult_skills_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).annotate(num_skaters=Count('adultskillsskatesession')).order_by('skate_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('skate_date', 'pk')
        context['session_skaters'] = session_skaters
        return context
