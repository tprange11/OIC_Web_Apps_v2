"""Shared removal behaviour for program skate sessions and skater records.

Django 4.0 changed DeleteView to route POST through form_valid(); the old
delete() hook is no longer called for POST and is removed in Django 5.0.
Every program app used to put its refund / cart-cleanup logic in delete(),
so none of it ran. These mixins put that logic in form_valid() once, with:

* ownership: only the user who registered the session (or staff, or a
  configured organizer) can remove it;
* refund decided from the session row (session.paid / session.goalie), never
  from URL parameters;
* cart cleanup scoped to the owner's own Cart rows;
* the whole thing inside one transaction with the credit row locked.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponseRedirect

from accounts.models import UserCredit
from cart.models import Cart
from programs.models import Program


class SessionRemovalMixin(LoginRequiredMixin):
    """Mixin for a DeleteView over a program *Session model.

    Subclasses set `model`, `success_url` and whichever of the attributes
    below differ from the defaults.
    """

    # FK on the session pointing at the User who registered (and pays for) it.
    owner_field = 'skater'
    # FK on the session pointing at the *Date row; None when the session row
    # carries the calendar date itself (stickandpuck, open_hockey).
    date_field = 'skate_date'
    # Attribute holding the calendar date (on the date row, or on the session
    # when date_field is None) and the start time (used only to narrow cart
    # matching; None to skip).
    date_attr = 'skate_date'
    start_time_attr = 'start_time'
    # How to find the Program row (prices, name). Either a lookup dict or None
    # when the app has no Program (then cart_item_name and prices must be
    # supplied by overriding get_program / get_refund_amount).
    program_filter = None
    # Cart.item value; defaults to program.program_name.
    cart_item_name = None
    # Refund goalie_price instead of skater_price for goalie sessions.
    goalie_aware = True
    # Users who skate free in this program (legacy hard-coded ids): no refund.
    free_user_ids = ()
    # Non-staff users who may remove other people's sessions (legacy organizer ids).
    manager_user_ids = ()
    # Email the owner and these admin users when a refund is issued.
    notify_on_refund = False
    admin_notify_ids = (1, 2)
    notify_subject = 'Credit Issued for Skate Session'
    notify_from = 'no-reply@oicwebapp.com'

    removed_message = 'You have been removed from that skate session!'
    http_method_names = ['post']

    # -- lookups -------------------------------------------------------------

    def get_program(self):
        if self.program_filter is None:
            return None
        return Program.objects.get(**self.program_filter)

    def get_owner(self, session):
        return getattr(session, self.owner_field)

    def get_date_row(self, session):
        return getattr(session, self.date_field) if self.date_field else session

    def get_session_date(self, session):
        return getattr(self.get_date_row(session), self.date_attr)

    def get_session_start_time(self, session):
        if not self.start_time_attr:
            return None
        return getattr(self.get_date_row(session), self.start_time_attr, None)

    def get_cart_item_name(self):
        if self.cart_item_name:
            return self.cart_item_name
        program = self.get_program()
        return program.program_name if program else None

    def get_cart_skater_names(self, session):
        """Candidate Cart.skater_name values for this session (apps differ in
        what they stored: str(skater), the owner's full name, 'First Last')."""
        owner = self.get_owner(session)
        names = {owner.get_full_name(), str(owner)}
        skater = getattr(session, 'skater', None)
        if skater is not None and skater is not owner:
            names.add(str(skater))
            first = getattr(skater, 'first_name', None)
            last = getattr(skater, 'last_name', None)
            if first or last:
                names.add(f'{first} {last}'.strip())
        return {n for n in names if n}

    # -- policy --------------------------------------------------------------

    def can_remove(self, user, session):
        return (user.is_staff or user.id in self.manager_user_ids
                or self.get_owner(session) == user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff or user.id in self.manager_user_ids:
            return qs
        return qs.filter(**{self.owner_field: user})

    def get_refund_amount(self, session):
        """Credits to return for a paid session. 0 for staff / free skaters."""
        owner = self.get_owner(session)
        if owner.is_staff or owner.id in self.free_user_ids:
            return 0
        program = self.get_program()
        if program is None:
            return 0
        goalie = self.goalie_aware and bool(getattr(session, 'goalie', False))
        price = program.goalie_price if goalie else program.skater_price
        return int(price or 0)

    # -- actions -------------------------------------------------------------

    def refund(self, owner, amount):
        """Add `amount` to the owner's credit balance (row locked). Returns (old, new)."""
        credit, _ = (UserCredit.objects.select_for_update()
                     .get_or_create(user=owner, defaults={'slug': owner.username}))
        old = credit.balance or 0
        credit.balance = old + amount
        credit.paid = True
        credit.save()
        return old, credit.balance

    def clear_cart(self, session):
        """Delete the owner's Cart rows for this session. Returns rows deleted."""
        item = self.get_cart_item_name()
        if item is None:
            return 0
        owner = self.get_owner(session)
        qs = Cart.objects.filter(customer=owner, item=item,
                                 event_date=self.get_session_date(session))
        narrowed = qs.filter(skater_name__in=self.get_cart_skater_names(session))
        if narrowed.exists():
            qs = narrowed
        start = self.get_session_start_time(session)
        if start is not None:
            by_time = qs.filter(event_start_time=str(start))
            if by_time.exists():
                qs = by_time
        return qs.delete()[0]

    def get_refund_message(self, session, old, new):
        owner = self.get_owner(session)
        return (f'{owner.get_full_name()} has been removed from the session. '
                f'The credit balance has been increased from ${old} to ${new}.')

    def notify(self, session, message):
        owner = self.get_owner(session)
        User = owner.__class__
        recipients = list(User.objects.filter(id__in=list(self.admin_notify_ids) + [owner.id])
                          .exclude(email='').values_list('email', flat=True))
        if not recipients:
            return
        try:
            send_mail(self.notify_subject, message, self.notify_from, recipients)
        except Exception as exc:  # email failure must not undo the removal
            messages.error(self.request, f'Failed to send email: {exc}')

    def form_valid(self, form):
        session = self.object
        refunded = 0
        with transaction.atomic():
            if session.paid:
                refunded = self.get_refund_amount(session)
                if refunded:
                    old, new = self.refund(self.get_owner(session), refunded)
                    msg = self.get_refund_message(session, old, new)
                else:
                    msg = self.removed_message
            else:
                self.clear_cart(session)
                msg = self.removed_message
            session.delete()
        messages.success(self.request, msg)
        if refunded and self.notify_on_refund:
            self.notify(session, msg)
        return HttpResponseRedirect(self.get_success_url())


class OwnedDeleteMixin(LoginRequiredMixin):
    """DeleteView mixin for a record owned by a user (child skater etc.):
    only the owner (or staff) may delete it; success message in form_valid."""

    owner_field = 'user'
    success_message = 'Removed.'
    http_method_names = ['post']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(**{self.owner_field: self.request.user})

    def form_valid(self, form):
        self.object.delete()
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())
