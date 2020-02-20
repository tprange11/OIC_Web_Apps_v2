from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from django.views.decorators.cache import never_cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from . import models
from datetime import datetime, time, date


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
        