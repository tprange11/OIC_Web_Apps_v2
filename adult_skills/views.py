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

from datetime import date

# Create your views here.

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
        self.join_adult_skills_group()
        
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
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('skate_date', 'pk', 'paid')
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

    def join_adult_skills_group(self, join_group='Adult Skills'):
        '''Adds user to Adult Skills group "behind the scenes", for communication purposes.'''

        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass

        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            # If a profile does not exist, create one and set adult_skills_email to True
            profile = self.profile_model(user=self.request.user, adult_skills_email=True, slug=self.request.user.id)
            profile.save()

        return


class CreateAdultSkillsSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = models.AdultSkillsSkateSession
    form_class = forms.CreateAdultSkillsSkateSessionForm
    # group_model = Group
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

            # If spots are not full do the following
            skater_cost = self.program_model.objects.get(id=5).skater_price
            goalie_cost = self.program_model.objects.get(id=5).goalie_price

            # Set the appropriate price
            if self.object.goalie:
                price = goalie_cost
            else:
                price = skater_cost
            
            # If the user credit balance is 0, set paid = False
            if user_credit.balance == 0:
                # User is paying with credit card, add item to cart
                user_credit.paid = False

            # If the user has enough credits, deduct credits and set session as paid
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
            # self.add_adult_skills_email_to_profile()
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

    # def add_adult_skills_email_to_profile(self):
    #     '''If no user profile exists, create one and set adult_skills_email to True.'''
        
    #     # If a profile already exists, do nothing
    #     try:
    #         self.profile_model.objects.get(user=self.request.user)
    #         return
    #     # If no profile exists, create one and set adult_skills_email to True
    #     except ObjectDoesNotExist:
    #         profile = self.profile_model(user=self.request.user, slug=self.request.user.id, adult_skills_email=True)
    #         profile.save()
    #         return


class DeleteAdultSkillsSkateSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from a skate session prior to paying.'''

    model = models.AdultSkillsSkateSession
    skate_date_model = models.AdultSkillsSkateDate
    success_url = reverse_lazy('adult_skills:adult-skills')

    def delete(self, *args, **kwargs):
        '''Things to do if a session is deleted.'''

        # Clear session from the cart
        skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('skate_date', flat=True)
        cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
        cart_item = Cart.objects.filter(item=Program.objects.all().get(id=5).program_name, event_date=cart_date[0].skate_date).delete()

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, 'You have been removed from that skate session!')
        return super().delete(*args, **kwargs)


#################### The following view is for staff only ##########################

class AdultSkillsSkateDateStaffListView(LoginRequiredMixin, ListView):
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
        session_skaters = self.sessions_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('skate_date')
        context['session_skaters'] = session_skaters
        return context
