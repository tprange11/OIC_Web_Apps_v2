###############################################################
#  This file to be run every day @ 1AM in a cron job or task  #
###############################################################

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from cart.models import Cart
from open_hockey.models import OpenHockeyMember, OpenHockeySessions
from stickandpuck.models import StickAndPuckSessions
from thane_storck.models import SkateSession

from datetime import date

def clear_cart_and_unpaid_items():
    '''Clears bailed shopping carts and unpaid memberships, stick and puck sessions and open hockey sessions.'''

    Cart.objects.all().delete()
    OpenHockeyMember.objects.filter(end_date__gt=date.today(), active=False).delete()
    OpenHockeySessions.objects.filter(paid=False, goalie=False, date__gte=date.today()).delete()
    StickAndPuckSessions.objects.filter(paid=False, session_date__gte=date.today()).delete()
    SkateSession.objects.filter(paid=False, session_date___gte=date.today()).delete()
    return

if __name__ == '__main__':
    clear_cart_and_unpaid_items()
