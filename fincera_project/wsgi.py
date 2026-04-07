import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fincera_project.settings")

# Run migrations on startup so tables always exist, regardless of start command
import django
django.setup()
from django.core.management import call_command
try:
    call_command("migrate", "--run-syncdb", verbosity=1)
except Exception as e:
    print(f"[wsgi] Migration warning: {e}")

application = get_wsgi_application()
