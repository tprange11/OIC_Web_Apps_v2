from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from schedule.services.ingest import run_schedule_ingest


class Command(BaseCommand):
    help = "Run schedule ingest (safe, snapshot-based)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run ingest without writing snapshots",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=3,
            help="How many days ahead to ingest",
        )
        parser.add_argument(
            "--triggered-by",
            default="manual",
            help="manual | scheduled | preview",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        days = options["days"]
        triggered_by = options["triggered_by"]

        run = run_schedule_ingest(
            triggered_by=triggered_by,
            dry_run=dry_run,
            user=None,  # PythonAnywhere / cron safe
            days_ahead=days,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingest run {run.run_id} completed "
                f"(dry_run={dry_run}, success={run.success})"
            )
        )
