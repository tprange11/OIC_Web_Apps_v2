from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.checks import messages
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import ListView, DeleteView
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from datetime import date

from django.views.generic.edit import CreateView

from . import models, forms
from accounts.models import Profile, UserCredit, ChildSkater
from cart.models import Cart

class PrivateSkateListView(LoginRequiredMixin, ListView):
    '''Page that displays private skates for which user is a member of the group.'''

    template_name = "private_skates_listview.html"
    model = models.PrivateSkate
    context_object_name = "private_skates"

    def get_queryset(self):
        queryset = super().get_queryset()
        # Get groups the user belongs to
        users_groups = self.request.user.groups.values_list('name', flat=True)
        queryset = queryset.filter(slug__in=users_groups)
        return queryset


class PrivateSkateDatesListView(LoginRequiredMixin, ListView):
    '''Page that displays skate dates for a particular private skate.'''

    template_name = "private_skate_dates_listview.html"
    model = models.PrivateSkateDate
    group_model = Group
    profile_model = Profile
    context_object_name = "skate_dates"

    def get(self, *args, **kwargs):
        '''Add user to private skate group, create user profile and add user to ChildSkater model when the page is requested.'''
        try:
            group = self.group_model.objects.get(name=kwargs['slug'])
            self.request.user.groups.add(group)
        except Group.DoesNotExist:
            messages.add_message(self.request, messages.ERROR, 'The URL you provided is incorrect.  Please verify the URL and try again!')

        try:
            # If a profile already exists, do nothing
            profile = self.profile_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            # If no profile exists, create one
            profile = self.profile_model(user=self.request.user, slug=self.request.user.id)
            profile.save()

        try:
            # Check if user is already in ChildSkater model
            ChildSkater.objects.get(user=self.request.user, first_name=self.request.user.first_name, last_name=self.request.user.last_name)
        except ObjectDoesNotExist:
            # Add user to ChildSkater model
            ChildSkater.objects.create(user=self.request.user, first_name=self.request.user.first_name, last_name=self.request.user.last_name, date_of_birth=None)
            pass

        return super().get(self.request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get or create user credit object
        try:
            credit = UserCredit.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            credit = UserCredit.objects.create(user=self.request.user, slug=self.request.user.username)
        context['credit'] = credit
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(private_skate__slug=self.kwargs['slug'], date__gte=date.today())
        return queryset


class PrivateSkateSessionCreateView(LoginRequiredMixin, CreateView):
    '''Page that displays form for registering for a private skate.'''
    model = models.PrivateSkateSession
    cart_model = Cart
    form_class = forms.PrivateSkateSessionForm
    template_name = 'private_skate_session_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['skate_date'] = self.kwargs['pk']
            initial['user'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get private skate date info to display on the template
        if self.request.method == 'GET':
            context['skate_info'] = models.PrivateSkateDate.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        # Get the slug for the PrivateSkate object to use in the success_url
        slug = self.object.skate_date.private_skate.slug
        self.success_url = reverse_lazy('private_skates:skate-dates', kwargs={'slug': slug})
        user_credit = UserCredit.objects.get(user=self.request.user)
        credit_used = False # Used to set the success message
        price = 0

        # Get the number of skaters and goalies that are registered for the skate
        registered_skaters = models.PrivateSkateDate.registered_skaters(self.object.skate_date)

        try:
            # If goalie or skater spots are full, do not save object and set message
            if self.object.goalie and registered_skaters['num_goalies'] == self.object.skate_date.private_skate.max_goalies:
                messages.add_message(self.request, messages.ERROR, 'Sorry, goalie spots are full!')
                return redirect('private_skates:skate-dates', slug=slug)
            elif not self.object.goalie and registered_skaters['num_skaters'] == self.object.skate_date.private_skate.max_skaters:
                messages.add_message(self.request, messages.ERROR, 'Sorry, skater spots are full!')
                return redirect('private_skates:skate-dates', slug=slug)

            # Get the price of the skate
            if self.object.goalie:
                price = self.object.skate_date.private_skate.goalie_price
                if price == 0:
                    self.object.paid = True
            else:
                price = self.object.skate_date.private_skate.skater_price

            # Determine if user credit was used to register
            if user_credit.balance >= price and user_credit.paid:
                self.object.paid = True
                user_credit.balance -= price
                if user_credit.balance == 0:
                    user_credit.paid = False
                user_credit.save()
                credit_used = True
            else:
                if price != 0:
                    self.add_to_cart(price)
            self.object.save()
        except:
            pass

        # If all goes well, set success message and return
        if price == 0:
            messages.add_message(self.request, messages.INFO, 'You have successfully registered for the skate!')
        elif credit_used:
            messages.add_message(self.request, messages.INFO, f'You have successfully registered for the skate! ${price} in credit has been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.INFO, 'To complete your registration, you must view your cart and pay for your item(s)!')
        return super().form_valid(form)

    def add_to_cart(self, price):
        '''Adds Private Skate session to shopping cart.'''

        item_name = self.object.skate_date.private_skate.name
        start_time = self.object.skate_date.start_time
        cart = self.cart_model(
            customer=self.request.user, 
            item=item_name, 
            skater_name=f"{self.object.skater.first_name} {self.object.skater.last_name}", 
            event_date = self.object.skate_date.date, 
            event_start_time=start_time.strftime('%I:%M %p'), 
            amount=price)
        cart.save()
        return False


class PrivateSkateSessionDeleteView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove themself from a skate session if it is unpaid.'''
    model = models.PrivateSkateSession
    
    def delete(self, *args, **kwargs):
        # Clear the session from the cart
        skate_date = self.model.objects.filter(id=kwargs['pk']).values_list('skate_date', flat=True)
        skate_date_object = models.PrivateSkateDate.objects.all().filter(id=skate_date[0])
        skater_id = self.model.objects.filter(id=kwargs['pk']).values_list('skater', flat=True)
        skater = ChildSkater.objects.get(id=skater_id[0])
        skater_name = f"{skater.first_name} {skater.last_name}"
        cart_date = skate_date_object[0].date
        Cart.objects.filter(
            item=skate_date_object[0].private_skate.name, 
            event_date=cart_date,
            skater_name=skater_name
            ).delete()

        # Set success message and return
        messages.add_message(self.request, messages.SUCCESS, 'Skater has been removed from the skate session!')
        self.success_url = reverse_lazy('private_skates:skate-dates', kwargs={'slug': skate_date_object[0].private_skate.slug})
        return super().delete(*args, **kwargs)
