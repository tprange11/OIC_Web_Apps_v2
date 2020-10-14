from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from . import models, scrape_schedule
from datetime import datetime, date
import os
from .scrape_schedule import scrape_oic_schedule, scrape_ochl_teams, scrape_owhl_teams, scrape_oyha_teams, add_schedule_to_model, team_events, oic_schedule

# Create your views here.

class ChooseRink(LoginRequiredMixin, TemplateView):
    template_name = 'choose_rink.html'


class RinkScheduleListView(LoginRequiredMixin, ListView):
    template_name = 'rinkschedule_list.html'
    model = models.RinkSchedule

    def get_queryset(self, **kwargs):
        # queryset = super().get_queryset().filter()
        queryset = super().get_queryset().filter(end_time__gte=datetime.now()).order_by('end_time')
        if self.kwargs['rink'] == 'north':
            return queryset.filter(rink__contains='North')
        elif self.kwargs['rink'] == 'south':
            return queryset.filter(rink__contains='South')
        elif self.kwargs['rink'] == 'separate':
            queryset = {'north': super().get_queryset().filter(rink__contains='North', end_time__gte=datetime.now()).order_by('end_time'),
                                'south': super().get_queryset().filter(rink__contains='South', end_time__gte=datetime.now()).order_by('end_time')}
            return queryset
        else:
            return queryset.exclude(rink__contains='Meeting/Party Room')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rink'] = self.kwargs['rink'] # Send rink back to page for display purposes

        # Return event start times as context
        start_times = self.model.objects.values('start_time').filter(start_time__gte=datetime.now()).order_by('start_time')
        if self.kwargs['rink'] == 'north':
            start_times = start_times.filter(rink__contains='North')
        elif self.kwargs['rink'] == 'south':
            start_times = start_times.filter(rink__contains='South')
        elif self.kwargs['rink'] == 'separate':
            north_start_times = start_times.filter(rink__contains='North')
            south_start_times = start_times.filter(rink__contains='South')
        else:
            start_times = start_times.exclude(rink__contains='Meeting/Party Room')

        # Return event end times as context
        end_times = self.model.objects.values('end_time').filter(end_time__gte=datetime.now()).order_by('end_time')
        if self.kwargs['rink'] == 'north':
            end_times = end_times.filter(rink__contains='North')
        elif self.kwargs['rink'] == 'south':
            end_times = end_times.filter(rink__contains='South')
        elif self.kwargs['rink'] == 'separate':
            north_end_times = end_times.filter(rink__contains='North')
            south_end_times = end_times.filter(rink__contains='South')
        else:
            end_times = end_times.exclude(rink__contains='Meeting/Party Room')

        # Convert date time format for use in Javascript resurface countdown timer
        next_start_times = []
        north_next_start_times = []
        south_next_start_times = []

        if self.kwargs['rink'] == 'separate':
            for item in north_start_times:
                north_next_start_times.append(date.isoformat(datetime.now())+" "+item['start_time'].strftime('%H:%M:%S'))
            for item in south_start_times:
                south_next_start_times.append(date.isoformat(datetime.now())+" "+item['start_time'].strftime('%H:%M:%S'))
            context['north_start_times'] = north_next_start_times
            context['south_start_times'] = south_next_start_times
        else:
            for item in start_times:
                next_start_times.append(date.isoformat(datetime.now())+" "+item['start_time'].strftime('%H:%M:%S'))
            context['start_times'] = next_start_times
        
        # Convert date time format for use in Javacript resurface countdown timer
        resurface_times = []
        north_resurface_times = []
        south_resurface_times = []

        if self.kwargs['rink'] == 'separate':
            for item in north_end_times:
                north_resurface_times.append(date.isoformat(datetime.now())+" "+item['end_time'].strftime('%H:%M:%S'))
            for item in south_end_times:
                south_resurface_times.append(date.isoformat(datetime.now())+" "+item['end_time'].strftime('%H:%M:%S'))
            context['north_resurface_times'] = north_resurface_times
            context['south_resurface_times'] = south_resurface_times
        else:
            for item in end_times:
                resurface_times.append(date.isoformat(datetime.now())+" "+item['end_time'].strftime('%H:%M:%S'))
            context['resurface_times'] = resurface_times
        
        return context


def scrape_schedule(request):
    '''This view is called when the Update Schedule button is clicked. I will update the zamboni resurface
    schedule if the online schedule has changed.'''
    
    the_date = date.today()
    # the_date = "2019-10-26"

    scrape_date = date.isoformat(the_date)
    scrape_oic_schedule(scrape_date)
    ### UNCOMMENT DURING HOCKEY SEASON ###
    # Scrape OYHA teams daily
    try:
        scrape_oyha_teams(scrape_date)
    except Exception as e:
        print(f"{e}, scrape_oyha_teams()")

    # If it is Friday, scrape OWHL teams
    if date.weekday(date.today()) == 4:
        try:
            scrape_owhl_teams(scrape_date)
        except Exception as e:
            print(f"{e}, scrape_owhl_teams()")

    # If it is Sunday, scrape OCHL teams
    if date.weekday(date.today()) == 6:
        try:
            scrape_ochl_teams()
        except Exception as e:
            print(f"{e}, scrape_ochl_teams()")

    if len(team_events) != 0:
        for item in team_events:
            for oic in oic_schedule:
                if item[0] == oic[1] and item[3] == oic[3]:
                    if item[2] == "":
                        oic[4] = f"{item[1]}"
                    else:
                        oic[4] = f"{item[1]} vs {item[2]}"

    # If anything ends at midnight, change to 11:59 PM
    # for item in oic_schedule:
    #     if item[2] == "12:00 AM":
    #         item[2] = "11:59 PM"

    # Insert data into Django model
    add_schedule_to_model(oic_schedule)

    messages.add_message(request, messages.SUCCESS, 'Rink Resurface Schedule has been updated.')
    return redirect('schedule:choose-rink')
