"""Square checkout: charges the user's shopping cart, records the payment and marks
the purchased sessions/credits as paid. See process_payment() for the full flow."""
from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.core.mail import send_mail
from datetime import date
import logging
import uuid
import os

# Square SDK imports for squareup 43.2.0.20251016 (pinned in requirements.txt); the
# module layout changed between major versions, so keep the pin and these imports in sync.
from square.client import Square, SquareEnvironment
from square.core.api_error import ApiError

from . import models
from cart.models import Cart
from programs.models import Program
from stickandpuck.models import StickAndPuckSession
from figure_skating.models import FigureSkatingSession
from adult_skills.models import AdultSkillsSkateSession
from yeti_skate.models import YetiSkateSession
from womens_hockey.models import WomensHockeySkateSession
from bald_eagles.models import BaldEaglesSession
from lady_hawks.models import LadyHawksSkateSession
from private_skates.models import PrivateSkateSession, PrivateSkate
from open_roller.models import OpenRollerSkateSession
from owhl.models import OWHLSkateSession
from kranich.models import KranichSkateSession
from nacho_skate.models import NachoSkateSession
from ament.models import AmentSkateSession
from accounts.models import UserCredit

logger = logging.getLogger(__name__)


def get_square_client():
    '''Builds a Square client from the environment. Anything other than
    SQUARE_API_ENVIRONMENT=production is treated as sandbox.'''
    token = os.getenv("SQUARE_API_ACCESS_TOKEN")
    if not token:
        raise ImproperlyConfigured("SQUARE_API_ACCESS_TOKEN is not configured")

    env_raw = os.getenv("SQUARE_API_ENVIRONMENT", "sandbox").lower()
    environment = (
        SquareEnvironment.PRODUCTION
        if env_raw == "production"
        else SquareEnvironment.SANDBOX
    )

    return Square(
        token=token,
        environment=environment,
    )


@login_required
def process_payment(request):
    '''Charges the whole shopping cart in one Square payment.

    Flow:
      1. The browser tokenizes the card with the Square Web Payments SDK and POSTs
         the one-time token as "payment-token" (see static/js/sq-card-pay.js and
         cart/templates/shopping_cart.html).
      2. The amount is the sum of the user's Cart rows; a per-program breakdown is
         built into the Square payment note, which the revenue reports later parse.
      3. On success a Payment row is recorded, every unpaid session the user has
         (across all program apps) is flagged paid, pending User Credits are moved
         to the balance, and the cart is emptied.
    Any Square error is logged to PaymentError and shown on the result page.
    '''
    template_name = "sq-payment-result.html"

    if request.method == "GET":
        return redirect("cart:shopping-cart")

    nonce = request.POST.get("payment-token")
    if not nonce:
        return render(request, template_name, {
            "error": True,
            "error_message": "Payment token missing.",
        })

    # Cart total plus a per-item breakdown for the payment note. The note keys are
    # program names, private skate names and "User Credits"; a cart item whose name
    # matches none of these still counts toward the total but is left out of the note.
    cart_items = Cart.objects.filter(
        customer=request.user
    ).values_list("item", "amount")

    total = 0
    programs = Program.objects.values_list("program_name", flat=True)
    note = {program: 0 for program in programs}

    for skate_name in PrivateSkate.objects.values_list("name", flat=True):
        note[skate_name] = 0

    note["User Credits"] = 0

    for item, amount in cart_items:
        total += amount
        if item in note:
            note[item] += amount

    # Cart amounts are whole dollars; Square wants the smallest currency unit.
    total_cents = int(total * 100)

    client = get_square_client()

    # Look the configured location up so the payment uses its currency.
    location_id = os.getenv("SQUARE_LOCATION_ID")
    if not location_id:
        raise ImproperlyConfigured("SQUARE_LOCATION_ID is not configured")

    try:
        loc_resp = client.locations.list()
    except ApiError as e:
        models.PaymentError.objects.create(
            payer=request.user,
            error=str(e),
        )
        return render(request, template_name, {
            "error": True,
            "error_message": "Square configuration error.",
        })

    if loc_resp.errors:
        models.PaymentError.objects.create(
            payer=request.user,
            error=str(loc_resp.errors),
        )
        return render(request, template_name, {
            "error": True,
            "error_message": "Unable to fetch Square locations.",
        })

    locations = loc_resp.locations or []
    location = next((l for l in locations if l.id == location_id), None)

    if not location:
        return render(request, template_name, {
            "error": True,
            "error_message": "Square location not found.",
        })

    currency = location.currency or "USD"

    # Note format is "(Program $amount) (Other $amount) ". accounts/views.py
    # (revenue_report, credit reports) parses this exact layout, so do not change it.
    payment_note = "".join(
        f"({k} ${v}) "
        for k, v in note.items()
        if v != 0
    )

    # A fresh idempotency key per request; the card token itself is single-use,
    # which is what actually prevents a resubmitted form from charging twice.
    body = {
        "idempotency_key": str(uuid.uuid4()),
        "source_id": nonce,
        "amount_money": {
            "amount": total_cents,
            "currency": currency,
        },
        "autocomplete": True,
        "note": payment_note,
        "location_id": location_id,
    }

    try:
        pay_resp = client.payments.create(**body)
    except ApiError as e:
        models.PaymentError.objects.create(
            payer=request.user,
            error=str(e),
        )
        return render(request, template_name, {
            "error": True,
            "error_message": "Payment processing failed.",
        })

    if pay_resp.errors:
        detail = pay_resp.errors[0].detail if pay_resp.errors else "Payment failed"
        models.PaymentError.objects.create(
            payer=request.user,
            error=detail,
        )
        return render(request, template_name, {
            "error": True,
            "error_message": detail,
        })

    # From here on the card has been charged. All bookkeeping below runs in one
    # transaction so a failure cannot leave a charged card with partial records; the
    # error is logged with the Square payment id and re-raised.
    payment = pay_resp.payment
    amount = payment.amount_money.amount / 100

    try:
        with transaction.atomic():
            models.Payment.objects.create(
                payer=request.user,
                square_id=payment.id,
                square_receipt=getattr(payment, "receipt_number", None),
                amount=amount,
                note=payment.note,
            )

            # Mark the user's unpaid sessions as paid. This is not tied to the cart contents:
            # every unpaid session for this user is flagged, on the assumption that unpaid
            # sessions and cart rows always exist together (clear_cart_and_unpaid_items.py
            # removes both nightly). Only Stick and Puck and Figure Skating limit this to
            # today or later.
            today = date.today()
            StickAndPuckSession.objects.filter(guardian=request.user, session_date__gte=today, paid=False).update(paid=True)
            FigureSkatingSession.objects.filter(guardian=request.user, session__skate_date__gte=today, paid=False).update(paid=True)
            AdultSkillsSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
            YetiSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
            WomensHockeySkateSession.objects.filter(user=request.user, paid=False).update(paid=True)
            BaldEaglesSession.objects.filter(skater=request.user, paid=False).update(paid=True)
            LadyHawksSkateSession.objects.filter(user=request.user, paid=False).update(paid=True)
            OpenRollerSkateSession.objects.filter(user=request.user, paid=False).update(paid=True)
            PrivateSkateSession.objects.filter(user=request.user, paid=False).update(paid=True)
            OWHLSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
            KranichSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
            NachoSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
            AmentSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)

            # User credits: UpdateUserCreditView (accounts/views.py) puts the dollar amount in
            # the cart and stores the credits to be granted (including any incentive bonus) in
            # `pending`. Paying moves pending into the spendable balance; `paid` is what the
            # program apps check before letting a user spend credits.
            try:
                user_credit = UserCredit.objects.get(user=request.user)
                if user_credit.pending > 0:
                    user_credit.balance += user_credit.pending
                    user_credit.pending = 0
                    user_credit.paid = True
                    user_credit.save()
            except ObjectDoesNotExist:
                user_credit = None

            Cart.objects.filter(customer=request.user).delete()
    except IntegrityError:
        logger.exception(
            "Post-charge bookkeeping failed for Square payment %s (user %s); rolled back.",
            payment.id, request.user.id,
        )
        raise

    # Notify the office of credit purchases (recipient is hard-coded).
    if user_credit and "User Credits" in (payment.note or ""):
        send_mail(
            "User Credits Purchased",
            f"{request.user.get_full_name()} purchased credits.\n"
            f"{payment.note}\n"
            f"Balance: {user_credit.balance}",
            "no-reply@mg.oicwebapp.com",
            ["brianc@wi.rr.com"],
            fail_silently=True,
        )

    return render(request, template_name, {
        "message": True,
        "amount": amount,
        "note": payment.note,
    })


@login_required
def payment_page(request):
    '''Standalone Square card form for the cart total (sq-payment-form.html).

    The shopping cart page embeds its own copy of this form, so this view is only
    reached from the "try again" link on the payment result page. Note it uses the
    first location Square returns and SQUARE_WEB_PAYMENT_APP_ID, whereas the cart
    page uses SQUARE_LOCATION_ID and SQUARE_APP_ID.
    '''
    client = get_square_client()

    loc_resp = client.locations.list()
    if loc_resp.errors:
        raise ImproperlyConfigured("Unable to fetch Square locations")

    location = loc_resp.locations[0]

    total = sum(
        Cart.objects.filter(customer=request.user)
        .values_list("amount", flat=True)
    )

    return render(request, "sq-payment-form.html", {
        "app_id": os.getenv("SQUARE_WEB_PAYMENT_APP_ID"),
        "loc_id": os.getenv("SQUARE_LOCATION_ID"),
        "currency": location.currency or "USD",
        "country": location.country or "US",
        "total": total,
    })


class PaymentListView(LoginRequiredMixin, ListView):
    '''The logged-in user's payment history, newest first.'''
    model = models.Payment
    template_name = "payments_made.html"
    context_object_name = "payments"

    def get_queryset(self):
        return self.model.objects.filter(
            payer=self.request.user
        ).order_by("-id")
