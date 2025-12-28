from django.db import models

# Create your models here.

class RinkSchedule(models.Model):
    '''Model that holds daily rink schedule.'''
    schedule_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    rink = models.CharField(max_length=15)
    event = models.CharField(max_length=100, help_text="Field format for two teams: Put home team first and separate with \' vs \', a space then, lowercase vs, then a space")
    home_locker_room = models.CharField(max_length=50, null=True, blank=True)
    visitor_locker_room = models.CharField(max_length=50, null=True, blank=True)
    notes = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['end_time']
        unique_together = ['schedule_date', 'start_time', 'end_time', 'rink']
        verbose_name_plural = 'Rink Schedule'

    def __str__(self):
        return f"{self.schedule_date} Start: {self.start_time}, End: {self.end_time}, Rink: {self.rink}, Event: {self.event}, Notes: {self.notes}"

# ================================
# NEW MODELS – DO NOT MODIFY ABOVE
# ================================

import uuid
from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class AuditModel(models.Model):
    """
    Abstract base model for created/updated tracking.
    Safe for cron, manual runs, and system tasks.
    """
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_dt = models.DateTimeField(auto_now_add=True)

    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_dt = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ScheduleIngestRun(AuditModel):
    """
    One record per ingest execution (manual, scheduled, preview, rollback).
    """
    run_id = models.UUIDField(default=uuid.uuid4, unique=True)
    triggered_by = models.CharField(
        max_length=50,
        help_text="manual | scheduled | preview | rollback"
    )
    dry_run = models.BooleanField(default=False)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    success = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

class RinkScheduleSnapshot(AuditModel):
    """
    Immutable snapshot of schedule data for a single ingest run.
    """
    run = models.ForeignKey(
        ScheduleIngestRun,
        on_delete=models.CASCADE,
        related_name="snapshots"
    )

    schedule_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    rink = models.CharField(max_length=50)
    event = models.CharField(max_length=255)

    home_locker_room = models.CharField(max_length=10, blank=True)
    visitor_locker_room = models.CharField(max_length=10, blank=True)

    locker_reason = models.TextField()
    locker_evaluation = models.JSONField(default=list)

    class Meta:
        unique_together = (
            "run",
            "schedule_date",
            "start_time",
            "rink",
        )
        ordering = ["schedule_date", "start_time"]


class LockerRoomRule(AuditModel):
    """
    Configurable locker room assignment rules.
    Evaluated in ascending priority order.
    """
    active = models.BooleanField(default=True)
    priority = models.IntegerField(help_text="Lower number = higher priority")

    rink = models.CharField(
        max_length=20,
        help_text="North, South, or Any"
    )
    event_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional match on event type (e.g. Game)"
    )
    team_contains = models.CharField(
        max_length=100,
        blank=True,
        help_text="Substring match on team/event name"
    )

    home_locker_room = models.CharField(max_length=10, blank=True)
    visitor_locker_room = models.CharField(max_length=10, blank=True)

    lock_during_games = models.BooleanField(
        default=True,
        help_text="Prevent edits during active games"
    )

    class Meta:
        ordering = ["priority"]

    def __str__(self):
        return f"{self.team_contains} ({self.rink}) [P{self.priority}]"



class ScheduleRunAcknowledgment(models.Model):
    """
    Records that ops has reviewed and approved a run.
    """
    run = models.ForeignKey(
        ScheduleIngestRun,
        on_delete=models.CASCADE,
        related_name="acknowledgments"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("run", "user")

class NameNormalizationRule(models.Model):
    priority = models.PositiveIntegerField(
        help_text="Lower number = higher priority"
    )
    match_text = models.CharField(
        max_length=255,
        help_text="Substring to match (case-insensitive)",
    )
    replace_with = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Replacement text (leave blank to delete)",
    )
    active = models.BooleanField(default=True)

    created_by = models.CharField(max_length=150, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=150, blank=True)
    updated_dt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority"]

    def __str__(self):
        return f"{self.match_text} → {self.replace_with}"



