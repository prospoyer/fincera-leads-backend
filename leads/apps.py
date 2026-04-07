import sys
from pathlib import Path
from django.apps import AppConfig


class LeadsConfig(AppConfig):
    name = "leads"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Skip during manage.py commands that don't need the DB (migrate, makemigrations, etc.)
        skip_cmds = {"migrate", "makemigrations", "check", "shell", "collectstatic"}
        if any(cmd in sys.argv for cmd in skip_cmds):
            return

        # Ensure pipeline tables (orgs, contacts) exist in leads.db
        # These are managed=False in Django, so migrations don't create them.
        # db.py owns their schema.
        project_root = Path(__file__).resolve().parents[2]
        if project_root not in sys.path:
            sys.path.insert(0, str(project_root))
        try:
            import db as pipeline_db
            pipeline_db.init_db()
        except Exception as e:
            print(f"[leads] Warning: could not init pipeline DB tables: {e}")
