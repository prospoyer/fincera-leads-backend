"""
Django management command to run pipeline stages.
Updates the PipelineRun record created by the API trigger (via --run-id),
or creates a new one when run directly from the CLI.

Usage:
  python manage.py run_pipeline --stage discover
  python manage.py run_pipeline --stage all
  python manage.py run_pipeline --stage enrich --run-id 42
"""
import sys
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class Command(BaseCommand):
    help = "Run a pipeline stage and update the PipelineRun record."

    def add_arguments(self, parser):
        parser.add_argument(
            "--stage",
            choices=["discover", "enrich", "scrape", "emails", "export", "all"],
            default="all",
        )
        parser.add_argument(
            "--run-id",
            type=int,
            default=None,
            help="ID of an existing PipelineRun to update (created by the API trigger).",
        )

    def handle(self, *args, **options):
        from leads.models import PipelineRun
        import db as pipeline_db
        import pipeline as p

        stage  = options["stage"]
        run_id = options["run_id"]

        # Use existing run if provided, otherwise create one (CLI direct use)
        if run_id:
            try:
                run = PipelineRun.objects.get(id=run_id)
            except PipelineRun.DoesNotExist:
                run = PipelineRun.objects.create(stage=stage, status="running")
        else:
            run = PipelineRun.objects.create(stage=stage, status="running")

        self.stdout.write(f"[pipeline] run_id={run.id} stage={stage}")

        try:
            pipeline_db.init_db()

            if stage in ("discover", "all"):
                p.stage_discover()
            if stage in ("enrich", "all"):
                p.stage_enrich()
            if stage in ("scrape", "all"):
                p.stage_scrape()
            if stage in ("emails", "all"):
                p.stage_emails()
            if stage in ("export", "all"):
                p.stage_export()

            run.status    = "completed"
            run.ended_at  = datetime.now()
            run.orgs_found = pipeline_db.get_org_count()
            run.save()

            self.stdout.write(self.style.SUCCESS(f"[pipeline] '{stage}' completed."))

        except Exception as e:
            run.status   = "failed"
            run.log      = str(e)
            run.ended_at = datetime.now()
            run.save()
            self.stderr.write(f"[pipeline] Failed: {e}")
            raise
