from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

from . import models, forms
from accounts.models import UserCredit
from programs.models import Program
from cart.models import Cart

from datetime import date


class OWHLSkateDateListView(LoginRequiredMixin, ListView):
    '''Page that displays upcoming OWHL Hockey skates.'''

    template_name = 'owhl_skate_dates.html'
    model = models.OWHLSkateDate
    session_model = models.OWHLSkateSession
    group_model = Group
    credit_model = UserCredit
    context_object_name = 'skate_dates'

    def get(self, request, *args, **kwargs):
        '''Adds user to OWHL Hockey group "behind the scenes", for communication purposes.'''
        
        try:
            group = self.group_model.objects.get(name='OWHL Hockey')
            self.request.user.groups.add(group)
        except IntegrityError:
            pass

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        queryset = queryset.filter(skate_date__gte=date.today()).values('pk', 'skate_date', 'start_time', 'end_time').annotate(num_skaters=Count('session_skaters'))
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


class CreateOWHLSkateSessionView(LoginRequiredMixin, CreateView):
    '''Page that displays form for user to register for skate sessions.'''

    model = models.OWHLSkateSession
    form_class = forms.CreateOWHLSkateSessionForm
    group_model = Group
    program_model = Program
    session_model = models.OWHLSkateDate
    cart_model = Cart
    credit_model = UserCredit
    template_name = 'owhl_skate_sessions_form.html'
    success_url = '/web_apps/owhl/'

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs.update({'user': self.request.user})
    #     return kwargs

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

        user_credit = self.credit_model.objects.get(user=self.request.user) # User credit model
        credit_used = False # Used to set the success message
        price = 0

        self.object = form.save(commit=False)

        try:
            # If goalie spots are full, do not save object
            if self.object.goalie == True and self.model.objects.filter(goalie=True, skate_date=self.object.skate_date).count() == Program.objects.get(pk=13).max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('owhl:index')
            # If skater spots are full, do not save object
            elif self.object.goalie == False and self.model.objects.filter(goalie=False, skate_date=self.object.skate_date).count() == Program.objects.get(pk=13).max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('owhl:index')

            # If spots are not full do the following
            skater_cost = self.program_model.objects.get(program_name='OWHL Hockey').skater_price
            goalie_cost = self.program_model.objects.get(program_name='OWHL Hockey').goalie_price

            # Set the appropriate price
            if self.object.goalie:
                price = goalie_cost
            else:
                price = skater_cost

            if user_credit.balance == 0:
                # If user credit has been depleted, make sure user credit paid is set to False
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
            self.object.save()
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
        '''Adds OWHL Hockey session to shopping cart.'''

        start_time = self.session_model.objects.filter(skate_date=self.object.skate_date.skate_date).values_list('start_time', flat=True)
        cart = self.cart_model(customer=self.request.user, item='OWHL Hockey', skater_name=self.object.skater, 
            event_date=self.object.skate_date.skate_date, event_start_time=start_time[0], amount=price)
        cart.save()
        return False


class DeleteOWHLSkateSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove skaters from a skate session'''
    model = models.OWHLSkateSession
    skate_date_model = models.OWHLSkateDate
    credit_model = UserCredit
    success_url = reverse_lazy('owhl:owhl')

    def delete(self, *args, **kwargs):
        '''Things that need doing once a session is removed.'''

        user = User.objects.get(pk=kwargs['skater_pk'])

        if kwargs['paid'] == 'True':
            # If the session is paid for, issue credit to the user
            # Get the program skater/goalie cost
            if User.objects.get(pk=kwargs['skater_pk']).goalie == True:
                price = self.program_model.objects.get(id=15).goalie_price
            else:
                price = self.program_model.objects.get(id=15).skater_price
            user_credit = self.credit_model.objects.get(slug=user)
            old_balance = user_credit.balance
            user_credit.balance += price
            user_credit.paid = True
            success_msg = f'{user.get_full_name()} has been removed from the session. The Users credit balance has been increased from ${old_balance} to ${user_credit.balance}.'
            user_credit.save()
        else:
            # Clear session from the cart
            skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('skate_date', flat=True)
            cart_date = self.skate_date_model.objects.filter(id=skate_date[0])
            cart_item = Cart.objects.filter(item=Program.objects.all().get(id=13).program_name, event_date=cart_date[0].skate_date).delete()
            cart_item.delete()
            success_msg = 'You have been removed from that skate session!'
    
        # Send email to user about the credit
        recipients = User.objects.filter(id__in=['1', '2', user.id]).values_list('email', flat=True)
        subject = 'Credit Issued for OWHL Skate Session'
        msg = 'test email'
        from_email = 'no-reply@oicwebapp.com'
        
        try:
            send_mail(subject, success_msg, from_email, recipients)
            messages.add_message(self.request, messages.INFO, 'Email message has been sent to the skater!')
            self.success_url = reverse_lazy('owhl:owhl')
        #except:
            #messages.add_message(self.request, messages.ERROR, 'Oops, something went wrong!  Please try again.')
            #return reverse('contact:contact-form', kwargs={ 'form': form.cleaned_data })
        except Exception as e:
            messages.add_message(self.request, messages.ERROR, f'Failed to send email: {str(e)}')
        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, 'Skater has been removed from that skate session!')
        return super().delete(*args, **kwargs)

################ The following views are for staff only ##########################################################

class OWHLSkateDateStaffListView(LoginRequiredMixin, ListView):
    '''Displays page with list of upcoming OWHL Hockey skates with buttons for viewing registered skaters.'''

    model = models.OWHLSkateDate
    sessions_model = models.OWHLSkateSession
    context_object_name = 'skate_dates'
    template_name = 'owhl_skate_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(skate_date__gte=date.today()).order_by('skate_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(skate_date__skate_date__gte=date.today()).order_by('skate_date')
        context['session_skaters'] = session_skaters
        return context
