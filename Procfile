web: mkdir -p /data && python manage.py migrate --run-syncdb && gunicorn fincera_project.wsgi --bind 0.0.0.0:$PORT --workers 2
