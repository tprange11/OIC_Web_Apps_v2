from datetime import date, timedelta
import os, sys, json, requests

if os.name == 'nt':
    sys.path.append("C:\\Users\\brian\\Documents\\Python\\OIC_Web_Apps\\")
else:
    # sys.path.append("/home/BrianC68/oicdev/OIC_Web_Apps/") # Uncomment in development
    sys.path.append("/home/OIC/OIC_Web_Apps/") # Uncomment in production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OIC_Web_Apps.settings')

import django
django.setup()

from django.db import IntegrityError
from figure_skating.models import FigureSkatingDate

skate_dates = ['2024-08-03',]

sessions = [
    ["7:30 AM", "8:30 AM", 5],
    ["8:30 AM", "9:30 AM", 5],
    ["9:30 AM", "10:30 AM", 5],
    ["10:45 AM", "11:45 AM", 5],
    ["11:45 AM", "12:45 PM", 5],
    ["2:30 PM", "3:30 PM", 5],
    ["3:30 PM", "4:30 PM", 5],
    ["4:45 PM", "5:45 PM", 5],
    ["5:45 PM", "6:45 PM", 5],
    ["6:45 PM", "7:15 PM", -5],
]

def add_camp_sessions():

    model = FigureSkatingDate


    for date in skate_dates:
        for session in sessions:
            print(f"{date}: {session}")
            try:
                fs_date = model(skate_date=date, start_time=session[0], end_time=session[1], available_spots=8, up_down_charge=session[2])
                fs_date.save()
            except IntegrityError:
                continue

if __name__ == "__main__":

    add_camp_sessions()
