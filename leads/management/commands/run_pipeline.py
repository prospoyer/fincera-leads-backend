"""
Django management command that runs pipeline stages.
Wraps the existing pipeline.py functions so they can be run via:
  python manage.py run_pipeline --stage discover
"""
import sys
from pathlib import Path
from datetime import datetime

from django.core.management.base import BaseCommand

# Add the project root to path so pipeline modules are importable
PROJECT_ROOT = str(Path(__file__).resolve().parents[4])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class Command(BaseCommand):
    help = "Run a pipeline stage (discover | enrich | scrape | emails | export | all)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--stage",
            choices=["discover", "enrich", "scrape", "emails", "export", "all"],
            default="all",
        )

    def handle(self, *args, **options):
        from leads.models import PipelineRun

        stage = options["stage"]
        self.stdout.write(f"[pipeline] Starting stage: {stage}")

        run = PipelineRun.objects.create(stage=stage, status="running")

        try:
            import pipeline as p
            import db
            db.init_db()

            if stage == "discover" or stage == "all":
                p.stage_discover()
            if stage == "enrich" or stage == "all":
                p.stage_enrich()
            if stage == "scrape" or stage == "all":
                p.stage_scrape()
            if stage == "emails" or stage == "all":
                p.stage_emails()
            if stage == "export" or stage == "all":
                p.stage_export()

            run.status = "completed"
            run.ended_at = datetime.now()
            run.orgs_found = db.get_org_count()
            run.save()

            self.stdout.write(self.style.SUCCESS(f"[pipeline] Stage '{stage}' completed."))

        except Exception as e:
            run.status = "failed"
            run.log = str(e)
            run.ended_at = datetime.now()
            run.save()
            self.stderr.write(f"[pipeline] Failed: {e}")
            raise
