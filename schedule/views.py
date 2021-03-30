from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from . import models
from datetime import datetime, date, timedelta
from .scrape_schedule import scrape_oic_schedule, add_locker_rooms_to_schedule, \
        add_schedule_to_model, team_events, oic_schedule

from rest_framework.generics import ListAPIView
from .serializers import RinkScheduleSerializer

# Create your views here.

class ChooseRink(LoginRequiredMixin, TemplateView):
    template_name = 'choose_rink.html'


class RinkScheduleListView(LoginRequiredMixin, ListView):
    template_name = 'rinkschedule_list.html'
    model = models.RinkSchedule

    def get_queryset(self, **kwargs):
        # queryset = super().get_queryset().filter()
        todays_date = date.isoformat(datetime.today())
        # print(todays_date)
        queryset = super().get_queryset().filter(schedule_date=todays_date).filter(end_time__gte=datetime.now()).order_by('end_time')
        if self.kwargs['rink'] == 'north':
            return queryset.filter(rink__contains='North')
        elif self.kwargs['rink'] == 'south':
            return queryset.filter(rink__contains='South')
        elif self.kwargs['rink'] == 'separate':
            queryset = {'north': super().get_queryset().filter(rink__contains='North', schedule_date=todays_date, end_time__gte=datetime.now()).order_by('end_time'),
                        'south': super().get_queryset().filter(rink__contains='South', schedule_date=todays_date, end_time__gte=datetime.now()).order_by('end_time')}
            return queryset
        else:
            return queryset.exclude(rink__contains='Meeting/Party Room')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rink'] = self.kwargs['rink'] # Send rink back to page for display purposes
        north_start_times = []
        south_start_times = []
        north_end_times = []
        south_end_times = []
        todays_date = date.isoformat(datetime.today())

        # Return event start times as context
        start_times = self.model.objects.values('start_time').filter(schedule_date=todays_date, start_time__gte=datetime.now()).order_by('start_time')
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
        end_times = self.model.objects.values('end_time').filter(schedule_date=todays_date, end_time__gte=datetime.now()).order_by('end_time')
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
    data_removed = False # used to check if the database table has been cleared once


    def swap_team_names():
        ''' Replace schedule event with team names if they match times'''
        if len(team_events) != 0:
            for item in team_events:
                for oic in oic_schedule:
                    if item[0] == oic[1] and item[3] == oic[3]:
                        if item[2] == "":
                            oic[4] = f"{item[1]}"
                        else:
                            oic[4] = f"{item[1]} vs {item[2]}"

    # If it's not Saturday or Sunday, scrape oic schedule
    if date.weekday(date.today()) not in [5, 6]:
        scrape_oic_schedule(scrape_date)
        # swap_team_names()
        add_locker_rooms_to_schedule()
        add_schedule_to_model(oic_schedule, data_removed)
        data_removed = True
        oic_schedule.clear()
        # team_events.clear()

        # If it is Friday, scrape Saturday and Sunday too
        if date.weekday(date.today()) == 4:
            saturday = date.isoformat(date.today() + timedelta(days=1))
            scrape_oic_schedule(saturday)
            # swap_team_names()
            add_locker_rooms_to_schedule()
            add_schedule_to_model(oic_schedule, data_removed)
            oic_schedule.clear()
            # team_events.clear()

            sunday = date.isoformat(date.today() + timedelta(days=2))
            # oic_schedule.clear()
            scrape_oic_schedule(sunday)
            # try:
            #     scrape_ochl_teams()
            # except Exception as e:
            #     print(f"{e}, scrape_ochl_teams()")
            # swap_team_names()
            add_locker_rooms_to_schedule()
            add_schedule_to_model(oic_schedule, data_removed)
            oic_schedule.clear()
            team_events.clear()

    messages.add_message(request, messages.SUCCESS, 'Rink Resurface Schedule has been updated.')
    return redirect('schedule:choose-rink')


class RinkScheduleListAPIView(ListAPIView):
    '''Return rink schedule.'''

    serializer_class = RinkScheduleSerializer
    todays_date = date.isoformat(datetime.today())
    queryset = models.RinkSchedule.objects.filter(schedule_date=todays_date).order_by('start_time')
