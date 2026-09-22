'''Yeti Skate (Program id 7): adult skaters register themselves for scheduled skates.

Staff, goalies and user id 359 skate for free. New skaters (YetiSkateNewSkater) cannot
sign up for Friday skates until Thursday. Near-copy of nacho_skate/owhl/thane_storck.
'''
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from .models import YetiSkateDate, YetiSkateSession, YetiSkateNewSkater
from .forms import CreateYetiSkateSessionForm
from accounts.models import Profile, UserCredit
from programs.models import Program
from cart.models import Cart
from programs.removal import SessionRemovalMixin
from programs.auth import StaffRequiredMixin

from datetime import date


class YetiSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Yeti skates.'''

    template_name = 'yeti_skate_dates.html'
    model = YetiSkateDate
    session_model = YetiSkateSession
    credit_model = UserCredit
    group_model = Group
    profile_model = Profile
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all skaters signed up for each session to display the list of skaters for each session.
        # Order by pk so the modal lists skaters in the order they registered
        # (earliest registration first). YetiSkateSession has no created_at
        # field, so the auto-increment primary key is the reliable proxy.
        skate_sessions = self.session_model.objects.filter(
            skate_date__skate_date__gte=date.today()
        ).order_by('pk')
        context['skate_sessions'] = skate_sessions
        
        # New skaters may only sign up for Friday skates on Thursday; the template
        # uses day_of_week and new_skater to hide the Friday button otherwise
        context['day_of_week'] = date.today().weekday() # 0-6
        try:
            YetiSkateNewSkater.objects.get(skater=self.request.user)
        except ObjectDoesNotExist:
            new_skater = False
        else:
            new_skater = True
        context['new_skater'] = new_skater

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
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('skate_date','pk', 'paid')
        # Annotate each date with skater/goalie counts and, if the user is already
        # signed up, the session details so the template can disable the button
        for item in queryset:
            item['registered_skaters'] = self.model.registered_skaters(skate_date=item['pk'])
            for session in skater_sessions:
                # Both branches do the same thing; paid/unpaid are handled identically here
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

    # Parked: automatic "Yeti Skate" group join and Profile creation is switched off
    # (nacho_skate still does this); users must join/opt in themselves.
    # def join_yeti_skate_group(self, join_group='Yeti Skate'):
    #     '''Adds user to Yeti Skate group "behind the scenes", for communication purposes.'''
        
    #     try:
    #         group = self.group_model.objects.get(name=join_group)
    #         self.request.user.groups.add(group)
    #     except IntegrityError:
    #         pass

    #     try:
    #         # If a profile already exists, do nothing
    #         profile = self.profile_model.objects.get(user=self.request.user)
    #     except ObjectDoesNotExist:
    #         # If no profile exists, create one and set yeti_skate_email to True
    #         profile = self.profile_model(user=self.request.user, yeti_skate_email=True, slug=self.request.user.id)
    #         profile.save()

    #     return

class CreateYetiSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = YetiSkateSession
    form_class = CreateYetiSkateSessionForm
    profile_model = Profile
    program_model = Program
    session_model = YetiSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'yeti_skate_sessions_form.html'
    success_url = reverse_lazy('yeti_skate:yeti-skate')

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
            context['skate_info'] = self.session_model.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        '''Enforce goalie/skater caps, then pay from user credit or add to the cart.'''

        user_credit = UserCredit.objects.get(user=self.request.user)
        credit_used = False # Used to set the message
        self.object = form.save(commit=False)

        # Program id 7 is Yeti Skate
        if self.object.goalie == True:
            cost = self.program_model.objects.get(id=7).goalie_price
        else:
            cost = self.program_model.objects.get(id=7).skater_price

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=7).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('yeti_skate:yeti-skate')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=7).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('yeti_skate:yeti-skate')
            
            if self.request.user.is_staff or self.object.goalie or self.request.user.id == 359: # Staff, goalies and user 359 skate for free
                self.object.paid = True
                cost = 0 # Set cost = 0 for correct message
            elif user_credit.balance >= cost and user_credit.paid:
                self.object.paid = True
                user_credit.balance -= cost
                # A zero balance is flagged as unpaid so it can't be spent again
                if user_credit.balance == 0:
                    user_credit.paid = False
                user_credit.save()
                credit_used = True # Used to set the message
            else:
                self.add_to_cart()
            self.object.save()
        # Duplicate sign-up is silently ignored; super().form_valid() will re-raise on save
        except IntegrityError:
            pass
        # If all goes well set success message and return
        if self.object.goalie or self.request.user.is_staff:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${cost} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self):
        '''Adds Yeti Skate session to shopping cart.

        Only reached for non-goalies (goalies are marked paid in form_valid), so the
        goalie branch below is dead.
        '''
        if self.object.goalie:
            price = self.program_model.objects.get(id=7).goalie_price
            if price == 0:
                return True
        else:
            price = self.program_model.objects.get(id=7).skater_price
            item_name = self.program_model.objects.get(id=7).program_name
            start_time = self.session_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
            cart = self.cart_model(customer=self.request.user, item=item_name, skater_name=self.request.user.get_full_name(), 
            event_date = self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
            cart.save()
            return False


class DeleteYetiSkateSessionView(SessionRemovalMixin, DeleteView):
    '''Allows user to remove themself from a skate session (refund / cart cleanup in the mixin).'''
    model = YetiSkateSession
    success_url = reverse_lazy('yeti_skate:yeti-skate')

    program_filter = {'pk': 7}
    free_user_ids = (359,)       # user 359 skates for free (see CreateYetiSkateSessionView)
    manager_user_ids = (359,)    # skate organizer; the template shows him the remove buttons
    notify_on_refund = True
    admin_notify_ids = (1, 2, 359)
    notify_subject = 'Credit Issued for Yeti Skate Session'

    def get_refund_amount(self, session):
        # Goalies are never charged in this program (see CreateYetiSkateSessionView), so nothing to refund
        if session.goalie:
            return 0
        return super().get_refund_amount(session)

# The following views are for staff only.

class YetiSkateDateStaffListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    '''Displays page with list of upcoming Yeti Skate skates with buttons for viewing registered skaters.'''

    model = YetiSkateDate
    sessions_model = YetiSkateSession
    context_object_name = 'skate_dates'
    template_name = 'yeti_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('skate_date', 'pk')
        context['session_skaters'] = session_skaters
        return context
