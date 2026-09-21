'''Views for the Open Figure Skating program: manage a user's skaters, register a skater for a
session, remove a registration, past sessions, and a staff list of registered skaters.'''
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import FigureSkatingDate, FigureSkater, FigureSkatingSession
from .forms import CreateFigureSkaterForm, CreateFigureSkatingSessionForm
from programs.models import Program
from cart.models import Cart
from accounts.models import Profile, UserCredit
from datetime import date


class FigureSkatingView(LoginRequiredMixin, TemplateView):
    '''Page that displays index view for Figure Skating web app.'''

    template_name = 'figure_skating.html'
    fs_dates_model = FigureSkatingDate
    skater_model = FigureSkater
    session_model = FigureSkatingSession
    program_model = Program
    credit_model = UserCredit

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fs_dates = self.fs_dates_model.objects.filter(skate_date__gte=date.today()).annotate(
            num_skaters=Count('figureskatingsession')).order_by('skate_date', 'start_time')
        context['fs_dates'] = fs_dates
        sessions = self.session_model.objects.filter(
            guardian=self.request.user, session__skate_date__gte=date.today()).order_by('session__skate_date')
        context['my_sessions'] = sessions
        skaters = self.skater_model.objects.filter(guardian=self.request.user)
        context['my_skaters'] = skaters
        max_skaters = self.program_model.objects.get(pk=3).max_skaters
        context['max_skaters'] = max_skaters
        # Get user credit model or create one if none exists
        try:
            credit = self.credit_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            credit = self.credit_model.objects.create(user=self.request.user, slug=self.request.user.username)
        context['credit'] = credit

        return context


class CreateFigureSkaterView(LoginRequiredMixin, CreateView):
    '''Page where user adds skaters to their My Skaters list (FigureSkater model).'''

    model = FigureSkater
    form_class = CreateFigureSkaterForm
    template_name = 'create_figure_skater_form.html'
    success_url = reverse_lazy('figure_skating:figure-skating')

    def form_valid(self, form):
        form.instance.guardian = self.request.user
        try:
            success = super().form_valid(form)
            messages.add_message(self.request, messages.SUCCESS,
                                 'Skater has been added to My Skaters!')
            return success
        except IntegrityError:
            messages.add_message(self.request, messages.ERROR,
                                 'This skater is already in My Skaters.')
            return render(self.request, template_name=self.template_name, context=self.get_context_data())


class DeleteFigureSkaterView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove their skaters from FigureSkater model.'''
    model = FigureSkater
    success_url = reverse_lazy('figure_skating:figure-skating')

    def delete(self, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS,
                             'Skater has been removed from My Skaters!')
        return super().delete(*args, **kwargs)


class CreateFigureSkatingSessionView(LoginRequiredMixin, CreateView):
    '''Page that allows users to sign up for figure skating sessions.'''

    model = FigureSkatingSession
    skater_model = FigureSkater
    program_model = Program
    cart_model = Cart
    group_model = Group
    profile_model = Profile
    credit_model = UserCredit
    template_name = 'create_figure_skating_session_form.html'
    success_url = reverse_lazy('figure_skating:figure-skating')
    form_class = CreateFigureSkatingSessionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['session'] = self.kwargs['session']
            return initial
        else:
            return {}

    def form_valid(self, form):
        '''Enforces the session's available_spots limit, then pays from credit balance or
        adds the session to the cart, and joins the user to the Figure Skating group.'''

        # Get the user credit model instance, or create if it does not exist
        try:
            user_credit = self.credit_model.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            user_credit = self.credit_model.objects.create(user=self.request.user, slug=self.request.user.username)
            user_credit.save()

        credit_used = False # Used to set the message

        form.instance.guardian = self.request.user
        self.object = form.save(commit=False)
        try:
            # If the session is full (capacity is per skate date, not per program), do not save object
            if self.model.objects.filter(session=form.instance.session.id).count() >= FigureSkatingDate.objects.get(pk=form.instance.session.id).available_spots:
                messages.add_message(
                    self.request, messages.ERROR, 'Sorry, this session is now full!')
                return redirect('figure_skating:figure-skating')
        except:
            pass
        # Price is the Figure Skating program (id 3) skater price plus the session's up/down charge
        cost = self.program_model.objects.get(id=3).skater_price + FigureSkatingDate.objects.get(pk=self.object.session.pk).up_down_charge

        # Pay from credit balance when the user has enough credit, otherwise add to cart
        if user_credit.balance >= cost:
            self.object.paid = True
            user_credit.balance -= cost
            # A $0 balance means there is no credit left to pay with
            if user_credit.balance == 0:
                user_credit.paid = False
            user_credit.save()
            credit_used = True
        else:
            self.add_to_cart(form.instance.skater, cost)

        self.join_figure_skating_group()
        self.add_figure_skating_email_to_profile()
        self.object.save()
        if credit_used:
            messages.add_message(self.request, messages.SUCCESS,
                                 f'Skater has been added to the session. ${cost} in credits have been deducted from your balance.')
        else:
            messages.add_message(self.request, messages.SUCCESS,
                                 'Skater has been added to the session. You must view your cart and pay for your session(s) to complete registration!')

        return super().form_valid(form)

    def add_to_cart(self, skater, price):
        '''Adds Open Figure Skating session to shopping cart.'''

        cart = self.cart_model(customer=self.request.user, item='Figure Skating', skater_name=skater,
                               event_date=self.object.session.skate_date, event_start_time=self.object.session.start_time, amount=price)
        cart.save()

    def join_figure_skating_group(self, join_group='Figure Skating'):
        '''Adds user to Figure Skating group "behind the scenes", for communication purposes.'''
        try:
            group = self.group_model.objects.get(name=join_group)
            self.request.user.groups.add(group)
        except IntegrityError:
            pass
        return

    def add_figure_skating_email_to_profile(self):
        '''If no user profile exists, create one and set figure_skating_email to True.'''
        # If a profile already exists, do nothing
        try:
            self.profile_model.objects.get(user=self.request.user)
        # If no profile exists, add one and set figure_skating_email to True
        except ObjectDoesNotExist:
            profile = self.profile_model(
                user=self.request.user, slug=self.request.user.id, figure_skating_email=True)
            profile.save()
        return


class DeleteFigureSkatingSessionView(LoginRequiredMixin, DeleteView):
    '''Allows user to remove a skater from a skate session, refunding credit if it was paid.'''
    model = FigureSkatingSession
    skate_date_model = FigureSkatingDate
    skater_model = FigureSkater
    credit_model = UserCredit
    program_model = Program
    success_url = reverse_lazy('figure_skating:figure-skating')

    def delete(self, *args, **kwargs):
        '''Refunds credit for a paid session, or clears the cart item for an unpaid one,
        before the session is deleted.'''

        credit_refund = False # Used to set the message.

        if self.model.objects.get(pk=kwargs['pk']).paid:
            # Refund the program price plus the session's up/down charge to the user's credit
            credits_to_refund = self.program_model.objects.get(id=3).skater_price + self.model.objects.get(pk=kwargs['pk']).session.up_down_charge
            user_credit = self.credit_model.objects.get(user=self.request.user)
            user_credit.balance += credits_to_refund
            user_credit.save()
            credit_refund = True
        else:
            # Clear session from the cart
            skate_date = self.model.objects.filter(
            id=kwargs['pk']).values_list('session__skate_date', flat=True)
            skate_time = self.model.objects.filter(
                id=kwargs['pk']).values_list('session__start_time', flat=True)
            skater_id = self.model.objects.filter(
                id=kwargs['pk']).values_list('skater', flat=True)
            skater = self.skater_model.objects.get(id=skater_id[0])
            cart_item = Cart.objects.filter(item=Program.objects.all().get(
                id=3).program_name, event_date=skate_date[0], event_start_time=skate_time[0], skater_name=skater).delete()

        # Set success message and return
        if credit_refund:
            messages.add_message(self.request, messages.SUCCESS,
                             f'Skater has been removed from the figure skating session!  ${credits_to_refund} in credit was added to your balance.')
        else:
            messages.add_message(self.request, messages.SUCCESS,
                             'Skater has been removed from the figure skating session!')
        return super().delete(*args, **kwargs)


class FigureSkatingPastSessionsListView(LoginRequiredMixin, ListView):
    '''Displays past figure skating sessions.'''

    model = FigureSkatingSession
    context_object_name = 'past_sessions'
    template_name = 'past_figure_skating_sessions_list.html'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(guardian=self.request.user, session__skate_date__lt=date.today()).order_by('-session__skate_date')
        return queryset


#################### The following view is for staff only ##########################

class FigureSkatingStaffListView(LoginRequiredMixin, ListView):
    '''Displays page for staff that lists upcoming figure skating sessions.'''

    model = FigureSkatingDate
    sessions_model = FigureSkatingSession
    context_object_name = 'skate_dates'
    template_name = 'figure_skating_sessions_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            skate_date__gte=date.today()).order_by('skate_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_skaters = self.sessions_model.objects.filter(
            session__skate_date__gte=date.today()).order_by('session')
        context['session_skaters'] = session_skaters
        return context
