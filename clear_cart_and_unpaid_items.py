###############################################################
#  This file to be run every day @ 1AM in a cron job or task  #
###############################################################

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from cart.models import Cart
from stickandpuck.models import StickAndPuckSession
from thane_storck.models import SkateSession
from figure_skating.models import FigureSkatingSession
from adult_skills.models import AdultSkillsSkateSession
from mike_schultz.models import MikeSchultzSkateSession
from yeti_skate.models import YetiSkateSession
from womens_hockey.models import WomensHockeySkateSession
from accounts.models import UserCredit

from datetime import date

def clear_cart_and_unpaid_items():
    '''Clears bailed shopping carts and unpaid memberships, stick and puck sessions and open hockey sessions.'''

    Cart.objects.all().delete()
    StickAndPuckSession.objects.filter(paid=False, session_date__gte=date.today()).delete()
    SkateSession.objects.filter(paid=False, skate_date__skate_date__gte=date.today()).delete()
    FigureSkatingSession.objects.filter(paid=False, session__skate_date__gte=date.today()).delete()
    AdultSkillsSkateSession.objects.filter(paid=False, skate_date__skate_date__gte=date.today()).delete()
    MikeSchultzSkateSession.objects.filter(paid=False, skate_date__skate_date__gte=date.today()).delete()
    YetiSkateSession.objects.filter(paid=False, skate_date__skate_date__gte=date.today()).delete()
    WomensHockeySkateSession.objects.filter(paid=False, skate_date__skate_date__gte=date.today()).delete()
    UserCredit.objects.filter(pending__gt=0).update(pending=0)
    return

if __name__ == '__main__':
    clear_cart_and_unpaid_items()
