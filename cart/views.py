from django.shortcuts import render
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import IntegrityError
from . import models
from figure_skating.models import FigureSkatingSession, FigureSkater, FigureSkatingDate
from open_hockey.models import OpenHockeySessions, OpenHockeyMember
from stickandpuck.models import StickAndPuckSessions, StickAndPuckSkaters
from thane_storck.models import SkateSession, SkateDate
from adult_skills.models import AdultSkillsSkateDate, AdultSkillsSkateSession

# Create your views here.


class CartView(LoginRequiredMixin, ListView):
    '''Shopping Cart View'''

    model = models.Cart
    template_name = 'shopping_cart.html'
    context_object_name = 'shopping_cart_items'

    def get_queryset(self):
        '''Returns the shopping cart items to the template.'''

        queryset = super().get_queryset()
        return queryset.filter(customer=self.request.user.id)

    def get_context_data(self, **kwargs):
        '''Returns the shopping cart total to the template.'''

        context = super().get_context_data(**kwargs)
        items_cost = self.model.objects.filter(customer=self.request.user).values_list('amount', flat=True)
        total = 0
        for item_cost in items_cost:
            total += item_cost
        context['cart_total'] = total
        return context


class RemoveItemFromCartView(LoginRequiredMixin, DeleteView):
    '''View removes an item from the cart and deletes the corresponding session record.'''

    model = models.Cart
    fs_model = FigureSkatingSession
    fs_skater_model = FigureSkater
    fs_date_model = FigureSkatingDate
    oh_model = OpenHockeySessions
    oh_member_model = OpenHockeyMember
    snp_model = StickAndPuckSessions
    snp_skater_model = StickAndPuckSkaters
    ts_model = SkateSession
    ts_skate_date_model = SkateDate
    as_model = AdultSkillsSkateSession
    as_skate_date_model = AdultSkillsSkateDate
    success_url = reverse_lazy('cart:shopping-cart')

    def delete(self, request, *args, **kwargs):
        # Determine which model session we are deleting that corresponds to cart item.
        cart_item = self.model.objects.get(pk=kwargs['pk'])
        if cart_item.item == 'Stick and Puck':
            skater_name = cart_item.skater_name.split(' ')
            skater_id = self.snp_skater_model.objects.filter(guardian=request.user, first_name=skater_name[0], last_name=skater_name[1])
            self.snp_model.objects.filter(skater=skater_id[0], session_date=cart_item.event_date, session_time=cart_item.event_start_time).delete()
        elif cart_item.item == 'Open Hockey':
            self.oh_model.objects.filter(skater=request.user, date=cart_item.event_date).delete()
        elif cart_item.item == 'Thane Storck':
            skate_date = self.ts_skate_date_model.objects.filter(skate_date=cart_item.event_date)
            self.ts_model.objects.filter(skater=request.user, skate_date=skate_date[0]).delete()
        elif cart_item.item == 'Adult Skills':
            skate_date = self.as_skate_date_model.objects.filter(skate_date=cart_item.event_date)
            self.as_model.objects.filter(skater=request.user, skate_date=skate_date[0]).delete()
        elif cart_item.item == 'Figure Skating':
            skater_name = cart_item.skater_name.split(' ')
            skater_id = self.fs_skater_model.objects.filter(guardian=request.user, first_name=skater_name[0], last_name=skater_name[1])
            skate_date_id = self.fs_date_model.objects.filter(skate_date=cart_item.event_date, start_time=cart_item.event_start_time)
            self.fs_model.objects.filter(skater=skater_id[0], session=skate_date_id[0].id).delete()
        elif cart_item.item == 'OH Membership':
            self.oh_member_model.objects.filter(member=request.user).delete()

        return super().delete(request, *args, **kwargs)
