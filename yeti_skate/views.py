from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from . import models, forms
from accounts.models import Profile
from programs.models import Program
from cart.models import Cart
from message_boards.models import Topic

from datetime import date

# Create your views here.

class YetiSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming Yeti skates.'''

    template_name = 'yeti_skate_dates.html'
    model = models.YetiSkateDate
    topic_model = Topic
    session_model = models.YetiSkateSession
    context_object_name = 'skate_dates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all skaters signed up for each session to display the list of skaters for each session
        skate_sessions = self.session_model.objects.filter(skate_date__skate_date__gte=date.today())
        context['skate_sessions'] = skate_sessions
        latest_topic = Topic.objects.filter(board=2).order_by('-last_updated').first()
        context['latest_topic'] = latest_topic
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).values('pk', 'skate_date', 'start_time', 'end_time')
        skater_sessions = self.session_model.objects.filter(skater=self.request.user).values_list('skate_date','pk', 'paid')
        # print(skater_sessions)
        # If user is already signed up for the skate, add key value pair to disable button
        for item in queryset:
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


class CreateYetiSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = models.YetiSkateSession
    form_class = forms.CreateYetiSkateSessionForm
    group_model = Group
    profile_model = Profile
    program_model = Program
    session_model = models.YetiSkateDate
    cart_model = Cart
    template_name = 'yeti_skate_sessions_form.html'
    # success_url = '/web_apps/yeti_skate/'
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

        self.object = form.save(commit=False)
        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=7).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('yeti_skate:yeti-skate')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=7).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('yeti_skate:yeti-skate')
            # If spots are not full do the following
            if self.request.user.is_staff or self.object.goalie: # Employees and goalies skate for free
                self.object.paid = True
            else:
                self.add_to_cart()
            self.join_yeti_skate_group()
            self.add_yeti_skate_email_to_profile()
            self.object.save()
        except IntegrityError:
            pass
        # If all goes well set success message and return
        if self.object.goalie or self.request.user.is_staff:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self):
        '''Adds Yeti Skate session to shopping cart.'''
        # Get price of Yeti Skate program
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

    def join_yeti_skate_group(self, join_group='Yeti Skate'):
        '''Adds user to Yeti Skate group "behind the scenes", for communication purposes.'''
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
            try:
                # If a profile already exists, set yeti_skate_email to True
                profile = self.profile_model.objects.get(user=self.request.user)
                profile.yeti_skate_email = True
                profile.save()
            except ObjectDoesNotExist:
                pass
        except IntegrityError:
            pass
        return

    def add_yeti_skate_email_to_profile(self):
        '''If no user profile exists, create one and set yeti_skate_email to True.'''
        
        # If a profile already exists, do nothing
        try:
            self.profile_model.objects.get(user=self.request.user)
            return
        # If no profile exists, add one and set open_hockey_email to True
        except ObjectDoesNotExist:
            profile = self.profile_model(user=self.request.user, slug=self.request.user.id, yeti_skate_email=True)
            profile.save()
            return


class DeleteYetiSkateSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from a skate session'''
    model = models.YetiSkateSession
    skate_date_model = models.YetiSkateDate
    success_url = reverse_lazy('yeti_skate:yeti-skate')

    def delete(self, *args, **kwargs):
        '''Things that need doing once a session is removed.'''

        # Clear session from the cart
        skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('skate_date', flat=True)
        cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
        # print(cart_date[0])
        cart_item = Cart.objects.filter(item=Program.objects.all().get(id=7).program_name, event_date=cart_date[0].skate_date).delete()

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, 'You have been removed from that skate session!')
        return super().delete(*args, **kwargs)

################ The following views are for staff only ##########################################################

class YetiSkateDateStaffListView(LoginRequiredMixin, ListView):
    '''Displays page with list of upcoming Yeti Skate skates with buttons for viewing registered skaters.'''

    model = models.YetiSkateDate
    sessions_model = models.YetiSkateSession
    context_object_name = 'skate_dates'
    template_name = 'yeti_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('skate_date')
        context['session_skaters'] = session_skaters
        return context
