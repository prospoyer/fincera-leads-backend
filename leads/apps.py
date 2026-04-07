import sys
from django.apps import AppConfig


class LeadsConfig(AppConfig):
    name = "leads"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Skip during management commands that don't need the DB
        skip_cmds = {"migrate", "makemigrations", "check", "shell", "collectstatic"}
        if any(cmd in sys.argv for cmd in skip_cmds):
            return

        # Try to init pipeline tables via db.py (works locally where db.py exists).
        # On Railway, db.py isn't deployed — tables are created by migration 0002 instead.
        from pathlib import Path
        project_root = str(Path(__file__).resolve().parents[2])
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        try:
            import db as pipeline_db
            pipeline_db.init_db()
        except ImportError:
            pass  # db.py not available (Railway) — migration 0002 handles table creation
        except Exception as e:
            print(f"[leads] Warning: pipeline DB init: {e}")
