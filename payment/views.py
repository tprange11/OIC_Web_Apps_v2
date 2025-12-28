from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import IntegrityError
from django.core.mail import send_mail
from datetime import date
import uuid
import os

# Square SDK — EXACT for squareup 43.2.0.20251016
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


# --------------------------------------------------------
# CREATE SQUARE CLIENT
# --------------------------------------------------------
def get_square_client():
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


# --------------------------------------------------------
# PAYMENT PROCESSING
# --------------------------------------------------------
@login_required
def process_payment(request):
    template_name = "sq-payment-result.html"

    if request.method == "GET":
        return redirect("cart:shopping-cart")

    nonce = request.POST.get("payment-token")
    if not nonce:
        return render(request, template_name, {
            "error": True,
            "error_message": "Payment token missing.",
        })

    # ----------------------------
    # CART TOTAL + NOTE
    # ----------------------------
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

    total_cents = int(total * 100)

    client = get_square_client()

    # ----------------------------
    # LOCATION LOOKUP
    # ----------------------------
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

    # ----------------------------
    # CREATE PAYMENT
    # ----------------------------
    payment_note = "".join(
        f"({k} ${v}) "
        for k, v in note.items()
        if v != 0
    )

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

    payment = pay_resp.payment
    amount = payment.amount_money.amount / 100

    models.Payment.objects.create(
        payer=request.user,
        square_id=payment.id,
        square_receipt=getattr(payment, "receipt_number", None),
        amount=amount,
        note=payment.note,
    )

    # ----------------------------
    # UPDATE SESSIONS
    # ----------------------------
    today = date.today()
    try:
        StickAndPuckSession.objects.filter(guardian=request.user, session_date__gte=today, paid=False).update(paid=True)
        FigureSkatingSession.objects.filter(guardian=request.user, session__skate_date__gte=today, paid=False).update(paid=True)
        AdultSkillsSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
        YetiSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
        WomensHockeySkateSession.objects.filter(user=request.user, paid=False).update(paid=True)
        BaldEaglesSession.objects.filter(skater=request.user, paid=False).update(paid=True)
        LadyHawksSkateSession.objects.filter(user=request.user, paid=False).update(paid=True)
        OpenRollerSkateSession.objects.filter(user=request.user).update(paid=True)
        PrivateSkateSession.objects.filter(user=request.user, paid=False).update(paid=True)
        OWHLSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
        KranichSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
        NachoSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
        AmentSkateSession.objects.filter(skater=request.user, paid=False).update(paid=True)
    except IntegrityError:
        pass

    # ----------------------------
    # USER CREDITS
    # ----------------------------
    try:
        user_credit = UserCredit.objects.get(user=request.user)
        if user_credit.pending > 0:
            user_credit.balance += user_credit.pending
            user_credit.pending = 0
            user_credit.paid = True
            user_credit.save()
    except ObjectDoesNotExist:
        user_credit = None

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

    Cart.objects.filter(customer=request.user).delete()

    return render(request, template_name, {
        "message": True,
        "amount": amount,
        "note": payment.note,
    })


# --------------------------------------------------------
# PAYMENT FORM PAGE
# --------------------------------------------------------
@login_required
def payment_page(request):
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


# --------------------------------------------------------
# PAYMENT LIST VIEW
# --------------------------------------------------------
class PaymentListView(ListView):
    model = models.Payment
    template_name = "payments_made.html"
    context_object_name = "payments"

    def get_queryset(self):
        return self.model.objects.filter(
            payer=self.request.user
        ).order_by("-id")
