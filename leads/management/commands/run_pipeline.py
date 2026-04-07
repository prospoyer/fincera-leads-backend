"""
Django management command to run pipeline stages.

Usage:
  python manage.py run_pipeline --stage discover --states CA TX NY
  python manage.py run_pipeline --stage all --revenue-min 500000 --revenue-max 3000000
  python manage.py run_pipeline --stage discover --max-orgs 100 --run-id 42
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
        parser.add_argument("--stage", choices=["discover", "enrich", "scrape", "emails", "export", "all"], default="all")
        parser.add_argument("--run-id", type=int, default=None)
        parser.add_argument("--states", nargs="+", default=None, help="e.g. --states CA TX NY")
        parser.add_argument("--revenue-min", type=int, default=None, help="Min annual revenue filter")
        parser.add_argument("--revenue-max", type=int, default=None, help="Max annual revenue filter")
        parser.add_argument("--max-orgs", type=int, default=None, help="Max orgs to discover per run")

    def handle(self, *args, **options):
        from leads.models import PipelineRun
        import db as pipeline_db
        import pipeline as p
        import config

        stage       = options["stage"]
        run_id      = options["run_id"]
        states      = options["states"] or config.TARGET_STATES
        revenue_min = options["revenue_min"] or config.REVENUE_MIN
        revenue_max = options["revenue_max"] or config.REVENUE_MAX
        max_orgs    = options["max_orgs"] or config.MAX_ORGS

        if run_id:
            try:
                run = PipelineRun.objects.get(id=run_id)
            except PipelineRun.DoesNotExist:
                run = PipelineRun.objects.create(stage=stage, status="running")
        else:
            run = PipelineRun.objects.create(stage=stage, status="running")

        self.stdout.write(
            f"[pipeline] run_id={run.id} stage={stage} states={states} "
            f"revenue={revenue_min}-{revenue_max} max_orgs={max_orgs}"
        )

        try:
            pipeline_db.init_db()

            if stage in ("discover", "all"):
                # Process in batches of 5 states to avoid long-running requests
                batch_size = 5
                total = 0
                for i in range(0, len(states), batch_size):
                    batch = states[i:i + batch_size]
                    self.stdout.write(f"[pipeline] discover batch {i//batch_size + 1}: {batch}")
                    added = p.stage_discover(
                        states=batch,
                        revenue_min=revenue_min,
                        revenue_max=revenue_max,
                        max_orgs=max_orgs,
                    )
                    total += added
                    if max_orgs and total >= max_orgs:
                        break

            if stage in ("enrich", "all"):
                p.stage_enrich()
            if stage in ("scrape", "all"):
                p.stage_scrape()
            if stage in ("emails", "all"):
                p.stage_emails()
            if stage in ("export", "all"):
                p.stage_export()

            run.status     = "completed"
            run.ended_at   = datetime.now()
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
