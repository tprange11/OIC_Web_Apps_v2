from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
import uuid, os
from datetime import date
from square_legacy.client import Client as SquareClient

from . import models
from cart.models import Cart
from programs.models import Program
# from open_hockey.models import OpenHockeySessions, OpenHockeyMember
from stickandpuck.models import StickAndPuckSession
# from thane_storck.models import SkateSession
from figure_skating.models import FigureSkatingSession
from adult_skills.models import AdultSkillsSkateSession
# from mike_schultz.models import MikeSchultzSkateSession
from yeti_skate.models import YetiSkateSession
from womens_hockey.models import WomensHockeySkateSession
from bald_eagles.models import BaldEaglesSession
from lady_hawks.models import LadyHawksSkateSession
# from chs_alumni.models import CHSAlumniSession
from private_skates.models import PrivateSkateSession, PrivateSkate
from open_roller.models import OpenRollerSkateSession
from owhl.models import OWHLSkateSession
from kranich.models import KranichSkateSession
from nacho_skate.models import NachoSkateSession
from ament.models import AmentSkateSession
from accounts.models import UserCredit

# Create your views here.

class PaymentView(LoginRequiredMixin, TemplateView):
    '''Displays page where user can pay for services.'''

    template_name = 'sq-payment-form.html'
    cart_model = Cart

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items_cost = self.cart_model.objects.filter(customer=self.request.user).values_list('amount', flat=True)
        total = 0
        for item_cost in items_cost:
            total += item_cost
        context['total'] = total
        context['app_id'] = os.getenv("SQUARE_APP_ID") # uncomment in production and development
        context['loc_id'] = os.getenv("SQUARE_LOCATION_ID") # uncomment in production and development
        access_token = os.getenv('SQUARE_API_ACCESS_TOKEN') # uncomment in production and development

        client = SquareClient(
            access_token=settings.SQUARE_API_ACCESS_TOKEN,
            environment=os.getenv('SQUARE_API_ENVIRONMENT'), # Uncomment in production and development
        )
        location = client.locations.retrieve_location(location_id=context['loc_id']).body['location']
        context['currency'] = location['currency']
        context['country'] = location['country']
        return context


class PaymentListView(LoginRequiredMixin, ListView):
    '''Displays page with users past payments.'''

    model = models.Payment
    template_name = 'payments-list.html'
    context_object_name = 'payments'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset().filter(payer=self.request.user)
        return queryset


@login_required
def process_payment(request, **kwargs):
    '''Processes the payment and returns an error or success page.'''

    context = None #Initialize context
    template_name = 'sq-payment-result.html'
    cart_model = Cart
    program_model = Program
    # open_hockey_sessions_model = OpenHockeySessions
    # open_hockey_member_model = OpenHockeyMember
    stick_and_puck_sessions_model = StickAndPuckSession
    # thane_storck_sessions_model = SkateSession
    figure_skating_sessions_model = FigureSkatingSession
    adult_skills_sessions_model = AdultSkillsSkateSession
    # mike_schultz_sessions_model = MikeSchultzSkateSession
    yeti_sessions_model = YetiSkateSession
    womens_hockey_sessions_model = WomensHockeySkateSession
    bald_eagles_sessions_model = BaldEaglesSession
    lady_hawks_sessions_model = LadyHawksSkateSession
    # chs_alumni_sessions_model = CHSAlumniSession
    private_skate_sessions_model = PrivateSkateSession
    open_roller_sessions_model = OpenRollerSkateSession
    owhl_sessions_model = OWHLSkateSession
    kranich_sessions_model = KranichSkateSession
    nacho_skate_sessions_model = NachoSkateSession
    ament_sessions_model = AmentSkateSession
    user_credit_model = UserCredit
    today = date.today()

    if request.method == 'GET':
        return redirect('cart:shopping-cart')
    else:

        token = request.POST['payment-token']
        # print(f"Token: {token}")
        access_token = os.getenv('SQUARE_API_ACCESS_TOKEN') # uncomment in production and development
        cart_items = cart_model.objects.filter(customer=request.user).values_list('item', 'amount')
        total = 0
        programs = program_model.objects.all().values_list('program_name', flat=True)
        note = {program: 0 for program in programs}
        private_skates = PrivateSkate.objects.all().values_list('name', flat=True)
        for skate in private_skates:
            note[skate] = 0
        note['User Credits'] = 0

        for item, amount in cart_items:
            total += amount
            # if item == 'OH Membership':
            #     note['Open Hockey'] += amount
            # else:
            note[item] += amount
        total *= 100 #convert to pennies for square

        client = Client(
            access_token=access_token,
            # environment='sandbox', # Uncomment on local machine
            environment=os.getenv('SQUARE_API_ENVIRONMENT'), # Uncomment in production and development
        )

        location_id = os.getenv("SQUARE_LOCATION_ID") # uncomment in production and development
        location = client.locations.retrieve_location(location_id=location_id).body['location']
        currency = location['currency']

        # Assemble the body for the create_payment() api function
        idempotency_key = str(uuid.uuid1())
        amount = {'amount': total, 'currency': currency}

        # Create the note depending on what the user is paying for....
        payment_note = ''
        for k, v in note.items():
            if v != 0:
                payment_note += f'({k} ${v}) '

        body = {
            'idempotency_key': idempotency_key, 
            'source_id': token, 'amount_money': amount, 
            'autocomplete': True, 
            'note': payment_note
            }

        # Send info to square api and react to the response
        api_response = client.payments.create_payment(body)

        if api_response.is_success():
            res = api_response.body['payment']
            # Add payment record to Payment Model
            model = models.Payment
            payer = request.user
            square_id = res['id']
            square_receipt = res['receipt_number']
            amount = float(res['amount_money']['amount']) / 100
            note = res['note']
            payment_record = model(payer=payer, square_id=square_id, square_receipt=square_receipt, amount=amount, note=note)
            payment_record.save()


            # Update model(s) to mark items as paid.
            try:
                # open_hockey_sessions_model.objects.filter(skater=request.user, date__gte=today).update(paid=True)
                stick_and_puck_sessions_model.objects.filter(guardian=request.user, session_date__gte=today, paid=False).update(paid=True)
                # open_hockey_member_model.objects.filter(member=request.user).update(active=True)
                # thane_storck_sessions_model.objects.filter(skater=request.user).update(paid=True)
                figure_skating_sessions_model.objects.filter(guardian=request.user, session__skate_date__gte=today, paid=False).update(paid=True)
                adult_skills_sessions_model.objects.filter(skater=request.user, paid=False).update(paid=True)
                # mike_schultz_sessions_model.objects.filter(user=request.user).update(paid=True)
                yeti_sessions_model.objects.filter(skater=request.user, paid=False).update(paid=True)
                womens_hockey_sessions_model.objects.filter(user=request.user, paid=False).update(paid=True)
                bald_eagles_sessions_model.objects.filter(skater=request.user, paid=False).update(paid=True)
                lady_hawks_sessions_model.objects.filter(user=request.user, paid=False).update(paid=True)
                # chs_alumni_sessions_model.objects.filter(skater=request.user).update(paid=True)
                open_roller_sessions_model.objects.filter(user=request.user).update(paid=True)
                private_skate_sessions_model.objects.filter(user=request.user, paid=False).update(paid=True)
                owhl_sessions_model.objects.filter(skater=request.user, paid=False).update(paid=True)
                kranich_sessions_model.objects.filter(skater=request.user, paid=False).update(paid=True)
                nacho_skate_sessions_model.objects.filter(skater=request.user, paid=False).update(paid=True)
                ament_sessions_model.objects.filter(skater=request.user, paid=False).update(paid=True)
            except IntegrityError:
                pass

            try:
                user_credit = user_credit_model.objects.get(user=request.user) # Get user credit model instance
                if user_credit.pending > 0: # If there are pending credits
                    user_credit.balance += user_credit.pending # Add pending credits to credit balance
                    user_credit.pending = 0 # Set pending credits to 0
                    user_credit.paid = True # Mark credits as paid
                    user_credit.save() # Save user credit model
            except ObjectDoesNotExist:
                pass

            if "User Credits" in note:
                new_user_credit = user_credit.balance
                send_mail(
                    "User Credits Purchased",
                    f"{payer.get_full_name()} has purchased credits.  {note}\n\n Credit Balance: {new_user_credit}",
                    "no-reply@mg.oicwebapps.com",
                    ['brianc@wi.rr.com'],
                    fail_silently=True
                )

            # Clear items from the Cart Model if the payment was successful
            Cart.objects.filter(customer=request.user).delete()

            # Construct context for result page.
            context = {'message': True, 'amount': amount, 'note': note}
        elif api_response.is_error():
            # Save the error in PaymentError model for debugging.
            model = models.PaymentError
            payer = request.user
            payment_error = model(payer=payer, error=api_response.errors)
            payment_error.save()
            
            # Create response context and send to template for display.
            error_message = api_response.errors[0]['detail']
            error_messages = {
                "Authorization error: 'ADDRESS_VERIFICATION_FAILURE'": "The zip code you entered was incorrect.",
                "Authorization error: 'CVV_FAILURE'": "The three digit security code you entered was incorrect.",
                "Authorization error: 'GENERIC_DECLINE'": "The credit card number you entered has been declined.",
            }
            error = error_messages.get(error_message, error_message) # Retrieve error msg, else return raw error_message
            context = {'error': True, 'error_message': error}

        return render(request, template_name, context)
