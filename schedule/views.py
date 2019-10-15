from django.shortcuts import render
from django.views.generic import ListView, TemplateView
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
        else:
            return queryset.exclude(rink__contains='Meeting/Party Room')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rink'] = self.kwargs['rink'] # Send rink back to page for display purposes
        end_times = self.model.objects.values('end_time').filter(end_time__gte=datetime.now()).order_by('end_time')
        if self.kwargs['rink'] == 'north':
            end_times = end_times.filter(rink__contains='North')
        elif self.kwargs['rink'] == 'south':
            end_times = end_times.filter(rink__contains='South')
        else:
            end_times = end_times.exclude(rink__contains='Meeting/Party Room')

        resurface_times = []
        for item in end_times:
            resurface_times.append(date.isoformat(datetime.now())+" "+item['end_time'].strftime('%H:%M:%S'))
        context['resurface_times'] = resurface_times
        return context
        