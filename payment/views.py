from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import IntegrityError
from django.core.mail import send_mail
from datetime import date
import uuid
import os

# Square REST SDK (your version)
from square.client import Square
from square.client import SquareEnvironment
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

    client = Square(
        token=token,
        environment=environment,
    )

    return client


# --------------------------------------------------------
# PAYMENT PROCESSING
# --------------------------------------------------------
@login_required
def process_payment(request, **kwargs):

    template_name = "sq-payment-result.html"

    if request.method == "GET":
        return redirect("cart:shopping-cart")

    token = request.POST.get("payment-token")
    if not token:
        return render(request, template_name, {
            "error": True,
            "error_message": "Payment token missing.",
        })

    # CART ITEMS
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

    total *= 100  # USD → cents

    client = get_square_client()

    # --------------------------------------------------------
    # LOCATION LOOKUP (CORRECT METHOD)
    # --------------------------------------------------------
    location_id = os.getenv("SQUARE_LOCATION_ID")
    if not location_id:
        raise ImproperlyConfigured("SQUARE_LOCATION_ID is not configured")

    try:
        locations_resp = client.locations.list()
    except ApiError as e:
        models.PaymentError.objects.create(payer=request.user, error=str(e))
        return render(request, template_name, {
            "error": True,
            "error_message": "Square configuration error.",
        })

    if locations_resp.errors:
        models.PaymentError.objects.create(
            payer=request.user,
            error=str(locations_resp.errors)
        )
        return render(request, template_name, {
            "error": True,
            "error_message": "Square location fetch failed.",
        })

    location = next((loc for loc in locations_resp.locations if loc.id == location_id), None)
    if not location:
        return render(request, template_name, {
            "error": True,
            "error_message": "Square location not found.",
        })

    currency = location.currency

    idempotency_key = str(uuid.uuid4())

    amount_money = {
        "amount": total,
        "currency": currency,
    }

    payment_note = "".join(f"({k} ${v}) " for k, v in note.items() if v != 0)

    body = {
        "idempotency_key": idempotency_key,
        "source_id": token,
        "amount_money": amount_money,
        "autocomplete": True,
        "note": payment_note,
    }

    # --------------------------------------------------------
    # CREATE PAYMENT (CORRECT METHOD: payments.create)
    # --------------------------------------------------------
    try:
        payment_resp = client.payments.create(**body)
    except ApiError as e:
        models.PaymentError.objects.create(payer=request.user, error=str(e))
        return render(request, template_name, {
            "error": True,
            "error_message": "Payment processing failed.",
        })

    if payment_resp.errors:
        err = payment_resp.errors[0]
        detail = getattr(err, "detail", str(err))
        models.PaymentError.objects.create(payer=request.user, error=detail)
        return render(request, template_name, {
            "error": True,
            "error_message": detail,
        })

    # SUCCESS
    res = payment_resp.payment
    amount = float(res.amount_money.amount) / 100

    models.Payment.objects.create(
        payer=request.user,
        square_id=res.id,
        square_receipt=getattr(res, "receipt_number", None),
        amount=amount,
        note=res.note,
    )

    # UPDATE SESSIONS
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

    # USER CREDITS
    try:
        user_credit = UserCredit.objects.get(user=request.user)
        if user_credit.pending > 0:
            user_credit.balance += user_credit.pending
            user_credit.pending = 0
            user_credit.paid = True
            user_credit.save()
    except ObjectDoesNotExist:
        user_credit = None

    if "User Credits" in res.note and user_credit:
        send_mail(
            "User Credits Purchased",
            f"{request.user.get_full_name()} purchased credits. {res.note}\nBalance: {user_credit.balance}",
            "no-reply@mg.oicwebapp.com",
            ["brianc@wi.rr.com"],
            fail_silently=True,
        )

    # CLEAR CART
    Cart.objects.filter(customer=request.user).delete()

    return render(request, template_name, {
        "message": True,
        "amount": amount,
        "note": res.note,
    })

@login_required
def payment_page(request):
    """Render the Square payment form page."""
    client = get_square_client()

    # Fetch location details
    loc_resp = client.locations.list_locations()
    location = loc_resp.locations[0]

    total = sum(
        Cart.objects.filter(customer=request.user)
        .values_list("amount", flat=True)
    )

    context = {
        "app_id": os.getenv("SQUARE_WEB_PAYMENT_APP_ID"),
        "loc_id": os.getenv("SQUARE_LOCATION_ID"),
        "currency": location.currency,
        "country": location.country,
        "total": total,
    }
    return render(request, "sq-payment-form.html", context)


# --------------------------------------------------------
# PAYMENT LIST VIEW
# --------------------------------------------------------
class PaymentListView(ListView):
    model = models.Payment
    template_name = 'payments_made.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return self.model.objects.filter(payer=self.request.user).order_by('-id')
