"""Shopping cart: lists the user's unpaid items and lets them remove one, which also
deletes the matching session registration in the owning program app."""
import os
from django.http import Http404
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from . import models

from accounts.models import ChildSkater, UserCredit
from programs.models import Program
from figure_skating.models import FigureSkatingSession, FigureSkater, FigureSkatingDate
from stickandpuck.models import StickAndPuckSession, StickAndPuckSkater
from thane_storck.models import SkateSession, SkateDate
from adult_skills.models import AdultSkillsSkateDate, AdultSkillsSkateSession
from mike_schultz.models import MikeSchultzSkateDate, MikeSchultzSkateSession
from yeti_skate.models import YetiSkateDate, YetiSkateSession
from womens_hockey.models import WomensHockeySkateDate, WomensHockeySkateSession
from bald_eagles.models import BaldEaglesSkateDate, BaldEaglesSession
from lady_hawks.models import LadyHawksSkateDate, LadyHawksSkateSession
from chs_alumni.models import CHSAlumniDate, CHSAlumniSession
from private_skates.models import PrivateSkate, PrivateSkateDate, PrivateSkateSession
from open_roller.models import OpenRollerSkateDate, OpenRollerSkateSession
from owhl.models import OWHLSkateDate, OWHLSkateSession
from kranich.models import KranichSkateDate, KranichSkateSession
from nacho_skate.models import NachoSkateDate, NachoSkateSession
from ament.models import AmentSkateDate, AmentSkateSession


class CartView(LoginRequiredMixin, ListView):
    '''Cart page with the total and the embedded Square card form.'''
    model = models.Cart
    template_name = 'shopping_cart.html'
    context_object_name = 'shopping_cart_items'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(customer=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        items_cost = self.model.objects.filter(
            customer=self.request.user
        ).values_list('amount', flat=True)

        total = 0
        for item_cost in items_cost:
            total += item_cost

        context['cart_total'] = total

        # Used by the inline Square checkout script in shopping_cart.html.
        context['square_app_id'] = os.getenv('SQUARE_APP_ID')
        context['square_location_id'] = os.getenv('SQUARE_LOCATION_ID')

        return context

class RemoveItemFromCartView(LoginRequiredMixin, DeleteView):
    """
    Removes a cart row and deletes the session registration it represents.

    The cart row only stores the program name, skater name, date and start time, so
    each branch in form_valid() re-finds the session from those strings. The program
    is identified by its Program id (hard-coded below), so the Program table ids must
    not change. The side-effects live in form_valid() rather than delete() as Django
    4 recommends; post() is overridden so a stale row just redirects instead of 404ing.
    """

    model = models.Cart

    progam_model = Program
    fs_model = FigureSkatingSession
    fs_skater_model = FigureSkater
    fs_date_model = FigureSkatingDate
    snp_model = StickAndPuckSession
    snp_skater_model = StickAndPuckSkater
    ts_model = SkateSession
    ts_skate_date_model = SkateDate
    as_model = AdultSkillsSkateSession
    as_skate_date_model = AdultSkillsSkateDate
    ms_model = MikeSchultzSkateSession
    ms_skate_date_model = MikeSchultzSkateDate
    yeti_skate_model = YetiSkateSession
    yeti_skate_date_model = YetiSkateDate
    wh_skate_model = WomensHockeySkateSession
    wh_skate_date_model = WomensHockeySkateDate
    be_skate_model = BaldEaglesSession
    be_skate_date_model = BaldEaglesSkateDate
    lh_skate_model = LadyHawksSkateSession
    lh_skate_date_model = LadyHawksSkateDate
    chs_skate_model = CHSAlumniSession
    chs_skate_date_model = CHSAlumniDate
    private_skate_model = PrivateSkateSession
    private_skate_date_model = PrivateSkateDate
    open_roller_model = OpenRollerSkateSession
    open_roller_skate_date_model = OpenRollerSkateDate
    owhl_model = OWHLSkateSession
    owhl_skate_date_model = OWHLSkateDate
    kranich_model = KranichSkateSession
    kranich_skate_date_model = KranichSkateDate
    nacho_skate_model = NachoSkateSession
    nacho_skate_date_model = NachoSkateDate
    ament_skate_model = AmentSkateSession
    ament_skate_date_model = AmentSkateDate

    user_credit_model = UserCredit
    success_url = reverse_lazy("cart:shopping-cart")

    def post(self, request, *args, **kwargs):
        """Redirect instead of 404 when the row is already gone (nightly cleanup, cached page)."""
        try:
            self.object = self.get_object()
        except Http404:
            return redirect("cart:shopping-cart")

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Delete the session behind this cart row, then let DeleteView delete the row."""
        request = self.request
        cart_item = self.object  # already fetched in post()

        # Skater names are split on spaces to look the skater up again, so a skater
        # with a multi-word first or last name will not be found (only the Figure
        # Skating branch handles a three-part name).

        if cart_item.item == Program.objects.all().get(id=2).program_name:  # Stick and Puck
            skater_name = cart_item.skater_name.split(" ")
            skater_id = self.snp_skater_model.objects.filter(
                guardian=request.user,
                first_name=skater_name[0],
                last_name=skater_name[1],
            )
            self.snp_model.objects.filter(
                skater=skater_id[0],
                session_date=cart_item.event_date,
                session_time=cart_item.event_start_time,
            ).delete()

        # Program id 1 (Open Hockey) is retired: its URLs are commented out in
        # OIC_Web_Apps/urls.py, so no cart rows are created for it any more.

        elif cart_item.item == Program.objects.all().get(id=4).program_name:  # Thane Storck
            skate_date = self.ts_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.ts_model.objects.filter(
                skater=request.user, skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=5).program_name:  # Adult Skills
            skate_date = self.as_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.as_model.objects.filter(
                skater=request.user, skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=6).program_name:  # Mike Schultz
            skate_date = self.ms_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            skater_name = cart_item.skater_name.split(" ")
            skater_id = ChildSkater.objects.filter(
                first_name=skater_name[0],
                last_name=skater_name[1],
                user=request.user,
            )
            self.ms_model.objects.filter(
                skater=skater_id[0], skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=7).program_name:  # Yeti Skate
            skate_date = self.yeti_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.yeti_skate_model.objects.filter(
                skater=request.user, skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=3).program_name:  # Figure Skating
            skater_name = cart_item.skater_name.split(" ")
            if len(skater_name) == 3:
                skater_name = [" ".join([skater_name[0], skater_name[1]]), skater_name[2]]
            skater_id = self.fs_skater_model.objects.filter(
                guardian=request.user,
                first_name=skater_name[0],
                last_name=skater_name[1],
            )
            skate_date_id = self.fs_date_model.objects.filter(
                skate_date=cart_item.event_date,
                start_time=cart_item.event_start_time,
            )
            self.fs_model.objects.filter(
                skater=skater_id[0],
                session=skate_date_id[0].id,
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=8).program_name:  # Womens Hockey
            skate_date = self.wh_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            skater_name = cart_item.skater_name.split(" ")
            skater_id = ChildSkater.objects.filter(
                first_name=skater_name[0],
                last_name=skater_name[1],
                user=request.user,
            )
            self.wh_skate_model.objects.filter(
                skater=skater_id[0], skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=9).program_name:  # Bald Eagles
            skate_date = self.be_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.be_skate_model.objects.filter(
                skater=request.user, session_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=10).program_name:  # Lady Hawks
            skate_date = self.lh_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            skater_name = cart_item.skater_name.split(" ")
            skater_id = ChildSkater.objects.filter(
                first_name=skater_name[0],
                last_name=skater_name[1],
                user=request.user,
            )
            self.lh_skate_model.objects.filter(
                skater=skater_id[0], skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=11).program_name:  # CHS Alumni
            skate_date = self.chs_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.chs_skate_model.objects.filter(
                skater=request.user, date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=12).program_name:  # Open Roller Hockey
            skate_date = self.open_roller_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            skater_name = cart_item.skater_name.split(" ")
            skater_id = ChildSkater.objects.filter(
                first_name=skater_name[0],
                last_name=skater_name[1],
                user=request.user,
            )
            self.open_roller_model.objects.filter(
                skater=skater_id[0], skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=13).program_name:  # OWHL Hockey
            skate_date = self.owhl_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.owhl_model.objects.filter(
                skater=request.user, skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=14).program_name:  # Kranich
            skate_date = self.kranich_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.kranich_model.objects.filter(
                skater=request.user, skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=15).program_name:  # Nacho Skate
            skate_date = self.nacho_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.nacho_skate_model.objects.filter(
                skater=request.user, skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == Program.objects.all().get(id=16).program_name:  # Ament Skate
            skate_date = self.ament_skate_date_model.objects.filter(
                skate_date=cart_item.event_date
            )
            self.ament_skate_model.objects.filter(
                skater=request.user, skate_date=skate_date[0]
            ).delete()

        elif cart_item.item == "User Credits":
            # Credits are never "registered"; just cancel the pending purchase.
            self.user_credit_model.objects.filter(user=request.user).update(pending=0)

        # Private skates are matched by name against the PrivateSkate table. The
        # lookup raises DoesNotExist for any other item, so this must stay the last
        # elif: anything that is not a known program has to be caught above it.
        elif cart_item.item == PrivateSkate.objects.all().get(
            name=cart_item.item
        ).name:  # Private Skate
            skate_date = self.private_skate_date_model.objects.filter(
                date=cart_item.event_date
            )
            skater_name = cart_item.skater_name.split(" ")
            skater_id = ChildSkater.objects.filter(
                first_name=skater_name[0],
                last_name=skater_name[1],
                user=request.user,
            )
            self.private_skate_model.objects.filter(
                skater=skater_id[0], skate_date=skate_date[0]
            ).delete()

        return super().form_valid(form)
