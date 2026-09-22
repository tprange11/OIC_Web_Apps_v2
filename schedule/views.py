"""Rink resurface schedule pages, the schedule JSON API, the legacy "Update Schedule"
scraper trigger, and the ingest-run review pages."""
from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from . import models
from datetime import datetime, date, timedelta
# Importing scrape_schedule runs django.setup() and appends to sys.path at import time.
from .scrape_schedule import get_schedule_data, process_data, add_locker_rooms_to_schedule, \
        add_schedule_to_model, oic_schedule

from rest_framework.generics import ListAPIView
from .serializers import RinkScheduleSerializer
from schedule.services.ingest import run_schedule_ingest


class ChooseRink(LoginRequiredMixin, TemplateView):
    '''Landing page: pick North, South, both, or both side by side.'''
    template_name = 'choose_rink.html'


class RinkScheduleListView(LoginRequiredMixin, ListView):
    '''Today's remaining events for the requested rink, plus the start/end time lists
    the countdown JS (static/js/schedule*.js) uses to work out the next resurface.

    `rink` is north, south, both, or separate. For "separate" the queryset is a dict
    with a north and a south queryset rather than a single queryset.
    '''
    template_name = 'rinkschedule_list.html'
    model = models.RinkSchedule

    def get_queryset(self, **kwargs):
        # Events that have not ended yet today (naive local time).
        todays_date = date.isoformat(datetime.today())
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
        context['rink'] = self.kwargs['rink']
        north_start_times = []
        south_start_times = []
        north_end_times = []
        south_end_times = []
        todays_date = date.isoformat(datetime.today())

        # Upcoming start times; the JS compares these to end times to detect
        # back-to-back events (no resurface in between).
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

        # End times are the resurface times.
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

        # Format as "YYYY-MM-DD HH:MM:SS" strings for the JavaScript countdown timer
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

        # Same formatting for the resurface (end) times
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


@staff_member_required
def scrape_schedule(request):
    '''"Update Schedule" button handler: re-runs the legacy scraper for today (and, on
    Fridays, the weekend) so the resurface schedule picks up online changes.

    This is a trimmed copy of the __main__ block in scrape_schedule.py without the
    OCHL/OWHL team-name merge. Unlike that script it never calls process_data() for
    today, so on weekdays oic_schedule is empty and nothing is written; only the
    Friday weekend branch actually adds rows. Rows are inserted, never replaced, so
    an event whose time changed keeps its old row (unique_together skips the new one).
    '''

    todays_date = date.today()
    formatted_date = date.isoformat(todays_date)
    start_date = f"{formatted_date[5:7]}/{formatted_date[8:]}/{formatted_date[0:4]}"
    data_removed = False # add_schedule_to_model() purges old rows only on its first call

    # Weekends are skipped; Friday's run covers Saturday and Sunday
    if date.weekday(date.today()) not in [5, 6]:
        data = get_schedule_data(start_date, start_date)
        add_locker_rooms_to_schedule()
        add_schedule_to_model(oic_schedule, data_removed)
        data_removed = True
        oic_schedule.clear()

        if date.weekday(date.today()) == 4:
            saturday = (date.today() + timedelta(days=1)).strftime("%m/%d/%Y")
            process_data(data, saturday)
            sunday = (date.today() + timedelta(days=2)).strftime("%m/%d/%Y")
            process_data(data, sunday)

            add_locker_rooms_to_schedule()
            add_schedule_to_model(oic_schedule, data_removed)
            oic_schedule.clear()

    messages.add_message(request, messages.SUCCESS, 'Rink Resurface Schedule has been updated.')
    return redirect('schedule:choose-rink')


class RinkScheduleListAPIView(ListAPIView):
    '''JSON schedule for one day: ?date=YYYY-MM-DD, defaulting to today.'''

    serializer_class = RinkScheduleSerializer

    def get_queryset(self):
        requested_date = self.request.query_params.get('date')

        if requested_date:
            return models.RinkSchedule.objects.filter(
                schedule_date=requested_date
            ).order_by('start_time')

        return models.RinkSchedule.objects.filter(
            schedule_date=date.today()
        ).order_by('start_time')


# Ingest pipeline review pages: staff only.
from django.shortcuts import render, get_object_or_404
from schedule.models import ScheduleIngestRun
from schedule.services.diff import diff_runs


@staff_member_required
def run_list(request):
    '''All ingest runs, newest first, with a flag if one is still in progress.'''
    runs = ScheduleIngestRun.objects.order_by("-started_at")

    ingest_in_progress = ScheduleIngestRun.objects.filter(
        completed_at__isnull=True
    ).exists()

    return render(
        request,
        "schedule/run_list.html",
        {
            "runs": runs,
            "ingest_in_progress": ingest_in_progress,
        },
    )



@staff_member_required
def run_detail(request, run_id):
    '''The snapshots captured by a single ingest run.'''
    run = get_object_or_404(ScheduleIngestRun, id=run_id)
    snapshots = run.snapshots.all().order_by(
        "schedule_date", "start_time"
    )
    return render(
        request,
        "schedule/run_detail.html",
        {
            "run": run,
            "snapshots": snapshots,
        },
    )


@staff_member_required
def run_diff(request, run_a, run_b):
    '''Added/removed/changed events between two runs (see services/diff.py).'''
    diff = diff_runs(run_a, run_b)
    return render(
        request,
        "schedule/run_diff.html",
        {
            "run_a": run_a,
            "run_b": run_b,
            "diff": diff,
        },
    )

@staff_member_required
def trigger_ingest(request):
    '''POST handler behind the "Run ingest" button; pulls 1-14 days, optionally as a dry run.'''
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect("schedule:schedule_run_list")

    # Block concurrent runs. A run killed mid-way (worker timeout, restart) leaves
    # completed_at null and blocks every later run until it is fixed in the admin.
    if ScheduleIngestRun.objects.filter(completed_at__isnull=True).exists():
        messages.warning(
            request,
            "A schedule ingest is already running. Please wait."
        )
        return redirect("schedule:schedule_run_list")

    try:
        days = int(request.POST.get("days", 3))
    except (TypeError, ValueError):
        days = 3

    days = max(1, min(days, 14))

    dry_run = request.POST.get("dry_run") == "on"

    run = run_schedule_ingest(
        triggered_by="manual",
        dry_run=dry_run,
        user=request.user,
        days_ahead=days,
    )

    if run.success:
        messages.success(
            request,
            f"{'Dry run' if dry_run else 'Live run'} completed. "
            f"Pulled {days} day(s). Run ID {run.id}."
        )
    else:
        messages.error(
            request,
            f"Schedule ingest failed: {run.notes}"
        )

    return redirect("schedule:schedule_run_list")
